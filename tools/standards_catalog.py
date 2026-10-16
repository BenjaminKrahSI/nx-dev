"""Read-only search prototype for NX standard part filenames."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path


DEFAULT_ROOT = Path(
    r"C:\Users\benjamin.krah\Desktop\Test_Standards\Standards"
)
VARIANT_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:\d+ZK|[BKW]\d{3}|T\d+)(?![A-Za-z0-9])", re.IGNORECASE
)
SERIES_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:HS|AS)\d{2,4}[A-Z]{0,3}(?![A-Za-z0-9])", re.IGNORECASE
)
DIMENSION_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:[-_.]\d+)?[ED](?![A-Za-z0-9])"
)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*")
LANGUAGE_MARKERS = {"englisch", "english", "en"}
QUALIFIER_MARKERS = {
    "alt",
    "kopie",
    "neu",
    "original",
    "orig",
    "vorschlag",
}
FILE_KIND_MARKERS = {"fraesbild", "fräsbild", "pattern"}
CATEGORY_PATTERNS = (
    ("Fräsbilder", re.compile(r"fraesbild|fräsbild|pattern", re.IGNORECASE)),
    ("Senkungen", re.compile(r"senk", re.IGNORECASE)),
    ("Treibstangen", re.compile(r"treibstang", re.IGNORECASE)),
    (
        "Zusatzkästen",
        re.compile(
            r"zusatzk(?:asten|aesten)|(?<![A-Za-z0-9])ZK(?:\d+|(?=[_. -]|$))",
            re.IGNORECASE,
        ),
    ),
    (
        "Hauptschlösser",
        re.compile(r"hauptschloss|hauptschloesser|(?<![A-Za-z0-9])HS\d{2,4}", re.IGNORECASE),
    ),
    (
        "Zeichnungsvorlagen",
        re.compile(
            r"schriftfeld|schriftkopf|rahmen_|(?:^|[_-])sap_|dina\d|din_a\d",
            re.IGNORECASE,
        ),
    ),
)
CATEGORY_ORDER = tuple(category for category, _ in CATEGORY_PATTERNS) + ("Sonstiges",)
FILTER_FIELDS = {
    "family": "families",
    "familie": "families",
    "series": "series",
    "serie": "series",
    "dimension": "dimensions",
    "dimensions": "dimensions",
    "mass": "dimensions",
    "measure": "dimensions",
    "language": "languages",
    "lang": "languages",
    "sprache": "languages",
    "tag": "qualifiers",
    "marker": "qualifiers",
    "folder": "directory_category",
    "ordner": "directory_category",
    "category": "category",
    "kategorie": "category",
    "cat": "category",
    "kind": "file_kind",
    "art": "file_kind",
    "name": "file_name",
    "datei": "file_name",
}


def _normalise(value):
    return (
        value.casefold()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def _classify_category(stem):
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(stem):
            return category
    return "Sonstiges"


def classify_path(path, root):
    """Extract provisional tokens without assigning unverified semantics."""
    path = Path(path)
    root = Path(root)
    stem = path.stem
    tokens = TOKEN_PATTERN.findall(stem)
    families = VARIANT_PATTERN.findall(stem)
    series = SERIES_PATTERN.findall(stem)
    dimensions = DIMENSION_PATTERN.findall(stem)
    languages = [token for token in tokens if token.casefold() in LANGUAGE_MARKERS]
    qualifiers = [token for token in tokens if token.casefold() in QUALIFIER_MARKERS]

    recognised = set()
    for group in (families, series, dimensions, languages, qualifiers):
        for token in group:
            recognised.add(token.casefold())
            recognised.update(
                part.casefold() for part in re.split(r"[-_.]", token)
            )
    recognised.update(
        token.casefold() for token in tokens if token.casefold() in FILE_KIND_MARKERS
    )
    unclassified = [token for token in tokens if token.casefold() not in recognised]

    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    directory_category = relative.parent.as_posix() or "."
    category = _classify_category(stem)
    file_kind = next(
        (token for token in tokens if token.casefold() in FILE_KIND_MARKERS),
        "",
    )

    return {
        "file_name": path.name,
        "relative_path": relative.as_posix(),
        "category": category,
        "directory_category": directory_category,
        "file_kind": file_kind,
        "families": families,
        "series": series,
        "dimensions": dimensions,
        "languages": languages,
        "qualifiers": qualifiers,
        "unclassified_tokens": unclassified,
    }


def scan(root):
    """Return a deterministic catalog of NX part files under root."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError("Standards-Ordner nicht erreichbar: %s" % root)
    paths = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.casefold() == ".prt"),
        key=lambda path: _normalise(path.relative_to(root).as_posix()),
    )
    return [classify_path(path, root) for path in paths]


def search(catalog, query):
    terms = [term.strip() for term in query if term.strip()]
    if not terms:
        return catalog
    matches = []
    for item in catalog:
        searchable = _normalise(
            " ".join(
                [
                    item["file_name"],
                    item["relative_path"],
                    item["category"],
                    item["directory_category"],
                    item["file_kind"],
                    *item["families"],
                    *item["series"],
                    *item["dimensions"],
                    *item["languages"],
                    *item["qualifiers"],
                    *item["unclassified_tokens"],
                ]
            )
        )
        matched = True
        for term in terms:
            if ":" in term:
                field_name, value = term.split(":", 1)
                field = FILTER_FIELDS.get(_normalise(field_name))
                if field and value:
                    values = item[field]
                    if not isinstance(values, list):
                        values = [values]
                    if not any(_normalise(value) in _normalise(candidate) for candidate in values):
                        matched = False
                        break
                    continue
            if _normalise(term) not in searchable:
                matched = False
                break
        if matched:
            matches.append(item)
    return matches


def _write_results(results, output_format):
    if output_format == "json":
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    if output_format == "csv":
        fields = (
            "file_name",
            "relative_path",
            "category",
            "directory_category",
            "file_kind",
            "families",
            "series",
            "dimensions",
            "languages",
            "qualifiers",
            "unclassified_tokens",
        )
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    **result,
                    **{
                        field: ";".join(result[field])
                        for field in fields
                        if isinstance(result[field], list)
                    },
                }
            )
        return
    for result in results:
        print(
            "[{category}] {file_name} | Familie: {families} | Serie: {series} "
            "| Masse: {dimensions} | Unklassifiziert: {unclassified_tokens}".format(
                category=result["category"],
                file_name=result["file_name"],
                families=", ".join(result["families"]) or "-",
                series=", ".join(result["series"]) or "-",
                dimensions=", ".join(result["dimensions"]) or "-",
                unclassified_tokens=", ".join(result["unclassified_tokens"]) or "-",
            )
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Durchsucht NX-Standards anhand von Dateinamen und Ordnern."
    )
    parser.add_argument("query", nargs="*", help="Suchbegriffe; alle muessen passen")
    parser.add_argument("--limit", type=int, default=50, help="maximale Trefferzahl; 0 = unbegrenzt")
    parser.add_argument("--format", choices=("text", "json", "csv"), default="text")
    args = parser.parse_args(argv)

    try:
        results = search(scan(DEFAULT_ROOT), args.query)
    except OSError as error:
        parser.error(str(error))
    total = len(results)
    if args.limit > 0:
        results = results[: args.limit]
    if args.format == "text":
        limited = args.limit > 0 and len(results) < total
        print("Treffer: %d%s" % (total, " (Ausgabe begrenzt)" if limited else ""))
    _write_results(results, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())