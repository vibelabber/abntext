"""Internal CLI entrypoint — invoked inside the Docker container.

The user never calls this directly. The bin/abntext shell script runs:
    docker run --rm -v $(pwd):/data abntext python -m abntext.cli convert [args]
"""
import argparse
import sys
from pathlib import Path

from abntext import pipeline

# /data is the Docker volume mount of the user's current directory.
DATA_DIR = Path("/data")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="abntext")
    sub = parser.add_subparsers(dest="command", required=True)

    convert_parser = sub.add_parser("convert", help="Convert Markdown to PDF")
    convert_parser.add_argument("md_file", help="Markdown file (relative to /data/)")
    convert_parser.add_argument("--bib", default=None, help="BibTeX file (relative to /data/)")
    convert_parser.add_argument("--output", default=None, help="Output PDF path (relative to /data/)")

    return parser.parse_args(argv)


def _main(argv: list[str]) -> None:
    args = _parse_args(argv)

    md_path = DATA_DIR / args.md_file
    if not md_path.exists():
        print(f"Error: file not found: {args.md_file}", file=sys.stderr)
        sys.exit(1)

    bib_path = DATA_DIR / args.bib if args.bib else None

    stem = Path(args.md_file).stem
    output_path = DATA_DIR / (args.output if args.output else f"{stem}.pdf")

    try:
        pipeline.convert(md_path, bib_path, output_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main(sys.argv[1:])
