"""Advanced merge view tests: chunk navigation and saving via dogtail AT-SPI."""
import os
import shutil
import subprocess
import tempfile

from dogtail.utils import doDelay

from conftest import find_app, send_keys, send_keys_until


FIXTURES = os.path.join(os.path.dirname(__file__), "../fixtures")


def _find_labels(app):
    """Return text of all visible labels."""
    labels = app.findChildren(lambda n: n.roleName == "label" and n.showing)
    texts = []
    for lbl in labels:
        try:
            texts.append(lbl.text or lbl.name or "")
        except Exception:
            pass
    return texts


def _copy_fixture(name, dest_dir):
    """Copy a fixture file into dest_dir and return the new path."""
    src = os.path.join(FIXTURES, name)
    dst = os.path.join(dest_dir, name)
    shutil.copy2(src, dst)
    return dst


def _focus_and_type(pid, text):
    """Focus the application window and type text via xdotool."""
    wids = (
        subprocess.check_output(["xdotool", "search", "--pid", str(pid)])
        .decode().strip().splitlines()
    )
    if wids:
        for wid in wids:
            result = subprocess.run(
                ["xdotool", "windowfocus", "--sync", wid],
                capture_output=True,
            )
            if result.returncode == 0:
                break
    doDelay(0.3)
    subprocess.run(["xdotool", "type", "--delay", "50", text], check=True)


def test_merge_chunk_navigation(app_process, fixture_path):
    """Ctrl+D in merge view should show a chunk navigation label."""
    proc = app_process(
        fixture_path("left.txt"),
        fixture_path("base.txt"),
        fixture_path("right.txt"),
    )
    app = find_app()
    doDelay(2)

    chunk_text = send_keys_until(
        app, "ctrl+d", proc.pid,
        lambda t: "of" in t.lower() or "change" in t.lower(),
        retries=5, delay=2,
    )
    assert chunk_text is not None, (
        f"Expected chunk navigation label after Ctrl+D in merge view. "
        f"Labels: {_find_labels(app)}"
    )


def test_merge_ctrl_s_saves_middle(app_process):
    """In merge view, typing and Ctrl+S should save the middle (base) pane."""
    with tempfile.TemporaryDirectory() as tmpdir:
        left = _copy_fixture("left.txt", tmpdir)
        base = _copy_fixture("base.txt", tmpdir)
        right = _copy_fixture("right.txt", tmpdir)

        original_base = open(base).read()

        proc = app_process(left, base, right)
        app = find_app()
        doDelay(2)

        # In merge mode the middle pane (base) is the editable output pane.
        # We need to click on the middle text view to focus it, then type.
        text_views = app.findChildren(
            lambda n: n.roleName == "text" and n.showing
        )
        # There should be at least 3 text views; the middle one is index 1
        # (left=0, middle=1, right=2), but ordering may vary.
        # We click the middle area to focus it.
        if len(text_views) >= 3:
            # Try to focus the middle text view
            try:
                text_views[1].grabFocus()
            except Exception:
                pass
        doDelay(1)

        # Type some text
        _focus_and_type(proc.pid, "MERGE_EDIT")
        doDelay(1)

        # Save with Ctrl+S
        send_keys("ctrl+s", proc.pid)
        doDelay(2)

        # The base file should have been modified
        new_base = open(base).read()
        assert new_base != original_base or "MERGE_EDIT" in new_base, (
            f"Expected base file to change after typing and saving. "
            f"Original length: {len(original_base)}, new length: {len(new_base)}"
        )
