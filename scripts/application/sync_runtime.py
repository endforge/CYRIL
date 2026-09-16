"""
AlphaOmega Synchronization Runtime

Purpose:
    Composes the production AlphaOmega synchronization components behind
    the UI-independent SynchronizationInteractionService boundary.

Responsibilities:
    - Create the authenticated AlphaOmega database connection.
    - Create repositories required by synchronization.
    - Compose the existing AlphaOmega Knowledge Pipeline.
    - Compose Source Container validation.
    - Compose synchronization conflict detection.
    - Compose synchronization admission.
    - Compose synchronization execution.
    - Compose the production SynchronizationApplicationService.
    - Compose Source browsing.
    - Return the UI-independent SynchronizationInteractionService.

Does NOT:
    - Implement synchronization business rules.
    - Implement Source-specific synchronization behavior.
    - Implement UI presentation.
    - Import or depend on pywebview.
    - Create a graphical application window.
    - Execute synchronization during runtime construction.
"""

# ============================================================
# Security / Database
# ============================================================

from common.security.local_credential_provider import (
    LocalCredentialProvider,
)

from scripts.database.database_connection import (
    DatabaseConnection,
)

from scripts.database.source_repository import (
    SourceRepository,
)

from scripts.database.source_container_repository import (
    SourceContainerRepository,
)

from scripts.database.source_container_refresh_status_repository import (
    SourceContainerRefreshStatusRepository,
)

from scripts.database.sync_run_repository import (
    SyncRunRepository,
)

from scripts.database.processing_job_repository import (
    ProcessingJobRepository,
)

from scripts.database.knowledge_object_repository import (
    KnowledgeObjectRepository,
)

from scripts.database.synchronization_reservation_repository import (
    SynchronizationReservationRepository,
)


# ============================================================
# Knowledge Pipeline
# ============================================================

from scripts.connectors.ms_graph.graph_connector import (
    GraphConnector,
)

from scripts.translator.graph_translator import (
    GraphTranslator,
)

from scripts.discovery.discovery_service import (
    DiscoveryService,
)

from scripts.extraction.extraction_service import (
    ExtractionService,
)

from scripts.load.load_repository import (
    LoadRepository,
)

from scripts.load.load_service import (
    LoadService,
)

from scripts.orchestration.sync_orchestrator import (
    SynchronizationOrchestrator,
)


# ============================================================
# Source Container Validation
# ============================================================

from scripts.connectors.source_container_validator import (
    SourceContainerValidator,
)

from scripts.connectors.ms_graph.onedrive_container_validator import (
    OneDriveContainerValidator,
)

from scripts.connectors.ms_graph.onenote_container_validator import (
    OneNoteContainerValidator,
)


# ============================================================
# Synchronization Application Services
# ============================================================

from scripts.application.source_browsing_service import (
    SourceBrowsingService,
)

from scripts.application.synchronization_admission_service import (
    SynchronizationAdmissionService,
)

from scripts.application.synchronization_scope_conflict_detector import (
    SynchronizationScopeConflictDetector,
)

from scripts.application.synchronization_conflict_service import (
    SynchronizationConflictService,
)

from scripts.application.synchronization_preliminary_conflict_service import (
    SynchronizationPreliminaryConflictService,
)

from scripts.application.synchronization_connector_service import (
    SynchronizationConnectorService,
)

from scripts.application.synchronization_execution_service import (
    SynchronizationExecutionService,
)

from scripts.application.synchronization_application_service import (
    SynchronizationApplicationService,
)

from scripts.application.synchronization_interaction_service import (
    SynchronizationInteractionService,
)


def build_sync_runtime(pipeline_version):
    """
    Build and return the production UI-independent synchronization
    interaction service.

    Runtime construction performs dependency composition only.

    It does not:
        - create a synchronization request
        - reserve synchronization
        - execute synchronization
        - communicate with Microsoft Graph for content enumeration

    Args:
        pipeline_version:
            Non-empty version identifier supplied by the caller and used
            when creating Processing Jobs.

    Returns:
        SynchronizationInteractionService
    """

    # --------------------------------------------------------
    # Validate runtime configuration
    # --------------------------------------------------------

    if not isinstance(pipeline_version, str):
        raise ValueError(
            "pipeline_version must be a string."
        )

    pipeline_version = pipeline_version.strip()

    if not pipeline_version:
        raise ValueError(
            "pipeline_version is required."
        )

    # --------------------------------------------------------
    # Database Infrastructure
    # --------------------------------------------------------

    credential_provider = LocalCredentialProvider()

    database_connection = DatabaseConnection(
        credential_provider
    )

    database_client = database_connection.connect()

    # --------------------------------------------------------
    # Repositories
    # --------------------------------------------------------

    source_repository = SourceRepository(
        database_client
    )

    source_container_repository = SourceContainerRepository(
        database_connection
    )

    source_container_refresh_status_repository = (
        SourceContainerRefreshStatusRepository(
            database_client
        )
    )

    sync_run_repository = SyncRunRepository(
        database_client
    )

    processing_job_repository = ProcessingJobRepository(
        database_client
    )

    knowledge_object_repository = KnowledgeObjectRepository(
        database_client
    )

    load_repository = LoadRepository(
        database_client
    )

    synchronization_reservation_repository = (
        SynchronizationReservationRepository(
            database_client
        )
    )

    # --------------------------------------------------------
    # AlphaOmega Knowledge Pipeline
    # --------------------------------------------------------

    whole_source_connector = GraphConnector()

    translator = GraphTranslator()

    discovery_service = DiscoveryService(
        source_repository,
        knowledge_object_repository,
    )

    extraction_service = ExtractionService()

    load_service = LoadService(
        source_repository,
        load_repository,
    )

    synchronization_orchestrator = (
        SynchronizationOrchestrator(
            connector=whole_source_connector,
            translator=translator,
            discovery_service=discovery_service,
            extraction_service=extraction_service,
            load_service=load_service,
            processing_job_repository=processing_job_repository,
            pipeline_version=pipeline_version,
        )
    )

    # --------------------------------------------------------
    # Source Container Validation
    # --------------------------------------------------------

    source_container_validator = SourceContainerValidator(
        {
            "onedrive": OneDriveContainerValidator(),
            "onenote": OneNoteContainerValidator(),
        }
    )

    # --------------------------------------------------------
    # Synchronization Conflict Detection
    # --------------------------------------------------------

    scope_conflict_detector = (
        SynchronizationScopeConflictDetector()
    )

    synchronization_conflict_service = (
        SynchronizationConflictService(
            sync_run_repository=sync_run_repository,
            source_container_repository=source_container_repository,
            scope_conflict_detector=scope_conflict_detector,
        )
    )

    preliminary_conflict_service = (
        SynchronizationPreliminaryConflictService(
            refresh_status_repository=(
                source_container_refresh_status_repository
            ),
            synchronization_conflict_service=(
                synchronization_conflict_service
            ),
        )
    )

    # --------------------------------------------------------
    # Synchronization Admission
    # --------------------------------------------------------

    synchronization_admission_service = (
        SynchronizationAdmissionService(
            source_repository=source_repository,
            source_container_repository=source_container_repository,
        )
    )

    # --------------------------------------------------------
    # Synchronization Connector Routing
    # --------------------------------------------------------

    synchronization_connector_service = (
        SynchronizationConnectorService(
            whole_source_connector=whole_source_connector,
        )
    )

    # --------------------------------------------------------
    # Synchronization Execution
    # --------------------------------------------------------

    synchronization_execution_service = (
        SynchronizationExecutionService(
            reservation_repository=(
                synchronization_reservation_repository
            ),
            processing_job_repository=(
                processing_job_repository
            ),
            connector_service=(
                synchronization_connector_service
            ),
            orchestrator=(
                synchronization_orchestrator
            ),
            pipeline_version=pipeline_version,
        )
    )

    # --------------------------------------------------------
    # Production Synchronization Application Boundary
    # --------------------------------------------------------

    synchronization_application_service = (
        SynchronizationApplicationService(
            admission_service=(
                synchronization_admission_service
            ),
            preliminary_conflict_service=(
                preliminary_conflict_service
            ),
            source_container_validator=(
                source_container_validator
            ),
            execution_service=(
                synchronization_execution_service
            ),
        )
    )

    # --------------------------------------------------------
    # Source Browsing
    # --------------------------------------------------------

    source_browsing_service = SourceBrowsingService(
        source_repository=source_repository,
        source_container_repository=source_container_repository,
    )

    # --------------------------------------------------------
    # UI-Independent Interaction Boundary
    # --------------------------------------------------------

    synchronization_interaction_service = (
        SynchronizationInteractionService(
            source_browsing_service=(
                source_browsing_service
            ),
            synchronization_application_service=(
                synchronization_application_service
            ),
        )
    )

    return synchronization_interaction_service