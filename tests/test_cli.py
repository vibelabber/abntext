import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from abntext.cli import _main, _parse_args

PDF_CONTENT = b"%PDF-1.4 fake"


class TestParseArgs:
    def test_convert_subcommand_required(self):
        with pytest.raises(SystemExit):
            _parse_args([])

    def test_md_file_required(self):
        with pytest.raises(SystemExit):
            _parse_args(["convert"])

    def test_md_file_parsed(self):
        args = _parse_args(["convert", "paper.md"])
        assert args.md_file == "paper.md"

    def test_bib_default_is_none(self):
        args = _parse_args(["convert", "paper.md"])
        assert args.bib is None

    def test_bib_flag(self):
        args = _parse_args(["convert", "paper.md", "--bib", "refs.bib"])
        assert args.bib == "refs.bib"

    def test_output_default_is_none(self):
        args = _parse_args(["convert", "paper.md"])
        assert args.output is None

    def test_output_flag(self):
        args = _parse_args(["convert", "paper.md", "--output", "out.pdf"])
        assert args.output == "out.pdf"


class TestMain:
    def test_resolves_md_path_under_data(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("hello")

        received = []

        def capture(md_path, bib_path, output_path):
            received.append((md_path, bib_path, output_path))
            Path(output_path).write_bytes(PDF_CONTENT)

        with patch("abntext.cli.DATA_DIR", tmp_path):
            with patch("abntext.cli.pipeline.convert", side_effect=capture):
                _main(["convert", "paper.md"])

        assert received[0][0] == tmp_path / "paper.md"

    def test_resolves_bib_path_under_data(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("hello")
        bib = tmp_path / "refs.bib"
        bib.write_text("")

        received = []

        def capture(md_path, bib_path, output_path):
            received.append((md_path, bib_path, output_path))
            Path(output_path).write_bytes(PDF_CONTENT)

        with patch("abntext.cli.DATA_DIR", tmp_path):
            with patch("abntext.cli.pipeline.convert", side_effect=capture):
                _main(["convert", "paper.md", "--bib", "refs.bib"])

        assert received[0][1] == tmp_path / "refs.bib"

    def test_default_output_is_md_stem_under_data(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("hello")

        received = []

        def capture(md_path, bib_path, output_path):
            received.append(output_path)
            Path(output_path).write_bytes(PDF_CONTENT)

        with patch("abntext.cli.DATA_DIR", tmp_path):
            with patch("abntext.cli.pipeline.convert", side_effect=capture):
                _main(["convert", "paper.md"])

        assert received[0] == tmp_path / "paper.pdf"

    def test_missing_md_file_exits_with_code_1(self, tmp_path, capsys):
        with patch("abntext.cli.DATA_DIR", tmp_path):
            with pytest.raises(SystemExit) as exc:
                _main(["convert", "nonexistent.md"])
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "nonexistent.md" in captured.err

    def test_pipeline_error_exits_with_code_1(self, tmp_path, capsys):
        md = tmp_path / "paper.md"
        md.write_text("hello")

        with patch("abntext.cli.DATA_DIR", tmp_path):
            with patch("abntext.cli.pipeline.convert") as mock:
                mock.side_effect = RuntimeError("xelatex failed")
                with pytest.raises(SystemExit) as exc:
                    _main(["convert", "paper.md"])

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "xelatex failed" in captured.err
