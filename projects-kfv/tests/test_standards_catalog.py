import contextlib
import io
import json
import os
import struct
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

standards_catalog = import_module("projects-kfv.standards_catalog")
classify_path = standards_catalog.classify_path
main = standards_catalog.main
resolve_root = standards_catalog.resolve_root
scan = standards_catalog.scan
search = standards_catalog.search


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


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

    def test_code_filters_are_exact_and_support_wildcards_and_alternatives(self):
        catalog = [classify_path(Path(name), Path(".")) for name in (
            "Fraesbild_B001_HS5000_192E.prt",
            "Fraesbild_B002_HS99_92E.prt",
            "Senk_3mmStulp_HS_ZK_geschraubt.prt",
        )]
        self.assertEqual(search(catalog, ["mass:92E"]), [catalog[1]])
        self.assertEqual(search(catalog, ["familie:B001|B002", "serie:HS*"]), catalog[:2])
        self.assertEqual(search(catalog, ["code:3mmStulp", "code:geschraubt"]), [catalog[2]])
        self.assertEqual(search(catalog, ["code:3mm"]), [])
        self.assertEqual(search(catalog, ["*B00?_HS*", "92E"]), catalog[:2])
        self.assertEqual(search(catalog, ["serie:HS99|", "mass:92E"]), [catalog[1]])

    def test_builder_options_count_each_file_once(self):
        catalog = [classify_path(Path(name), Path(".")) for name in (
            "Fraesbild_B001_B001_HS5000.prt", "Fraesbild_b001_HS99.prt"
        )]
        self.assertEqual(standards_catalog.code_options(catalog, "familie"), [("B001", 2)])
        options = standards_catalog.code_options(
            [classify_path(Path("Senk_3mmStulp_geschraubt.prt"), Path("."))], "code"
        )
        self.assertIn(("3mmStulp", 1), options)

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

    def test_fixture_catalog_covers_existing_filename_cases(self):
        catalog = scan(FIXTURE_ROOT)
        self.assertEqual(len(catalog), 10)
        self.assertEqual(
            {item["category"] for item in catalog},
            set(standards_catalog.CATEGORY_ORDER),
        )
        results = search(catalog, ["familie:b001", "serie:hs99", "mass:55_65D"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["unclassified_tokens"], [])

    def test_cli_accepts_root_argument(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "--root", str(FIXTURE_ROOT), "--format", "json", "B001", "HS99"
            ])
        self.assertEqual(result, 0)
        results = json.loads(output.getvalue())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["series"], ["HS99"])

    def test_cli_uses_environment_root(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"KFV_STANDARDS_DIR": str(FIXTURE_ROOT)}):
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--format", "json"]), 0)
        self.assertEqual(len(json.loads(output.getvalue())), 10)

    def test_cli_root_argument_overrides_environment(self):
        with patch.dict(os.environ, {"KFV_STANDARDS_DIR": str(FIXTURE_ROOT / "missing")}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--root", str(FIXTURE_ROOT)]), 0)

    def test_cli_requires_root_or_environment(self):
        error_output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stderr(error_output):
                with self.assertRaises(SystemExit) as raised:
                    main([])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--root", error_output.getvalue())
        self.assertIn("KFV_STANDARDS_DIR", error_output.getvalue())

    def test_cli_rejects_empty_environment_root(self):
        with patch.dict(os.environ, {"KFV_STANDARDS_DIR": "   "}):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main([])
        self.assertEqual(raised.exception.code, 2)

    def test_cli_rejects_missing_root(self):
        error_output = io.StringIO()
        with contextlib.redirect_stderr(error_output):
            with self.assertRaises(SystemExit) as raised:
                main(["--root", str(FIXTURE_ROOT / "missing")])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("Standards-Ordner nicht erreichbar", error_output.getvalue())

    @unittest.skipUnless(os.environ.get("KFV_STANDARDS_DIR"), "KFV_STANDARDS_DIR fehlt")
    def test_optional_real_standards_directory(self):
        root = resolve_root()
        self.assertTrue(root.is_dir())
        self.assertTrue(all(item["file_name"].lower().endswith(".prt") for item in scan(root)))

    def test_zero_limit_exports_all_csv_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Fraesbild_B001.prt").touch()
            (root / "Fraesbild_K091.prt").touch()
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    main(["--root", str(root), "--format", "csv", "--limit", "0"]), 0
                )

        self.assertEqual(len(output.getvalue().splitlines()), 3)

    def _load_journal(self):
        with patch.dict("sys.modules", {
            "NXOpen": Mock(),
            "NXOpen.BlockStyler": Mock(),
            "NXOpen.Assemblies": Mock(),
            "NXOpen.UF": Mock(),
        }):
            return import_module("projects-kfv.standards_search")

    def test_reuse_pilot_launches_local_pattern_search_without_inserting(self):
        with patch.dict("sys.modules", {"NXOpen": Mock()}):
            launcher = import_module("projects-kfv.reuse-pilot.KFV_Mustersuche")
        application = Mock()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / "Desktop" / "Test_Standards" / "Standards"
            root.mkdir(parents=True)
            source = root / launcher.PATTERN_NAME
            source.touch()
            with patch.object(launcher.Path, "home", return_value=home), patch.object(
                launcher.runpy, "run_path", return_value={"StandardsSearch": application}
            ) as run_journal, patch.dict("sys.modules", {"NXOpen": Mock()}):
                launcher.main()
                application.assert_called_once_with(
                    root=root, initial_query="name:" + launcher.PATTERN_NAME
                )
                application.return_value.launch.assert_called_once_with()
                application.return_value.dispose.assert_called_once_with()
                application.return_value.ok_cb.assert_not_called()
                self.assertEqual(
                    Path(run_journal.call_args.args[0]).name, "standards_search.py"
                )
                self.assertEqual(source.stat().st_size, 0)
                source.unlink()
                run_journal.reset_mock()
                launcher.main()
                run_journal.assert_not_called()

        configuration = ET.parse(
            Path(__file__).resolve().parents[1] / "docs" / "reuse-pilot-library.krx"
        ).getroot()
        entry = configuration.find("RootNodeEntry")
        self.assertEqual(entry.get("Type"), "2")
        self.assertEqual(entry.get("Name"), "KFV-Muster (Pilot)")
        self.assertEqual(Path(entry.get("Path")).name, "reuse-pilot")

    def test_nx_dialog_applies_initial_query_from_reuse_launcher(self):
        journal = self._load_journal()
        app = journal.StandardsSearch.__new__(journal.StandardsSearch)
        app.dialog = Mock()
        app.initial_query = "name:Fraesbild_3ZK_B001_HS3050.prt"
        app._scan_catalog = Mock()
        app._apply_search = Mock()
        app._show_error = Mock()
        app.initialize_cb()
        self.assertEqual(app.query_block.WideValue, app.initial_query)
        app._scan_catalog.assert_called_once_with()
        app._apply_search.assert_called_once_with()
        app._show_error.assert_not_called()
        self.assertFalse(app.updating_controls)

    def test_nx_builder_filters_in_memory_and_loads_only_clicked_part(self):
        journal = self._load_journal()
        app = journal.StandardsSearch.__new__(journal.StandardsSearch)
        app.root = FIXTURE_ROOT
        app.catalog = scan(FIXTURE_ROOT)
        app.catalog_error = None
        app.initialization_error = None
        app.updating_controls = False
        app.query_block = Mock(Value="", WideValue="")
        app.category_block = Mock(ValueAsString="Alle")
        app.category_options = {"Alle": None, "Senkungen": "Senkungen"}
        app.code_group = Mock(ValueAsString=next(iter(journal.BUILDER_GROUPS)))
        app.code_value = Mock(ValueAsString="Auswaehlen")
        app.code_choices = {}
        app.add_code = Mock()
        app.search_button = Mock()
        app.reset_search = Mock()
        app.refresh_button = Mock()
        app.results_list = Mock()
        app.preview_area = Mock()
        app.status_block = Mock()
        app._load_part = Mock()
        app._show_error = Mock()

        with patch.object(journal, "scan") as scanner:
            app._apply_search()
            self.assertEqual(len(app.matches), 10)
            app.query_block.WideValue = "mass:55_65D"
            app.update_cb(app.search_button)
            self.assertEqual(len(app.matches), 2)
            self.assertTrue(all("55_65D" in item["dimensions"] for item in app.matches))
            self.assertEqual(app.query_block.Value, "")
            app.update_cb(app.reset_search)
            app.code_group.ValueAsString = "Seriencodes"
            app.update_cb(app.code_group)
            app.code_value.ValueAsString = next(
                label for label, value in app.code_choices.items() if value == "HS99"
            )
            app.update_cb(app.code_value)
            self.assertEqual(len(app.matches), 1)
            self.assertEqual(app.matches[0]["series"], ["HS99"])
            self.assertEqual(app.query_block.WideValue, "")
            self.assertIn("HS5000", app.code_choices.values())
            app.code_value.ValueAsString = next(
                label for label, value in app.code_choices.items() if value == "HS5000"
            )
            app.update_cb(app.code_value)
            self.assertEqual(len(app.matches), 2)
            self.assertTrue(all(item["series"] == ["HS5000"] for item in app.matches))
            app.update_cb(app.reset_search)
            self.assertEqual(len(app.matches), 10)
            app.code_group.ValueAsString = next(iter(journal.BUILDER_GROUPS))
            app.update_cb(app.code_group)
            app.code_value.ValueAsString = next(
                label for label, value in app.code_choices.items() if value == "B001"
            )
            app.update_cb(app.add_code)
            self.assertEqual(app.query_block.WideValue, "familie:B001")
            self.assertTrue(all("B001" in item["families"] for item in app.matches))
            app.update_cb(app.add_code)
            self.assertEqual(app.query_block.WideValue, "familie:B001")
            app.category_block.ValueAsString = "Senkungen"
            app.update_cb(app.category_block)
            self.assertEqual(app.matches, [])
            app.update_cb(app.reset_search)
            self.assertEqual(app.query_block.WideValue, "")
            self.assertEqual(len(app.matches), 10)
            scanner.assert_not_called()
            app._load_part.assert_not_called()

            label = next(iter(app.result_by_label))
            app.results_list.GetSelectedItemStrings.return_value = [label]
            app._load_part.return_value.GetPreviewImage.return_value = (0, 0, [])
            app.update_cb(app.results_list)
            app._load_part.assert_called_once_with(
                os.path.join(FIXTURE_ROOT, app.result_by_label[label]["relative_path"])
            )
            app._show_error.assert_not_called()

            scanner.return_value = []
            app.update_cb(app.refresh_button)
            scanner.assert_called_once_with(FIXTURE_ROOT)
            self.assertEqual(app.matches, [])

    def test_nx_inserts_legacy_pattern_not_an_assembly_component(self):
        journal = self._load_journal()
        app = journal.StandardsSearch.__new__(journal.StandardsSearch)
        app.root = FIXTURE_ROOT
        app.results_list = Mock()
        app.results_list.GetSelectedItemStrings.return_value = ["selected"]
        item = scan(FIXTURE_ROOT)[0]
        app.result_by_label = {"selected": item}
        app.session = Mock()
        app.position_block = Mock(Point=Mock(X=10.0, Y=20.0, Z=30.0))
        app.session.Parts.Work.WCS.CoordinateSystem.Orientation.Element = Mock(
            Xx=0.0, Xy=1.0, Xz=0.0,
            Yx=-1.0, Yy=0.0, Yz=0.0,
            Zx=0.0, Zy=0.0, Zz=1.0,
        )
        app._show_error = Mock()
        app._show_message = Mock()
        app._listing_message = Mock()
        app._load_part = Mock()
        with patch.object(journal.NXOpen.UF.UFSession, "GetUFSession") as uf_session:
            importer = uf_session.return_value.Patt.Import
            importer.return_value = 42
            self.assertEqual(app.ok_cb(), 0)
            importer.assert_called_once_with(
                os.path.join(FIXTURE_ROOT, item["relative_path"]),
                Path(item["file_name"]).stem,
                1,
                [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 10.0, 20.0, 30.0, 1.0],
            )
            app.session.Parts.Work.AssemblyManager.CreateAddComponentBuilder.assert_not_called()
            app._load_part.assert_not_called()
            importer.side_effect = RuntimeError("No pattern data")
            self.assertEqual(app.ok_cb(), 1)
            app.session.UndoToMark.assert_called_once()
            app.session.DeleteUndoMark.assert_called_once()
            self.assertIn("No pattern data", app._show_error.call_args.args[0])
            importer.side_effect = None
            importer.return_value = 0
            self.assertEqual(app.ok_cb(), 1)
            uf_session.return_value.Patt.Import = None
            self.assertEqual(app.ok_cb(), 1)
            app._show_message.assert_called_once()
            app.session.Parts.Work = None
            self.assertEqual(app.ok_cb(), 1)

    def test_preview_bitmap_can_be_doubled_without_changing_source_pixels(self):
        journal = self._load_journal()
        pixels = [0xFF112233, 0xFF445566]
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "preview.bmp"
            journal._write_bmp(image_path, 2, 1, pixels, scale=2)
            image = image_path.read_bytes()
        self.assertEqual(struct.unpack_from("<ii", image, 18), (4, 2))
        expected_row = bytes.fromhex("332211ff332211ff665544ff665544ff")
        self.assertEqual(image[54:], expected_row * 2)
        self.assertEqual(struct.unpack_from("<I", image, 2)[0], len(image))
        self.assertEqual(pixels, [0xFF112233, 0xFF445566])

    def test_nx_journal_accepts_host_arguments_but_checks_explicit_arguments(self):
        journal = self._load_journal()

        with patch.object(journal, "StandardsSearch") as application:
            with patch.dict(os.environ, {"KFV_STANDARDS_DIR": ""}), patch(
                "sys.argv", ["nx", "--nx-host-option", "host-value"]
            ):
                journal.main()
            application.assert_called_once_with(journal.LOCAL_TEST_ROOT)
            application.return_value.launch.assert_called_once_with()
            application.return_value.dispose.assert_called_once_with()

            application.reset_mock()
            with patch.dict(os.environ, {"KFV_STANDARDS_DIR": str(FIXTURE_ROOT)}):
                journal.main([])
            application.assert_called_once_with(None)

            application.reset_mock()
            with patch("sys.argv", [
                "nx", "--nx-host-option", "host-value", "--root", str(FIXTURE_ROOT)
            ]):
                journal.main()
            application.assert_called_once_with(FIXTURE_ROOT)

            application.reset_mock()
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    journal.main(["--unknown-option"])
            self.assertEqual(raised.exception.code, 2)
            application.assert_not_called()

    def test_nx_dialog_resource_contains_unique_expected_controls(self):
        dialog_path = Path(__file__).resolve().parents[1] / "standards_search.dlx"
        root = ET.parse(dialog_path).getroot()
        items = [child for child in list(root) if child.tag == "item"]
        identifiers = [item.attrib["id"] for item in items]
        block_classes = [item.attrib["class"] for item in items]

        self.assertEqual(root.attrib["ContainerItems"], "12")
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(items), 12)
        self.assertIn("apply_search", identifiers)
        self.assertTrue({"code_group", "code_value", "add_code", "reset_search"} <= set(identifiers))
        for item in items:
            if item.get("class") == "UICOMP_enum":
                self.assertEqual(
                    item.find("./PropertyList/Property[@id='PresentationStyle']").get("selected"),
                    "0",
                )
        self.assertIn("UICOMP_string", block_classes)
        self.assertIn("UICOMP_enum", block_classes)
        self.assertIn("UICOMP_list_box", block_classes)
        self.assertIn("UGS::UI::Comp::DrawingArea", block_classes)


if __name__ == "__main__":
    unittest.main()