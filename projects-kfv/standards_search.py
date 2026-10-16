"""Interactive KFV standards search and legacy pattern placement for NX 2412."""
import argparse
import importlib
import os
import struct
import sys
import tempfile
import traceback
from pathlib import Path

import NXOpen
import NXOpen.BlockStyler
import NXOpen.UF


KFV_ROOT = os.path.dirname(os.path.abspath(__file__))
DIALOG_PATH = os.path.join(KFV_ROOT, "standards_search.dlx")
PREVIEW_PATH = os.path.join(tempfile.gettempdir(), "nx_kfv_standard_preview.bmp")
MAX_VISIBLE_RESULTS = 300
LOCAL_TEST_ROOT = Path.home() / "Desktop" / "Test_Standards" / "Standards"

if KFV_ROOT not in sys.path:
    sys.path.insert(0, KFV_ROOT)

import standards_catalog

importlib.reload(standards_catalog)
from standards_catalog import BUILDER_GROUPS, CATEGORY_ORDER, code_options, resolve_root, scan, search


def _write_bmp(path, width, height, argb_pixels, scale=1):
    if width < 1 or height < 1 or scale < 1 or len(argb_pixels) != width * height:
        raise ValueError("Ungueltiges NX-Vorschaubild.")

    pixel_data = bytearray()
    for row in range(height - 1, -1, -1):
        start = row * width
        row_data = bytearray()
        for pixel_value in argb_pixels[start : start + width]:
            pixel = int(pixel_value) & 0xFFFFFFFF
            row_data.extend(
                bytes((
                    pixel & 0xFF,
                    (pixel >> 8) & 0xFF,
                    (pixel >> 16) & 0xFF,
                    (pixel >> 24) & 0xFF,
                )) * scale
            )
        pixel_data.extend(row_data * scale)

    width *= scale
    height *= scale
    file_size = 54 + len(pixel_data)
    file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    dib_header = struct.pack(
        "<IiiHHIIiiII", 40, width, height, 1, 32, 0, len(pixel_data), 2835, 2835, 0, 0
    )
    with open(path, "wb") as image_file:
        image_file.write(file_header)
        image_file.write(dib_header)
        image_file.write(pixel_data)


class StandardsSearch:
    def __init__(self, root=None, initial_query=""):
        self.root = resolve_root(root)
        self.initial_query = initial_query
        self.session = NXOpen.Session.GetSession()
        self.ui = NXOpen.UI.GetUI()
        if not os.path.isfile(DIALOG_PATH) or os.path.getmtime(__file__) > os.path.getmtime(DIALOG_PATH):
            import build_standards_search_dlx

            importlib.reload(build_standards_search_dlx).build(DIALOG_PATH)
        self.dialog = self.ui.CreateDialog(DIALOG_PATH)
        self.dialog.AddInitializeHandler(self.initialize_cb)
        self.dialog.AddUpdateHandler(self.update_cb)
        self.dialog.AddOkHandler(self.ok_cb)
        self.dialog.AddCloseHandler(self.close_cb)
        self.query_block = None
        self.category_block = None
        self.code_group = None
        self.code_value = None
        self.add_code = None
        self.search_button = None
        self.reset_search = None
        self.code_choices = {}
        self.matches = []
        self.updating_controls = False
        self.refresh_button = None
        self.results_list = None
        self.position_block = None
        self.preview_area = None
        self.status_block = None
        self.initialization_error = None
        self.catalog = []
        self.catalog_error = None
        self.category_options = {}
        self.result_by_label = {}
        self.preview_part = None
        self.preview_file_path = None

    def initialize_cb(self):
        self.updating_controls = True
        try:
            self.query_block = self.dialog.TopBlock.FindBlock("stringBlockID")
            self.category_block = self.dialog.TopBlock.FindBlock("enumBlockID")
            self.code_group = self.dialog.TopBlock.FindBlock("code_group")
            self.code_value = self.dialog.TopBlock.FindBlock("code_value")
            self.add_code = self.dialog.TopBlock.FindBlock("add_code")
            self.search_button = self.dialog.TopBlock.FindBlock("apply_search")
            self.reset_search = self.dialog.TopBlock.FindBlock("reset_search")
            self.refresh_button = self.dialog.TopBlock.FindBlock("button0")
            self.results_list = self.dialog.TopBlock.FindBlock("list_box0")
            self.position_block = self.dialog.TopBlock.FindBlock("positionBlockID")
            self.preview_area = self.dialog.TopBlock.FindBlock("drawingArea0")
            self.status_block = self.dialog.TopBlock.FindBlock("label0")

            self.query_block.Label = "Suchanfrage"
            self.query_block.PresentationStyleAsString = "Wide"
            self.query_block.WideValue = self.initial_query
            self.category_block.Label = "Kategorie"
            self.category_block.PresentationStyleAsString = "Option Menu"
            self.code_group.Label = "Codegruppe"
            self.code_group.SetEnumMembers(list(BUILDER_GROUPS))
            self.code_group.ValueAsString = next(iter(BUILDER_GROUPS))
            self.code_value.Label = "Code"
            self.add_code.Label = "Baustein hinzufuegen"
            self.search_button.Label = "Suchen"
            self.reset_search.Label = "Suche zuruecksetzen"
            self.refresh_button.Label = "Standards aktualisieren"
            self.results_list.Label = "Treffer"
            self.results_list.Height = 12
            self.position_block.Label = "Musterposition im aktiven Teil"
            self.preview_area.Width = 480
            self.preview_area.Height = 360
            self.status_block.Label = "Standards werden eingelesen ..."

            self._scan_catalog()
            self._apply_search()
        except Exception:
            self.initialization_error = traceback.format_exc()
            self._show_error(self.initialization_error)
        finally:
            self.updating_controls = False

    def update_cb(self, block):
        if self.updating_controls:
            return 0
        if self.initialization_error:
            return 1
        try:
            if block == self.refresh_button:
                self._scan_catalog()
                self._apply_search()
            elif block == self.category_block:
                self._apply_search()
            elif block == self.query_block:
                self._apply_search()
            elif block == self.search_button:
                self._apply_search()
            elif block == self.code_group:
                self.updating_controls = True
                try:
                    self.code_value.ValueAsString = "Auswaehlen"
                finally:
                    self.updating_controls = False
                self._apply_search()
            elif block == self.code_value:
                self._apply_search()
            elif block == self.add_code:
                value = self.code_choices.get(self.code_value.ValueAsString)
                if value:
                    prefix = BUILDER_GROUPS[self.code_group.ValueAsString]
                    term = "%s:%s" % (prefix, value)
                    terms = self.query_block.WideValue.split()
                    self.updating_controls = True
                    try:
                        if term not in terms:
                            self.query_block.WideValue = " ".join([*terms, term])
                        self.code_value.ValueAsString = "Auswaehlen"
                    finally:
                        self.updating_controls = False
                    self._apply_search()
            elif block == self.reset_search:
                self.updating_controls = True
                try:
                    self.query_block.WideValue = ""
                    self.category_block.ValueAsString = next(iter(self.category_options))
                    self.code_value.ValueAsString = "Auswaehlen"
                finally:
                    self.updating_controls = False
                self._apply_search()
            elif block == self.results_list:
                self._update_preview()
        except Exception:
            self._show_error(traceback.format_exc())
        return 0

    def _scan_catalog(self):
        try:
            self.catalog = scan(self.root)
            self.catalog_error = None
        except OSError as error:
            self.catalog = []
            self.catalog_error = str(error)
        self.updating_controls = True
        try:
            self._set_category_options()
        finally:
            self.updating_controls = False
        self.status_block.Label = "%d NX-Teile im KFV-Standardsordner" % len(self.catalog)

    def _set_category_options(self):
        counts = {}
        for item in self.catalog:
            category = item["category"]
            counts[category] = counts.get(category, 0) + 1

        previous_option = self.category_block.ValueAsString
        previous_category = self.category_options.get(previous_option)
        self.category_options = {"Alle (%d)" % len(self.catalog): None}
        for category in CATEGORY_ORDER:
            count = counts.get(category, 0)
            if count:
                self.category_options["%s (%d)" % (category, count)] = category

        options = list(self.category_options)
        self.category_block.SetEnumMembers(options)
        selected = next(
            (
                option
                for option, category in self.category_options.items()
                if category == previous_category
            ),
            options[0],
        )
        self.category_block.ValueAsString = selected

    def _apply_search(self):
        previous = self.updating_controls
        self.updating_controls = True
        try:
            self._render_search()
        finally:
            self.updating_controls = previous

    def _set_code_options(self):
        previous = self.code_choices.get(self.code_value.ValueAsString)
        prefix = BUILDER_GROUPS[self.code_group.ValueAsString]
        self.code_choices = {"Auswaehlen": None}
        self.code_choices.update({
            "%s (%d)" % (value, count): value
            for value, count in code_options(self.matches, prefix)
        })
        self.code_value.SetEnumMembers(list(self.code_choices))
        self.code_value.ValueAsString = next(
            (label for label, value in self.code_choices.items() if value == previous),
            "Auswaehlen",
        )
        self.add_code.Enable = len(self.code_choices) > 1

    def _render_search(self):
        if self.catalog_error:
            self.matches = []
            self._set_code_options()
            self.result_by_label = {}
            self.results_list.SetListItems([])
            self.preview_area.Image = ""
            self._release_preview_part()
            self.status_block.Label = "KFV-Ordner nicht erreichbar: %s" % self.catalog_error
            return
        query = self.query_block.WideValue.split()
        matches = search(self.catalog, query)
        selected_category = self.category_options.get(self.category_block.ValueAsString)
        if selected_category:
            matches = [item for item in matches if item["category"] == selected_category]
        self.matches = matches
        self._set_code_options()
        value = self.code_choices.get(self.code_value.ValueAsString)
        if value:
            prefix = BUILDER_GROUPS[self.code_group.ValueAsString]
            matches = search(matches, ["%s:%s" % (prefix, value)])
        self.matches = matches
        self.result_by_label = {}
        labels = []
        for index, item in enumerate(matches[:MAX_VISIBLE_RESULTS], 1):
            label = "%04d | %s | %s" % (
                index,
                item["file_name"],
                item["directory_category"],
            )
            labels.append(label)
            self.result_by_label[label] = item
        self.results_list.SetListItems(labels)
        self.preview_area.Image = ""
        self._release_preview_part()
        if len(matches) > MAX_VISIBLE_RESULTS:
            self.status_block.Label = "Zeige %d von %d Treffern; Suche verfeinern" % (
                MAX_VISIBLE_RESULTS,
                len(matches),
            )
        else:
            self.status_block.Label = "%d Treffer" % len(matches)

    def _load_part(self, file_path):
        parts = self.session.Parts
        try:
            return parts.FindObject(file_path)
        except Exception:
            part, load_status = parts.OpenBase(file_path)
            load_status.Dispose()
            return part

    def _update_preview(self):
        selected = self.results_list.GetSelectedItemStrings()
        self.preview_area.Image = ""
        self._release_preview_part()
        if not selected:
            return

        item = self.result_by_label.get(selected[0])
        if item is None:
            return
        file_path = os.path.join(self.root, item["relative_path"])
        self.preview_part = self._load_part(file_path)
        self.preview_file_path = file_path
        width, height, pixels = self.preview_part.GetPreviewImage()
        if width < 1 or height < 1 or not pixels:
            self.status_block.Label = "Für diesen Treffer ist kein Modell-Vorschaubild gespeichert."
            self._release_preview_part()
            return
        _write_bmp(PREVIEW_PATH, width, height, pixels, scale=2)
        self.preview_area.Image = PREVIEW_PATH
        self.status_block.Label = "Vorschau: %s" % item["file_name"]

    def _release_preview_part(self):
        # NX may mark a model-preview part as changed while loading its stored image.
        # Keep it in the session instead of closing it from a UI callback.
        self.preview_part = None
        self.preview_file_path = None

    def ok_cb(self):
        selected = self.results_list.GetSelectedItemStrings()
        if not selected:
            self._show_message("Bitte zuerst ein Suchergebnis auswählen.")
            return 1
        item = self.result_by_label.get(selected[0])
        if item is None:
            self._show_message("Das ausgewählte Suchergebnis ist nicht mehr verfügbar.")
            return 1

        work_part = self.session.Parts.Work
        if work_part is None:
            self._show_message("Zum Bemustern muss ein Zielteil aktiv sein.")
            return 1

        file_path = os.path.join(self.root, item["relative_path"])
        undo_mark = None
        try:
            pattern_api = NXOpen.UF.UFSession.GetUFSession().Patt
            import_pattern = getattr(pattern_api, "Import", None)
            if not callable(import_pattern):
                self._show_message(
                    "Die Legacy-Musterschnittstelle UF.Patt.Import ist nicht verfuegbar. "
                    "Es wird keine Komponente eingefuegt."
                )
                return 1
            orientation = work_part.WCS.CoordinateSystem.Orientation.Element
            position = self.position_block.Point
            transform = [
                orientation.Xx, orientation.Xy, orientation.Xz,
                orientation.Yx, orientation.Yy, orientation.Yz,
                orientation.Zx, orientation.Zy, orientation.Zz,
                position.X, position.Y, position.Z, 1.0,
            ]
            undo_mark = self.session.SetUndoMark(
                NXOpen.Session.MarkVisibility.Visible, "KFV-Muster platzieren"
            )
            pattern_tag = import_pattern(file_path, Path(file_path).stem, 1, transform)
            if not pattern_tag:
                raise RuntimeError("Die Musterschnittstelle hat kein Pattern-Objekt erzeugt.")
            self._listing_message("Legacy-Muster platziert: %s" % item["file_name"])
            return 0
        except Exception:
            error = traceback.format_exc()
            if undo_mark is not None:
                try:
                    self.session.UndoToMark(undo_mark, None)
                    self.session.DeleteUndoMark(undo_mark, None)
                except Exception:
                    error += "\nRueckgaengig machen fehlgeschlagen:\n" + traceback.format_exc()
            self._show_error(error)
            return 1

    def close_cb(self):
        self._release_preview_part()
        try:
            if os.path.isfile(PREVIEW_PATH):
                os.remove(PREVIEW_PATH)
        except OSError:
            pass
        return 0

    def _listing_message(self, message):
        listing = self.session.ListingWindow
        listing.Open()
        listing.WriteLine(message)

    def _show_message(self, message):
        self.ui.NXMessageBox.Show(
            "KFV-Standardsuche", NXOpen.NXMessageBox.DialogType.Information, message
        )

    def _show_error(self, message):
        self.ui.NXMessageBox.Show(
            "KFV-Standardsuche", NXOpen.NXMessageBox.DialogType.Error, message
        )

    def launch(self):
        return self.dialog.Launch()

    def dispose(self):
        if self.dialog is not None:
            self.dialog.Dispose()
            self.dialog = None
        self.close_cb()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--root", type=Path,
        default=None if os.environ.get("KFV_STANDARDS_DIR") else LOCAL_TEST_ROOT,
        help="Standardsordner; sonst KFV_STANDARDS_DIR oder lokaler Desktop-Testbestand",
    )
    if argv is None:
        args, _ = parser.parse_known_args()
    else:
        args = parser.parse_args(argv)
    try:
        app = StandardsSearch(args.root)
    except ValueError as error:
        parser.error(str(error))
    try:
        app.launch()
    finally:
        app.dispose()


if __name__ == "__main__":
    main()