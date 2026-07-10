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

This server exposes the **complete AnkiConnect API** — 100+ tools covering
everything AnkiConnect can do. Grouped by category:

**Connection & misc** — `anki_version`, `request_permission`,
`list_supported_actions`, `sync`, `reload_collection`, `get_profiles`,
`get_active_profile`, `load_profile`, `export_package`, `import_package`,
`raw_request` (escape hatch: call any AnkiConnect action directly).

**Decks** — `list_decks`, `list_decks_with_ids`, `get_decks_for_cards`,
`create_deck`, `delete_deck`, `move_cards`, `deck_stats`.
Deck options: `get_deck_config`, `save_deck_config`, `set_deck_config_id`,
`clone_deck_config`, `remove_deck_config`.

**Note types (models)** — `list_note_types`, `list_note_types_with_ids`,
`find_note_types_by_id`, `find_note_types_by_name`, `note_type_fields`,
`note_type_field_descriptions`, `note_type_field_fonts`,
`note_type_fields_on_templates`, `create_note_type`, `note_type_templates`,
`note_type_styling`, `update_note_type_templates`, `update_note_type_styling`,
`find_and_replace_in_note_types`.
Structure editing: `note_type_template_{rename,reposition,add,remove}`,
`note_type_field_{rename,reposition,add,remove,set_font,set_font_size,set_description}`.

**Notes** — `add_note`, `add_notes`, `can_add_notes`, `find_notes`,
`notes_info`, `notes_mod_time`, `update_note_fields`, `update_note`,
`update_note_tags`, `get_note_tags`, `delete_notes`, `remove_empty_notes`.

**Tags** — `list_tags`, `add_tags`, `remove_tags`, `clear_unused_tags`,
`replace_tag`, `replace_tag_in_all_notes`.

**Cards** — `find_cards`, `cards_info`, `cards_to_notes`, `cards_mod_time`,
`suspend_cards`, `unsuspend_cards`, `are_suspended`, `are_due`,
`get_intervals`, `get_ease_factors`, `set_ease_factors`, `set_card_values`,
`forget_cards`, `relearn_cards`, `set_due_date`, `answer_cards`.

**Media** — `store_media_file`, `retrieve_media_file`, `list_media_files`,
`get_media_dir_path`, `delete_media_file`.

**Statistics** — `cards_reviewed_today`, `cards_reviewed_by_day`,
`collection_stats_html`, `card_reviews`, `get_reviews_of_cards`,
`get_latest_review_id`, `insert_reviews`.

**GUI (drive Anki's windows)** — `gui_browse`, `gui_selected_notes`,
`gui_add_cards`, `gui_edit_note`, `gui_current_card`, `gui_show_question`,
`gui_show_answer`, `gui_answer_card`, `gui_undo`, `gui_deck_overview`,
`gui_deck_browser`, `gui_deck_review`, `gui_import_file`, `gui_check_database`,
`gui_exit_anki`.

Every tool has a description the assistant reads, so you can just ask in plain
language — e.g. "move all suspended cards in Deck A to Deck B", "create a Cloze
note type called X", "reschedule these cards to be due in 3 days".

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
