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
- Citations via `[@key]` syntax (Pandoc citeproc)
- Bibliography via an accompanying `.bib` (BibTeX) file
- No figure support in MVP

### Deployment targets
- Local network (FLAM-hosted server)
- Public internet
- Portable via Docker (single image covers both targets)

---

## Architecture

```
Student uploads .md + .bib
         │
    FastAPI web endpoint
         │
    Conversion pipeline (pipeline.py — shared)
         ├── Write files to temp dir
         ├── Pandoc: .md → .tex
         │     └── --citeproc --bibliography=refs.bib
         │     └── --template=flam.tex
         └── pdflatex (run twice for citations/TOC)
              └── returns PDF path
         │
    Web:  stream PDF as HTTP response (download)
    CLI:  write PDF to /data/<output> in container
```

The conversion pipeline (`pipeline.py`) is a single Python module called by both the web handler and the internal CLI entrypoint. It accepts file paths, shells out to Pandoc then pdflatex (twice), and returns the path to the produced PDF. Temp directories are always cleaned up via `finally` blocks.

### Key OSS dependencies
| Tool | Role |
|------|------|
| Pandoc | Markdown → LaTeX conversion, citeproc citation processing |
| TeX Live (slim) + abntex2 | LaTeX → PDF compilation with ABNT styles |
| FastAPI | Web server and internal CLI host |
| Docker | Runtime environment bundling all dependencies |

---

## Project Structure

```
abntext/
├── abntext              # Shell script CLI (the user-facing "binary")
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

The `.bib` file is uploaded alongside the `.md` and passed to Pandoc via `--bibliography`. Citations render according to ABNT citation style (using a CSL file for ABNT, or abntex2cite).

---

## Interfaces

### Web UI

A single-page HTML form (`web/index.html`) with:
- File input for `.md` file (required)
- File input for `.bib` file (optional)
- Submit button

On success: browser triggers a PDF download.
On error: HTTP 422 with a plain-text excerpt of the Pandoc/pdflatex stderr.

### CLI (Shell Script)

The `abntext` shell script at the project root is the user-facing CLI binary:

```bash
#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  -v "$(pwd):/data" \
  abntext \
  convert "$@"
```

**Usage:**
```bash
./abntext convert paper.md --bib refs.bib
./abntext convert paper.md --bib refs.bib --output paper.pdf
```

The container mounts the current working directory to `/data`. The internal `cli.py` entrypoint reads inputs from `/data/` and writes the PDF back to `/data/`. The Python CLI is not intended for direct user installation.

---

## Error Handling

- Subprocess return codes are checked after every Pandoc and pdflatex call.
- On failure, stderr is captured and surfaced:
  - Web: HTTP 422 with the relevant log excerpt
  - CLI: non-zero exit code + stderr printed to terminal
- Temp directories are always cleaned up via `finally` blocks regardless of success or failure.

---

## Out of Scope (MVP)

- Figure/image support
- User accounts or document history
- Real-time preview
- Multiple output formats (only PDF)
