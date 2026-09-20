"""
CYRIL pywebview Synchronization API

Purpose:
    Provides the pywebview-specific adapter between the CYRIL user
    interface and the UI-independent AlphaOmega synchronization
    interaction service.

Responsibilities:
    - Expose synchronization interaction operations to pywebview.
    - Convert application results into data suitable for the
      pywebview JavaScript bridge.
    - Keep pywebview-specific concerns outside AlphaOmega
      application services.

Does NOT:
    - Implement synchronization business rules.
    - Access the database directly.
    - Communicate directly with a Source of Truth.
    - Create SynchronizationRequest objects.
    - Perform synchronization admission.
    - Detect synchronization conflicts.
    - Execute the synchronization pipeline.
    - Determine authoritative synchronization policy.
"""

from dataclasses import asdict
from dataclasses import is_dataclass
from datetime import date
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class SynchronizationApi:
    """
    Expose synchronization interaction capabilities to pywebview.
    """

    def __init__(
        self,
        *,
        synchronization_interaction_service,
    ):
        """
        Initialize the pywebview synchronization adapter.
        """

        if synchronization_interaction_service is None:
            raise ValueError(
                "synchronization_interaction_service is required."
            )

        self._synchronization_interaction_service = (
            synchronization_interaction_service
        )

    def list_sources(
        self,
    ):
        """
        Return Sources available for synchronization.
        """

        sources = (
            self
            ._synchronization_interaction_service
            .list_sources()
        )

        return self._to_json_safe(
            sources
        )

    def browse_source(
        self,
        source_id,
    ):
        """
        Return the synchronization interaction model for one Source.
        """

        result = (
            self
            ._synchronization_interaction_service
            .browse_source(
                source_id
            )
        )

        return self._to_json_safe(
            result
        )

    def synchronize(
        self,
        source_id,
        source_container_id,
    ):
        """
        Submit one Source Container synchronization request.
        """

        result = (
            self
            ._synchronization_interaction_service
            .synchronize(
                source_id=source_id,
                source_container_id=(
                    source_container_id
                ),
                metadata={
                    "requested_by":
                        "pywebview",
                },
            )
        )

        return self._to_json_safe(
            result
        )

    def refresh_container_inventory(self, source_id):
        """Refresh one complete Source inventory through the application boundary."""
        result = self._synchronization_interaction_service.refresh_container_inventory(
            source_id=source_id,
            metadata={"requested_by": "pywebview"},
        )
        return self._to_json_safe(result)

    @staticmethod
    def _to_json_safe(
        value,
    ):
        """
        Convert application-facing Python values into structures
        suitable for the pywebview JavaScript bridge.

        AlphaOmega application services remain free to use their
        normal Python-facing contracts.
        """

        # ----------------------------------------------------
        # Values already safe for JSON
        # ----------------------------------------------------

        if (
            value is None
            or isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            )
        ):
            return value

        # ----------------------------------------------------
        # Common AlphaOmega / Python scalar types
        # ----------------------------------------------------

        if isinstance(
            value,
            UUID,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            (
                datetime,
                date,
            ),
        ):
            return value.isoformat()

        if isinstance(
            value,
            Path,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            Enum,
        ):
            return (
                SynchronizationApi
                ._to_json_safe(
                    value.value
                )
            )

        # ----------------------------------------------------
        # Dataclasses
        # ----------------------------------------------------

        if (
            is_dataclass(value)
            and not isinstance(
                value,
                type,
            )
        ):
            return (
                SynchronizationApi
                ._to_json_safe(
                    asdict(value)
                )
            )

        # ----------------------------------------------------
        # Mapping structures
        # ----------------------------------------------------

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key):
                    SynchronizationApi._to_json_safe(
                        item
                    )
                for key, item
                in value.items()
            }

        # ----------------------------------------------------
        # Collection structures
        # ----------------------------------------------------

        if isinstance(
            value,
            (
                tuple,
                list,
                set,
                frozenset,
            ),
        ):
            return [
                SynchronizationApi._to_json_safe(
                    item
                )
                for item
                in value
            ]

        # ----------------------------------------------------
        # Unsupported type
        # ----------------------------------------------------

        raise TypeError(
            "SynchronizationApi cannot convert "
            f"{type(value).__name__} "
            "to a JSON-safe value."
        )