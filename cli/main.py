#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, "/workspace/repos/amstero-core/cli")
os.chdir("/workspace/repos/amstero-core/cli")

import questionary
from commands.config import init_config


def main():
    print("\n🤖 Amstero CLI")
    print("-" * 20)

    choice = questionary.select(
        "Scegli un comando:",
        choices=[
            "am config init - Inizializza user-config",
            "am project list - Lista progetti",
            "am workspace status - Status workspace",
            "Esci"
        ]
    ).ask()

    if choice == "Esci":
        return

    if "config init" in choice:
        init_config()
    elif "project list" in choice:
        print("\n📋 Progetti nel workspace:")
        print("  (nessun progetto configurato - esegui prima am config init)")
    elif "workspace status" in choice:
        print("\n📊 Status workspace:")
        print("  Workspace: /workspace")
        print("  Repos: /workspace/repos")
    elif "shell" in choice:
        print("\n🐚 Apertura shell interattiva...")
        import os
        os.execvp("bash", ["bash"])


if __name__ == "__main__":
    main()