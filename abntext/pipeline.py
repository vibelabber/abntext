import shutil
import subprocess
import tempfile
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_LATEX_DIR = Path(__file__).parent.parent / "latex"


def convert(md_path: Path, bib_path: Path | None, output_path: Path) -> None:
    """Convert a Markdown file to PDF using Pandoc + XeLaTeX + abntex2cite.

    Writes the compiled PDF to output_path. Manages its own temp directory
    internally and always cleans it up, whether the conversion succeeds or fails.

    Args:
        md_path: Absolute path to the Markdown source file.
        bib_path: Optional absolute path to the BibTeX file. Always written into
            the temp dir as refs.bib so the template's \\bibliography{refs} finds it.
        output_path: Destination path for the compiled PDF.

    Raises:
        RuntimeError: If any pipeline step fails, with the failing command's stderr.
    """
    tmpdir = Path(tempfile.mkdtemp())
    try:
        tex_path = tmpdir / "document.tex"
        pdf_path = tmpdir / "document.pdf"

        # Copy LaTeX class into cwd so xelatex finds it by name.
        cls_src = _LATEX_DIR / "flam.cls"
        if cls_src.exists():
            shutil.copy(cls_src, tmpdir / "flam.cls")

        # BibTeX expects refs.bib (hardcoded in the template's \bibliography{refs}).
        if bib_path is not None:
            shutil.copy(bib_path, tmpdir / "refs.bib")

        # Step 1: Pandoc — Markdown → LaTeX (citations passed through as \cite{key})
        _run(
            [
                "pandoc",
                str(md_path),
                "--natbib",
                "--template", str(_TEMPLATES_DIR / "flam.tex"),
                "-o", str(tex_path),
            ],
            cwd=tmpdir,
        )

        # Steps 2–5: xelatex → bibtex → xelatex → xelatex
        _run(["xelatex", "-interaction=nonstopmode", "document.tex"], cwd=tmpdir)
        _run(["bibtex", "document.aux"], cwd=tmpdir)
        _run(["xelatex", "-interaction=nonstopmode", "document.tex"], cwd=tmpdir)
        _run(["xelatex", "-interaction=nonstopmode", "document.tex"], cwd=tmpdir)

        shutil.copy(pdf_path, output_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run(cmd: list[str], cwd: Path) -> None:
    """Run a subprocess; raise RuntimeError with stderr if it exits non-zero."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command '{cmd[0]}' failed (exit {result.returncode}):\n{result.stderr}"
        )
