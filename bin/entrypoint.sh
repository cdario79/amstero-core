#!/bin/bash

set -e

echo ""
echo "🤖 Amstero Core - Avvio"
echo "========================"

USER_CONFIG="/workspace/repos/amstero-user-config"
RUNTIME_CREDS="/workspace/runtime/credentials"

if [ -d "$USER_CONFIG" ]; then
    ACCOUNTS_FILE="$USER_CONFIG/accounts.json"

    if [ -f "$ACCOUNTS_FILE" ]; then
        if [ -f "$RUNTIME_CREDS/.unlocked" ]; then
            echo "✅ Credentials già sbloccati"
        else
            echo ""
            echo "🔐 I tuoi credentials sono bloccati."
            read -p "Inserisci la passphrase per sbloccarli (invio per ignorare): " -s passphrase
            echo ""

            if [ -n "$passphrase" ]; then
                mkdir -p "$RUNTIME_CREDS"

                for cred_file in "$USER_CONFIG"/credentials/*.age; do
                    if [ -f "$cred_file" ]; then
                        name=$(basename "$cred_file" .age)

                        decrypted=$(echo "$passphrase" | age -d -p "$cred_file" 2>/dev/null) || continue

                        echo "$decrypted" > "$RUNTIME_CREDS/$name.token"
                        echo "   ✅ $name sbloccato"
                    fi
                done

                default_cred=$(grep -o '"default"[[:space:]]*:[[:space:]]*"[^"]*"' "$ACCOUNTS_FILE" | sed 's/.*"\([^"]*\)".*/\1/')

                if [ -n "$default_cred" ] && [ -f "$RUNTIME_CREDS/${default_cred}.token" ]; then
                    touch "$RUNTIME_CREDS/.unlocked"

                    token=$(cat "$RUNTIME_CREDS/${default_cred}.token")
                    echo "https://x-access-token:${token}@github.com" > "$RUNTIME_CREDS/git-credentials"
                    git config --global credential.helper "store --file /workspace/runtime/credentials/git-credentials"

                    echo "✅ Git credential helper configurato!"
                fi

                rm -f /tmp/git_cred
            fi
        fi
    fi
else
    echo "ℹ️ User-config non configurato. Esegui 'am config init' per iniziare."
fi

echo ""
echo "Benvenuto nel container Amstero!"
echo "Usa 'am' per i comandi, 'am config status' per vedere lo stato."
echo ""

exec /bin/bash