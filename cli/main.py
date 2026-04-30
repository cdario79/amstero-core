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
    list_credentials,
    remove_credential
)


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "init":
            init_config()
            return
        elif cmd == "unlock":
            unlock()
            return
        elif cmd == "lock":
            lock()
            return
        elif cmd == "status":
            status()
            return
        elif cmd == "list":
            list_credentials()
            return
        elif cmd == "add":
            add_credential(sys.argv[2:] if len(sys.argv) > 2 else [])
            return
        elif cmd == "remove":
            remove_credential(sys.argv[2:] if len(sys.argv) > 2 else [])
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
            "am config add - Aggiungi nuovo credential (wizard)",
            "am config add github - Aggiungi credential GitHub",
            "am config list - Lista tutti i credential",
            "am config remove - Rimuovi credential",
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
        if "github" in choice:
            add_credential(["--type", "github"])
        else:
            add_credential()
    elif "config list" in choice:
        list_credentials()
    elif "config remove" in choice:
        remove_credential()
    elif "project list" in choice:
        print("\n📋 Progetti nel workspace:")
        print("  (nessun progetto configurato)")
    elif "workspace status" in choice:
        print("\n📊 Status workspace:")
        print("  Workspace: /workspace")
        print("  Repos: /workspace/repos")


if __name__ == "__main__":
    main()