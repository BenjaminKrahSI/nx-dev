"""Compose the NX Block Styler controls used by the KFV standards pilot."""
import argparse
import copy
import os
import xml.etree.ElementTree as ET
from pathlib import Path


BLOCK_TEMPLATES = (
    "String.dlx",
    "Enumeration.dlx",
    "Button.dlx",
    "List Box.dlx",
    "Specify Point.dlx",
    "Drawing Area.dlx",
    "Label.dlx",
)
BUILDER_CONTROLS = (
    ("Enumeration.dlx", "code_group"),
    ("Enumeration.dlx", "code_value"),
    ("Button.dlx", "add_code"),
    ("Button.dlx", "apply_search"),
    ("Button.dlx", "reset_search"),
)


def _dialog_dir():
    nx_base = os.environ.get("UGII_BASE_DIR")
    candidates = []
    if nx_base:
        candidates.append(Path(nx_base) / "UGOPEN" / "SNAP" / "Dialog")
    candidates.append(
        Path(r"C:\Program Files\Siemens\NX2412\UGOPEN\SNAP\Dialog")
    )
    for candidate in candidates:
        if all((candidate / name).is_file() for name in BLOCK_TEMPLATES):
            return candidate
    raise FileNotFoundError(
        "NX-SNAP-Dialogvorlagen nicht gefunden. UGII_BASE_DIR muss auf die NX-Installation zeigen."
    )


def build(output_path):
    dialog_dir = _dialog_dir()
    root = ET.parse(dialog_dir / BLOCK_TEMPLATES[0]).getroot()
    root_items = [child for child in list(root) if child.tag == "item"]
    if len(root_items) != 1:
        raise ValueError("String.dlx enthaelt nicht genau einen Dialogblock.")

    items = [root_items[0]]
    for template_name in BLOCK_TEMPLATES[1:]:
        template_root = ET.parse(dialog_dir / template_name).getroot()
        template_items = [child for child in list(template_root) if child.tag == "item"]
        if len(template_items) != 1:
            raise ValueError("%s enthaelt nicht genau einen Dialogblock." % template_name)
        items.append(copy.deepcopy(template_items[0]))

    controls = []
    for template_name, identifier in BUILDER_CONTROLS:
        control = copy.deepcopy(ET.parse(dialog_dir / template_name).getroot().find("item"))
        control.set("id", identifier)
        control.set("name", identifier)
        control.find("./PropertyList/Property[@id='API Name']").set("value", identifier)
        controls.append(control)
    items[2:2] = controls
    for item in items:
        style = item.find("./PropertyList/Property[@id='PresentationStyle']")
        if item.get("class") == "UICOMP_enum":
            style.set("selected", "0")
        elif item.get("class") == "UICOMP_string":
            style.set("selected", "1")

    for item in list(root):
        if item.tag == "item":
            root.remove(item)
    insertion_index = next(
        (index for index, child in enumerate(list(root)) if child.tag == "PropertyList"),
        len(root),
    )
    for offset, item in enumerate(items):
        root.insert(insertion_index + offset, item)
    root.set("ContainerItems", str(len(items)))
    root.set("title", "KFV Standardsuche")

    title = root.find("./PropertyList/Property[@id='Title']")
    if title is not None:
        title.set("value", "KFV Standardsuche")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="UTF-8", xml_declaration=True)
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "standards_search.dlx",
    )
    args = parser.parse_args(argv)
    print(build(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())