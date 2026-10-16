# -*- coding: utf-8 -*-
"""Kleine Helfer fuer die NXOpen-Entwicklung (Logging, Listing Window)."""
import logging
import os

import NXOpen

_DEV_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE = os.path.join(_DEV_ROOT, ".nxdev", "nx_dev.log")


def get_logger(name="nxdev"):
    """Logger, der nach .nxdev/nx_dev.log schreibt (Task 'NX: Log live verfolgen').

    Der Handler wird nur einmal pro NX-Session angehaengt, auch wenn der Loader
    dieses Modul bei jedem Lauf neu importiert.
    """
    logger = logging.getLogger(name)
    if not any(getattr(h, "_nxdev", False) for h in logger.handlers):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        h = logging.FileHandler(LOG_FILE, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                                         "%H:%M:%S"))
        h._nxdev = True
        logger.addHandler(h)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


def lw(*parts):
    """print()-Ersatz fuers Listing Window."""
    w = NXOpen.Session.GetSession().ListingWindow
    w.Open()
    w.WriteLine(" ".join(str(p) for p in parts))
