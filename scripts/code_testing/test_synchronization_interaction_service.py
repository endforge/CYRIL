"""
AlphaOmega Synchronization Interaction Service Test

Purpose:
    Validate the UI-independent synchronization interaction boundary.

Validates:
    - Source listing is delegated to SourceBrowsingService.
    - Source browsing is delegated to SourceBrowsingService.
    - Entire OneDrive is presented as not selectable.
    - OneDrive descendants are presented as selectable.
    - Entire OneNote is presented as selectable.
    - OneNote descendants are presented as selectable.
    - Synchronization selection is converted into a
      SynchronizationRequest.
    - Synchronization execution is delegated to
      SynchronizationApplicationService.
    - Metadata is preserved across the interaction boundary.
    - Required dependencies are enforced.

Does NOT:
    - Access the database.
    - Communicate with a Source of Truth.
    - Execute the production synchronization pipeline.
    - Test authoritative synchronization policy enforcement.
    - Test pywebview or any other UI technology.
"""

from scripts.application.synchronization_interaction_service import (
    SynchronizationInteractionService,
)
from scripts.sync.sync_request import (
    SynchronizationRequest,
)


SOURCE_ID = "source-123"
SOURCE_CONTAINER_ID = "container-456"
CHILD_CONTAINER_ID = "container-789"


class FakeSourceBrowsingService:

    def __init__(
        self,
        *,
        source_name="onenote",
    ):
        self.source_name = source_name
        self.list_sources_called = False
        self.browse_source_id = None

    def list_sources(
        self,
    ):
        self.list_sources_called = True

        return (
            {
                "source_id":
                    SOURCE_ID,

                "name":
                    self.source_name,
            },
        )

    def browse_source(
        self,
        source_id,
    ):
        self.browse_source_id = source_id

        return {
            "source": {
                "source_id":
                    source_id,

                "name":
                    self.source_name,
            },

            "container_count":
                2,

            "roots": (
                {
                    "source_container_id":
                        SOURCE_CONTAINER_ID,

                    "name":
                        "Entire Source",

                    "children": (
                        {
                            "source_container_id":
                                CHILD_CONTAINER_ID,

                            "name":
                                "Child Container",

                            "children":
                                (),
                        },
                    ),
                },
            ),
        }


class FakeSynchronizationApplicationService:

    def __init__(
        self,
    ):
        self.request = None
        self.metadata = None

    def execute(
        self,
        request,
        *,
        metadata=None,
    ):
        self.request = request
        self.metadata = metadata

        return {
            "status":
                "completed",
        }


def create_interaction_service(
    *,
    source_name,
):
    """
    Create one isolated interaction service and its test doubles.
    """

    browsing_service = (
        FakeSourceBrowsingService(
            source_name=source_name,
        )
    )

    application_service = (
        FakeSynchronizationApplicationService()
    )

    interaction_service = (
        SynchronizationInteractionService(
            source_browsing_service=(
                browsing_service
            ),

            synchronization_application_service=(
                application_service
            ),
        )
    )

    return (
        interaction_service,
        browsing_service,
        application_service,
    )


def main():

    # -------------------------------------------------
    # OneNote interaction service
    # -------------------------------------------------

    (
        interaction_service,
        browsing_service,
        application_service,
    ) = create_interaction_service(
        source_name="onenote",
    )

    # -------------------------------------------------
    # Source listing
    # -------------------------------------------------

    sources = (
        interaction_service
        .list_sources()
    )

    assert (
        browsing_service
        .list_sources_called
        is True
    )

    assert (
        sources[0][
            "source_id"
        ]
        == SOURCE_ID
    )

    print(
        "PASS: Source listing delegated."
    )

    # -------------------------------------------------
    # OneNote source browsing
    # -------------------------------------------------

    browse_result = (
        interaction_service
        .browse_source(
            SOURCE_ID
        )
    )

    assert (
        browsing_service
        .browse_source_id
        == SOURCE_ID
    )

    assert (
        browse_result[
            "source"
        ][
            "source_id"
        ]
        == SOURCE_ID
    )

    print(
        "PASS: Source browsing delegated."
    )

    onenote_root = (
        browse_result[
            "roots"
        ][0]
    )

    onenote_child = (
        onenote_root[
            "children"
        ][0]
    )

    assert (
        onenote_root[
            "selectable"
        ]
        is True
    )

    assert (
        onenote_child[
            "selectable"
        ]
        is True
    )

    print(
        "PASS: Entire OneNote selectable."
    )

    print(
        "PASS: OneNote descendant selectable."
    )

    # -------------------------------------------------
    # OneDrive source browsing
    # -------------------------------------------------

    (
        onedrive_interaction_service,
        _,
        _,
    ) = create_interaction_service(
        source_name="onedrive",
    )

    onedrive_result = (
        onedrive_interaction_service
        .browse_source(
            SOURCE_ID
        )
    )

    onedrive_root = (
        onedrive_result[
            "roots"
        ][0]
    )

    onedrive_child = (
        onedrive_root[
            "children"
        ][0]
    )

    assert (
        onedrive_root[
            "selectable"
        ]
        is False
    )

    assert (
        onedrive_child[
            "selectable"
        ]
        is True
    )

    print(
        "PASS: Entire OneDrive not selectable."
    )

    print(
        "PASS: OneDrive descendant selectable."
    )

    # -------------------------------------------------
    # Synchronization request creation
    # -------------------------------------------------

    metadata = {
        "requested_by":
            "interaction-test",
    }

    result = (
        interaction_service
        .synchronize(
            source_id=SOURCE_ID,

            source_container_id=(
                CHILD_CONTAINER_ID
            ),

            metadata=metadata,
        )
    )

    assert isinstance(
        application_service.request,
        SynchronizationRequest,
    )

    assert (
        application_service
        .request
        .source_id
        == SOURCE_ID
    )

    assert (
        application_service
        .request
        .source_container_id
        == CHILD_CONTAINER_ID
    )

    assert (
        application_service.metadata
        == metadata
    )

    assert (
        result[
            "status"
        ]
        == "completed"
    )

    print(
        "PASS: Synchronization request created."
    )

    print(
        "PASS: Synchronization delegated."
    )

    print(
        "PASS: Metadata preserved."
    )

    # -------------------------------------------------
    # Required dependency validation
    # -------------------------------------------------

    try:

        SynchronizationInteractionService(
            source_browsing_service=None,

            synchronization_application_service=(
                application_service
            ),
        )

        raise AssertionError(
            "Missing browsing service was accepted."
        )

    except ValueError:
        pass

    try:

        SynchronizationInteractionService(
            source_browsing_service=(
                browsing_service
            ),

            synchronization_application_service=None,
        )

        raise AssertionError(
            "Missing synchronization application "
            "service was accepted."
        )

    except ValueError:
        pass

    print(
        "PASS: Required dependencies enforced."
    )

    print()
    print(
        "Synchronization Interaction Service: PASS"
    )


if __name__ == "__main__":
    main()