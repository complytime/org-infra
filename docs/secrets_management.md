# Secure Secrets Management with SOPS and age

This document explains how to use SOPS (Secrets OPerationS) with `age` to manage encrypted secrets in this repository, ensuring secure collaboration among maintainers and seamless integration with GitHub Actions.

## Why SOPS + age?

We use SOPS with `age` for the following reasons:
*   **Easy Editing:** SOPS decrypts files into your default text editor for plaintext modifications and automatically re-encrypts them on save.
*   **Multi-User Support:** Secrets are encrypted for multiple `age` public keys, allowing any authorized maintainer to decrypt and modify them using their private key.
*   **Git Friendly:** Encrypted files (YAML, JSON, etc.) are text-based and safe to commit to Git.
*   **CI/CD Integration:** SOPS can decrypt secrets within GitHub Actions using a dedicated key, enabling automation without exposing raw secrets.

## Local Setup for Maintainers

To work with encrypted secrets, each maintainer needs to:

1.  **Install `age` and `sops`:**
    ```bash
    # For macOS with Homebrew:
    brew install age sops

    # For Fedora:
    sudo dnf install age
    # sops is not packaged for Fedora; install via Homebrew/LinuxBrew:
    brew install sops
    # Or install from GitHub releases:
    curl -LO https://github.com/getsops/sops/releases/download/v3.11.0/sops-v3.11.0.linux.amd64
    sudo mv sops-v3.11.0.linux.amd64 /usr/local/bin/sops
    sudo chmod +x /usr/local/bin/sops

    # For other operating systems, refer to their official documentation.
    # age: https://github.com/FiloSottile/age#installation
    # sops: https://github.com/getsops/sops#installation
    ```

2.  **Generate an `age` key pair:**
    If you don't already have one, generate a new `age` key. It's recommended to store it in the default location.
    ```bash
    mkdir -p ~/.config/age
    age-keygen -o ~/.config/age/keys.txt
    ```
    *Keep your private key (`~/.config/age/keys.txt`) secure and never share it.*
    *The output will show your `Public key: age1...`. You will need this to be added to `.sops.yaml`.*

3.  **Set `SOPS_AGE_KEY_FILE` environment variable:**
    Add the following line to your shell profile (e.g., `~/.zshrc`, `~/.bashrc`, `~/.profile`) to tell SOPS where to find your private key:
    ```bash
    export SOPS_AGE_KEY_FILE=~/.config/age/keys.txt
    ```
    Then, reload your shell config: `source ~/.zshrc` (or your respective file).

## Repository Structure

*   **`.sops.yaml`**: This file defines the encryption rules, specifying which `age` public keys are authorized to decrypt files matching certain patterns (e.g., `*.enc.yaml`).
*   **`secrets.enc.yaml`**: This is the encrypted file where your secrets are stored. It is safe to commit this file to Git.

## How to Edit Secrets

To edit the `secrets.enc.yaml` file:

```bash
sops org-infra/secrets.enc.yaml
```
SOPS will decrypt the file, open it in your default text editor (e.g., `vim`, `nano`, `VS Code`), and automatically re-encrypt it when you save and close the editor.

## Adding New Maintainers

To grant a new maintainer access to the encrypted secrets:

1.  **Get their `age` Public Key:** Ask the new maintainer to generate their `age` key (if they haven't) and provide you with their public key (e.g., `age1...`).
2.  **Update `.sops.yaml`:** Edit the `org-infra/.sops.yaml` file to add their public key to the `age` recipient list.
    Example:
    ```yaml
    creation_rules:
      - path_regex: .*.enc.yaml$
        age: >-
          age1YOUR_PUBLIC_KEY_1,
          age1NEW_MAINTAINERS_PUBLIC_KEY
    ```
3.  **Update Keys in `secrets.enc.yaml`:** Run the `sops updatekeys` command from the `org-infra` directory to re-encrypt the `secrets.enc.yaml` file with the updated key list.
    ```bash
    cd org-infra
    sops updatekeys secrets.enc.yaml
    ```
    This ensures that the file is encrypted for all specified public keys.
4.  **Commit Changes:** Commit both the updated `.sops.yaml` and `secrets.enc.yaml` files to the repository.

## GitHub Actions Integration

For GitHub Actions to decrypt secrets, a dedicated `age` key is used, so your personal key does not need to be shared.

1.  **CI Private Key:**
    During the setup, a private key was generated specifically for GitHub Actions. This key needs to be stored in GitHub Secrets.

2.  **Add to GitHub Repository Secrets:**
    You must add this private key to your GitHub repository's secrets:
    *   Go to your repository on GitHub.
    *   Navigate to **Settings** > **Secrets and variables** > **Actions**.
    *   Click "New repository secret".
    *   Name the secret `SOPS_AGE_KEY`.
    *   Paste the *generated CI private key value* into the "Secret value" field.
        *Remember: This is the full `AGE-SECRET-KEY-...` string you received when the CI key was generated.*

3.  **Using Secrets in Workflows:**
    Refer to the `org-infra/.github/workflows/demo_secrets.yml` workflow for an example of how to decrypt `secrets.enc.yaml` in a GitHub Action. The workflow uses the `SOPS_AGE_KEY` secret as an environment variable to allow `sops` to decrypt the file.
