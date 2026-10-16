"""Interactive KFV standards search and component insertion for NX 2412."""
import os
import struct
import sys
import tempfile
import traceback
from pathlib import Path

import NXOpen
import NXOpen.BlockStyler
import NXOpen.Assemblies


NX_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(NX_ROOT)
TOOLS_ROOT = os.path.join(REPO_ROOT, "tools")
DIALOG_PATH = os.path.join(NX_ROOT, "standards_search.dlx")
PREVIEW_PATH = os.path.join(tempfile.gettempdir(), "nx_kfv_standard_preview.bmp")
MAX_VISIBLE_RESULTS = 300

if TOOLS_ROOT not in sys.path:
    sys.path.insert(0, TOOLS_ROOT)

from standards_catalog import CATEGORY_ORDER, DEFAULT_ROOT, scan, search


def _write_bmp(path, width, height, argb_pixels):
    if width < 1 or height < 1 or len(argb_pixels) != width * height:
        raise ValueError("Ungueltiges NX-Vorschaubild.")

    pixel_data = bytearray()
    for row in range(height - 1, -1, -1):
        start = row * width
        for pixel_value in argb_pixels[start : start + width]:
            pixel = int(pixel_value) & 0xFFFFFFFF
            pixel_data.extend(
                (
                    pixel & 0xFF,
                    (pixel >> 8) & 0xFF,
                    (pixel >> 16) & 0xFF,
                    (pixel >> 24) & 0xFF,
                )
            )

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
    def __init__(self):
        self.session = NXOpen.Session.GetSession()
        self.ui = NXOpen.UI.GetUI()
        if not os.path.isfile(DIALOG_PATH):
            from build_standards_search_dlx import build

            build(DIALOG_PATH)
        self.dialog = self.ui.CreateDialog(DIALOG_PATH)
        self.dialog.AddInitializeHandler(self.initialize_cb)
        self.dialog.AddUpdateHandler(self.update_cb)
        self.dialog.AddOkHandler(self.ok_cb)
        self.dialog.AddCloseHandler(self.close_cb)
        self.query_block = None
        self.category_block = None
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
        try:
            self.query_block = self.dialog.TopBlock.FindBlock("stringBlockID")
            self.category_block = self.dialog.TopBlock.FindBlock("enumBlockID")
            self.refresh_button = self.dialog.TopBlock.FindBlock("button0")
            self.results_list = self.dialog.TopBlock.FindBlock("list_box0")
            self.position_block = self.dialog.TopBlock.FindBlock("positionBlockID")
            self.preview_area = self.dialog.TopBlock.FindBlock("drawingArea0")
            self.status_block = self.dialog.TopBlock.FindBlock("label0")

            self.query_block.Label = "Suchbegriffe und Filter"
            self.category_block.Label = "Kategorie"
            self.category_block.PresentationStyleAsString = "Option Menu"
            self.refresh_button.Label = "Standards aktualisieren"
            self.results_list.Label = "Treffer"
            self.results_list.Height = 12
            self.position_block.Label = "Einfügepunkt in der Baugruppe"
            self.preview_area.Width = 240
            self.preview_area.Height = 180
            self.status_block.Label = "Standards werden eingelesen ..."

            self._scan_catalog()
            self._apply_search()
        except Exception:
            self.initialization_error = traceback.format_exc()
            self._show_error(self.initialization_error)

    def update_cb(self, block):
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
            elif block == self.results_list:
                self._update_preview()
        except Exception:
            self._show_error(traceback.format_exc())
        return 0

    def _scan_catalog(self):
        try:
            self.catalog = scan(DEFAULT_ROOT)
            self.catalog_error = None
        except OSError as error:
            self.catalog = []
            self.catalog_error = str(error)
        self._set_category_options()
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
        if self.catalog_error:
            self.result_by_label = {}
            self.results_list.SetListItems([])
            self.preview_area.Image = ""
            self._release_preview_part()
            self.status_block.Label = "KFV-Ordner nicht erreichbar: %s" % self.catalog_error
            return
        query = self.query_block.Value.split()
        matches = search(self.catalog, query)
        selected_category = self.category_options.get(self.category_block.ValueAsString)
        if selected_category:
            matches = [item for item in matches if item["category"] == selected_category]
        self.result_by_label = {}
        labels = []
        for index, item in enumerate(matches[:MAX_VISIBLE_RESULTS], 1):
            label = "%04d | %s | %s" % (
                index,
                item["file_name"],
                item["relative_path"],
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
        file_path = os.path.join(DEFAULT_ROOT, item["relative_path"])
        self.preview_part = self._load_part(file_path)
        self.preview_file_path = file_path
        width, height, pixels = self.preview_part.GetPreviewImage()
        if width < 1 or height < 1 or not pixels:
            self.status_block.Label = "Für diesen Treffer ist kein Modell-Vorschaubild gespeichert."
            self._release_preview_part()
            return
        _write_bmp(PREVIEW_PATH, width, height, pixels)
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
        if work_part is None or work_part.ComponentAssembly.RootComponent is None:
            self._show_message("Zum Einfügen muss eine NX-Baugruppe aktiv sein.")
            return 1

        file_path = os.path.join(DEFAULT_ROOT, item["relative_path"])
        try:
            part = self._part_for_insert(file_path)
            builder = work_part.AssemblyManager.CreateAddComponentBuilder()
            try:
                builder.SetCount(1)
                builder.SetScatterOption(False)
                builder.SetInitialLocationType(
                    NXOpen.Assemblies.AddComponentBuilder.LocationType.DisplayedPartWCS
                )
                builder.SetInitialLocationAndOrientation(
                    self.position_block.Point,
                    work_part.WCS.CoordinateSystem.Orientation.Element,
                )
                builder.ReferenceSet = "None"
                builder.Layer = -1
                builder.ComponentName = Path(file_path).stem
                builder.SetPartsToAdd([part])
                builder.Commit()
            finally:
                builder.Destroy()

            self._listing_message("Komponente eingefügt: %s" % item["file_name"])
            return 0
        except Exception:
            self._show_error(traceback.format_exc())
            return 1

    def _part_for_insert(self, file_path):
        if (
            self.preview_part is not None
            and os.path.normcase(os.path.abspath(self.preview_file_path))
            == os.path.normcase(os.path.abspath(file_path))
        ):
            return self.preview_part
        return self._load_part(file_path)

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


def main():
    app = StandardsSearch()
    try:
        app.launch()
    finally:
        app.dispose()


if __name__ == "__main__":
    main()