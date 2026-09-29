# Codex

Codex reads the key from an environment variable, so the key never goes into `~/.codex/config.toml`.

**1. Store the key.** macOS or Linux — add to `~/.zshrc` or `~/.bashrc`:

```bash
export UMLOUT_API_KEY="YOUR_API_KEY"
```

Windows:

```powershell
setx UMLOUT_API_KEY "YOUR_API_KEY"
```

**2. Add the server** (writes `~/.codex/config.toml`):

```bash
codex mcp add umlout --url https://www.umlout.com/mcp/http --bearer-token-env-var UMLOUT_API_KEY
```

which is the same as writing this yourself:

```toml
[mcp_servers.umlout]
url = "https://www.umlout.com/mcp/http"
bearer_token_env_var = "UMLOUT_API_KEY"
```

**3. Open a new terminal, then start Codex.** A shell sees `UMLOUT_API_KEY` only if it was opened
after you set it. The Codex app and the editor extension, started from the Dock or the Start menu,
do not read `~/.zshrc`: start them from that terminal, or set the variable where your system gives
it to apps.
