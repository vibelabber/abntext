from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from abntext.pipeline import _run, convert


# ── _run ─────────────────────────────────────────────────────────────────────

class TestRun:
    def test_passes_on_zero_returncode(self):
        with patch("abntext.pipeline.subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stderr="", stdout="")
            _run(["echo", "hi"], cwd=Path("/tmp"))  # must not raise

    def test_raises_on_nonzero_returncode(self):
        with patch("abntext.pipeline.subprocess.run") as mock:
            mock.return_value = MagicMock(
                returncode=1, stderr="! Undefined control sequence."
            )
            with pytest.raises(RuntimeError, match="Undefined control sequence"):
                _run(["xelatex", "doc.tex"], cwd=Path("/tmp"))

    def test_error_message_includes_command_name(self):
        with patch("abntext.pipeline.subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1, stderr="oops")
            with pytest.raises(RuntimeError, match="pandoc"):
                _run(["pandoc", "input.md"], cwd=Path("/tmp"))


# ── convert ───────────────────────────────────────────────────────────────────

def _fake_subprocess(cmd, **kwargs):
    """Mock subprocess.run: succeeds; creates document.pdf on any xelatex call."""
    if cmd[0] == "xelatex":
        (Path(kwargs["cwd"]) / "document.pdf").write_bytes(b"%PDF-1.4")
    return MagicMock(returncode=0, stderr="", stdout="")


class TestConvert:
    def test_pandoc_receives_natbib_flag(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        with patch("abntext.pipeline.subprocess.run", side_effect=_fake_subprocess) as mock:
            convert(md, None, out)

        pandoc_call = mock.call_args_list[0]
        cmd = pandoc_call[0][0]
        assert cmd[0] == "pandoc"
        assert "--natbib" in cmd
        assert "-o" in cmd

    def test_bib_is_saved_as_refs_bib(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        bib = tmp_path / "myrefs.bib"
        bib.write_text("@book{k, title={T}, author={A}, year={2020}}\n")
        out = tmp_path / "out.pdf"

        refs_bib_present = []

        def check_refs_bib(cmd, **kwargs):
            if cmd[0] == "bibtex":
                refs_bib_present.append(
                    (Path(kwargs["cwd"]) / "refs.bib").exists()
                )
            if cmd[0] == "xelatex":
                (Path(kwargs["cwd"]) / "document.pdf").write_bytes(b"%PDF-1.4")
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch("abntext.pipeline.subprocess.run", side_effect=check_refs_bib):
            convert(md, bib, out)

        assert refs_bib_present == [True]

    def test_compile_sequence_is_pandoc_xelatex_bibtex_xelatex_xelatex(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        with patch("abntext.pipeline.subprocess.run", side_effect=_fake_subprocess) as mock:
            convert(md, None, out)

        commands = [c[0][0][0] for c in mock.call_args_list]
        assert commands == ["pandoc", "xelatex", "bibtex", "xelatex", "xelatex"]

    def test_output_pdf_is_written_to_output_path(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        with patch("abntext.pipeline.subprocess.run", side_effect=_fake_subprocess):
            convert(md, None, out)

        assert out.exists()
        assert out.read_bytes() == b"%PDF-1.4"

    def test_tmpdir_cleaned_up_on_success(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        captured_tmpdir = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def spy_mkdtemp():
            d = original_mkdtemp()
            captured_tmpdir.append(Path(d))
            return d

        with patch("abntext.pipeline.tempfile.mkdtemp", side_effect=spy_mkdtemp):
            with patch("abntext.pipeline.subprocess.run", side_effect=_fake_subprocess):
                convert(md, None, out)

        assert len(captured_tmpdir) == 1
        assert not captured_tmpdir[0].exists()

    def test_tmpdir_cleaned_up_on_failure(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        captured_tmpdir = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def spy_mkdtemp():
            d = original_mkdtemp()
            captured_tmpdir.append(Path(d))
            return d

        with patch("abntext.pipeline.tempfile.mkdtemp", side_effect=spy_mkdtemp):
            with patch("abntext.pipeline.subprocess.run") as mock:
                mock.return_value = MagicMock(returncode=1, stderr="pandoc: error")
                with pytest.raises(RuntimeError):
                    convert(md, None, out)

        assert len(captured_tmpdir) == 1
        assert not captured_tmpdir[0].exists()

    def test_raises_runtime_error_on_pipeline_failure(self, tmp_path):
        md = tmp_path / "input.md"
        md.write_text("---\ntitle: T\nauthor: A\n---\n\nBody.\n")
        out = tmp_path / "out.pdf"

        with patch("abntext.pipeline.subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=1, stderr="xelatex: ! error")
            with pytest.raises(RuntimeError):
                convert(md, None, out)
