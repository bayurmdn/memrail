"""memrail CLI. Commands: compress, stats, restore, init."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from memrail.core.budget import DEFAULT_MAX_TOKENS, count_tokens
from memrail.core.classifier import Tier, classify_all, tier_counts, tier_tokens
from memrail.core.compressor import compress as compress_fn
from memrail.core.store import MemrailStore
from memrail.integrations.claude_code import install as install_claude

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Context budget manager for long-running AI agents.",
)
err = Console(stderr=True)
DEFAULT_STORE_PATH = Path.home() / ".memrail" / "store.json"


def _read_messages(input_path: Optional[Path]) -> list[dict]:
    if input_path:
        raw = Path(input_path).read_text()
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise typer.BadParameter("Input must be a JSON array of messages.")
    return data


@app.command()
def compress(
    input: Optional[Path] = typer.Option(None, "--input", "-i", help="JSON file with messages; default stdin."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write compressed JSON here; default stdout."),
    max_tokens: int = typer.Option(DEFAULT_MAX_TOKENS, "--max-tokens", "-m"),
    store_path: Path = typer.Option(DEFAULT_STORE_PATH, "--store", help="Pointer store path."),
) -> None:
    """Compress a message list. Reads JSON, writes compressed JSON."""
    messages = _read_messages(input)
    store = MemrailStore(store_path)
    result = compress_fn(messages, max_tokens=max_tokens, store=store)
    payload = json.dumps(result.messages, indent=2)
    if output:
        Path(output).write_text(payload)
    else:
        sys.stdout.write(payload)
        sys.stdout.write("\n")
    err.print(
        f"[bold cyan]memrail[/]: {result.summary} (ratio={result.ratio:.1%})",
    )


@app.command()
def stats(
    input: Optional[Path] = typer.Option(None, "--input", "-i"),
    max_tokens: int = typer.Option(DEFAULT_MAX_TOKENS, "--max-tokens", "-m"),
) -> None:
    """Show token usage + tier breakdown. No mutation."""
    messages = _read_messages(input)
    classified = classify_all(messages)
    counts = tier_counts(classified)
    tokens = tier_tokens(classified)
    total = count_tokens(messages)

    table = Table(title="memrail stats")
    table.add_column("Tier")
    table.add_column("Count", justify="right")
    table.add_column("Tokens", justify="right")
    for t in Tier:
        table.add_row(t.name, str(counts[t]), str(tokens[t]))
    table.add_row("[bold]TOTAL[/]", str(len(messages)), str(total))
    table.add_row("budget", "-", f"{total}/{max_tokens}")
    Console().print(table)


@app.command()
def restore(
    pointer_id: str = typer.Argument(..., help="Pointer UUID or full [memrail:label:uuid] string."),
    store_path: Path = typer.Option(DEFAULT_STORE_PATH, "--store"),
) -> None:
    """Retrieve original artifact by pointer id."""
    pid = pointer_id.strip("[]").split(":")[-1]
    store = MemrailStore(store_path)
    content = store.get(pid)
    if content is None:
        err.print(f"[red]pointer not found: {pid}[/]")
        raise typer.Exit(code=1)
    sys.stdout.write(json.dumps(content, indent=2, default=str))
    sys.stdout.write("\n")


init_app = typer.Typer(help="Install memrail into project scaffolds.")
app.add_typer(init_app, name="init")


@init_app.command("claude")
def init_claude(
    project: Path = typer.Option(Path.cwd(), "--project", "-p", help="Project root."),
) -> None:
    """Write .claude/skills/memrail/SKILL.md + .claude/settings.json."""
    written = install_claude(project)
    for p in written:
        err.print(f"[green]wrote[/] {p}")


if __name__ == "__main__":
    app()
