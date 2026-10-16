# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, ".nxdev")


def state_file(name):
    os.makedirs(STATE, exist_ok=True)
    return os.path.join(STATE, name)
