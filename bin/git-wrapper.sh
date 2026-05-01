#!/bin/bash

AMSTERO_ROOT="/workspace/repos/amstero-core"
RUNTIME_CREDS="/workspace/runtime/credentials"
GIT_BIN="/usr/bin/git-orig"

get_credential_for_remote() {
    local remote_url="$1"
    
    if [[ -z "$remote_url" ]]; then
        return 1
    fi
    
    # Extract owner from URL patterns:
    # https://github.com/owner/repo.git
    # git@github.com:owner/repo.git
    # https://github.com/org/repo.git
    
    local owner=""
    
    if [[ "$remote_url" =~ github\.com[:/]([^/]+) ]]; then
        owner="${BASH_REMATCH[1]}"
    elif [[ "$remote_url" =~ gitlab\.com[:/]([^/]+) ]]; then
        owner="${BASH_REMATCH[1]}"
    elif [[ "$remote_url" =~ bitbucket\.org[:/]([^/]+) ]]; then
        owner="${BASH_REMATCH[1]}"
    elif [[ "$remote_url" =~ dev\.azure\.com[:/]([^/]+) ]]; then
        owner="${BASH_REMATCH[1]}"
    fi
    
    if [[ -z "$owner" ]]; then
        return 1
    fi
    
    # Check GitHub credentials
    if [[ -d "$RUNTIME_CREDS/github" ]]; then
        for cred_file in "$RUNTIME_CREDS/github"/*.token; do
            if [[ -f "$cred_file" ]]; then
                local name=$(basename "$cred_file" .token)
                local cred_info_file="$AMSTERO_ROOT/repos/amstero-user-config/credentials/github/${name}.age"
                
                if [[ -f "$cred_info_file" ]]; then
                    # Check if this owner is in the owners list
                    if grep -q "\"$owner\"" "$cred_info_file" 2>/dev/null; then
                        echo "github:$name"
                        return 0
                    fi
                fi
            fi
        done
    fi
    
    # Check SSH credentials for hosts
    if [[ "$remote_url" =~ @([^:]+): ]]; then
        local host="${BASH_REMATCH[1]}"
        if [[ -d "$RUNTIME_CREDS/ssh/keys" ]]; then
            for key_file in "$RUNTIME_CREDS/ssh/keys"/*.key; do
                if [[ -f "$key_file" ]]; then
                    local name=$(basename "$key_file" .key)
                    local cred_info_file="$AMSTERO_ROOT/repos/amstero-user-config/credentials/ssh/${name}.age"
                    
                    if [[ -f "$cred_info_file" ]] && grep -q "$host" "$cred_info_file" 2>/dev/null; then
                        echo "ssh:$name"
                        return 0
                    fi
                fi
            done
        fi
    fi
    
    return 1
}

setup_git_credential() {
    local cred_type="$1"
    local cred_name="$2"
    
    if [[ "$cred_type" == "github" ]]; then
        local token_file="$RUNTIME_CREDS/github/${cred_name}.token"
        if [[ -f "$token_file" ]]; then
            local token=$(cat "$token_file")
            echo "https://x-access-token:${token}@github.com" > "$RUNTIME_CREDS/git-credentials"
            git config --global credential.helper store
            git config --global credential.store "$RUNTIME_CREDS/git-credentials"
        fi
    elif [[ "$cred_type" == "ssh" ]]; then
        local key_file="$RUNTIME_CREDS/ssh/keys/${cred_name}.key"
        if [[ -f "$key_file" ]]; then
            export GIT_SSH_COMMAND="ssh -i $key_file -o StrictHostKeyChecking=no"
        fi
    fi
}

get_git_user_info() {
    local cred_type="$1"
    local cred_name="$2"
    
    if [[ "$cred_type" == "github" ]]; then
        local cred_info_file="$AMSTERO_ROOT/repos/amstero-user-config/credentials/github/${cred_name}.age"
        if [[ -f "$cred_info_file" ]]; then
            # Read from decrypted data - we'd need to store it somewhere accessible
            # For now, try to get from runtime
            local token_file="$RUNTIME_CREDS/github/${cred_name}.token"
            # This is a limitation - we'd need to store user/email separately
        fi
    fi
}

# Main logic
CURRENT_DIR=$(pwd)

# Get remote URL if in a git repo
REMOTE_URL=""
if [[ -d "$CURRENT_DIR/.git" ]]; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
fi

# If we have a remote, try to setup credential
if [[ -n "$REMOTE_URL" ]]; then
    CRED_RESULT=$(get_credential_for_remote "$REMOTE_URL" 2>/dev/null || true)
    if [[ -n "$CRED_RESULT" ]]; then
        CRED_TYPE="${CRED_RESULT%%:*}"
        CRED_NAME="${CRED_RESULT#*:}"
        setup_git_credential "$CRED_TYPE" "$CRED_NAME"
    fi
fi

# Execute the original git command
exec "$GIT_BIN" "$@"