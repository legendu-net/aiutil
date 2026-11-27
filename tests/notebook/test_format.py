"""Tests for aiutil.notebook.format."""

from pathlib import Path

import nbformat
import pytest
from nbformat.v4 import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
    new_raw_cell,
)

from aiutil.notebook.format import (
    format_notebook,
    format_notebook_markdown,
    format_notebooks,
    main,
)


def _write_notebook(path: Path, cells: list) -> Path:
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nbformat.write(nb, path)
    return path


def test_format_notebook_markdown_preserves_non_markdown_and_outputs(
    tmp_path: Path,
) -> None:
    """Format markdown prose & fenced blocks while leaving code/raw/outputs untouched."""
    output = new_output("stream", name="stdout", text="hello   world\n")
    unformatted_code = "x=1+2\nprint(  'hi'  )"
    raw_text = "raw   content   untouched"
    frontmatter_cell = "---\ntitle: MyST Notebook\n---\n\n#   Heading\n"
    md_with_fences = (
        "* item 1\n"
        "*   item 2\n\n"
        "```python\n"
        "def foo( x,y ):\n"
        "  return x+y\n"
        "```\n\n"
        "```json\n"
        '{"a":1,"b":2}\n'
        "```\n\n"
        "```bash\n"
        "if [ -f foo ]; then\n"
        "echo hi\n"
        "fi\n"
        "```"
    )

    nb_path = _write_notebook(
        tmp_path / "sample.ipynb",
        [
            new_markdown_cell(frontmatter_cell),
            new_markdown_cell(md_with_fences),
            new_markdown_cell("   \n  "),
            new_code_cell(
                unformatted_code,
                execution_count=7,
                outputs=[output],
            ),
            new_raw_cell(raw_text),
        ],
    )

    changed = format_notebook_markdown(nb_path)
    assert changed is True

    nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)
    # Cell 0: frontmatter preserved, heading formatted, trailing newline kept
    assert nb.cells[0].source.startswith("---\ntitle: MyST Notebook\n---\n")
    assert "# Heading\n" in nb.cells[0].source
    assert nb.cells[0].source.endswith("\n")

    # Cell 1: markdown prose and fenced blocks formatted, no trailing newline added
    cell1 = nb.cells[1].source
    assert not cell1.endswith("\n")
    assert "- item 1\n- item 2" in cell1
    assert "def foo(x, y):\n    return x + y" in cell1
    assert '{\n  "a": 1,\n  "b": 2\n}' in cell1
    assert "if [ -f foo ]; then\n    echo hi\nfi" in cell1

    # Cell 2: whitespace-only markdown cell left untouched
    assert nb.cells[2].source == "   \n  "

    # Cell 3: code cell, execution_count, and outputs completely untouched
    assert nb.cells[3].source == unformatted_code
    assert nb.cells[3].execution_count == 7
    assert nb.cells[3].outputs == [output]

    # Cell 4: raw cell completely untouched
    assert nb.cells[4].source == raw_text

    # Idempotent on second call
    assert format_notebook_markdown(nb_path) is False


def test_format_notebook_code_and_markdown_flags(tmp_path: Path) -> None:
    """Format code and markdown cells while respecting toggle flags and outputs."""
    output = new_output(
        "execute_result", data={"text/plain": "'untouched'"}, execution_count=3
    )
    nb_path = _write_notebook(
        tmp_path / "both.ipynb",
        [
            new_markdown_cell("#   Title\n\nSome   text."),
            new_code_cell("x=1+2\ny =   [1,2,3]", execution_count=3, outputs=[output]),
        ],
    )

    # Only markdown
    assert format_notebook(nb_path, format_code=False, format_markdown=True) is True
    nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)
    assert nb.cells[0].source == "# Title\n\nSome text."
    assert nb.cells[1].source == "x=1+2\ny =   [1,2,3]"
    assert nb.cells[1].outputs == [output]

    # Now format code only
    assert format_notebook(nb_path, format_code=True, format_markdown=False) is True
    nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)
    assert nb.cells[1].source == "x = 1 + 2\ny = [1, 2, 3]"
    assert nb.cells[1].execution_count == 3
    assert nb.cells[1].outputs == [output]


def test_format_notebook_missing_or_invalid(tmp_path: Path) -> None:
    """Return False cleanly on missing, corrupted, or non-notebook JSON files."""
    missing = tmp_path / "missing.ipynb"
    assert format_notebook(missing) is False

    corrupt = tmp_path / "corrupt.ipynb"
    corrupt.write_text("{not valid json", encoding="utf-8")
    assert format_notebook(corrupt) is False

    json_list = tmp_path / "list.ipynb"
    json_list.write_text("[]", encoding="utf-8")
    assert format_notebook(json_list, format_code=False) is False

    json_empty_obj = tmp_path / "empty_obj.ipynb"
    json_empty_obj.write_text("{}", encoding="utf-8")
    assert format_notebook(json_empty_obj, format_code=False) is False


def test_format_notebook_markdown_v3_and_leading_dash_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Handle nbformat v3 worksheets and relative filenames starting with '-'."""
    v3_nb = tmp_path / "v3.ipynb"
    v3_nb.write_text(
        '{"nbformat": 3, "nbformat_minor": 0, "worksheets": [{"cells": ['
        '{"cell_type": "markdown", "source": "#   V3 Heading\\n"}'
        "]}]}",
        encoding="utf-8",
    )
    assert format_notebook_markdown(v3_nb) is True
    v3_loaded = nbformat.read(v3_nb, as_version=nbformat.NO_CONVERT)
    assert v3_loaded.worksheets[0].cells[0].source == "# V3 Heading\n"

    monkeypatch.chdir(tmp_path)
    dash_nb = _write_notebook(
        Path("-notes.ipynb"),
        [new_markdown_cell("#   Dash\n"), new_code_cell("x=1+2")],
    )
    assert format_notebook(dash_nb) is True
    nb = nbformat.read(dash_nb, as_version=nbformat.NO_CONVERT)
    assert nb.cells[0].source == "# Dash\n"
    assert nb.cells[1].source == "x = 1 + 2"


def test_format_notebooks_skips_checkpoints_and_cli_main(tmp_path: Path) -> None:
    """Handle files and directories, skip .ipynb_checkpoints, and verify CLI main."""
    good_nb = _write_notebook(
        tmp_path / "good.ipynb",
        [
            new_markdown_cell("#   Header\n"),
            new_code_cell("a=1+1"),
        ],
    )
    sub_dir = tmp_path / "nested"
    sub_dir.mkdir()
    nested_nb = _write_notebook(
        sub_dir / "nested.ipynb",
        [new_code_cell("b=2+2")],
    )
    ckpt_dir = tmp_path / ".ipynb_checkpoints"
    ckpt_dir.mkdir()
    ckpt_nb = _write_notebook(
        ckpt_dir / "good-checkpoint.ipynb",
        [new_code_cell("c=3+3")],
    )
    ignored_venv_dir = tmp_path / ".venv"
    ignored_venv_dir.mkdir()
    ignored_venv_nb = _write_notebook(
        ignored_venv_dir / "ignored.ipynb",
        [new_code_cell("d=4+4")],
    )
    explicit_venv_ancestor = tmp_path / "venv" / "notebooks"
    explicit_venv_ancestor.mkdir(parents=True)
    explicit_venv_nb = _write_notebook(
        explicit_venv_ancestor / "explicit.ipynb",
        [new_code_cell("e=5+5")],
    )

    failed = format_notebooks([tmp_path, ckpt_nb, explicit_venv_ancestor])
    assert failed == []
    assert (
        nbformat.read(good_nb, as_version=nbformat.NO_CONVERT).cells[0].source
        == "# Header\n"
    )
    assert (
        nbformat.read(good_nb, as_version=nbformat.NO_CONVERT).cells[1].source
        == "a = 1 + 1"
    )
    assert (
        nbformat.read(nested_nb, as_version=nbformat.NO_CONVERT).cells[0].source
        == "b = 2 + 2"
    )
    # Checkpoint and .venv notebooks must remain untouched
    assert (
        nbformat.read(ckpt_nb, as_version=nbformat.NO_CONVERT).cells[0].source
        == "c=3+3"
    )
    assert (
        nbformat.read(ignored_venv_nb, as_version=nbformat.NO_CONVERT).cells[0].source
        == "d=4+4"
    )
    # Explicitly passed directory under a 'venv' ancestor must still be formatted
    assert (
        nbformat.read(explicit_venv_nb, as_version=nbformat.NO_CONVERT).cells[0].source
        == "e = 5 + 5"
    )

    # CLI main with --no-code and --no-markdown flags
    cli_nb = _write_notebook(
        tmp_path / "cli.ipynb",
        [new_markdown_cell("#   CLI\n"), new_code_cell("z=4+4")],
    )
    main([str(cli_nb), "--no-code"])
    nb_after = nbformat.read(cli_nb, as_version=nbformat.NO_CONVERT)
    assert nb_after.cells[0].source == "# CLI\n"
    assert nb_after.cells[1].source == "z=4+4"

    main([str(cli_nb), "--no-markdown"])
    nb_after_code = nbformat.read(cli_nb, as_version=nbformat.NO_CONVERT)
    assert nb_after_code.cells[0].source == "# CLI\n"
    assert nb_after_code.cells[1].source == "z = 4 + 4"

    # CLI main exits non-zero on missing path
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "does_not_exist.ipynb")])
    assert exc_info.value.code == 1
