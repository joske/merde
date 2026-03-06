"""Shared fixtures for dogtail UI integration tests."""
import os
import signal
import subprocess
import time

import dogtail.tree
from dogtail.utils import doDelay
import pytest

MERGERS_BIN = os.environ.get(
    "MERGERS_BIN",
    os.path.join(os.path.dirname(__file__), "../../target/release/mergers"),
)
FIXTURES = os.path.join(os.path.dirname(__file__), "../fixtures")


def find_app(name="mergers", retries=5):
    """Find the application in the AT-SPI tree, retrying on failure."""
    for i in range(retries):
        try:
            app = dogtail.tree.root.application(name)
            doDelay(1)  # Let the AT-SPI tree populate
            return app
        except Exception:
            if i == retries - 1:
                raise
            doDelay(1)
    return None


def wait_for_label(app, predicate, timeout=5, interval=0.5):
    """Poll AT-SPI labels until `predicate(text)` returns True or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        labels = app.findChildren(lambda n: n.roleName == "label" and n.showing)
        for label in labels:
            try:
                text = label.text or label.name or ""
                if predicate(text):
                    return text
            except Exception:
                continue
        doDelay(interval)
    return None


def send_keys_until(app, key_combo, pid, predicate, retries=3, delay=1):
    """Send a key combo and retry if the expected label change doesn't happen."""
    for _ in range(retries):
        _send_keys_impl(key_combo, pid)
        result = wait_for_label(app, predicate, timeout=delay)
        if result is not None:
            return result
    return None


def send_keys(key_combo, pid):
    """Public wrapper for sending keys."""
    _send_keys_impl(key_combo, pid)


def _send_keys_impl(key_combo, pid):
    """Focus the mergers window by PID and send a key combo via xdotool."""
    wids = (
        subprocess.check_output(["xdotool", "search", "--pid", str(pid)])
        .decode()
        .strip()
        .splitlines()
    )
    if not wids:
        return
    for wid in wids:
        result = subprocess.run(
            ["xdotool", "windowfocus", "--sync", wid],
            capture_output=True,
        )
        if result.returncode == 0:
            break
    time.sleep(0.2)  # Let GTK process the focus event
    subprocess.run(["xdotool", "key", key_combo], check=True)


@pytest.fixture
def app_process():
    """Launch mergers and yield the process. Kill on teardown."""
    processes = []

    def _launch(*args):
        proc = subprocess.Popen(
            [MERGERS_BIN, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(proc)
        time.sleep(3)  # Wait for GTK to initialize
        return proc

    yield _launch

    for proc in processes:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
    # Give AT-SPI time to deregister the app before the next test
    time.sleep(1)


@pytest.fixture
def fixture_path():
    """Return path to a fixture file."""
    def _path(name):
        return os.path.join(FIXTURES, name)
    return _path
