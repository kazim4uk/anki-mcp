"""MCP server exposing the full AnkiConnect API to AI assistants.

Each tool is a thin wrapper around one AnkiConnect action. The docstrings are
what the assistant reads to decide when and how to call a tool, so they double
as the user-facing tool descriptions.

Search queries (``query`` arguments) use Anki's native search syntax, e.g.
``deck:Default``, ``tag:new``, ``deck:"My Deck" -is:suspended``.

Anki concepts used throughout:
- A *note* holds the data (fields + tags) and belongs to a *note type* (model).
- Each note generates one or more *cards* (what you actually review).
- You move/suspend/schedule *cards*; you edit fields/tags on *notes*.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from anki_mcp.anki_connect import invoke

mcp = FastMCP("anki")


def _note_payload(
    deck: str,
    model: str,
    fields: dict[str, str],
    tags: list[str] | None,
    allow_duplicate: bool,
) -> dict[str, Any]:
    """Build the AnkiConnect ``note`` object shared by add/can-add/gui tools."""
    return {
        "deckName": deck,
        "modelName": model,
        "fields": fields,
        "tags": tags or [],
        "options": {"allowDuplicate": allow_duplicate},
    }


# ==========================================================================
# Connection & miscellaneous
# ==========================================================================

@mcp.tool()
def anki_version() -> dict[str, Any]:
    """Health check: confirm AnkiConnect is reachable and return its API
    version (expected: 6). Call this first if other tools are failing."""
    return {"anki_connect_version": invoke("version")}


@mcp.tool()
def request_permission() -> dict[str, Any]:
    """Ask AnkiConnect whether this client is permitted to make requests.
    Returns the permission status (and requires user approval in Anki the
    first time if an origin allow-list is configured)."""
    return invoke("requestPermission")


@mcp.tool()
def list_supported_actions() -> list[str]:
    """List every AnkiConnect action supported by the running Anki/add-on
    version (via apiReflect). Useful to discover capabilities or debug."""
    return invoke("apiReflect", scopes=["actions"], actions=None)["actions"]


@mcp.tool()
def sync() -> str:
    """Sync the local collection with AnkiWeb (so changes reach AnkiDroid /
    other devices). Requires AnkiWeb login configured in Anki Desktop."""
    invoke("sync")
    return "Sync triggered."


@mcp.tool()
def reload_collection() -> str:
    """Tell Anki to reload the collection from disk."""
    invoke("reloadCollection")
    return "Collection reloaded."


@mcp.tool()
def get_profiles() -> list[str]:
    """List the names of all Anki user profiles."""
    return invoke("getProfiles")


@mcp.tool()
def get_active_profile() -> dict[str, Any]:
    """Return the name of the currently active Anki profile."""
    return {"active_profile": invoke("getActiveProfile")}


@mcp.tool()
def load_profile(name: str) -> str:
    """Switch Anki to the given user profile."""
    ok = invoke("loadProfile", name=name)
    return f"Loaded profile '{name}'." if ok else f"Could not load '{name}'."


@mcp.tool()
def export_package(deck: str, path: str, include_sched: bool = False) -> str:
    """Export a deck to an .apkg file at 'path'. Set include_sched=True to keep
    scheduling info (due dates, review history)."""
    invoke("exportPackage", deck=deck, path=path, includeSched=include_sched)
    return f"Exported deck '{deck}' to {path}."


@mcp.tool()
def import_package(path: str) -> str:
    """Import an .apkg package file from 'path' into the collection."""
    invoke("importPackage", path=path)
    return f"Imported package {path}."


@mcp.tool()
def raw_request(action: str, params: dict[str, Any] | None = None) -> Any:
    """Escape hatch: call ANY AnkiConnect action by name with raw params.
    Use only when no dedicated tool covers what you need (e.g. a brand-new
    AnkiConnect action). 'params' must match AnkiConnect's exact keys."""
    return invoke(action, **(params or {}))


# ==========================================================================
# Decks
# ==========================================================================

@mcp.tool()
def list_decks() -> list[str]:
    """List the names of all decks in the collection."""
    return invoke("deckNames")


@mcp.tool()
def list_decks_with_ids() -> dict[str, Any]:
    """List all decks as a map of deck name -> deck ID."""
    return invoke("deckNamesAndIds")


@mcp.tool()
def get_decks_for_cards(card_ids: list[int]) -> dict[str, Any]:
    """Given card IDs, return a map of deck name -> the card IDs it contains."""
    return invoke("getDecks", cards=card_ids)


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
def move_cards(card_ids: list[int], deck: str) -> str:
    """Move the given cards to another deck. The target deck is created
    automatically if it does not exist. Note: in Anki you move *cards*, not
    notes — get card IDs from `find_cards`, or from the `cards` field returned
    by `find_notes`."""
    invoke("changeDeck", cards=card_ids, deck=deck)
    return f"Moved {len(card_ids)} card(s) to deck '{deck}'."


@mcp.tool()
def deck_stats(decks: list[str]) -> dict[str, Any]:
    """Get review statistics (new/learning/review counts, totals) for the
    given deck names."""
    return invoke("getDeckStats", decks=decks)


# --- Deck options (config groups) -----------------------------------------

@mcp.tool()
def get_deck_config(deck: str) -> dict[str, Any]:
    """Get the options/config group for a deck (new/review limits, intervals,
    etc.)."""
    return invoke("getDeckConfig", deck=deck)


@mcp.tool()
def save_deck_config(config: dict[str, Any]) -> str:
    """Save a modified deck options group. Pass a config object previously
    obtained from get_deck_config with your changes applied."""
    ok = invoke("saveDeckConfig", config=config)
    return "Saved deck config." if ok else "Failed to save deck config."


@mcp.tool()
def set_deck_config_id(decks: list[str], config_id: int) -> str:
    """Assign the given decks to an existing options group by its config ID."""
    ok = invoke("setDeckConfigId", decks=decks, configId=config_id)
    return "Assigned config group." if ok else "Failed to assign config group."


@mcp.tool()
def clone_deck_config(name: str, clone_from: int | None = None) -> dict[str, Any]:
    """Create a new options group named 'name', optionally cloned from an
    existing group's config ID. Returns the new config ID (or False)."""
    return {"config_id": invoke("cloneDeckConfigId", name=name, cloneFrom=clone_from)}


@mcp.tool()
def remove_deck_config(config_id: int) -> str:
    """Remove an options group by its config ID (decks using it revert to the
    default group)."""
    ok = invoke("removeDeckConfigId", configId=config_id)
    return "Removed config group." if ok else "Failed to remove config group."


# ==========================================================================
# Note types (models)
# ==========================================================================

@mcp.tool()
def list_note_types() -> list[str]:
    """List all note type (model) names, e.g. 'Basic', 'Cloze'."""
    return invoke("modelNames")


@mcp.tool()
def list_note_types_with_ids() -> dict[str, Any]:
    """List all note types as a map of model name -> model ID."""
    return invoke("modelNamesAndIds")


@mcp.tool()
def find_note_types_by_id(model_ids: list[int]) -> list[dict[str, Any]]:
    """Get full definitions (fields, templates, css) for note types by ID."""
    return invoke("findModelsById", modelIds=model_ids)


@mcp.tool()
def find_note_types_by_name(model_names: list[str]) -> list[dict[str, Any]]:
    """Get full definitions (fields, templates, css) for note types by name."""
    return invoke("findModelsByName", modelNames=model_names)


@mcp.tool()
def note_type_fields(model_name: str) -> list[str]:
    """List the field names of a note type, in order (e.g. Basic ->
    ['Front', 'Back']). Use this before add_note to supply the right fields."""
    return invoke("modelFieldNames", modelName=model_name)


@mcp.tool()
def note_type_field_descriptions(model_name: str) -> list[str]:
    """List each field's description (placeholder text) for a note type."""
    return invoke("modelFieldDescriptions", modelName=model_name)


@mcp.tool()
def note_type_field_fonts(model_name: str) -> dict[str, Any]:
    """Return the editor font and size configured for each field of a note
    type."""
    return invoke("modelFieldFonts", modelName=model_name)


@mcp.tool()
def note_type_fields_on_templates(model_name: str) -> dict[str, Any]:
    """Return, per card template, which fields appear on the front and back."""
    return invoke("modelFieldsOnTemplates", modelName=model_name)


@mcp.tool()
def create_note_type(
    model_name: str,
    fields: list[str],
    card_templates: list[dict[str, str]],
    css: str | None = None,
    is_cloze: bool = False,
) -> dict[str, Any]:
    """Create a new note type. 'fields' are the ordered field names.
    'card_templates' is a list of {'Name','Front','Back'} template dicts whose
    Front/Back are HTML using {{Field}} placeholders. Optional 'css' styles the
    cards; set is_cloze=True for a cloze-deletion type."""
    return invoke(
        "createModel",
        modelName=model_name,
        inOrderFields=fields,
        css=css,
        isCloze=is_cloze,
        cardTemplates=card_templates,
    )


@mcp.tool()
def note_type_templates(model_name: str) -> dict[str, Any]:
    """Return the card templates (Front/Back HTML) of a note type."""
    return invoke("modelTemplates", modelName=model_name)


@mcp.tool()
def note_type_styling(model_name: str) -> dict[str, Any]:
    """Return the CSS styling of a note type."""
    return invoke("modelStyling", modelName=model_name)


@mcp.tool()
def update_note_type_templates(model_name: str, templates: dict[str, Any]) -> str:
    """Update card templates of a note type. 'templates' maps template name ->
    {'Front': html, 'Back': html}."""
    invoke("updateModelTemplates", model={"name": model_name, "templates": templates})
    return f"Updated templates of '{model_name}'."


@mcp.tool()
def update_note_type_styling(model_name: str, css: str) -> str:
    """Replace the CSS styling of a note type."""
    invoke("updateModelStyling", model={"name": model_name, "css": css})
    return f"Updated styling of '{model_name}'."


@mcp.tool()
def find_and_replace_in_note_types(
    model_name: str,
    find_text: str,
    replace_text: str,
    front: bool = True,
    back: bool = True,
    css: bool = False,
) -> dict[str, Any]:
    """Find & replace text within a note type's templates/css. Toggle which
    parts to touch with front/back/css."""
    return invoke(
        "findAndReplaceInModels",
        model={
            "modelName": model_name,
            "findText": find_text,
            "replaceText": replace_text,
            "front": front,
            "back": back,
            "css": css,
        },
    )


# --- Note type template / field structure editing -------------------------

@mcp.tool()
def note_type_template_rename(model_name: str, old_name: str, new_name: str) -> str:
    """Rename a card template within a note type."""
    invoke("modelTemplateRename", modelName=model_name,
           oldTemplateName=old_name, newTemplateName=new_name)
    return f"Renamed template '{old_name}' -> '{new_name}'."


@mcp.tool()
def note_type_template_reposition(model_name: str, template_name: str, index: int) -> str:
    """Move a card template to a new position (0-based index)."""
    invoke("modelTemplateReposition", modelName=model_name,
           templateName=template_name, index=index)
    return f"Repositioned template '{template_name}' to {index}."


@mcp.tool()
def note_type_template_add(model_name: str, template: dict[str, str]) -> str:
    """Add a card template to a note type. 'template' is
    {'Name','Front','Back'}."""
    invoke("modelTemplateAdd", modelName=model_name, template=template)
    return f"Added template to '{model_name}'."


@mcp.tool()
def note_type_template_remove(model_name: str, template_name: str) -> str:
    """Remove a card template from a note type. Irreversible."""
    invoke("modelTemplateRemove", modelName=model_name, templateName=template_name)
    return f"Removed template '{template_name}'."


@mcp.tool()
def note_type_field_rename(model_name: str, old_name: str, new_name: str) -> str:
    """Rename a field of a note type."""
    invoke("modelFieldRename", modelName=model_name,
           oldFieldName=old_name, newFieldName=new_name)
    return f"Renamed field '{old_name}' -> '{new_name}'."


@mcp.tool()
def note_type_field_reposition(model_name: str, field_name: str, index: int) -> str:
    """Move a field to a new position (0-based index)."""
    invoke("modelFieldReposition", modelName=model_name,
           fieldName=field_name, index=index)
    return f"Repositioned field '{field_name}' to {index}."


@mcp.tool()
def note_type_field_add(model_name: str, field_name: str, index: int | None = None) -> str:
    """Add a new field to a note type, optionally at a 0-based index."""
    params: dict[str, Any] = {"modelName": model_name, "fieldName": field_name}
    if index is not None:
        params["index"] = index
    invoke("modelFieldAdd", **params)
    return f"Added field '{field_name}' to '{model_name}'."


@mcp.tool()
def note_type_field_remove(model_name: str, field_name: str) -> str:
    """Remove a field from a note type. Irreversible (data in it is lost)."""
    invoke("modelFieldRemove", modelName=model_name, fieldName=field_name)
    return f"Removed field '{field_name}'."


@mcp.tool()
def note_type_field_set_font(model_name: str, field_name: str, font: str) -> str:
    """Set the editor font of a field."""
    invoke("modelFieldSetFont", modelName=model_name, fieldName=field_name, font=font)
    return f"Set font of '{field_name}' to {font}."


@mcp.tool()
def note_type_field_set_font_size(model_name: str, field_name: str, font_size: int) -> str:
    """Set the editor font size of a field."""
    invoke("modelFieldSetFontSize", modelName=model_name,
           fieldName=field_name, fontSize=font_size)
    return f"Set font size of '{field_name}' to {font_size}."


@mcp.tool()
def note_type_field_set_description(model_name: str, field_name: str, description: str) -> str:
    """Set the description (placeholder text) of a field."""
    invoke("modelFieldSetDescription", modelName=model_name,
           fieldName=field_name, description=description)
    return f"Set description of '{field_name}'."


# ==========================================================================
# Notes
# ==========================================================================

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
    note = _note_payload(deck, model, fields, tags, allow_duplicate)
    return {"note_id": invoke("addNote", note=note)}


@mcp.tool()
def add_notes(notes: list[dict[str, Any]]) -> dict[str, Any]:
    """Add many notes in one call. Each item is
    {'deck': str, 'model': str, 'fields': {..}, 'tags': [..]?,
    'allow_duplicate': bool?}. Returns a note ID per note (null where a note
    could not be added, e.g. a duplicate)."""
    payload = [
        _note_payload(n["deck"], n["model"], n["fields"],
                      n.get("tags"), n.get("allow_duplicate", False))
        for n in notes
    ]
    ids = invoke("addNotes", notes=payload)
    added = sum(1 for i in ids if i is not None)
    return {"note_ids": ids, "added": added, "failed": len(ids) - added}


@mcp.tool()
def can_add_notes(notes: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether notes could be added (without adding them). Same note
    shape as add_notes. Returns a list of booleans plus per-note error detail."""
    payload = [
        _note_payload(n["deck"], n["model"], n["fields"],
                      n.get("tags"), n.get("allow_duplicate", False))
        for n in notes
    ]
    return {"detail": invoke("canAddNotesWithErrorDetail", notes=payload)}


@mcp.tool()
def find_notes(query: str, limit: int = 50) -> dict[str, Any]:
    """Search notes with Anki's query syntax (e.g. 'deck:Default tag:new').
    Returns the total count, all matching note IDs, and detailed field data
    for up to 'limit' notes."""
    note_ids = invoke("findNotes", query=query)
    info = invoke("notesInfo", notes=note_ids[:limit]) if note_ids else []
    return {"count": len(note_ids), "note_ids": note_ids, "notes": info}


@mcp.tool()
def notes_info(note_ids: list[int]) -> list[dict[str, Any]]:
    """Get detailed info (fields, tags, model, cards) for specific note IDs."""
    return invoke("notesInfo", notes=note_ids)


@mcp.tool()
def notes_mod_time(note_ids: list[int]) -> list[dict[str, Any]]:
    """Get the last-modified timestamp for specific note IDs."""
    return invoke("notesModTime", notes=note_ids)


@mcp.tool()
def update_note_fields(note_id: int, fields: dict[str, str]) -> str:
    """Update one or more fields of an existing note. Only the fields you pass
    are changed; omitted fields keep their current values."""
    invoke("updateNoteFields", note={"id": note_id, "fields": fields})
    return f"Updated note {note_id}."


@mcp.tool()
def update_note(
    note_id: int,
    fields: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Update fields and/or the full tag set of a note in one call. Pass
    'fields' to change fields and/or 'tags' to REPLACE the note's tags."""
    note: dict[str, Any] = {"id": note_id}
    if fields is not None:
        note["fields"] = fields
    if tags is not None:
        note["tags"] = tags
    invoke("updateNote", note=note)
    return f"Updated note {note_id}."


@mcp.tool()
def update_note_tags(note_id: int, tags: list[str]) -> str:
    """Replace the entire tag set of a note with 'tags'."""
    invoke("updateNoteTags", note=note_id, tags=tags)
    return f"Set tags of note {note_id}."


@mcp.tool()
def get_note_tags(note_id: int) -> list[str]:
    """Get the tags of a single note."""
    return invoke("getNoteTags", note=note_id)


@mcp.tool()
def delete_notes(note_ids: list[int]) -> str:
    """Permanently delete the given notes (and all their cards). Irreversible."""
    invoke("deleteNotes", notes=note_ids)
    return f"Deleted {len(note_ids)} note(s)."


@mcp.tool()
def remove_empty_notes() -> str:
    """Delete all notes that have no cards (empty notes). Irreversible."""
    invoke("removeEmptyNotes")
    return "Removed empty notes."


# ==========================================================================
# Tags
# ==========================================================================

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


@mcp.tool()
def clear_unused_tags() -> str:
    """Delete tags that are no longer used by any note."""
    invoke("clearUnusedTags")
    return "Cleared unused tags."


@mcp.tool()
def replace_tag(note_ids: list[int], old_tag: str, new_tag: str) -> str:
    """Rename a tag on the given notes (replace old_tag with new_tag)."""
    invoke("replaceTags", notes=note_ids,
           tag_to_replace=old_tag, replace_with_tag=new_tag)
    return f"Replaced tag '{old_tag}' -> '{new_tag}' on {len(note_ids)} note(s)."


@mcp.tool()
def replace_tag_in_all_notes(old_tag: str, new_tag: str) -> str:
    """Rename a tag across the ENTIRE collection (replace old_tag with
    new_tag on every note)."""
    invoke("replaceTagsInAllNotes", tag_to_replace=old_tag, replace_with_tag=new_tag)
    return f"Replaced tag '{old_tag}' -> '{new_tag}' collection-wide."


# ==========================================================================
# Cards
# ==========================================================================

@mcp.tool()
def find_cards(query: str, limit: int = 50) -> dict[str, Any]:
    """Search cards with Anki's query syntax. Returns the total count, all
    matching card IDs, and detailed info (deck, note, interval, due,
    suspended state) for up to 'limit' cards."""
    card_ids = invoke("findCards", query=query)
    info = invoke("cardsInfo", cards=card_ids[:limit]) if card_ids else []
    return {"count": len(card_ids), "card_ids": card_ids, "cards": info}


@mcp.tool()
def cards_info(card_ids: list[int]) -> list[dict[str, Any]]:
    """Get detailed info for specific card IDs (deck, fields, interval, due,
    ease, review count, suspended/marked state)."""
    return invoke("cardsInfo", cards=card_ids)


@mcp.tool()
def cards_to_notes(card_ids: list[int]) -> list[int]:
    """Map card IDs to their parent note IDs (deduplicated)."""
    return invoke("cardsToNotes", cards=card_ids)


@mcp.tool()
def cards_mod_time(card_ids: list[int]) -> list[dict[str, Any]]:
    """Get the last-modified timestamp for specific card IDs."""
    return invoke("cardsModTime", cards=card_ids)


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


@mcp.tool()
def are_suspended(card_ids: list[int]) -> list[Any]:
    """For each card ID, return True if suspended, False if not, null if the
    card does not exist."""
    return invoke("areSuspended", cards=card_ids)


@mcp.tool()
def are_due(card_ids: list[int]) -> list[bool]:
    """For each card ID, return whether it is currently due for review."""
    return invoke("areDue", cards=card_ids)


@mcp.tool()
def get_intervals(card_ids: list[int], complete: bool = False) -> list[Any]:
    """Get the current interval of each card. With complete=True, returns the
    full list of all intervals in each card's history instead."""
    return invoke("getIntervals", cards=card_ids, complete=complete)


@mcp.tool()
def get_ease_factors(card_ids: list[int]) -> list[int]:
    """Get the ease factor (per mille, e.g. 2500) of each card."""
    return invoke("getEaseFactors", cards=card_ids)


@mcp.tool()
def set_ease_factors(card_ids: list[int], ease_factors: list[int]) -> list[bool]:
    """Set the ease factor of each card (parallel lists). Ease is per mille,
    e.g. 2500 = 250%."""
    return invoke("setEaseFactors", cards=card_ids, easeFactors=ease_factors)


@mcp.tool()
def set_card_values(card_id: int, keys: list[str], new_values: list[str]) -> list[bool]:
    """Advanced: set specific low-level fields of one card (parallel keys/
    values lists). Use with care — writing raw card properties can corrupt
    scheduling if misused."""
    return invoke("setSpecificValueOfCard", card=card_id,
                  keys=keys, newValues=new_values)


@mcp.tool()
def forget_cards(card_ids: list[int]) -> str:
    """Reset cards to the 'new' state (forget all review progress)."""
    invoke("forgetCards", cards=card_ids)
    return f"Reset {len(card_ids)} card(s) to new."


@mcp.tool()
def relearn_cards(card_ids: list[int]) -> str:
    """Put the given cards into the relearning queue."""
    invoke("relearnCards", cards=card_ids)
    return f"Set {len(card_ids)} card(s) to relearning."


@mcp.tool()
def set_due_date(card_ids: list[int], days: str) -> str:
    """Reschedule cards to be due in 'days'. 'days' is Anki's set-due-date
    spec: '0' = today, '3' = in 3 days, '1-7' = random within a range, add
    '!' (e.g. '3!') to also reset the interval to that value."""
    ok = invoke("setDueDate", cards=card_ids, days=days)
    return f"Set due date ({days}) on {len(card_ids)} card(s)." if ok else "Failed."


@mcp.tool()
def answer_cards(answers: list[dict[str, int]]) -> list[bool]:
    """Programmatically answer cards as if reviewed. Each item is
    {'cardId': int, 'ease': 1-4} where 1=Again, 2=Hard, 3=Good, 4=Easy."""
    return invoke("answerCards", answers=answers)


# ==========================================================================
# Media
# ==========================================================================

@mcp.tool()
def store_media_file(
    filename: str,
    path: str | None = None,
    url: str | None = None,
    data_b64: str | None = None,
    delete_existing: bool = True,
) -> dict[str, Any]:
    """Store a media file (image/audio) in the collection's media folder so it
    can be referenced from a note, e.g. '[sound:word.mp3]' or
    '<img src="pic.png">'. Provide exactly one source: a local 'path', a
    'url' to download, or base64 'data_b64'. Returns the stored filename."""
    sources = [s for s in (path, url, data_b64) if s]
    if len(sources) != 1:
        raise ValueError("Provide exactly one of: path, url, data_b64.")
    kwargs: dict[str, Any] = {"filename": filename, "deleteExisting": delete_existing}
    if path:
        kwargs["path"] = path
    elif url:
        kwargs["url"] = url
    else:
        kwargs["data"] = data_b64
    return {"filename": invoke("storeMediaFile", **kwargs)}


@mcp.tool()
def retrieve_media_file(filename: str) -> dict[str, Any]:
    """Retrieve a media file's contents as base64 (or false if not found)."""
    return {"data_b64": invoke("retrieveMediaFile", filename=filename)}


@mcp.tool()
def list_media_files(pattern: str = "*") -> list[str]:
    """List media file names, optionally filtered by a glob pattern
    (e.g. '*.mp3')."""
    return invoke("getMediaFilesNames", pattern=pattern)


@mcp.tool()
def get_media_dir_path() -> dict[str, Any]:
    """Return the absolute path of the collection's media folder."""
    return {"path": invoke("getMediaDirPath")}


@mcp.tool()
def delete_media_file(filename: str) -> str:
    """Delete a file from the collection's media folder. Irreversible."""
    invoke("deleteMediaFile", filename=filename)
    return f"Deleted media file '{filename}'."


# ==========================================================================
# Statistics
# ==========================================================================

@mcp.tool()
def cards_reviewed_today() -> dict[str, Any]:
    """Return how many cards have been reviewed so far today."""
    return {"reviewed_today": invoke("getNumCardsReviewedToday")}


@mcp.tool()
def cards_reviewed_by_day() -> list[Any]:
    """Return review counts per day as [date_string, count] pairs."""
    return invoke("getNumCardsReviewedByDay")


@mcp.tool()
def collection_stats_html(whole_collection: bool = True) -> dict[str, Any]:
    """Return Anki's statistics report as an HTML string."""
    return {"html": invoke("getCollectionStatsHTML", wholeCollection=whole_collection)}


@mcp.tool()
def card_reviews(deck: str, start_id: int = 0) -> list[Any]:
    """Return all review log entries for a deck made after the given review ID
    (a Unix-ms timestamp; use 0 for all)."""
    return invoke("cardReviews", deck=deck, startID=start_id)


@mcp.tool()
def get_reviews_of_cards(card_ids: list[int]) -> dict[str, Any]:
    """Return the full review history for specific card IDs."""
    return invoke("getReviewsOfCards", cards=[str(c) for c in card_ids])


@mcp.tool()
def get_latest_review_id(deck: str) -> dict[str, Any]:
    """Return the most recent review ID for a deck (0 if none)."""
    return {"latest_review_id": invoke("getLatestReviewID", deck=deck)}


@mcp.tool()
def insert_reviews(reviews: list[list[int]]) -> str:
    """Insert raw review-log rows (advanced; each row is AnkiConnect's review
    tuple). Mainly for migrating history."""
    invoke("insertReviews", reviews=reviews)
    return f"Inserted {len(reviews)} review row(s)."


# ==========================================================================
# Graphical (drive the Anki GUI)
# ==========================================================================

@mcp.tool()
def gui_browse(query: str) -> list[int]:
    """Open Anki's Card Browser filtered by 'query' and return the shown card
    IDs. Anki must be in the foreground to see it."""
    return invoke("guiBrowse", query=query)


@mcp.tool()
def gui_selected_notes() -> list[int]:
    """Return the note IDs currently selected in the open Card Browser."""
    return invoke("guiSelectedNotes")


@mcp.tool()
def gui_add_cards(
    deck: str,
    model: str,
    fields: dict[str, str],
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Open Anki's Add dialog pre-filled with the given note (does not save it
    automatically). Returns the note ID if the user confirms."""
    note = _note_payload(deck, model, fields, tags, False)
    return {"note_id": invoke("guiAddCards", note=note)}


@mcp.tool()
def gui_edit_note(note_id: int) -> str:
    """Open the Edit dialog for a specific note."""
    invoke("guiEditNote", note=note_id)
    return f"Opened editor for note {note_id}."


@mcp.tool()
def gui_current_card() -> dict[str, Any]:
    """Return info about the card currently shown in the reviewer (or null)."""
    return invoke("guiCurrentCard")


@mcp.tool()
def gui_show_question() -> str:
    """Show the question side of the current reviewer card."""
    invoke("guiShowQuestion")
    return "Showing question."


@mcp.tool()
def gui_show_answer() -> str:
    """Show the answer side of the current reviewer card."""
    invoke("guiShowAnswer")
    return "Showing answer."


@mcp.tool()
def gui_answer_card(ease: int) -> str:
    """Answer the current reviewer card with an ease button
    (1=Again, 2=Hard, 3=Good, 4=Easy)."""
    invoke("guiAnswerCard", ease=ease)
    return f"Answered current card with ease {ease}."


@mcp.tool()
def gui_undo() -> str:
    """Trigger an undo in the Anki GUI."""
    invoke("guiUndo")
    return "Undo triggered."


@mcp.tool()
def gui_deck_overview(name: str) -> str:
    """Open the deck overview screen for a deck."""
    invoke("guiDeckOverview", name=name)
    return f"Opened overview for '{name}'."


@mcp.tool()
def gui_deck_browser() -> str:
    """Open the main deck list screen."""
    invoke("guiDeckBrowser")
    return "Opened deck browser."


@mcp.tool()
def gui_deck_review(name: str) -> str:
    """Start reviewing a deck in the GUI."""
    invoke("guiDeckReview", name=name)
    return f"Started review of '{name}'."


@mcp.tool()
def gui_import_file(path: str) -> str:
    """Open Anki's import dialog for the file at 'path' (e.g. a .apkg/.csv)."""
    invoke("guiImportFile", path=path)
    return f"Opened import dialog for {path}."


@mcp.tool()
def gui_check_database() -> str:
    """Run Anki's 'Check Database' maintenance operation."""
    invoke("guiCheckDatabase")
    return "Database check triggered."


@mcp.tool()
def gui_exit_anki() -> str:
    """Close Anki Desktop. AnkiConnect will be unavailable afterwards until
    Anki is restarted."""
    invoke("guiExitAnki")
    return "Anki is exiting."


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
