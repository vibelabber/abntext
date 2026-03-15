# BibTeX File Creation — Design Spec

**Date:** 2026-03-15
**Status:** Approved

---

## Overview

Add an inline BibTeX builder to the existing ABNText web page. Users who don't have a `.bib` file can construct one entry-by-entry directly in the UI. The generated file can be downloaded and is automatically used for PDF conversion without re-uploading.

---

## Requirements

- Feature lives on the same page as the upload form (no new routes or pages)
- Supported entry types: `@book`, `@online`
- Users add entries one at a time; entries accumulate in a list
- Users can remove individual entries; no in-place editing (too complex for v1)
- Cite keys are auto-generated (`LastName + Year`, e.g. `Silva2023`) and shown to the user
- Generated `.bib` takes precedence over any uploaded `.bib` file when active
- No persistence in v1; state is in-memory only
- Design must not require changes to `main.py` or `pipeline.py`
- Pure functions for all BibTeX generation logic, enabling unit testing

---

## Architecture

### New file: `web/bibtex.js` (ES module)

Contains all BibTeX generation logic as pure, exported functions — no DOM access.

**Entry shape:**
```js
// @book
{ type: 'book', author, title, publisher, address, year }

// @online
{ type: 'online', author, title, url, urldate, year }
```

`author` is a free-form string entered by the user in last-name-first format. Multiple authors are separated by ` and ` (standard BibTeX convention), e.g. `"Silva, João and Souza, Maria"`.

**Exported functions:**

| Function | Signature | Description |
|---|---|---|
| `generateCiteKey` | `(author: string, year: string) → string` | Extracts the last name of the **first listed author** + year. Splits on ` and `, takes the first author, then takes the part before the first comma (or the last word if no comma). E.g. `"Silva, João and Souza, Maria"` + `"2023"` → `"Silva2023"` |
| `serializeEntry` | `(entry: object) → string` | Returns a single BibTeX entry block as a string |
| `serializeBibFile` | `(entries: object[]) → string` | Joins all serialized entries separated by blank lines |

**Expected serialization output examples:**

```bibtex
@book{Silva2023,
  author    = {Silva, João},
  title     = {Título do Livro},
  publisher = {Editora Exemplo},
  address   = {São Paulo},
  year      = {2023},
}

@online{Souza2022,
  author  = {Souza, Maria},
  title   = {Título do Artigo Online},
  url     = {https://exemplo.com},
  urldate = {2022-05-10},
  year    = {2022},
}
```

Fields use `{...}` quoting. Field order matches the example above for each type. The `urldate` field is used directly (not `note`) — this matches the ABNT BibTeX style used by this project.

### Modified file: `web/index.html`

Imports `bibtex.js` as an ES module. Handles all DOM interaction and state.

**State object (in-memory, not persisted):**
```js
const state = {
  entries: [],     // array of entry objects
  useBuilt: false, // whether generated .bib overrides any uploaded file
}
```

No changes to backend (`main.py`, `pipeline.py`).

---

## UI Structure

The builder is an **inline expandable section** placed between the `.bib` file upload field and the submit button.

### Collapsed state
A single link: `▶ Não tem um .bib? Crie um aqui`
Clicking it expands the section and changes the indicator to `▼`.

### Expanded state

1. **Entry form**
   - `<select>` for type: `Livro (@book)` / `Online (@online)`
   - Swaps visible fields based on type:
     - `@book`: Autor, Título, Editora, Cidade, Ano
     - `@online`: Autor, Título, URL, Data de acesso (YYYY-MM-DD), Ano
   - All fields required
   - "Adicionar" button appends to the list

2. **Entry list** (shown when `entries.length > 0`)
   - Each row: cite key + title + type tag + trash icon to remove

3. **Action bar** (shown when `entries.length > 0`)
   - "Baixar .bib" — downloads `serializeBibFile(entries)` as `refs.bib`
   - "Usar este BibTeX" toggle — when active, the generated content is used for conversion

### Upload field interaction
When `useBuilt` is `true`, the `.bib` upload field is visually dimmed with a note:
*"Será usado o BibTeX gerado abaixo."*
The user can toggle `useBuilt` off to revert to an uploaded file.

---

## State & Conversion Flow

1. User adds an entry → pushed to `state.entries`; `state.useBuilt` is auto-set to `true` **only when transitioning from zero to one entry** (i.e. first add). Subsequent adds do not force `useBuilt` back on if the user has manually toggled it off.
2. User removes all entries → `state.useBuilt` resets to `false`
3. User can manually toggle `useBuilt`
4. On form submit:
   - If `state.useBuilt && state.entries.length > 0`:
     - Call `serializeBibFile(state.entries)` to get `.bib` content
     - Create `new File([content], 'refs.bib', { type: 'text/plain' })`
     - Set it on the `FormData` under key `bib_file`
   - Otherwise: existing upload behavior unchanged
5. The `/convert` endpoint receives `bib_file` as a normal `UploadFile` — no backend changes needed

---

## Testing

### JS unit tests

- New `package.json` at project root with Vitest as the sole dev dependency
- Test files in `tests/js/`
- Tests import `web/bibtex.js` directly (no bundler needed)
- `npm test` runs Vitest

**Functions to test (`web/bibtex.js`):**
- `generateCiteKey`: various author formats (with/without comma, single name, multiple authors), edge cases
- `serializeEntry`: correct BibTeX output for `@book` and `@online`
- `serializeBibFile`: correct joining of multiple entries, empty array

### Python tests
No new Python tests required (no backend changes).

---

## File Changes Summary

| File | Change |
|---|---|
| `web/bibtex.js` | **New** — pure BibTeX generation functions |
| `web/index.html` | **Modified** — add builder UI, import bibtex.js |
| `package.json` | **New** — Vitest dev dependency |
| `tests/js/bibtex.test.js` | **New** — unit tests for bibtex.js |
| `.gitignore` | **Modified** — add `node_modules/` |

---

## Out of Scope (v1)

- Persisting entries across sessions
- Editing existing entries (only removal supported)
- Entry types beyond `@book` and `@online`
- Merging uploaded and built `.bib` files
