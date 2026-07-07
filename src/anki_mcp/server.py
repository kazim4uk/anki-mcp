"""MCP server exposing Anki operations via AnkiConnect.

Each tool is a thin wrapper around one or more AnkiConnect actions. The
docstrings are what Claude reads to decide when and how to call a tool, so
they double as the user-facing tool descriptions.

Search queries (``query`` arguments) use Anki's native search syntax, e.g.
``deck:Default``, ``tag:new``, ``deck:"My Deck" -is:suspended``.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from anki_mcp.anki_connect import invoke

mcp = FastMCP("anki")


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------

@mcp.tool()
def anki_version() -> dict[str, Any]:
    """Health check: confirm AnkiConnect is reachable and return its API
    version (expected: 6). Call this first if other tools are failing."""
    return {"anki_connect_version": invoke("version")}


# --------------------------------------------------------------------------
# Decks
# --------------------------------------------------------------------------

@mcp.tool()
def list_decks() -> list[str]:
    """List the names of all decks in the collection."""
    return invoke("deckNames")


@mcp.tool()
def create_deck(name: str) -> dict[str, Any]:
    """Create a new deck. Use '::' in the name to create a nested subdeck
    (e.g. 'Languages::Romanian'). Existing decks are left untouched."""
    return {"deck_id": invoke("createDeck", deck=name)}


@mcp.tool()
def delete_deck(name: str, cards_too: bool = True) -> str:
    """Delete a deck. If cards_too is True (default) its cards are deleted as
    well; otherwise the cards are moved to the Default deck. Irreversible."""
    invoke("deleteDecks", decks=[name], cardsToo=cards_too)
    return f"Deleted deck '{name}'."


@mcp.tool()
def deck_stats(decks: list[str]) -> dict[str, Any]:
    """Get review statistics (new/learning/review counts, totals) for the
    given deck names."""
    return invoke("getDeckStats", decks=decks)


# --------------------------------------------------------------------------
# Note types (models)
# --------------------------------------------------------------------------

@mcp.tool()
def list_note_types() -> list[str]:
    """List all note type (model) names, e.g. 'Basic', 'Cloze'."""
    return invoke("modelNames")


@mcp.tool()
def note_type_fields(model_name: str) -> list[str]:
    """List the field names of a note type, in order (e.g. Basic ->
    ['Front', 'Back']). Use this before add_note to supply the right fields."""
    return invoke("modelFieldNames", modelName=model_name)


# --------------------------------------------------------------------------
# Notes
# --------------------------------------------------------------------------

@mcp.tool()
def add_note(
    deck: str,
    model: str,
    fields: dict[str, str],
    tags: list[str] | None = None,
    allow_duplicate: bool = False,
) -> dict[str, Any]:
    """Add a single note. 'fields' maps the note type's field names to their
    HTML/text values (e.g. {'Front': '...', 'Back': '...'}). The deck and
    note type (model) must already exist. Returns the new note ID."""
    note = {
        "deckName": deck,
        "modelName": model,
        "fields": fields,
        "tags": tags or [],
        "options": {"allowDuplicate": allow_duplicate},
    }
    return {"note_id": invoke("addNote", note=note)}


@mcp.tool()
def add_notes(notes: list[dict[str, Any]]) -> dict[str, Any]:
    """Add many notes in one call. Each item is
    {'deck': str, 'model': str, 'fields': {..}, 'tags': [..]?,
    'allow_duplicate': bool?}. Returns a note ID per note (null where a note
    could not be added, e.g. a duplicate)."""
    payload = []
    for n in notes:
        payload.append(
            {
                "deckName": n["deck"],
                "modelName": n["model"],
                "fields": n["fields"],
                "tags": n.get("tags", []),
                "options": {"allowDuplicate": n.get("allow_duplicate", False)},
            }
        )
    ids = invoke("addNotes", notes=payload)
    added = sum(1 for i in ids if i is not None)
    return {"note_ids": ids, "added": added, "failed": len(ids) - added}


@mcp.tool()
def find_notes(query: str, limit: int = 50) -> dict[str, Any]:
    """Search notes with Anki's query syntax (e.g. 'deck:Default tag:new').
    Returns the total count, all matching note IDs, and detailed field data
    for up to 'limit' notes."""
    note_ids = invoke("findNotes", query=query)
    info = invoke("notesInfo", notes=note_ids[:limit]) if note_ids else []
    return {"count": len(note_ids), "note_ids": note_ids, "notes": info}


@mcp.tool()
def update_note_fields(note_id: int, fields: dict[str, str]) -> str:
    """Update one or more fields of an existing note. Only the fields you pass
    are changed; omitted fields keep their current values."""
    invoke("updateNoteFields", note={"id": note_id, "fields": fields})
    return f"Updated note {note_id}."


@mcp.tool()
def delete_notes(note_ids: list[int]) -> str:
    """Permanently delete the given notes (and all their cards). Irreversible."""
    invoke("deleteNotes", notes=note_ids)
    return f"Deleted {len(note_ids)} note(s)."


# --------------------------------------------------------------------------
# Tags
# --------------------------------------------------------------------------

@mcp.tool()
def list_tags() -> list[str]:
    """List every tag used anywhere in the collection."""
    return invoke("getTags")


@mcp.tool()
def add_tags(note_ids: list[int], tags: list[str]) -> str:
    """Add one or more tags to the given notes."""
    invoke("addTags", notes=note_ids, tags=" ".join(tags))
    return f"Added {tags} to {len(note_ids)} note(s)."


@mcp.tool()
def remove_tags(note_ids: list[int], tags: list[str]) -> str:
    """Remove one or more tags from the given notes."""
    invoke("removeTags", notes=note_ids, tags=" ".join(tags))
    return f"Removed {tags} from {len(note_ids)} note(s)."


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------

@mcp.tool()
def find_cards(query: str, limit: int = 50) -> dict[str, Any]:
    """Search cards with Anki's query syntax. Returns the total count, all
    matching card IDs, and detailed info (deck, note, interval, due,
    suspended state) for up to 'limit' cards."""
    card_ids = invoke("findCards", query=query)
    info = invoke("cardsInfo", cards=card_ids[:limit]) if card_ids else []
    return {"count": len(card_ids), "card_ids": card_ids, "cards": info}


@mcp.tool()
def suspend_cards(card_ids: list[int]) -> str:
    """Suspend the given cards so they stop appearing in reviews."""
    invoke("suspend", cards=card_ids)
    return f"Suspended {len(card_ids)} card(s)."


@mcp.tool()
def unsuspend_cards(card_ids: list[int]) -> str:
    """Unsuspend the given cards so they return to the review queue."""
    invoke("unsuspend", cards=card_ids)
    return f"Unsuspended {len(card_ids)} card(s)."


# --------------------------------------------------------------------------
# Media & service
# --------------------------------------------------------------------------

@mcp.tool()
def store_media_file(
    filename: str,
    path: str | None = None,
    url: str | None = None,
    data_b64: str | None = None,
) -> dict[str, Any]:
    """Store a media file (image/audio) in the collection's media folder so it
    can be referenced from a note, e.g. '[sound:word.mp3]' or
    '<img src="pic.png">'. Provide exactly one source: a local 'path', a
    'url' to download, or base64 'data_b64'. Returns the stored filename."""
    sources = [s for s in (path, url, data_b64) if s]
    if len(sources) != 1:
        raise ValueError("Provide exactly one of: path, url, data_b64.")
    kwargs: dict[str, Any] = {"filename": filename}
    if path:
        kwargs["path"] = path
    elif url:
        kwargs["url"] = url
    else:
        kwargs["data"] = data_b64
    return {"filename": invoke("storeMediaFile", **kwargs)}


@mcp.tool()
def cards_reviewed_today() -> dict[str, Any]:
    """Return how many cards have been reviewed so far today."""
    return {"reviewed_today": invoke("getNumCardsReviewedToday")}


@mcp.tool()
def sync() -> str:
    """Sync the local collection with AnkiWeb (so changes reach AnkiDroid /
    other devices). Requires AnkiWeb login configured in Anki Desktop."""
    invoke("sync")
    return "Sync triggered."


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
