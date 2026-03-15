import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response

from abntext import pipeline

app = FastAPI(title="ABNText")

_WEB_DIR = Path(__file__).parent.parent / "web"


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
