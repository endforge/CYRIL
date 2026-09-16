"""
CYRIL pywebview Application

Purpose:
    Starts the CYRIL pywebview application and connects the graphical
    interface to the UI-independent AlphaOmega synchronization boundary.

Responsibilities:
    - Build the production synchronization runtime.
    - Create the pywebview synchronization API adapter.
    - Locate the CYRIL HTML entry point.
    - Create the application window.
    - Start the pywebview GUI loop.

Does NOT:
    - Implement synchronization business logic.
    - Access the AlphaOmega database directly.
    - Communicate directly with Microsoft Graph.
    - Create Synchronization Requests directly.
    - Perform synchronization admission or conflict detection.
    - Execute the synchronization pipeline directly.
"""

from pathlib import Path

import webview

from scripts.application.sync_runtime import (
    build_sync_runtime,
)

from scripts.ui.pywebview.synchronization_api import (
    SynchronizationApi,
)


PIPELINE_VERSION = "lab8-cyril-ui"

WINDOW_TITLE = "CYRIL"

WINDOW_WIDTH = 1000

WINDOW_HEIGHT = 700


def get_ui_entry_point():
    """
    Return the local CYRIL HTML entry point.
    """

    ui_directory = Path(__file__).resolve().parent

    entry_point = (
        ui_directory
        / "index.html"
    )

    if not entry_point.is_file():
        raise RuntimeError(
            "CYRIL UI entry point was not found: "
            f"{entry_point}"
        )

    return entry_point


def build_application_api():
    """
    Build the production synchronization runtime and wrap it with
    the pywebview-specific API adapter.
    """

    synchronization_interaction_service = (
        build_sync_runtime(
            pipeline_version=PIPELINE_VERSION
        )
    )

    return SynchronizationApi(
        synchronization_interaction_service=(
            synchronization_interaction_service
        )
    )


def run():
    """
    Start the CYRIL desktop application.
    """

    entry_point = get_ui_entry_point()

    synchronization_api = (
        build_application_api()
    )

    webview.create_window(
        title=WINDOW_TITLE,
        url=str(entry_point),
        js_api=synchronization_api,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
    )

    webview.start()


if __name__ == "__main__":
    run()