import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from unittest.mock import patch

from tools import standards_catalog
from tools.standards_catalog import DEFAULT_ROOT, classify_path, main, scan, search


class StandardsCatalogTests(unittest.TestCase):
    def test_classifies_representative_filename_tokens(self):
        root = Path("standards")
        result = classify_path(
            root / "Fraesbilder" / "Fraesbild_T0_B001_HS5000_neu_92E_englisch.prt",
            root,
        )

        self.assertEqual(result["category"], "Fräsbilder")
        self.assertEqual(result["directory_category"], "Fraesbilder")
        self.assertEqual(result["families"], ["T0", "B001"])
        self.assertEqual(result["series"], ["HS5000"])
        self.assertEqual(result["dimensions"], ["92E"])
        self.assertEqual(result["languages"], ["englisch"])
        self.assertEqual(result["qualifiers"], ["neu"])
        self.assertEqual(result["unclassified_tokens"], [])

    def test_compound_dimensions_do_not_become_unknown_fragments(self):
        result = classify_path(
            Path("Fraesbild_B001_HS99_92E_55_65D_englisch.prt"), Path(".")
        )

        self.assertEqual(result["dimensions"], ["92E", "55_65D"])
        self.assertEqual(result["unclassified_tokens"], [])

    def test_preserves_unknown_tokens(self):
        result = classify_path(
            Path("Fraesbild_B001_HS5000_KFV-Sonder.prt"), Path(".")
        )

        self.assertEqual(result["unclassified_tokens"], ["KFV-Sonder"])

    def test_does_not_treat_lowercase_2d_marker_as_dimension(self):
        result = classify_path(Path("logo-si_a_2d.prt"), Path("."))

        self.assertEqual(result["dimensions"], [])
        self.assertEqual(result["unclassified_tokens"], ["logo-si", "a", "2d"])

    def test_scan_and_search_are_recursive_and_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "Fraesbilder"
            nested.mkdir()
            (nested / "Fraesbild_B001_HS5000.prt").touch()
            (nested / "Fraesbild_K091_HS99.prt").touch()
            (nested / "not-a-part.txt").touch()

            catalog = scan(root)
            results = search(catalog, ["fräsbild", "b001", "hs5000"])

        self.assertEqual(len(catalog), 2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_name"], "Fraesbild_B001_HS5000.prt")

    def test_search_supports_field_filters(self):
        root = Path("standards")
        item = classify_path(
            root / "Fraesbilder" / "Fraesbild_4ZK_B001_HS5000_55_65D_neu.prt",
            root,
        )

        results = search(
            [item],
            ["familie:B001", "serie:HS5000", "mass:55_65D", "ordner:Fraesbilder"],
        )

        self.assertEqual(results, [item])
        self.assertEqual(search([item], ["series:HS99"]), [])

    def test_classifies_categories_from_filename_tokens(self):
        expected = {
            "Fraesbild_B001_HS5000.prt": "Fräsbilder",
            "Senk8_2mmStulp.prt": "Senkungen",
            "Treibstange_WN0161_F1.prt": "Treibstangen",
            "ZK2000_geschraubt.prt": "Zusatzkästen",
            "HS8250_35-65D_geschraubt.prt": "Hauptschlösser",
            "sap_A0q_si_0.prt": "Zeichnungsvorlagen",
            "unbekannte_datei.prt": "Sonstiges",
        }

        for file_name, category in expected.items():
            with self.subTest(file_name=file_name):
                result = classify_path(Path(file_name), Path("."))
                self.assertEqual(result["category"], category)

        fräesbild = classify_path(Path("Fraesbild_B001_HS5000.prt"), Path("."))
        self.assertEqual(search([fräesbild], ["kategorie:Fräsbilder"]), [fräesbild])
        self.assertEqual(search([fräesbild], ["cat:Senkungen"]), [])

    def test_scan_rejects_missing_root(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaises(FileNotFoundError):
                scan(missing)

    def test_cli_is_locked_to_the_local_test_directory(self):
        self.assertEqual(
            DEFAULT_ROOT,
            Path(r"C:\Users\benjamin.krah\Desktop\Test_Standards\Standards"),
        )
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--root", r"T:\KFV-SIEMENSSTRASSE-Gruppen\CAD\ugsshare-2412\Standards"])

    def test_zero_limit_exports_all_csv_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Fraesbild_B001.prt").touch()
            (root / "Fraesbild_K091.prt").touch()
            output = io.StringIO()

            with patch.object(standards_catalog, "DEFAULT_ROOT", root):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--format", "csv", "--limit", "0"]), 0)

        self.assertEqual(len(output.getvalue().splitlines()), 3)

    def test_nx_dialog_resource_contains_unique_expected_controls(self):
        dialog_path = Path(__file__).resolve().parents[1] / "nx" / "standards_search.dlx"
        root = ET.parse(dialog_path).getroot()
        items = [child for child in list(root) if child.tag == "item"]
        identifiers = [item.attrib["id"] for item in items]
        block_classes = [item.attrib["class"] for item in items]

        self.assertEqual(root.attrib["ContainerItems"], "7")
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(items), 7)
        self.assertIn("UICOMP_string", block_classes)
        self.assertIn("UICOMP_enum", block_classes)
        self.assertIn("UICOMP_list_box", block_classes)
        self.assertIn("UGS::UI::Comp::DrawingArea", block_classes)


if __name__ == "__main__":
    unittest.main()