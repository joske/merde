"""Test for the -L flag (custom pane labels) via dogtail AT-SPI."""
from dogtail.utils import doDelay

from conftest import find_app


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


def test_custom_labels_shown(app_process, fixture_path):
    """Passing -L flags should display custom labels instead of file paths."""
    proc = app_process(
        fixture_path("left.txt"),
        fixture_path("right.txt"),
        "-L", "Original",
        "-L", "Modified",
    )
    app = find_app()
    doDelay(2)

    labels = _find_labels(app)
    assert any("Original" in t for t in labels), (
        f"Expected 'Original' in labels: {labels}"
    )
    assert any("Modified" in t for t in labels), (
        f"Expected 'Modified' in labels: {labels}"
    )
