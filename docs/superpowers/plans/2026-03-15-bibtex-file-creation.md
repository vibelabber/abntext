# BibTeX File Creation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an inline BibTeX builder to the ABNText web page so users can create a `.bib` file entry-by-entry and use it directly for PDF conversion.

**Architecture:** All BibTeX generation logic lives in a new `web/bibtex.js` ES module as pure, exported functions with no DOM access — making them fully unit-testable with Vitest. `web/index.html` imports that module and handles all DOM and state. The existing `/convert` endpoint receives the generated `.bib` as a standard `UploadFile` injected via `FormData` — no backend conversion logic changes. One minimal infrastructure change to `main.py` is required: mounting `StaticFiles` on `/static` so `bibtex.js` can be served as a module (the spec intended "no new conversion logic", which holds).

**Tech Stack:** FastAPI, Vanilla JS (ES modules), Vitest (JS unit tests), pytest (existing Python tests)

---

## File Structure

| File | Status | Responsibility |
|------|--------|----------------|
| `web/bibtex.js` | **Create** | Pure functions: `generateCiteKey`, `serializeEntry`, `serializeBibFile` |
| `web/index.html` | **Modify** | Builder UI (HTML/CSS/JS), state management, FormData injection |
| `abntext/main.py` | **Modify** | Add `StaticFiles` mount at `/static` (2-line infrastructure change) |
| `package.json` | **Create** | Vitest dev dependency, `npm test` script |
| `tests/js/bibtex.test.js` | **Create** | Unit tests for all three pure functions |
| `.gitignore` | **Modify** | Add `node_modules/` |

---

## Chunk 1: JS Infrastructure + Pure Functions (TDD)

### Task 1: Setup JS test infrastructure

**Files:**
- Create: `package.json`
- Modify: `.gitignore`

- [ ] **Step 1: Create `package.json`**

```json
{
  "type": "module",
  "scripts": {
    "test": "vitest run"
  },
  "devDependencies": {
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Add `node_modules/` to `.gitignore`**

Append to the bottom of `.gitignore`:
```
# Node
node_modules/
```

- [ ] **Step 3: Create `tests/js/` directory and empty test file**

```bash
mkdir -p tests/js
```

Create `tests/js/bibtex.test.js` with a placeholder to verify the harness works:
```js
import { describe, it, expect } from 'vitest'

describe('placeholder', () => {
  it('test harness works', () => {
    expect(1 + 1).toBe(2)
  })
})
```

- [ ] **Step 4: Install dependencies and run the placeholder test**

```bash
npm install
npm test
```

Expected output:
```
✓ tests/js/bibtex.test.js (1)
  ✓ placeholder > test harness works

Test Files  1 passed (1)
Tests  1 passed (1)
```

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json .gitignore tests/js/bibtex.test.js
git commit -m "chore: add vitest for js unit tests"
```

---

### Task 2: Implement `generateCiteKey` (TDD)

**Files:**
- Create: `web/bibtex.js`
- Modify: `tests/js/bibtex.test.js`

- [ ] **Step 1: Replace placeholder with failing tests for `generateCiteKey`**

Replace all content in `tests/js/bibtex.test.js` with:

```js
import { describe, it, expect } from 'vitest'
import { generateCiteKey } from '../../web/bibtex.js'

describe('generateCiteKey', () => {
  it('extracts last name before comma and appends year', () => {
    expect(generateCiteKey('Silva, João', '2023')).toBe('Silva2023')
  })

  it('uses last word when no comma present', () => {
    expect(generateCiteKey('João Silva', '2021')).toBe('Silva2021')
  })

  it('uses single token as-is when no comma or space', () => {
    expect(generateCiteKey('Silva', '2019')).toBe('Silva2019')
  })

  it('uses first listed author when multiple authors separated by " and "', () => {
    expect(generateCiteKey('Souza, Maria and Silva, João', '2020')).toBe('Souza2020')
  })

  it('trims whitespace from author name', () => {
    expect(generateCiteKey('  Silva, João  ', '2023')).toBe('Silva2023')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm test
```

Expected: FAIL — `Cannot find module '../../web/bibtex.js'`

- [ ] **Step 3: Create `web/bibtex.js` with `generateCiteKey`**

```js
/**
 * Extracts the last name of the first listed author and appends the year.
 * Author string: last-name-first, comma-separated. Multiple authors separated by " and ".
 * Examples:
 *   generateCiteKey("Silva, João", "2023")              → "Silva2023"
 *   generateCiteKey("Souza, Maria and Silva, João", "2020") → "Souza2020"
 *   generateCiteKey("João Silva", "2021")               → "Silva2021"
 *
 * @param {string} author
 * @param {string} year
 * @returns {string}
 */
export function generateCiteKey(author, year) {
  const firstAuthor = author.split(' and ')[0].trim()
  const lastName = firstAuthor.includes(',')
    ? firstAuthor.split(',')[0].trim()
    : firstAuthor.split(' ').pop()
  return `${lastName}${year}`
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm test
```

Expected:
```
✓ tests/js/bibtex.test.js (5)
  ✓ generateCiteKey > extracts last name before comma and appends year
  ✓ generateCiteKey > uses last word when no comma present
  ✓ generateCiteKey > uses single token as-is when no comma or space
  ✓ generateCiteKey > uses first listed author when multiple authors separated by " and "
  ✓ generateCiteKey > trims whitespace from author name

Test Files  1 passed (1)
Tests  5 passed (5)
```

- [ ] **Step 5: Commit**

```bash
git add web/bibtex.js tests/js/bibtex.test.js
git commit -m "feat: add generateCiteKey pure function with tests"
```

---

### Task 3: Implement `serializeEntry` (TDD)

**Files:**
- Modify: `web/bibtex.js`
- Modify: `tests/js/bibtex.test.js`

- [ ] **Step 1: Add failing tests for `serializeEntry`**

First, update the import at the top of `tests/js/bibtex.test.js` to include `serializeEntry`:

```js
import { generateCiteKey, serializeEntry } from '../../web/bibtex.js'
```

Then append the following describe block after the existing one (after the closing `})`):

```js
describe('serializeEntry', () => {
  it('serializes a @book entry with correct field order and braces', () => {
    const entry = {
      type: 'book',
      author: 'Silva, João',
      title: 'Título do Livro',
      publisher: 'Editora Exemplo',
      address: 'São Paulo',
      year: '2023',
    }
    const expected = [
      '@book{Silva2023,',
      '  author    = {Silva, João},',
      '  title     = {Título do Livro},',
      '  publisher = {Editora Exemplo},',
      '  address   = {São Paulo},',
      '  year      = {2023},',
      '}',
    ].join('\n')
    expect(serializeEntry(entry)).toBe(expected)
  })

  it('serializes an @online entry with correct field order and braces', () => {
    const entry = {
      type: 'online',
      author: 'Souza, Maria',
      title: 'Título do Artigo Online',
      url: 'https://exemplo.com',
      urldate: '2022-05-10',
      year: '2022',
    }
    const expected = [
      '@online{Souza2022,',
      '  author  = {Souza, Maria},',
      '  title   = {Título do Artigo Online},',
      '  url     = {https://exemplo.com},',
      '  urldate = {2022-05-10},',
      '  year    = {2022},',
      '}',
    ].join('\n')
    expect(serializeEntry(entry)).toBe(expected)
  })

  it('throws for unknown entry types', () => {
    expect(() => serializeEntry({ type: 'unknown' })).toThrow('Unknown entry type: unknown')
  })
})
```

- [ ] **Step 2: Run tests to verify `serializeEntry` tests fail**

```bash
npm test
```

Expected: FAIL — `serializeEntry is not a function`

- [ ] **Step 3: Add `serializeEntry` to `web/bibtex.js`**

Append to `web/bibtex.js`:

```js
/**
 * Serializes a single BibTeX entry object to a BibTeX string block.
 * Supported types: 'book', 'online'.
 *
 * @param {{ type: string, author: string, title: string, year: string, [key: string]: string }} entry
 * @returns {string}
 */
export function serializeEntry(entry) {
  const key = generateCiteKey(entry.author, entry.year)

  if (entry.type === 'book') {
    return [
      `@book{${key},`,
      `  author    = {${entry.author}},`,
      `  title     = {${entry.title}},`,
      `  publisher = {${entry.publisher}},`,
      `  address   = {${entry.address}},`,
      `  year      = {${entry.year}},`,
      `}`,
    ].join('\n')
  }

  if (entry.type === 'online') {
    return [
      `@online{${key},`,
      `  author  = {${entry.author}},`,
      `  title   = {${entry.title}},`,
      `  url     = {${entry.url}},`,
      `  urldate = {${entry.urldate}},`,
      `  year    = {${entry.year}},`,
      `}`,
    ].join('\n')
  }

  throw new Error(`Unknown entry type: ${entry.type}`)
}
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
npm test
```

Expected:
```
✓ tests/js/bibtex.test.js (8)
  ✓ generateCiteKey > ... (5 tests)
  ✓ serializeEntry > serializes a @book entry ...
  ✓ serializeEntry > serializes an @online entry ...
  ✓ serializeEntry > throws for unknown entry types

Tests  8 passed (8)
```

- [ ] **Step 5: Commit**

```bash
git add web/bibtex.js tests/js/bibtex.test.js
git commit -m "feat: add serializeEntry pure function with tests"
```

---

### Task 4: Implement `serializeBibFile` (TDD)

**Files:**
- Modify: `web/bibtex.js`
- Modify: `tests/js/bibtex.test.js`

- [ ] **Step 1: Add failing tests for `serializeBibFile`**

First, update the import at the top of `tests/js/bibtex.test.js` to include `serializeBibFile`:

```js
import { generateCiteKey, serializeEntry, serializeBibFile } from '../../web/bibtex.js'
```

Then append the following describe block after the existing ones:

```js
describe('serializeBibFile', () => {
  const bookEntry = {
    type: 'book',
    author: 'Silva, João',
    title: 'Livro',
    publisher: 'Editora',
    address: 'SP',
    year: '2023',
  }
  const onlineEntry = {
    type: 'online',
    author: 'Souza, Maria',
    title: 'Artigo',
    url: 'https://exemplo.com',
    urldate: '2022-05-10',
    year: '2022',
  }

  it('returns empty string for empty array', () => {
    expect(serializeBibFile([])).toBe('')
  })

  it('returns single entry string unchanged', () => {
    expect(serializeBibFile([bookEntry])).toBe(serializeEntry(bookEntry))
  })

  it('joins multiple entries with a blank line between them', () => {
    const result = serializeBibFile([bookEntry, onlineEntry])
    expect(result).toBe(serializeEntry(bookEntry) + '\n\n' + serializeEntry(onlineEntry))
  })
})
```

- [ ] **Step 2: Run tests to verify `serializeBibFile` tests fail**

```bash
npm test
```

Expected: FAIL — `serializeBibFile is not a function`

- [ ] **Step 3: Add `serializeBibFile` to `web/bibtex.js`**

Append to `web/bibtex.js`:

```js
/**
 * Serializes an array of entry objects to a full .bib file string.
 * Entries are separated by a blank line.
 *
 * @param {object[]} entries
 * @returns {string}
 */
export function serializeBibFile(entries) {
  return entries.map(serializeEntry).join('\n\n')
}
```

- [ ] **Step 4: Run all tests**

```bash
npm test
```

Expected:
```
✓ tests/js/bibtex.test.js (11)
  ✓ generateCiteKey > ... (5 tests)
  ✓ serializeEntry > ... (3 tests)
  ✓ serializeBibFile > returns empty string for empty array
  ✓ serializeBibFile > returns single entry string unchanged
  ✓ serializeBibFile > joins multiple entries with a blank line between them

Tests  11 passed (11)
```

- [ ] **Step 5: Commit**

```bash
git add web/bibtex.js tests/js/bibtex.test.js
git commit -m "feat: add serializeBibFile pure function with tests"
```

---

## Chunk 2: UI Integration

### Task 5: Serve `bibtex.js` as a static file

**Files:**
- Modify: `abntext/main.py`

The browser needs to fetch `bibtex.js` as an ES module. The app currently only serves `index.html`. Add `StaticFiles` mounting so the `web/` directory is reachable at `/static/`.

- [ ] **Step 1: Add `StaticFiles` mount to `main.py`**

Current `main.py` top:
```python
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
```

Add the import and mount. The final `main.py` should look like:
```python
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from abntext import pipeline

app = FastAPI(title="ABNText")

_WEB_DIR = Path(__file__).parent.parent / "web"

app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (_WEB_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/convert")
async def convert(
    md_file: UploadFile = File(...),
    bib_file: UploadFile | None = File(default=None),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        md_path = tmp / "input.md"
        md_path.write_bytes(await md_file.read())

        bib_path: Path | None = None
        if bib_file is not None:
            bib_path = tmp / "upload.bib"
            bib_path.write_bytes(await bib_file.read())

        pdf_path = tmp / "output.pdf"

        try:
            pipeline.convert(md_path, bib_path, pdf_path)
        except RuntimeError as exc:
            return Response(
                content=str(exc),
                status_code=422,
                media_type="text/plain",
            )

        pdf_bytes = pdf_path.read_bytes()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="output.pdf"'},
    )
```

Note: `StaticFiles` is part of `starlette`, which is already a transitive dependency of `fastapi` — no new packages needed.

- [ ] **Step 2: Verify existing Python tests still pass**

```bash
pytest tests/ -v
```

Expected: all existing tests pass. The `StaticFiles` mount does not affect the `/` or `/convert` endpoints.

- [ ] **Step 3: Commit**

```bash
git add abntext/main.py
git commit -m "chore: serve web/ as static files at /static"
```

---

### Task 6: Add builder HTML and CSS to `index.html`

**Files:**
- Modify: `web/index.html`

This task adds only the HTML structure and CSS. No JavaScript yet.

- [ ] **Step 1: Add builder CSS inside the `<style>` block**

In `web/index.html`, inside the existing `<style>` tag, append these rules before the closing `</style>`:

```css
    .builder-toggle {
      background: none;
      border: none;
      color: #1a56db;
      cursor: pointer;
      font-size: 0.9rem;
      padding: 0;
      margin-bottom: 0.5rem;
    }
    .builder-toggle:disabled { color: #93b4f0; cursor: not-allowed; }
    #builder-body { border: 1px dashed #93b4f0; border-radius: 4px; padding: 1rem; margin-top: 0.5rem; }
    #entry-list { list-style: none; padding: 0; margin: 1rem 0 0; }
    #entry-list li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.4rem 0.5rem;
      background: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 0.4rem;
      font-size: 0.85rem;
    }
    .entry-info { display: flex; gap: 0.5rem; align-items: center; }
    .entry-key { font-family: monospace; color: #1a56db; font-size: 0.8rem; }
    .entry-type-tag {
      font-size: 0.7rem;
      background: #e8edf5;
      color: #555;
      padding: 1px 5px;
      border-radius: 3px;
    }
    .remove-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: #999;
      font-size: 1rem;
      line-height: 1;
      padding: 0 2px;
    }
    .remove-btn:hover { color: #c00; }
    #action-bar { display: flex; gap: 0.75rem; align-items: center; margin-top: 1rem; flex-wrap: wrap; }
    .use-built-btn {
      background: none;
      border: 1px solid #1a56db;
      color: #1a56db;
      padding: 0.35rem 0.9rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.875rem;
    }
    .use-built-btn.active { background: #1a56db; color: #fff; }
    #bib-active-note { font-size: 0.8rem; color: #555; font-style: italic; margin-top: 0.25rem; display: none; }
    .field-group { margin-top: 0.75rem; }
    .field-group .field { margin-bottom: 0.75rem; }
    input[type="text"], input[type="url"], select {
      display: block;
      width: 100%;
      padding: 0.4rem 0.6rem;
      font-size: 0.9rem;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
    }
```

- [ ] **Step 2: Add builder HTML to the form**

In `web/index.html`, locate the line:
```html
    <button type="submit" id="btn">Converter e Baixar PDF</button>
```

Insert the following HTML block **before** that line:

```html
    <div id="bib-builder" class="field">
      <button type="button" class="builder-toggle" id="builder-toggle">▶ Não tem um .bib? Crie um aqui</button>
      <div id="builder-body" hidden>

        <div class="field">
          <label for="entry-type">Tipo</label>
          <select id="entry-type">
            <option value="book">Livro (@book)</option>
            <option value="online">Online (@online)</option>
          </select>
        </div>

        <div class="field-group">
          <div class="field">
            <label for="entry-author">Autor <span style="color:#c00">*</span></label>
            <input type="text" id="entry-author" placeholder="Sobrenome, Nome (ex: Silva, João)">
            <p class="hint">Use formato: Sobrenome, Nome. Múltiplos autores separados por " and ".</p>
          </div>
          <div class="field">
            <label for="entry-title">Título <span style="color:#c00">*</span></label>
            <input type="text" id="entry-title">
          </div>
          <div class="field">
            <label for="entry-year">Ano <span style="color:#c00">*</span></label>
            <input type="text" id="entry-year" placeholder="2023">
          </div>
        </div>

        <!-- @book-only fields -->
        <div class="field-group" id="book-fields">
          <div class="field">
            <label for="entry-publisher">Editora <span style="color:#c00">*</span></label>
            <input type="text" id="entry-publisher">
          </div>
          <div class="field">
            <label for="entry-address">Cidade <span style="color:#c00">*</span></label>
            <input type="text" id="entry-address">
          </div>
        </div>

        <!-- @online-only fields -->
        <div class="field-group" id="online-fields" hidden>
          <div class="field">
            <label for="entry-url">URL <span style="color:#c00">*</span></label>
            <input type="url" id="entry-url" placeholder="https://exemplo.com">
          </div>
          <div class="field">
            <label for="entry-urldate">Data de acesso (YYYY-MM-DD) <span style="color:#c00">*</span></label>
            <input type="text" id="entry-urldate" placeholder="2023-06-15">
          </div>
        </div>

        <button type="button" id="add-entry-btn">Adicionar referência</button>

        <ul id="entry-list" hidden></ul>

        <div id="action-bar" hidden>
          <button type="button" id="download-bib-btn">Baixar .bib</button>
          <button type="button" class="use-built-btn" id="use-built-btn">Usar este BibTeX</button>
        </div>

      </div>
    </div>

```

Also add after the `.bib` file field hint, inside the `.field` div for `bib_file`:

```html
      <p id="bib-active-note">Será usado o BibTeX gerado abaixo.</p>
```

(This goes after the existing `<p class="hint">` inside the `bib_file` field div.)

- [ ] **Step 3: Verify the page still loads and convert still works**

```bash
pytest tests/test_main.py -v
```

Expected: all tests pass (HTML change does not affect API behavior).

- [ ] **Step 4: Commit**

```bash
git add web/index.html
git commit -m "feat: add bibtex builder HTML and CSS structure"
```

---

### Task 7: Wire up JS state — entry form and type switching

**Files:**
- Modify: `web/index.html`

This task adds the JavaScript that handles type switching and adding entries to state.

- [ ] **Step 1: Replace the `<script>` block in `index.html`**

Replace the entire existing `<script>` block (everything between `<script>` and `</script>` at the bottom of the file) with:

```html
  <script type="module">
    import { generateCiteKey, serializeBibFile } from '/static/bibtex.js'

    // ── State ──────────────────────────────────────────────────────────────
    const state = {
      entries: [],
      useBuilt: false,
    }

    // ── DOM refs ───────────────────────────────────────────────────────────
    const form          = document.getElementById('form')
    const btn           = document.getElementById('btn')
    const status        = document.getElementById('status')
    const errorBox      = document.getElementById('error')
    const bibFileInput  = document.getElementById('bib_file')
    const bibActiveNote = document.getElementById('bib-active-note')

    const builderToggle = document.getElementById('builder-toggle')
    const builderBody   = document.getElementById('builder-body')
    const entryType     = document.getElementById('entry-type')
    const bookFields    = document.getElementById('book-fields')
    const onlineFields  = document.getElementById('online-fields')
    const addEntryBtn   = document.getElementById('add-entry-btn')
    const entryList     = document.getElementById('entry-list')
    const actionBar     = document.getElementById('action-bar')
    const downloadBtn   = document.getElementById('download-bib-btn')
    const useBuiltBtn   = document.getElementById('use-built-btn')

    // ── Builder toggle ─────────────────────────────────────────────────────
    builderToggle.addEventListener('click', () => {
      const isHidden = builderBody.hasAttribute('hidden')
      if (isHidden) {
        builderBody.removeAttribute('hidden')
        builderToggle.textContent = '▼ Não tem um .bib? Crie um aqui'
      } else {
        builderBody.setAttribute('hidden', '')
        builderToggle.textContent = '▶ Não tem um .bib? Crie um aqui'
      }
    })

    // ── Type switcher ──────────────────────────────────────────────────────
    entryType.addEventListener('change', () => {
      if (entryType.value === 'book') {
        bookFields.removeAttribute('hidden')
        onlineFields.setAttribute('hidden', '')
      } else {
        bookFields.setAttribute('hidden', '')
        onlineFields.removeAttribute('hidden')
      }
    })

    // ── Add entry ──────────────────────────────────────────────────────────
    addEntryBtn.addEventListener('click', () => {
      const author = document.getElementById('entry-author').value.trim()
      const title  = document.getElementById('entry-title').value.trim()
      const year   = document.getElementById('entry-year').value.trim()

      if (!author || !title || !year) {
        alert('Preencha Autor, Título e Ano.')
        return
      }

      const type = entryType.value
      let entry = { type, author, title, year }

      if (type === 'book') {
        const publisher = document.getElementById('entry-publisher').value.trim()
        const address   = document.getElementById('entry-address').value.trim()
        if (!publisher || !address) {
          alert('Preencha Editora e Cidade.')
          return
        }
        entry = { ...entry, publisher, address }
      } else {
        const url     = document.getElementById('entry-url').value.trim()
        const urldate = document.getElementById('entry-urldate').value.trim()
        if (!url || !urldate) {
          alert('Preencha URL e Data de acesso.')
          return
        }
        entry = { ...entry, url, urldate }
      }

      const wasEmpty = state.entries.length === 0
      state.entries.push(entry)
      if (wasEmpty) setUseBuilt(true)

      renderEntryList()
      clearEntryForm()
    })

    // ── Render entry list ──────────────────────────────────────────────────
    function renderEntryList() {
      entryList.innerHTML = ''
      state.entries.forEach((entry, idx) => {
        const key = generateCiteKey(entry.author, entry.year)
        const li = document.createElement('li')
        li.innerHTML = `
          <span class="entry-info">
            <span class="entry-key">${key}</span>
            <span>${entry.title}</span>
            <span class="entry-type-tag">@${entry.type}</span>
          </span>
          <button class="remove-btn" data-idx="${idx}" title="Remover">✕</button>
        `
        entryList.appendChild(li)
      })

      const hasEntries = state.entries.length > 0
      hasEntries ? entryList.removeAttribute('hidden') : entryList.setAttribute('hidden', '')
      hasEntries ? actionBar.removeAttribute('hidden') : actionBar.setAttribute('hidden', '')

      if (!hasEntries) setUseBuilt(false)
    }

    // ── Remove entry ───────────────────────────────────────────────────────
    entryList.addEventListener('click', (e) => {
      const btn = e.target.closest('.remove-btn')
      if (!btn) return
      const idx = parseInt(btn.dataset.idx, 10)
      state.entries.splice(idx, 1)
      renderEntryList()
    })

    // ── useBuilt toggle ────────────────────────────────────────────────────
    function setUseBuilt(val) {
      state.useBuilt = val
      useBuiltBtn.classList.toggle('active', val)
      bibFileInput.disabled = val
      bibActiveNote.style.display = val ? 'block' : 'none'
    }

    useBuiltBtn.addEventListener('click', () => setUseBuilt(!state.useBuilt))

    // ── Download .bib ──────────────────────────────────────────────────────
    downloadBtn.addEventListener('click', () => {
      const content = serializeBibFile(state.entries)
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'refs.bib'
      a.click()
      URL.revokeObjectURL(url)
    })

    // ── Clear entry form ───────────────────────────────────────────────────
    function clearEntryForm() {
      document.getElementById('entry-author').value = ''
      document.getElementById('entry-title').value  = ''
      document.getElementById('entry-year').value   = ''
      document.getElementById('entry-publisher').value = ''
      document.getElementById('entry-address').value   = ''
      document.getElementById('entry-url').value     = ''
      document.getElementById('entry-urldate').value = ''
    }

    // ── Form submit (conversion) ───────────────────────────────────────────
    form.addEventListener('submit', async (e) => {
      e.preventDefault()
      btn.disabled = true
      status.textContent = 'Convertendo…'
      errorBox.textContent = ''

      const data = new FormData(form)

      if (state.useBuilt && state.entries.length > 0) {
        const content = serializeBibFile(state.entries)
        const bibFile = new File([content], 'refs.bib', { type: 'text/plain' })
        data.set('bib_file', bibFile, 'refs.bib')
      }

      try {
        const res = await fetch('/convert', { method: 'POST', body: data })
        if (res.ok) {
          const blob = await res.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'output.pdf'
          a.click()
          URL.revokeObjectURL(url)
          status.textContent = 'PDF gerado com sucesso.'
        } else {
          const text = await res.text()
          status.textContent = 'Erro na conversão:'
          errorBox.textContent = text
        }
      } catch (err) {
        status.textContent = 'Erro de rede.'
        errorBox.textContent = err.message
      } finally {
        btn.disabled = false
      }
    })
  </script>
```

- [ ] **Step 2: Run all Python tests to verify nothing broke**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Run JS tests**

```bash
npm test
```

Expected: all 11 tests pass (bibtex.js unchanged).

- [ ] **Step 4: Commit**

```bash
git add web/index.html
git commit -m "feat: add bibtex builder UI and state management"
```

---

### Task 8: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

```bash
pytest tests/ -v && npm test
```

Expected: all Python tests pass, all 11 JS tests pass.

- [ ] **Step 2: Manual smoke test (optional but recommended)**

Start the dev server:
```bash
uvicorn abntext.main:app --reload
```

Open `http://localhost:8000` and verify:
1. Page loads, existing form works as before
2. "▶ Não tem um .bib? Crie um aqui" link is visible below the .bib field
3. Clicking it expands the builder section (toggle changes to ▼)
4. Selecting "Online (@online)" hides Publisher/City, shows URL/Access date
5. Filling in a book entry and clicking "Adicionar referência" adds a row to the list with the cite key
6. The "Baixar .bib" and "Usar este BibTeX" buttons appear
7. "Usar este BibTeX" activates (blue background), dims the .bib file upload, shows the note
8. Clicking "✕" on an entry removes it; removing all entries hides the action bar and deactivates the toggle
9. "Baixar .bib" downloads a valid `refs.bib` file
10. With entries and "Usar este BibTeX" active, submitting the form with a `.md` file sends the generated bib to `/convert`

- [ ] **Step 3: Commit if any final tweaks were made**

```bash
git add -p
git commit -m "fix: <describe any final tweaks>"
```
