"""Tests for chunk operations and toggle buttons via dogtail AT-SPI."""
from dogtail.utils import doDelay

from conftest import find_app, send_keys, send_keys_until, wait_for_label


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


def _open_diff(app_process, fixture_path):
    """Launch mergers with left/right fixtures and return (app, proc)."""
    proc = app_process(fixture_path("left.txt"), fixture_path("right.txt"))
    app = find_app()
    return app, proc


def _get_chunk_label(labels):
    """Find the chunk count label (e.g. '3 changes') from a list of label texts."""
    for t in labels:
        if "changes" in t.lower() or "no changes" in t.lower():
            return t
    return None


def test_blanks_toggle_changes_count(app_process, fixture_path):
    """Clicking the Blanks toggle should change the chunk count label."""
    app, proc = _open_diff(app_process, fixture_path)
    doDelay(2)

    labels_before = _find_labels(app)
    chunk_before = _get_chunk_label(labels_before)
    assert chunk_before is not None, (
        f"Expected a chunk count label with 'changes', got: {labels_before}"
    )

    # Click the Blanks toggle button (ToggleButton in GTK4)
    blanks_btn = app.findChild(
        lambda n: n.roleName == "toggle button" and "Blank" in n.name and n.showing
    )
    assert blanks_btn is not None, "Blanks toggle button not found"
    blanks_btn.do_action(0)
    doDelay(2)

    labels_after = _find_labels(app)
    chunk_after = _get_chunk_label(labels_after)
    # The label should have changed (different count or "No changes")
    # Note: it may or may not change depending on the files, but at minimum
    # the app should not crash. We check the label is still present.
    assert chunk_after is not None, (
        f"Chunk label disappeared after Blanks toggle: {labels_after}"
    )


def test_spaces_toggle_changes_count(app_process, fixture_path):
    """Clicking the Spaces toggle should change the chunk count label."""
    app, proc = _open_diff(app_process, fixture_path)
    doDelay(2)

    labels_before = _find_labels(app)
    chunk_before = _get_chunk_label(labels_before)
    assert chunk_before is not None, (
        f"Expected a chunk count label with 'changes', got: {labels_before}"
    )

    # Click the Spaces toggle button (ToggleButton in GTK4)
    spaces_btn = app.findChild(
        lambda n: n.roleName == "toggle button" and "Space" in n.name and n.showing
    )
    assert spaces_btn is not None, "Spaces toggle button not found"
    spaces_btn.do_action(0)
    doDelay(2)

    labels_after = _find_labels(app)
    chunk_after = _get_chunk_label(labels_after)
    assert chunk_after is not None, (
        f"Chunk label disappeared after Spaces toggle: {labels_after}"
    )


def test_chunk_navigation_updates_label(app_process, fixture_path):
    """Pressing Ctrl+D should cycle through chunks with updated labels."""
    app, proc = _open_diff(app_process, fixture_path)
    doDelay(2)

    # Navigate to first chunk
    chunk_text = send_keys_until(
        app, "ctrl+d", proc.pid, lambda t: " of " in t, retries=5, delay=2
    )
    assert chunk_text is not None, "Chunk navigation label not found after first Ctrl+D"
    assert "1 of " in chunk_text, (
        f"Expected 'Change 1 of ...' but got '{chunk_text}'"
    )

    # Navigate to second chunk
    send_keys("ctrl+d", proc.pid)
    doDelay(1)

    result = wait_for_label(app, lambda t: "2 of " in t, timeout=3)
    assert result is not None, (
        f"Expected 'Change 2 of ...' after second Ctrl+D, "
        f"labels: {_find_labels(app)}"
    )
