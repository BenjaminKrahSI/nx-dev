VERSION 120
! NX Dev - generiert von setup.ps1
! Erscheint im NX-Menue (Menue > NX Dev). Befehle lassen sich per
! Anpassen (Strg+1) auf die Schnellzugriffsleiste ziehen / mit Shortcut belegen.
EDIT UG_GATEWAY_MAIN_MENUBAR

BEFORE UG_HELP
  CASCADE_BUTTON NXDEV_CASCADE
  LABEL NX Dev
END_OF_BEFORE

MENU NXDEV_CASCADE
  BUTTON NXDEV_RUN_TARGET
  LABEL Ziel aus VS Code ausfuehren
  ACTIONS {{DEV_ROOT}}\nx\nx_dev_loader.py

  BUTTON NXDEV_DISCOVER
  LABEL Umgebung erfassen (Discovery)
  ACTIONS {{DEV_ROOT}}\nx\nx_discover.py
END_OF_MENU
