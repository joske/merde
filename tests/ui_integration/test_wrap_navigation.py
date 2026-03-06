"""Tests for wrap-around navigation setting via dogtail AT-SPI."""
import re

from conftest import find_app, send_keys_until


def _open_diff(app_process, fixture_path):
    """Launch mergers with left/right fixtures and return (app, proc)."""
    proc = app_process(fixture_path("left.txt"), fixture_path("right.txt"))
    app = find_app()
    return app, proc



def _get_chunk_label(app):
    """Find the chunk navigation label (e.g. 'Change 1 of 3') in the app."""
    labels = app.findChildren(lambda n: n.roleName == "label" and n.showing)
    for label in labels:
        try:
            text = label.text or label.name or ""
            if " of " in text or "changes" in text:
                return text
        except Exception:
            continue
    return None


def _parse_chunk_label(text):
    """Parse 'Change X of Y' into (current, total) or None."""
    m = re.match(r"Change (\d+) of (\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def test_no_wrap_by_default(app_process, fixture_path):
    """Navigation should NOT wrap around by default (wrap_around_navigation=false)."""
    app, proc = _open_diff(app_process, fixture_path)

    # Navigate to first chunk
    label = send_keys_until(
        app, "ctrl+d", proc.pid,
        lambda t: "Change " in t and " of " in t,
    )
    assert label is not None, "Chunk label not found after first Ctrl+D"
    parsed = _parse_chunk_label(label)
    assert parsed is not None, f"Could not parse chunk label: '{label}'"
    total = parsed[1]

    # Navigate to the last chunk
    for i in range(total - 1):
        expected = i + 2  # already at 1, so next is 2, 3, ...
        send_keys_until(
            app, "ctrl+d", proc.pid,
            lambda t, e=expected: f"Change {e} of " in t,
        )

    label = _get_chunk_label(app)
    parsed = _parse_chunk_label(label)
    assert parsed is not None, f"Could not parse chunk label: '{label}'"
    assert parsed[0] == total, f"Expected to be at last chunk ({total}), got {parsed[0]}"

    # Press next again — should NOT wrap, label stays at last chunk
    send_keys_until(
        app, "ctrl+d", proc.pid,
        lambda t: f"Change {total} of " in t,
    )
    label = _get_chunk_label(app)
    parsed = _parse_chunk_label(label)
    assert parsed is not None, f"Could not parse chunk label: '{label}'"
    assert parsed[0] == total, (
        f"Expected label to stay at last chunk ({total} of {total}) with no wrap, "
        f"but got 'Change {parsed[0]} of {parsed[1]}'"
    )
