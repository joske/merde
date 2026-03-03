"""Tests for wrap-around navigation setting via dogtail AT-SPI."""
import subprocess

from dogtail.utils import doDelay

from conftest import find_app


def _open_diff(app_process, fixture_path):
    """Launch mergers with left/right fixtures and return (app, proc)."""
    proc = app_process(fixture_path("left.txt"), fixture_path("right.txt"))
    app = find_app()
    return app, proc


def _send_keys(key_combo, pid):
    """Focus the mergers window by PID and send a key combo via xdotool."""
    wids = (
        subprocess.check_output(["xdotool", "search", "--pid", str(pid)])
        .decode()
        .strip()
        .splitlines()
    )
    assert wids, f"No window found for PID {pid}"
    for wid in wids:
        result = subprocess.run(
            ["xdotool", "windowfocus", "--sync", wid],
            capture_output=True,
        )
        if result.returncode == 0:
            break
    subprocess.run(["xdotool", "key", key_combo], check=True)


def _get_chunk_label(app):
    """Find the chunk navigation label (e.g. 'Change 1 of 2') in the app."""
    labels = app.findChildren(lambda n: n.roleName == "label" and n.showing)
    for label in labels:
        try:
            text = label.text or label.name or ""
            if " of " in text or "changes" in text:
                return text
        except Exception:
            continue
    return None


def test_no_wrap_by_default(app_process, fixture_path):
    """Navigation should NOT wrap around by default (wrap_around_navigation=false)."""
    app, proc = _open_diff(app_process, fixture_path)

    # Navigate to chunk 1
    _send_keys("ctrl+d", proc.pid)
    doDelay(1)
    label = _get_chunk_label(app)
    assert label is not None, "Chunk label not found after first Ctrl+D"
    assert "1 of " in label, f"Expected 'Change 1 of ...' but got '{label}'"

    # Navigate to chunk 2 (last chunk)
    _send_keys("ctrl+d", proc.pid)
    doDelay(1)
    label = _get_chunk_label(app)
    assert "2 of 2" in label, f"Expected 'Change 2 of 2' but got '{label}'"

    # Press next again — should NOT wrap, label stays at "Change 2 of 2"
    _send_keys("ctrl+d", proc.pid)
    doDelay(1)
    label = _get_chunk_label(app)
    assert "2 of 2" in label, (
        f"Expected label to stay at 'Change 2 of 2' (no wrap), but got '{label}'"
    )
