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
- Citations via `[@key]` syntax (passed through as `\cite{key}` via Pandoc `--natbib`, resolved by abntex2cite)
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
         │     └── --natbib (passes [@key] through as \cite{key}; no citeproc)
         │     └── --template=flam.tex
         └── xelatex → bibtex → xelatex → xelatex (4 steps for abntex2cite)
              └── returns PDF path
         │
    Web:  stream PDF as HTTP response
          Content-Type: application/pdf
          Content-Disposition: attachment; filename="output.pdf"
    CLI:  write PDF to /data/<output> in container
```

The conversion pipeline (`pipeline.py`) is a single Python module called by both the web handler and the internal CLI entrypoint. It accepts file paths, shells out to Pandoc then runs the 4-step LaTeX sequence, and returns the path to the produced PDF. Temp directories are always cleaned up via `finally` blocks.

**LaTeX engine:** XeLaTeX. Chosen for native UTF-8 support, which is required for Portuguese documents with accented characters. No `inputenc`/`fontenc` boilerplate needed.

**Citation engine:** abntex2cite via Pandoc `--natbib`. Pandoc passes `[@key]` references through as `\cite{key}` LaTeX commands without resolving them. The LaTeX template includes `\usepackage[alf]{abntex2cite}` and `\bibliographystyle{abntex2-alf}`. BibTeX resolves citations during the compile sequence. This matches the workflow used by the example FLAM document and produces citations identical to native abntex2 documents.

**Why not Pandoc citeproc + ABNT CSL:** The canonical ABNT CSL file (`associacao-brasileira-de-normas-tecnicas.csl`) only claims NBR 6023:2002 compliance, not 2018. The 2018 revision changed reference formatting rules significantly (electronic sources, DOI placement, etc.). There is an open, unresolved issue in the CSL styles repository for this gap. abntex2cite, which ships with abntex2, is the de facto standard in Brazilian academia and handles all ABNT edge cases.

**Compile sequence:**
```
xelatex document.tex   # first pass — writes .aux with \citation{} entries
bibtex document.aux    # reads .aux + .bib, produces .bbl with formatted references
xelatex document.tex   # second pass — inserts formatted bibliography from .bbl
xelatex document.tex   # third pass — resolves page numbers for cross-references
```

### Key OSS dependencies
| Tool | Role |
|------|------|
| Pandoc | Markdown → LaTeX conversion (`--natbib` passes citations through as `\cite{}`) |
| XeLaTeX + abntex2 + abntex2cite | LaTeX → PDF compilation with ABNT styles and citation formatting |
| BibTeX | Citation resolution — reads `.bib` and generates formatted references via abntex2cite `.bst` style files |
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
  - `bibtex` (resolves citations from `.bib` via abntex2cite during the compile sequence; abntex2cite uses the traditional BibTeX engine, not biber/biblatex)

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

The `.bib` file is uploaded alongside the `.md` and written to the same temp directory as the generated `.tex` file. The Pandoc template includes `\bibliography{refs}` so BibTeX can locate it by name. Pandoc is invoked with `--natbib` only; `--bibliography` is not passed, as citeproc is not active and there is nothing for Pandoc to look up. Citations remain as `\cite{key}` in the `.tex` output and are resolved by abntex2cite during the BibTeX compile step.

---

## Interfaces

### Web UI

**Endpoint:** `POST /convert` — `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `md_file` | file | Yes | The Markdown source document |
| `bib_file` | file | No* | BibTeX bibliography file (* required if the document contains `[@key]` citations) |

**Success response:**
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="output.pdf"`
- Body: the compiled PDF

**Error response:**
- HTTP 422 with `Content-Type: text/plain`
- Body: relevant excerpt from Pandoc or xelatex stderr

**Validation:**
- If `md_file` is missing: HTTP 422 with message "Markdown file is required"
- If `bib_file` is absent but the document contains `[@key]` citations: BibTeX will not find the `.bib` file and will exit with a non-zero code, which the pipeline treats as a hard error (HTTP 422). The error message will identify the missing bibliography.
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

- Subprocess return codes are checked after every Pandoc, xelatex, and bibtex call.
- On failure, stderr is captured and surfaced:
  - Web: HTTP 422 with the relevant log excerpt (from whichever step failed: Pandoc, bibtex, or xelatex)
  - CLI: non-zero exit code + stderr printed to terminal
- Temp directories are always cleaned up via `finally` blocks regardless of success or failure.

---

## Out of Scope (MVP)

- **Figure/image support** — deferred; adds file handling complexity and is not needed for the initial student use cases
- **User accounts or document history** — deferred; the service is stateless by design for simplicity
- **Real-time preview** — deferred; requires a separate rendering pipeline and is out of scope for the initial release
- **Multiple output formats** — PDF only; other formats (DOCX, HTML) may be added in a future iteration
