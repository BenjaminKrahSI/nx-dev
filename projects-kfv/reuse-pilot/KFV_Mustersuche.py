"""Local Reuse Library journal for the first KFV legacy-pattern pilot."""
import runpy
from pathlib import Path


PATTERN_NAME = "Fraesbild_3ZK_B001_HS3050.prt"


def main():
    import NXOpen

    root = Path.home() / "Desktop" / "Test_Standards" / "Standards"
    source = root / PATTERN_NAME
    if not source.is_file():
        NXOpen.UI.GetUI().NXMessageBox.Show(
            "KFV-Musterpilot",
            NXOpen.NXMessageBox.DialogType.Information,
            "Lokales Pilot-Fraesbild nicht gefunden:\n%s" % source,
        )
        return

    journal_path = Path(__file__).resolve().parents[1] / "standards_search.py"
    namespace = runpy.run_path(str(journal_path), run_name="kfv_reuse_pattern_pilot")
    app = namespace["StandardsSearch"](
        root=root, initial_query="name:" + PATTERN_NAME
    )
    try:
        app.launch()
    finally:
        app.dispose()


if __name__ == "__main__":
    main()