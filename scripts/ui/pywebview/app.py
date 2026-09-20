"""CYRIL pywebview application entry point and Windows window icon configuration."""

import ctypes
import os
import sys
import time
from pathlib import Path

import webview

from common.security.configuration import load_local_configuration

# Graph configuration is read during imports, so load it before importing the runtime.
load_local_configuration()

from scripts.application.sync_runtime import build_sync_runtime
from scripts.ui.pywebview.synchronization_api import SynchronizationApi

PIPELINE_VERSION = "lab8-cyril-ui"
WINDOW_TITLE = "CYRIL"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
ICON_FILENAME = "CYRIL.ico"


def ui_directory():
    """Locate bundled UI assets or the development UI directory."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "scripts" / "ui" / "pywebview"
    return Path(__file__).resolve().parent


def get_ui_entry_point():
    entry_point = ui_directory() / "index.html"
    if not entry_point.is_file():
        raise RuntimeError(f"CYRIL UI entry point was not found: {entry_point}")
    return entry_point


def build_application_api():
    interaction_service = build_sync_runtime(pipeline_version=PIPELINE_VERSION)
    return SynchronizationApi(synchronization_interaction_service=interaction_service)


def configure_windows_identity():
    """Give the running Python process a CYRIL taskbar identity on Windows."""
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CYRIL.Desktop")


def apply_windows_window_icon():
    """Apply CYRIL.ico to this process's native CYRIL window after it exists."""
    if os.name != "nt":
        return

    icon_path = ui_directory() / ICON_FILENAME
    if not icon_path.is_file():
        raise RuntimeError(f"CYRIL icon was not found: {icon_path}")

    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                                  ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    kernel32.GetCurrentProcessId.restype = wintypes.DWORD

    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x0010
    WM_SETICON = 0x0080
    icons = []
    for size in (16, 32):
        handle = user32.LoadImageW(None, str(icon_path), IMAGE_ICON, size, size, LR_LOADFROMFILE)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        icons.append(handle)

    process_id = kernel32.GetCurrentProcessId()
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    for _ in range(50):
        matches = []

        @callback_type
        def inspect_window(hwnd, _):
            owner = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, len(title))
            if owner.value == process_id and title.value == WINDOW_TITLE:
                matches.append(hwnd)
            return True

        user32.EnumWindows(inspect_window, 0)
        if matches:
            for hwnd in matches:
                user32.SendMessageW(hwnd, WM_SETICON, 0, icons[0])
                user32.SendMessageW(hwnd, WM_SETICON, 1, icons[1])
            return
        time.sleep(0.1)
    raise RuntimeError("Could not locate the CYRIL window to apply its icon.")


def run():
    configure_windows_identity()
    entry_point = get_ui_entry_point()
    synchronization_api = build_application_api()
    webview.create_window(
        title=WINDOW_TITLE,
        url=str(entry_point),
        js_api=synchronization_api,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
    )
    webview.start(func=apply_windows_window_icon)


if __name__ == "__main__":
    run()
