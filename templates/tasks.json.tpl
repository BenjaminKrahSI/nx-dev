{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "NX: aktuelle Datei als Ziel setzen",
      "type": "process",
      "command": "{{TOOL_PY_FWD}}",
      "args": [
        "${workspaceFolder}/tools/set_target.py",
        "${file}"
      ],
      "options": {
        "cwd": "${workspaceFolder}/tools"
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent",
        "panel": "shared",
        "clear": true
      }
    },
    {
      "label": "NX: Batch ausfuehren (run_journal)",
      "type": "process",
      "command": "{{TOOL_PY_FWD}}",
      "args": [
        "${workspaceFolder}/tools/run_batch.py",
        "${file}"
      ],
      "options": {
        "cwd": "${workspaceFolder}/tools"
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "clear": true
      }
    },
    {
      "label": "NX: Log live verfolgen",
      "type": "process",
      "command": "{{TOOL_PY_FWD}}",
      "args": [
        "${workspaceFolder}/tools/tail_log.py"
      ],
      "options": {
        "cwd": "${workspaceFolder}/tools"
      },
      "problemMatcher": [],
      "isBackground": true,
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "NX: Debug-Modus umschalten",
      "type": "process",
      "command": "{{TOOL_PY_FWD}}",
      "args": [
        "${workspaceFolder}/tools/toggle_debug.py"
      ],
      "options": {
        "cwd": "${workspaceFolder}/tools"
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared",
        "clear": true
      }
    }
  ]
}
