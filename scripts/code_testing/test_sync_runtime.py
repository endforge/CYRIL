"""
AlphaOmega Synchronization Runtime Test

Purpose:
    Verifies that the production synchronization runtime can be constructed
    and reached through its UI-independent interaction boundary.

Test Scope:
    - Construct the complete production synchronization runtime.
    - Confirm the returned application boundary is available.
    - Perform a read-only Source listing through the interaction service.
    - Confirm enabled Sources can be returned.

Does NOT:
    - Request synchronization.
    - Create a Processing Job.
    - Create a Synchronization Run.
    - Reserve synchronization scope.
    - Retrieve Source-of-Truth content.
    - Modify the Canonical Knowledge Repository.
"""

import sys

from pathlib import Path


# ============================================================================
# Project Root
# ============================================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================================
# Production Runtime
# ============================================================================

from scripts.application.sync_runtime import (
    build_sync_runtime,
)


# ============================================================================
# Test Configuration
# ============================================================================

PIPELINE_VERSION = (
    "lab8-runtime-composition-test"
)


# ============================================================================
# Runtime Construction
# ============================================================================

print()
print(
    "AlphaOmega Synchronization Runtime Test"
)
print(
    "======================================="
)
print()

print(
    "Building production synchronization runtime..."
)

runtime = (
    build_sync_runtime(
        pipeline_version=(
            PIPELINE_VERSION
        )
    )
)

print(
    "Runtime construction: PASS"
)

print()


# ============================================================================
# Interaction Boundary
# ============================================================================

runtime_class_name = (
    runtime.__class__.__name__
)

print(
    "Runtime boundary:",
    runtime_class_name,
)

if (
    runtime_class_name
    != "SynchronizationInteractionService"
):
    raise RuntimeError(
        "Production runtime did not return "
        "SynchronizationInteractionService."
    )

print(
    "Interaction boundary: PASS"
)

print()


# ============================================================================
# Read-Only Source Listing
# ============================================================================

print(
    "Requesting registered Sources "
    "through the interaction boundary..."
)

sources = (
    runtime.list_sources()
)

if sources is None:
    raise RuntimeError(
        "Source listing returned None."
    )

if not isinstance(
    sources,
    (
        tuple,
        list,
    ),
):
    raise RuntimeError(
        "Source listing returned an "
        "unexpected collection type."
    )

print(
    "Source listing: PASS"
)

print()

print(
    "Enabled Sources:",
    len(
        sources
    ),
)

for source in sources:

    if not isinstance(
        source,
        dict,
    ):
        raise RuntimeError(
            "Source listing contains an "
            "invalid Source record."
        )

    source_id = (
        source.get(
            "source_id"
        )
    )

    source_name = (
        source.get(
            "name"
        )
    )

    if (
        source_id is None
        or not str(
            source_id
        ).strip()
    ):
        raise RuntimeError(
            "Source record is missing source_id."
        )

    if (
        source_name is None
        or not str(
            source_name
        ).strip()
    ):
        raise RuntimeError(
            "Source record is missing name."
        )

    print(
        " -",
        source_name,
        "|",
        source_id,
    )


# ============================================================================
# Final Result
# ============================================================================

print()
print(
    "Synchronization Runtime: PASS"
)
print()