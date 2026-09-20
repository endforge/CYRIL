"""
AlphaOmega Discovery Batch Test

Purpose:
    Verify that Discovery retrieves Knowledge Objects in bounded batches
    without changing synchronization decisions.

Verifies:
    - Multiple records are retrieved with fewer database requests.
    - Requests respect the configured batch size.
    - Full result pages are retrieved through pagination.
    - Missing identities are not returned as existing objects.
    - Duplicate source identities are rejected.
    - Database failures are not interpreted as NEW objects.
    - Discovery preserves NEW, MODIFIED, and UNCHANGED classification.
    - Discovery preserves correlation identity and previous content hashes.

Does NOT:
    - Connect to the live database.
    - Modify Knowledge Objects.
    - Perform Extraction or Load.
    - Test HTTP/2 connection recovery.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from scripts.database.knowledge_object_repository import (
    KnowledgeObjectRepository,
)
from scripts.discovery.discovery_service import DiscoveryService
from scripts.sync.sync_exceptions import DiscoveryError
from scripts.sync.sync_state import SyncState
from scripts.translator.translator_record import TranslatorRecord
from scripts.translator.translator_section import TranslatorSection


SOURCE_ID = "test-source-id"
SOURCE_NAME = "OneNote"
MODIFIED_AT = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


class FakeQuery:
    """Implement the Supabase query operations used by batch retrieval."""

    def __init__(self, client):
        self.client = client
        self.filters = {}
        self.requested_ids = []
        self.start = 0
        self.end = 0

    def select(self, fields):
        self.fields = fields
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def in_(self, field, values):
        if field != "source_object_id":
            raise AssertionError(f"Unexpected IN field: {field}")

        self.requested_ids = list(values)
        return self

    def order(self, field):
        return self

    def range(self, start, end):
        self.start = start
        self.end = end
        return self

    def execute(self):
        self.client.request_count += 1

        self.client.request_sizes.append(
            len(self.requested_ids)
        )

        if self.client.fail_on_request == self.client.request_count:
            raise ConnectionError("Simulated database connection failure.")

        matching = [
            row
            for row in self.client.rows
            if (
                row["source_id"] == self.filters["source_id"]
                and row["source_object_id"] in self.requested_ids
            )
        ]

        matching.sort(
            key=lambda row: (
                row["source_object_id"],
                row["id"],
            )
        )

        page = matching[self.start:self.end + 1]

        return SimpleNamespace(
            data=[
                {
                    key: value
                    for key, value in row.items()
                    if key != "source_id"
                }
                for row in page
            ]
        )


class FakeClient:
    """Provide controlled Knowledge Object rows and count requests."""

    def __init__(self, rows=None, fail_on_request=None):
        self.rows = list(rows or [])
        self.fail_on_request = fail_on_request
        self.request_count = 0
        self.request_sizes = []

    def table(self, name):
        if name != "knowledge_objects":
            raise AssertionError(f"Unexpected table: {name}")

        return FakeQuery(self)


class FakeSourceRepository:
    """Resolve the test source and count source lookups."""

    def __init__(self):
        self.lookup_count = 0

    def find_id_by_name(self, source_name):
        self.lookup_count += 1

        if source_name != SOURCE_NAME:
            return None

        return SOURCE_ID


def make_row(number, name=None):
    """Build a stored Knowledge Object for repository testing."""

    return {
        "id": f"knowledge-object-{number:04d}",
        "source_id": SOURCE_ID,
        "source_object_id": f"object-{number:04d}",
        "title": name or f"Object {number}",
        "source_parent_object_id": "test-parent",
        "source_modified_at": MODIFIED_AT.isoformat(),
        "content_hash": f"previous-hash-{number}",
    }


def make_translator_record(number, name=None):
    """Build a TranslatorRecord with a unique correlation identity."""

    record = TranslatorRecord()

    record.correlation_id = str(uuid4())
    record.source_name = SOURCE_NAME
    record.source_object_id = f"object-{number:04d}"
    record.source_parent_object_id = "test-parent"
    record.source_modified_at = MODIFIED_AT
    record.name = name or f"Object {number}"

    return record


def make_translator_section(records):
    """Build completed Translator output for Discovery."""

    section = TranslatorSection()
    section.translated_records.extend(records)
    section.translation_succeeded = True
    section.lock()

    return section


def test_bounded_requests():
    """Verify that 205 identities are divided into bounded requests."""

    rows = [make_row(number) for number in range(205)]
    client = FakeClient(rows)
    repository = KnowledgeObjectRepository(client)

    identities = [
        row["source_object_id"]
        for row in rows
    ]

    results = repository.find_by_source_identities(
        source_id=SOURCE_ID,
        source_object_ids=identities,
    )

    assert len(results) == 205
    assert client.request_sizes == [100, 100, 100, 100, 5]
    assert client.request_count == 5

    print("Bounded batch requests PASSED.")


def test_missing_identity():
    """Verify that an absent identity is not returned as existing."""

    client = FakeClient([make_row(1)])
    repository = KnowledgeObjectRepository(client)

    results = repository.find_by_source_identities(
        source_id=SOURCE_ID,
        source_object_ids=[
            "object-0001",
            "object-missing",
        ],
    )

    assert "object-0001" in results
    assert "object-missing" not in results
    assert client.request_count == 1

    print("Missing identity handling PASSED.")


def test_duplicate_requested_identity():
    """Verify that repeated input IDs do not produce extra requests."""

    client = FakeClient([make_row(1)])
    repository = KnowledgeObjectRepository(client)

    results = repository.find_by_source_identities(
        source_id=SOURCE_ID,
        source_object_ids=[
            "object-0001",
            "object-0001",
            "object-0001",
        ],
    )

    assert len(results) == 1
    assert client.request_sizes == [1]
    assert client.request_count == 1

    print("Duplicate input handling PASSED.")


def test_duplicate_database_identity():
    """Verify that duplicate stored identities cause a failure."""

    first = make_row(1)
    second = dict(first)
    second["id"] = "duplicate-knowledge-object"

    client = FakeClient([first, second])
    repository = KnowledgeObjectRepository(client)

    try:
        repository.find_by_source_identities(
            source_id=SOURCE_ID,
            source_object_ids=["object-0001"],
        )
    except RuntimeError as error:
        assert "Multiple Knowledge Objects" in str(error)
    else:
        raise AssertionError(
            "Duplicate database identities were not rejected."
        )

    print("Duplicate database identity detection PASSED.")


def test_repository_failure():
    """Verify that a failed batch request raises an exception."""

    client = FakeClient(
        rows=[make_row(1)],
        fail_on_request=1,
    )

    repository = KnowledgeObjectRepository(client)

    try:
        repository.find_by_source_identities(
            source_id=SOURCE_ID,
            source_object_ids=["object-0001"],
        )
    except RuntimeError as error:
        assert isinstance(error.__cause__, ConnectionError)
    else:
        raise AssertionError(
            "Repository failure was incorrectly treated as a result."
        )

    print("Repository failure handling PASSED.")


def test_discovery_classification():
    """Verify classification, correlation, and batch integration."""

    client = FakeClient([
        make_row(1),
        make_row(2),
    ])

    source_repository = FakeSourceRepository()
    knowledge_repository = KnowledgeObjectRepository(client)

    service = DiscoveryService(
        source_repository=source_repository,
        knowledge_object_repository=knowledge_repository,
    )

    new_record = make_translator_record(3)
    unchanged_record = make_translator_record(1)
    modified_record = make_translator_record(
        2,
        name="Object 2 Renamed",
    )

    records = [
        new_record,
        unchanged_record,
        modified_record,
    ]

    result = service.run(
        make_translator_section(records)
    )

    assert result.discovery_succeeded is True
    assert result.is_locked
    assert len(result.discovery_records) == 3
    assert not result.record_errors

    new_result, unchanged_result, modified_result = (
        result.discovery_records
    )

    assert new_result.sync_state == SyncState.NEW
    assert new_result.knowledge_object_id is None
    assert new_result.previous_content_hash is None
    assert new_result.requires_extraction is True

    assert unchanged_result.sync_state == SyncState.UNCHANGED
    assert unchanged_result.knowledge_object_id == (
        "knowledge-object-0001"
    )
    assert unchanged_result.previous_content_hash == (
        "previous-hash-1"
    )
    assert unchanged_result.requires_extraction is False

    assert modified_result.sync_state == SyncState.MODIFIED
    assert modified_result.knowledge_object_id == (
        "knowledge-object-0002"
    )
    assert modified_result.previous_content_hash == (
        "previous-hash-2"
    )
    assert modified_result.comparison_reason == "name changed"
    assert modified_result.requires_extraction is True

    for original, discovered in zip(
        records,
        result.discovery_records,
    ):
        assert discovered.correlation_id == original.correlation_id

    assert source_repository.lookup_count == 1
    assert client.request_count == 1

    print("Discovery classification and batch integration PASSED.")


def test_discovery_repository_failure():
    """Verify that a batch failure terminates Discovery."""

    client = FakeClient(
        rows=[make_row(1)],
        fail_on_request=1,
    )

    service = DiscoveryService(
        source_repository=FakeSourceRepository(),
        knowledge_object_repository=KnowledgeObjectRepository(client),
    )

    section = make_translator_section([
        make_translator_record(1),
        make_translator_record(2),
    ])

    try:
        service.run(section)
    except DiscoveryError as error:
        assert isinstance(error.__cause__, RuntimeError)
        assert isinstance(
            error.__cause__.__cause__,
            ConnectionError,
        )
    else:
        raise AssertionError(
            "Discovery incorrectly continued after a batch failure."
        )

    print("Discovery batch failure propagation PASSED.")


def main():
    print("Testing Discovery batch retrieval...\n")

    test_bounded_requests()
    test_missing_identity()
    test_duplicate_requested_identity()
    test_duplicate_database_identity()
    test_repository_failure()
    test_discovery_classification()
    test_discovery_repository_failure()

    print("\nAll Discovery batch tests PASSED.")


if __name__ == "__main__":
    main()