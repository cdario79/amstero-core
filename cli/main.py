#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, "/workspace/repos/amstero-core/cli")
os.chdir("/workspace/repos/amstero-core/cli")

import questionary
from commands.config import (
    init_config,
    unlock,
    lock,
    status,
    add_credential,
    list_credentials
)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            init_config()
            return
        elif sys.argv[1] == "unlock":
            unlock()
            return
        elif sys.argv[1] == "lock":
            lock()
            return
        elif sys.argv[1] == "status":
            status()
            return
        elif sys.argv[1] == "add":
            add_credential()
            return
        elif sys.argv[1] == "list":
            list_credentials()
            return

    print("\n🤖 Amstero CLI")
    print("-" * 20)

    choice = questionary.select(
        "Scegli un comando:",
        choices=[
            "am config init - Setup iniziale user-config",
            "am config unlock - Sblocca i token con passphrase",
            "am config lock - Blocca i token (logout)",
            "am config status - Mostra stato credentials",
            "am config add - Aggiungi nuovo credential",
            "am config list - Lista tutti i credential",
            "am project list - Lista progetti",
            "am workspace status - Status workspace",
            "Esci"
        ]
    ).ask()

    if choice == "Esci":
        return

    if "config init" in choice:
        init_config()
    elif "config unlock" in choice:
        unlock()
    elif "config lock" in choice:
        lock()
    elif "config status" in choice:
        status()
    elif "config add" in choice:
        add_credential()
    elif "config list" in choice:
        list_credentials()
    elif "project list" in choice:
        print("\n📋 Progetti nel workspace:")
        print("  (nessun progetto configurato)")
    elif "workspace status" in choice:
        print("\n📊 Status workspace:")
        print("  Workspace: /workspace")
        print("  Repos: /workspace/repos")


if __name__ == "__main__":
    main()