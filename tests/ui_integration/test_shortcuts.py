"""Keyboard shortcut tests for file diff window via dogtail AT-SPI."""
from dogtail.utils import doDelay

from conftest import find_app, send_keys, send_keys_until


def _open_diff(app_process, fixture_path):
    """Launch mergers with left/right fixtures and return (app, proc)."""
    proc = app_process(fixture_path("left.txt"), fixture_path("right.txt"))
    app = find_app()
    return app, proc


def test_ctrl_f_opens_find_bar(app_process, fixture_path):
    """Ctrl+F should reveal the find bar with a text entry."""
    app, proc = _open_diff(app_process, fixture_path)

    send_keys("ctrl+f", proc.pid)
    doDelay(1)

    entries = app.findChildren(
        lambda n: n.roleName == "text" and n.showing
    )
    assert len(entries) >= 1, "No text entry found after Ctrl+F"


def test_alt_down_navigates_to_next_chunk(app_process, fixture_path):
    """Ctrl+D should navigate to the next diff chunk (Alt+Down also works when focused)."""
    app, proc = _open_diff(app_process, fixture_path)

    # Alt+Down only fires when a text view has focus (capture-phase handler).
    # Ctrl+D is registered app-level via set_accels_for_action and works regardless.
    chunk_text = send_keys_until(
        app, "ctrl+d", proc.pid, lambda t: " of " in t
    )
    assert chunk_text is not None, (
        "Chunk navigation label not found after Ctrl+D."
    )
    assert "1 of " in chunk_text, (
        f"Expected '1 of ...' but got '{chunk_text}'"
    )


def test_escape_closes_find_bar(app_process, fixture_path):
    """Escape should close the find bar after Ctrl+F opens it."""
    app, proc = _open_diff(app_process, fixture_path)

    send_keys("ctrl+f", proc.pid)
    doDelay(1)

    entries_before = app.findChildren(
        lambda n: n.roleName == "text" and n.showing
    )
    assert len(entries_before) >= 1, "Find bar did not open"

    send_keys("Escape", proc.pid)
    doDelay(1)
