"""Run an existing Python script with narrowly filtered HTTP transport diagnostics.

Usage (from the CYRIL repository root):
    python run_with_http_diagnostics.py path/to/existing_script.py [arguments...]

No HTTP settings, credentials, retry policy, or production files are changed.
"""

import datetime
import logging
import pathlib
import runpy
import sys
import traceback


class SafeTransportFilter(logging.Filter):
    """Keep transport event names only, never request/response details."""

    ALLOWED = (
        "connect_tcp.",
        "start_tls.",
        "close.",
        "receive_connection_terminated.",
        "receive_response_headers.",
        "send_request_headers.",
        "receive_data.",
        "send_data.",
    )

    def filter(self, record):
        if not record.name.startswith("httpcore"):
            return False
        message = record.getMessage()
        event = message.split("(", 1)[0].split(" ", 1)[0]
        if not event.startswith(self.ALLOWED):
            return False
        # Discard parameters, headers, bodies, URLs, exception reprs and tracebacks.
        record.msg = event
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python run_with_http_diagnostics.py SCRIPT.py [args...]")

    target = pathlib.Path(sys.argv[1]).resolve()
    if not target.is_file():
        raise SystemExit(f"Script not found: {target}")

    log_dir = pathlib.Path("artifacts") / "diagnostics"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / f"http_transport_{timestamp}.log"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)sZ %(name)s %(levelname)s %(message)s"))
    handler.formatter.converter = __import__("time").gmtime
    handler.addFilter(SafeTransportFilter())
    logger = logging.getLogger("httpcore")
    old_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    print(f"HTTP diagnostic log: {log_path.resolve()}", flush=True)
    print(f"Start UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}", flush=True)
    original_argv = sys.argv
    try:
        sys.argv = [str(target), *original_argv[2:]]
        runpy.run_path(str(target), run_name="__main__")
    except BaseException as error:
        print(f"Failure UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}", file=sys.stderr, flush=True)
        print(f"Exception type: {type(error).__module__}.{type(error).__name__}", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise SystemExit(1) from None
    finally:
        sys.argv = original_argv
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        handler.close()
        print(f"End UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}", flush=True)
        print(f"HTTP diagnostic log: {log_path.resolve()}", flush=True)


if __name__ == "__main__":
    main()
