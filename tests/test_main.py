import io
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from abntext.main import app

client = TestClient(app)

MD_CONTENT = b"---\ntitle: Test\nauthor: Author\n---\n\n## Intro\n\nHello.\n"
BIB_CONTENT = b"@book{key, title={T}, author={A}, year={2020}}\n"
PDF_CONTENT = b"%PDF-1.4 fake pdf"


def _fake_convert(md_path, bib_path, output_path):
    """Mock pipeline.convert: writes a fake PDF to output_path."""
    Path(output_path).write_bytes(PDF_CONTENT)


class TestGetRoot:
    def test_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPostConvert:
    def test_returns_pdf_on_valid_md(self):
        with patch("abntext.main.pipeline.convert", side_effect=_fake_convert):
            response = client.post(
                "/convert",
                files={"md_file": ("paper.md", io.BytesIO(MD_CONTENT), "text/markdown")},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == PDF_CONTENT

    def test_returns_pdf_with_bib(self):
        with patch("abntext.main.pipeline.convert", side_effect=_fake_convert):
            response = client.post(
                "/convert",
                files={
                    "md_file": ("paper.md", io.BytesIO(MD_CONTENT), "text/markdown"),
                    "bib_file": ("refs.bib", io.BytesIO(BIB_CONTENT), "text/plain"),
                },
            )
        assert response.status_code == 200
        assert response.content == PDF_CONTENT

    def test_missing_md_file_returns_422(self):
        response = client.post("/convert", files={})
        assert response.status_code == 422

    def test_pipeline_error_returns_422_with_message(self):
        with patch("abntext.main.pipeline.convert") as mock:
            mock.side_effect = RuntimeError("xelatex: ! Undefined control sequence.")
            response = client.post(
                "/convert",
                files={"md_file": ("paper.md", io.BytesIO(MD_CONTENT), "text/markdown")},
            )
        assert response.status_code == 422
        assert "xelatex" in response.text

    def test_bib_path_is_none_when_not_uploaded(self):
        """pipeline.convert must receive bib_path=None when no .bib is uploaded."""
        received_bib = []

        def capture(md_path, bib_path, output_path):
            received_bib.append(bib_path)
            Path(output_path).write_bytes(PDF_CONTENT)

        with patch("abntext.main.pipeline.convert", side_effect=capture):
            client.post(
                "/convert",
                files={"md_file": ("paper.md", io.BytesIO(MD_CONTENT), "text/markdown")},
            )

        assert received_bib == [None]
