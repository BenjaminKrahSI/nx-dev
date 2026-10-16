{
  "folders": [
{{WORKSPACE_FOLDERS}}
  ],
  "settings": {
    "python.defaultInterpreterPath": "{{PY_EXE_FWD}}",
    // Gilt fuer die Beispiel-/Uebungsordner. Der Dev-Ordner nutzt pyrightconfig.json.
    "python.analysis.extraPaths": [
      "{{STUBS_FWD}}",
      "{{DEV_ROOT_FWD}}/src"
    ],
    "python.analysis.diagnosticSeverityOverrides": {
      "reportMissingModuleSource": "none"
    },
    "files.readonlyInclude": {
{{READONLY_GLOBS}}
    },
    "files.associations": { "*.men": "plaintext", "*.rtb": "plaintext" },
    "search.exclude": { "**/_debugpy/**": true, "**/__pycache__/**": true },
    "files.encoding": "utf8"
  },
  "extensions": {
    "recommendations": [
      "ms-python.python",
      "ms-python.vscode-pylance",
      "ms-python.debugpy"
    ]
  }
}
