# anki-mcp

An [MCP](https://modelcontextprotocol.io) server that lets AI assistants (Claude
Code, Claude Desktop, and other MCP clients) manage your [Anki](https://apps.ankiweb.net)
collection — decks, note types, notes, cards, tags and media — through the
**AnkiConnect** add-on.

It is a thin, local wrapper: each MCP tool maps to one or more AnkiConnect
actions over `http://127.0.0.1:8765`. Nothing leaves your machine and no
telemetry is collected — requests are proxied straight to your local Anki.

> **Unofficial project.** Not affiliated with, endorsed by, or sponsored by
> Anki / AnkiWeb. "Anki" is a trademark of its respective owner. AnkiConnect is
> a separate third-party add-on. See [Prior art](#prior-art) for similar tools.

## Prerequisites (one-time)

1. Install **Anki Desktop** — https://apps.ankiweb.net
2. Install the **AnkiConnect** add-on:
   Anki → *Tools → Add-ons → Get Add-ons…* → paste code **`2055492159`** → OK →
   restart Anki.
3. Keep **Anki Desktop running** whenever you use the tools.

> AnkiConnect only talks to Anki **Desktop**. To get cards onto your phone,
> use the `sync` tool (or Anki's own sync) and pull them in AnkiDroid via AnkiWeb.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/kazim4uk/anki-mcp.git
cd anki-mcp
python -m venv .venv
```

Install into the venv:

```bash
# Windows (PowerShell)
.venv\Scripts\python.exe -m pip install -e .

# macOS / Linux
.venv/bin/python -m pip install -e .
```

### Smoke test (optional, verifies the connection)

With Anki running:

```bash
# Windows
.venv\Scripts\python.exe scripts\smoke_test.py
# macOS / Linux
.venv/bin/python scripts/smoke_test.py
```

Expected: `AnkiConnect version: 6` and a list of your decks. With Anki closed
you'll get a friendly "cannot reach AnkiConnect" message — that confirms the
error handling works.

## Register the server

Use the **absolute path** to the venv's console script (installed as
`anki-mcp`). It works from any working directory.

- Windows: `<repo>\.venv\Scripts\anki-mcp.exe`
- macOS / Linux: `<repo>/.venv/bin/anki-mcp`

### Claude Code

```bash
claude mcp add anki -s user -- "/absolute/path/to/anki-mcp/.venv/bin/anki-mcp"
```

### Claude Desktop

Add to your `claude_desktop_config.json`
(`%APPDATA%\Claude\` on Windows, `~/Library/Application Support/Claude/` on
macOS), then restart Claude Desktop:

```json
{
  "mcpServers": {
    "anki": {
      "command": "/absolute/path/to/anki-mcp/.venv/bin/anki-mcp"
    }
  }
}
```

On Windows use the `.exe` and escaped backslashes, e.g.
`"C:\\path\\to\\anki-mcp\\.venv\\Scripts\\anki-mcp.exe"`.

## Tools

| Tool | What it does |
|------|--------------|
| `anki_version` | Health check — is AnkiConnect reachable? |
| `list_decks` | List all deck names |
| `create_deck` | Create a deck (`A::B` = nested) |
| `delete_deck` | Delete a deck (optionally keep its cards) |
| `deck_stats` | Review stats for given decks |
| `list_note_types` | List note type (model) names |
| `note_type_fields` | Field names of a note type |
| `add_note` | Add one note |
| `add_notes` | Add many notes at once |
| `find_notes` | Search notes → IDs + field data |
| `update_note_fields` | Edit fields of an existing note |
| `delete_notes` | Delete notes (and their cards) |
| `list_tags` | List all tags |
| `add_tags` / `remove_tags` | Tag / untag notes |
| `find_cards` | Search cards → IDs + card info |
| `suspend_cards` / `unsuspend_cards` | Suspend / unsuspend cards |
| `move_cards` | Move cards to another deck (created if missing) |
| `store_media_file` | Add image/audio to the media folder |
| `cards_reviewed_today` | Count of today's reviews |
| `sync` | Sync with AnkiWeb |

### Search syntax

`find_notes` / `find_cards` use Anki's native
[search syntax](https://docs.ankiweb.net/searching.html), e.g.:

- `deck:Default`
- `tag:new -is:suspended`
- `deck:"My Deck" front:*hello*`

## Configuration

Environment variables (see [`.env.example`](.env.example)) — all optional:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANKI_CONNECT_URL` | `http://127.0.0.1:8765` | AnkiConnect endpoint |
| `ANKI_CONNECT_API_KEY` | *(none)* | Only if you set an `apiKey` in the add-on config |
| `ANKI_CONNECT_TIMEOUT` | `15` | Request timeout (seconds) |

## Troubleshooting

- **"Cannot reach AnkiConnect"** — Anki Desktop isn't running, or the add-on
  isn't installed. Start Anki; verify `2055492159` is under *Tools → Add-ons*.
- **Tool calls hang / time out** — Anki is showing a modal dialog (e.g. a sync
  prompt). Dismiss it in Anki.
- **`duplicate` error on `add_note`** — pass `allow_duplicate=true`, or change a
  field so the first field is unique.

## Prior art

Several other open-source Anki MCP servers exist — worth a look if you want
different trade-offs (TypeScript, read-only, extra features):
[ankimcp/anki-mcp-server](https://github.com/ankimcp/anki-mcp-server),
[nailuoGG/anki-mcp-server](https://github.com/nailuoGG/anki-mcp-server),
[CamdenClark/anki-mcp-server](https://github.com/CamdenClark/anki-mcp-server).

## Credits

Built on [AnkiConnect](https://github.com/FooSoft/anki-connect) and the
[Model Context Protocol](https://modelcontextprotocol.io).

## License

[MIT](LICENSE)
