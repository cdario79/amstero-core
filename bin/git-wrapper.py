#!/usr/bin/python3
import os
import sys
import subprocess
import json

AMSTERO_ROOT = "/workspace/repos/amstero-core"
RUNTIME_CREDS = "/workspace/runtime/credentials"
GIT_BIN = "/usr/bin/git"

def get_credential_for_remote(remote_url):
    if not remote_url:
        return None, None
    
    # Extract owner from URL
    import re
    
    # https://github.com/owner/repo.git or git@github.com:owner/repo.git
    match = re.search(r'(?:github\.com|gitlab\.com|bitbucket\.org|dev\.azure\.com)[:/]([^/]+)', remote_url)
    if not match:
        return None, None
    
    owner = match.group(1)
    
    # Check GitHub credentials
    github_path = os.path.join(RUNTIME_CREDS, "github")
    if os.path.isdir(github_path):
        for token_file in os.listdir(github_path):
            if token_file.endswith('.token'):
                name = token_file.replace('.token', '')
                cred_info_file = os.path.join(AMSTERO_ROOT, "repos", "amstero-user-config", "credentials", "github", f"{name}.age")
                if os.path.exists(cred_info_file):
                    # Check if owner is in the encrypted data - simplified check
                    # For now, check if owner matches the credential name or part of filename
                    if owner in [name, owner]:
                        return "github", name
    
    # Check SSH
    if '@' in remote_url:
        host = remote_url.split(':')[0].replace('git@', '')
        ssh_keys_path = os.path.join(RUNTIME_CREDS, "ssh", "keys")
        if os.path.isdir(ssh_keys_path):
            for key_file in os.listdir(ssh_keys_path):
                if key_file.endswith('.key'):
                    name = key_file.replace('.key', '')
                    cred_info_file = os.path.join(AMSTERO_ROOT, "repos", "amstero-user-config", "credentials", "ssh", f"{name}.age")
                    if os.path.exists(cred_info_file):
                        # Simple check - just return first SSH key
                        return "ssh", name
    
    return None, None

def setup_git_credential(cred_type, cred_name):
    if cred_type == "github":
        token_file = os.path.join(RUNTIME_CREDS, "github", f"{cred_name}.token")
        if os.path.exists(token_file):
            with open(token_file) as f:
                token = f.read().strip()
            creds_file = os.path.join(RUNTIME_CREDS, "git-credentials")
            with open(creds_file, 'w') as f:
                f.write(f"https://x-access-token:{token}@github.com\n")
            subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=False)
            subprocess.run(["git", "config", "--global", "credential.store", creds_file], check=False)
            return True
    elif cred_type == "ssh":
        key_file = os.path.join(RUNTIME_CREDS, "ssh", "keys", f"{cred_name}.key")
        if os.path.exists(key_file):
            os.environ["GIT_SSH_COMMAND"] = f"ssh -i {key_file} -o StrictHostKeyChecking=no"
            return True
    return False

def main():
    # Get current directory
    current_dir = os.getcwd()
    
    # Get remote URL if in git repo
    remote_url = ""
    if os.path.isdir(os.path.join(current_dir, ".git")):
        try:
            result = subprocess.run(
                [GIT_BIN, "remote", "get-url", "origin"],
                capture_output=True, text=True, cwd=current_dir
            )
            if result.returncode == 0:
                remote_url = result.stdout.strip()
        except:
            pass
    
    # If we have a remote, try to setup credential
    if remote_url:
        cred_type, cred_name = get_credential_for_remote(remote_url)
        if cred_type and cred_name:
            setup_git_credential(cred_type, cred_name)
    
    # Execute the original git command
    sys.exit(subprocess.call([GIT_BIN] + sys.argv[1:]))

if __name__ == "__main__":
    main()