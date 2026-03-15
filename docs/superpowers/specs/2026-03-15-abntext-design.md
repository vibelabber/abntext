# ABNText — Design Spec
**Date:** 2026-03-15

## Overview

ABNText converts Markdown documents into ABNT-compliant PDFs for FLAM students. It uses a custom LaTeX class that inherits from abntex2 and applies FLAM-specific styles. Students write in Markdown; ABNText produces a properly formatted PDF.

Two interfaces are provided:
- A web UI (file upload → PDF download) for browser-based use
- A shell script CLI wrapper around Docker for terminal use

---

## Requirements

### Supported Markdown features
- Headings (map to ABNT sections)
- Lists
- Tables (GFM syntax)
- Citations via `[@key]` syntax (Pandoc citeproc + ABNT CSL)
- Bibliography via an accompanying `.bib` (BibTeX) file
- No figure support in MVP

### Deployment targets
- Local network (FLAM-hosted server)
- Public internet
- Portable via Docker (single image covers both targets)

---

## Architecture

```
Student uploads .md + (optional) .bib
         │
    FastAPI web endpoint  POST /convert  (multipart/form-data)
         │
    Conversion pipeline (pipeline.py — shared)
         ├── Write files to temp dir
         ├── Pandoc: .md → .tex
         │     └── --citeproc --bibliography=refs.bib
         │     └── --csl=abnt.csl (bundled in image at /app/csl/abnt.csl)
         │     └── --template=flam.tex
         └── xelatex (run twice for citations/TOC)
              └── returns PDF path
         │
    Web:  stream PDF as HTTP response
          Content-Type: application/pdf
          Content-Disposition: attachment; filename="output.pdf"
    CLI:  write PDF to /data/<output> in container
```

The conversion pipeline (`pipeline.py`) is a single Python module called by both the web handler and the internal CLI entrypoint. It accepts file paths, shells out to Pandoc then xelatex (twice), and returns the path to the produced PDF. Temp directories are always cleaned up via `finally` blocks.

**LaTeX engine:** XeLaTeX. Chosen for native UTF-8 support, which is required for Portuguese documents with accented characters. No `inputenc`/`fontenc` boilerplate needed.

**Citation engine:** Pandoc citeproc with a bundled ABNT CSL file (`csl/abnt.csl` inside the image). Citations are resolved entirely by Pandoc before LaTeX is invoked; no `abntex2cite` LaTeX package is used.

### Key OSS dependencies
| Tool | Role |
|------|------|
| Pandoc | Markdown → LaTeX conversion, citeproc citation processing with ABNT CSL |
| XeLaTeX (TeX Live) + abntex2 | LaTeX → PDF compilation with ABNT styles |
| FastAPI | Web server and internal CLI host |
| Docker | Runtime environment bundling all dependencies |

### Docker image
- Image name/tag: `abntext` (built by `docker-compose.yml` via `build: .`)
- The `docker-compose.yml` builds and tags the image as `abntext:latest`
- Required Debian/Ubuntu packages installed in Dockerfile:
  - `pandoc`
  - `texlive-xetex`
  - `texlive-lang-portuguese`
  - `texlive-fonts-recommended`
  - `texlive-latex-extra` (includes abntex2)
  - (no biber — citations are resolved entirely by Pandoc citeproc before xelatex is invoked; xelatex never processes bibliography data)

---

## Project Structure

```
abntext/
├── bin/
│   └── abntext          # Shell script CLI (the user-facing "binary")
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
│
├── abntext/             # Python package
│   ├── __init__.py
│   ├── main.py          # FastAPI app (web endpoints)
│   ├── cli.py           # Internal CLI entrypoint (runs inside container)
│   └── pipeline.py      # Shared conversion logic
│
├── templates/
│   └── flam.tex         # Pandoc LaTeX template using the FLAM class
│
├── csl/
│   └── abnt.csl         # ABNT citation style (CSL format, bundled in image)
│
├── latex/
│   └── flam.cls         # Custom LaTeX class (inherits abntex2)
│
├── web/
│   └── index.html       # Single-page HTML upload form
│
└── example/
    ├── example.md
    └── example.bib
```

---

## Markdown Frontmatter Pattern

Students include a YAML frontmatter block at the top of their `.md` file. The Pandoc template maps these fields to abntex2 macros (`\titulo`, `\autor`, `\instituicao`, `\local`, `\data`, etc.) to generate the cover and title pages.

```markdown
---
title: "Análise do Pensamento de Tomás de Aquino"
author: "João Silva"
institution: "Faculdade Latino-Americana de Música"
course: "História da Igreja II"
professor: "Prof. Dr. Carlos Santos"
city: "São Paulo"
year: "2026"
---

## Introdução

Neste artigo...[@aquino1265]
```

The `.bib` file is uploaded alongside the `.md` and passed to Pandoc via `--bibliography`. Pandoc citeproc resolves all `[@key]` references using the bundled ABNT CSL file before the LaTeX step.

---

## Interfaces

### Web UI

**Endpoint:** `POST /convert` — `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `md_file` | file | Yes | The Markdown source document |
| `bib_file` | file | No | BibTeX bibliography file |

**Success response:**
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="output.pdf"`
- Body: the compiled PDF

**Error response:**
- HTTP 422 with `Content-Type: text/plain`
- Body: relevant excerpt from Pandoc or xelatex stderr

**Validation:**
- If `md_file` is missing: HTTP 422 with message "Markdown file is required"
- If `bib_file` is absent but the document contains `[@key]` citations: Pandoc will emit a warning and references will appear as `[?]`; this is not treated as an error by the server (students can discover this through the output)
- No file-type enforcement beyond the field names; malformed files will fail at the Pandoc/xelatex step and surface as HTTP 422

The form is served statically at `GET /` from `web/index.html`.

### CLI (Shell Script)

The `bin/abntext` shell script is the user-facing CLI binary:

```bash
#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  -v "$(pwd):/data" \
  abntext \
  convert "$@"
```

**Internal CLI interface (handled by `cli.py` via argparse subparsers):**

`cli.py` exposes a `convert` subcommand. The shell script passes `convert "$@"` verbatim, so `convert` is the first positional argument received by `cli.py`.

```
usage: cli.py convert <md_file> [--bib <bib_file>] [--output <output_file>]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `convert` | Yes | — | Subcommand (literal word, dispatched by argparse) |
| `md_file` | Yes | — | Path to the `.md` file, relative to `/data/` inside the container |
| `--bib` | No | none | Path to the `.bib` file, relative to `/data/` |
| `--output` | No | `<md_file stem>.pdf` | Output PDF filename, written to `/data/` |

**Usage (from the host, via the shell script):**
```bash
bin/abntext convert paper.md
bin/abntext convert paper.md --bib refs.bib
bin/abntext convert paper.md --bib refs.bib --output paper.pdf
```

All paths are relative to the directory where the script is run (mounted as `/data` inside the container). If the input `.md` file is not found at `/data/<md_file>`, the CLI exits with code 1 and prints an error to stderr.

---

## Error Handling

- Subprocess return codes are checked after every Pandoc and xelatex call.
- On failure, stderr is captured and surfaced:
  - Web: HTTP 422 with the relevant log excerpt
  - CLI: non-zero exit code + stderr printed to terminal
- Temp directories are always cleaned up via `finally` blocks regardless of success or failure.

---

## Out of Scope (MVP)

- **Figure/image support** — deferred; adds file handling complexity and is not needed for the initial student use cases
- **User accounts or document history** — deferred; the service is stateless by design for simplicity
- **Real-time preview** — deferred; requires a separate rendering pipeline and is out of scope for the initial release
- **Multiple output formats** — PDF only; other formats (DOCX, HTML) may be added in a future iteration
