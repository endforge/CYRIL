"""
AIOS pywebview Synchronization API Test

Purpose:
    Validate the pywebview synchronization adapter independently
    from pywebview and AlphaOmega production services.

Validates:
    - Source listing is delegated to the interaction service.
    - Source browsing is delegated to the interaction service.
    - Synchronization is delegated to the interaction service.
    - Python tuples are converted to JSON-safe lists.
    - Nested hierarchy data is converted recursively.
    - pywebview request metadata is supplied by the adapter.
    - Required dependency validation is enforced.

Does NOT:
    - Start pywebview.
    - Display a graphical interface.
    - Access the database.
    - Communicate with a Source of Truth.
    - Execute production synchronization.
"""


from scripts.ui.pywebview.synchronization_api import (
    SynchronizationApi,
)


SOURCE_ID = "source-123"
ROOT_CONTAINER_ID = "container-root"
CHILD_CONTAINER_ID = "container-child"


class FakeSynchronizationInteractionService:

    def __init__(
        self,
    ):
        self.list_sources_called = False
        self.browse_source_id = None
        self.synchronize_source_id = None
        self.synchronize_source_container_id = None
        self.synchronize_metadata = None

    def list_sources(
        self,
    ):
        self.list_sources_called = True

        return (
            {
                "source_id":
                    SOURCE_ID,

                "name":
                    "onenote",
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
                    "onenote",
            },

            "container_count":
                2,

            "roots": (
                {
                    "source_container_id":
                        ROOT_CONTAINER_ID,

                    "name":
                        "Entire Source",

                    "selectable":
                        True,

                    "children": (
                        {
                            "source_container_id":
                                CHILD_CONTAINER_ID,

                            "name":
                                "Notebook",

                            "selectable":
                                True,

                            "children":
                                (),
                        },
                    ),
                },
            ),
        }

    def synchronize(
        self,
        *,
        source_id,
        source_container_id,
        metadata=None,
    ):
        self.synchronize_source_id = (
            source_id
        )

        self.synchronize_source_container_id = (
            source_container_id
        )

        self.synchronize_metadata = (
            metadata
        )

        return {
            "status":
                "completed",

            "source_id":
                source_id,

            "source_container_id":
                source_container_id,
        }


def main():

    interaction_service = (
        FakeSynchronizationInteractionService()
    )

    api = SynchronizationApi(
        synchronization_interaction_service=(
            interaction_service
        ),
    )

    # -------------------------------------------------
    # Source listing
    # -------------------------------------------------

    sources = (
        api
        .list_sources()
    )

    assert (
        interaction_service
        .list_sources_called
        is True
    )

    assert isinstance(
        sources,
        list,
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

    print(
        "PASS: Source list converted to JSON-safe data."
    )

    # -------------------------------------------------
    # Source browsing
    # -------------------------------------------------

    browse_result = (
        api
        .browse_source(
            SOURCE_ID
        )
    )

    assert (
        interaction_service
        .browse_source_id
        == SOURCE_ID
    )

    assert isinstance(
        browse_result[
            "roots"
        ],
        list,
    )

    root = (
        browse_result[
            "roots"
        ][0]
    )

    assert isinstance(
        root[
            "children"
        ],
        list,
    )

    assert (
        root[
            "children"
        ][0][
            "source_container_id"
        ]
        == CHILD_CONTAINER_ID
    )

    print(
        "PASS: Source browsing delegated."
    )

    print(
        "PASS: Nested hierarchy converted to JSON-safe data."
    )

    # -------------------------------------------------
    # Synchronization
    # -------------------------------------------------

    result = (
        api
        .synchronize(
            SOURCE_ID,
            CHILD_CONTAINER_ID,
        )
    )

    assert (
        interaction_service
        .synchronize_source_id
        == SOURCE_ID
    )

    assert (
        interaction_service
        .synchronize_source_container_id
        == CHILD_CONTAINER_ID
    )

    assert (
        interaction_service
        .synchronize_metadata
        == {
            "requested_by":
                "pywebview",
        }
    )

    assert (
        result[
            "status"
        ]
        == "completed"
    )

    print(
        "PASS: Synchronization delegated."
    )

    print(
        "PASS: pywebview metadata supplied."
    )

    # -------------------------------------------------
    # Required dependency
    # -------------------------------------------------

    try:

        SynchronizationApi(
            synchronization_interaction_service=None,
        )

        raise AssertionError(
            "Missing interaction service was accepted."
        )

    except ValueError:
        pass

    print(
        "PASS: Required dependency enforced."
    )

    print()
    print(
        "Synchronization API: PASS"
    )


if __name__ == "__main__":
    main()