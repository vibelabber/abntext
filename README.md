# ABNText

Converte documentos Markdown para PDF no formato ABNT com estilos FLAM.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado e em execução.

## Instalação

```bash
git clone <repo-url>
cd abntext
docker compose build
```

## Interface Web

```bash
docker compose up
```

Acesse `http://localhost:8000` no navegador. Envie um arquivo `.md` e,
opcionalmente, um `.bib`. O PDF será baixado automaticamente.

## CLI

```bash
# Converter sem citações
bin/abntext convert meu_artigo.md

# Converter com bibliography
bin/abntext convert meu_artigo.md --bib referencias.bib

# Especificar nome do PDF de saída
bin/abntext convert meu_artigo.md --bib referencias.bib --output artigo_final.pdf
```

Os arquivos são resolvidos relativos ao diretório atual.

## Formato do documento

O arquivo Markdown deve começar com um bloco YAML com os metadados:

```markdown
---
title: "Título do Trabalho"
author: "Nome do Autor"
institution: "Nome da Instituição"
course: "Nome do Curso"
professor: "Nome do Professor"
city: "Cidade"
year: "2026"
---

## Seção

Texto com citação [@chave2020].

## Referências
```

Citações usam a sintaxe `[@chave]`. As chaves correspondem às entradas
do arquivo `.bib`.

## Exemplo

```bash
cd example
../bin/abntext convert example.md --bib example.bib
```

## Deploy com Docker Compose

Baixe o `docker-compose.yml` e suba o serviço:

```bash
curl -O https://raw.githubusercontent.com/vibelabber/abntext/main/docker-compose.yml
docker compose up -d
```

A imagem é baixada automaticamente do GHCR. O serviço ficará disponível em
`http://localhost:8000` e reiniciará automaticamente com o sistema.

Para atualizar:

```bash
docker compose pull && docker compose up -d
```

## Desenvolvimento local (sem Docker)

Requer [Pandoc](https://pandoc.org/installing.html) e TeX Live com abntex2
instalados nativamente.

```bash
# Instalar dependências Python
pip install -e ".[dev]"

# Iniciar o servidor web
uvicorn abntext.main:app --reload

# Executar os testes
pytest tests/ -v

# Usar a CLI diretamente (sem Docker)
python -m abntext.cli convert paper.md --bib refs.bib
```

> **Nota:** Em sistemas Debian/Ubuntu, instale as dependências do sistema com:
> ```bash
> sudo apt-get install pandoc texlive-xetex texlive-lang-portuguese \
>   texlive-fonts-recommended texlive-latex-extra
> ```
