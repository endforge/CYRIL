"""
AlphaOmega Synchronization Interaction Service

Purpose:
    Provides the UI-independent application interface for browsing
    synchronization scope and submitting synchronization requests.

Responsibilities:
    - Expose enabled Sources available for synchronization.
    - Expose the persisted Source Container hierarchy for one Source.
    - Describe whether each Source Container may be selected for
      synchronization through the normal application interaction path.
    - Convert an application-facing Source and Source Container selection
      into a SynchronizationRequest.
    - Submit the SynchronizationRequest through the authoritative
      SynchronizationApplicationService.
    - Provide a stable interaction boundary for replaceable clients such
      as graphical UIs, command-line tools, tests, or future applications.

Does NOT:
    - Perform UI presentation.
    - Depend on pywebview or any other UI technology.
    - Expose source-native Source Container identity to clients.
    - Access the database directly.
    - Communicate directly with a Source of Truth.
    - Determine authoritative synchronization admission.
    - Detect synchronization conflicts.
    - Validate Source-of-Truth state.
    - Create Processing Jobs or Synchronization Runs.
    - Execute the synchronization pipeline directly.
    - Replace authoritative synchronization policy enforcement owned by
      downstream application services.
"""

from scripts.sync.sync_request import (
    SynchronizationRequest,
)


class SynchronizationInteractionService:
    """
    Provide the UI-independent interaction boundary for
    synchronization browsing and execution.
    """

    def __init__(
        self,
        *,
        source_browsing_service,
        synchronization_application_service,
        source_container_refresh_services=None,
    ):
        """
        Initialize interaction dependencies.
        """

        if source_browsing_service is None:
            raise ValueError(
                "source_browsing_service is required."
            )

        if synchronization_application_service is None:
            raise ValueError(
                "synchronization_application_service is required."
            )

        self._source_browsing_service = (
            source_browsing_service
        )

        self._synchronization_application_service = (
            synchronization_application_service
        )

        self._source_container_refresh_services = (
            source_container_refresh_services or {}
        )

    def refresh_container_inventory(self, *, source_id, metadata=None):
        """Refresh the complete inventory for one enabled Source."""
        sources = self.list_sources()
        source = next(
            (item for item in sources
             if str(item.get("source_id")) == str(source_id)),
            None,
        )
        if source is None:
            raise ValueError("Source is not enabled or does not exist.")
        source_name = str(source.get("name", "")).strip().casefold()
        service = self._source_container_refresh_services.get(source_name)
        if service is None:
            raise ValueError("Inventory refresh is not supported for this Source.")
        return service.refresh(source_id=source_id, job_metadata=metadata)

    def list_sources(
        self,
    ):
        """
        Return enabled registered Sources available to an
        application client.
        """

        return (
            self
            ._source_browsing_service
            .list_sources()
        )

    def browse_source(
        self,
        source_id,
    ):
        """
        Return the active persisted Source Container hierarchy
        with synchronization selection capability added.

        The returned model remains UI-independent.
        """

        browsing_result = (
            self
            ._source_browsing_service
            .browse_source(
                source_id
            )
        )

        if not isinstance(
            browsing_result,
            dict,
        ):
            raise RuntimeError(
                "Source browsing returned an invalid result."
            )

        source = browsing_result.get(
            "source"
        )

        if not isinstance(
            source,
            dict,
        ):
            raise RuntimeError(
                "Source browsing result is missing source data."
            )

        source_name = source.get(
            "name"
        )

        if (
            source_name is None
            or not str(
                source_name
            ).strip()
        ):
            raise RuntimeError(
                "Source browsing result is missing source name."
            )

        normalized_source_name = (
            str(
                source_name
            )
            .strip()
            .casefold()
        )

        roots = browsing_result.get(
            "roots"
        )

        if roots is None:
            raise RuntimeError(
                "Source browsing result is missing roots."
            )

        interaction_roots = tuple(
            self._add_selection_capability(
                node,
                source_name=(
                    normalized_source_name
                ),
                is_root=True,
            )
            for node
            in roots
        )

        return {
            "source":
                dict(
                    source
                ),

            "container_count":
                browsing_result.get(
                    "container_count"
                ),

            "roots":
                interaction_roots,
        }

    def synchronize(
        self,
        *,
        source_id,
        source_container_id,
        metadata=None,
    ):
        """
        Submit one selected Source Container for synchronization.

        Selection is converted into the production
        SynchronizationRequest contract.

        Authoritative admission, scope policy, conflict detection,
        Source-of-Truth validation, reservation, and execution remain
        the responsibility of SynchronizationApplicationService.
        """

        request = SynchronizationRequest(
            source_id=source_id,
            source_container_id=(
                source_container_id
            ),
        )

        return (
            self
            ._synchronization_application_service
            .execute(
                request,
                metadata=metadata,
            )
        )

    @staticmethod
    def _add_selection_capability(
        node,
        *,
        source_name,
        is_root,
    ):
        """
        Return one application-facing Source Container node with
        synchronization selection capability.

        Entire OneDrive is not selectable through the normal
        application interaction path.

        Other currently supported Source Container scopes are
        selectable.

        Authoritative enforcement remains downstream in
        SynchronizationApplicationService.
        """

        if not isinstance(
            node,
            dict,
        ):
            raise RuntimeError(
                "Source browsing returned an invalid "
                "Source Container node."
            )

        source_container_id = node.get(
            "source_container_id"
        )

        if (
            source_container_id is None
            or not str(
                source_container_id
            ).strip()
        ):
            raise RuntimeError(
                "Source Container node is missing "
                "source_container_id."
            )

        name = node.get(
            "name"
        )

        if (
            name is None
            or not str(
                name
            ).strip()
        ):
            raise RuntimeError(
                "Source Container node is missing name."
            )

        children = node.get(
            "children"
        )

        if children is None:
            raise RuntimeError(
                "Source Container node is missing children."
            )

        selectable = not (
            source_name == "onedrive"
            and is_root
        )

        interaction_children = tuple(
            SynchronizationInteractionService
            ._add_selection_capability(
                child,
                source_name=source_name,
                is_root=False,
            )
            for child
            in children
        )

        return {
            "source_container_id":
                str(
                    source_container_id
                ).strip(),

            "name":
                str(
                    name
                ).strip(),

            "selectable":
                selectable,

            "children":
                interaction_children,
        }