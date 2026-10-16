# -*- coding: utf-8 -*-
"""Rauchtest: in VS Code 'NX: aktuelle Datei als Ziel setzen', dann in NX ausfuehren."""
import NXOpen
from nxdev import get_logger, lw

log = get_logger("hello_nx")


def main():
    session = NXOpen.Session.GetSession()
    work = session.Parts.Work
    if work is None:
        lw("Kein Work Part geladen.")
        log.warning("kein Work Part")
        return
    bodies = list(work.Bodies)
    lw("Work Part: %s - %d Koerper" % (work.Leaf, len(bodies)))
    log.info("%s: %d Koerper", work.Leaf, len(bodies))


if __name__ == "__main__":
    main()
