# ABNText Docker image
# Contains: Python + FastAPI, Pandoc, XeLaTeX + abntex2 + abntex2cite
FROM python:3.11-slim

# Enable contrib repo (required for ttf-mscorefonts-installer).
RUN sed -i 's/^Components: main$/Components: main contrib/' /etc/apt/sources.list.d/debian.sources

# Pre-accept the Microsoft core fonts EULA non-interactively.
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" \
    | debconf-set-selections

# Install system dependencies.
# ttf-mscorefonts-installer downloads Times New Roman (and other MS fonts)
# from SourceForge during the build — requires internet access.
# fontconfig is installed explicitly so fc-cache is available on PATH.
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-xetex \
    texlive-lang-portuguese \
    texlive-fonts-recommended \
    texlive-latex-extra \
    ttf-mscorefonts-installer \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source before install so pip can resolve the package.
COPY pyproject.toml ./
COPY abntext/ ./abntext/
COPY templates/ ./templates/
COPY latex/ ./latex/
COPY web/ ./web/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "abntext.main:app", "--host", "0.0.0.0", "--port", "8000"]
