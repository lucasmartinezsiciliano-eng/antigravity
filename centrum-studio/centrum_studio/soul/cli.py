from __future__ import annotations

import json
import sys

import click

from ..config import configure_logging, get_config
from ..errors import CentrumStudioError
from .loader import SoulLoader


@click.group(help="centrum-studio CLI — Soul File management")
def cli() -> None:
    pass


@cli.group(help="Soul File management")
def soul() -> None:
    pass


@soul.command("list", help="List souls and versions in the data directory")
def soul_list() -> None:
    loader = SoulLoader()
    cfg = get_config()
    cfg.ensure_directories()
    rows = loader.list_souls()
    if not rows:
        click.echo(f"No souls found in {loader.souls_dir}")
        return
    click.echo(f"Souls dir: {loader.souls_dir}")
    for row in rows:
        active = f" (active: {row['active']})" if row["active"] else ""
        versions = ", ".join(row["versions"]) or "<none>"
        click.echo(f"  - {row['name']}{active}  [versions: {versions}]")


@soul.command("create", help="Create a new Soul File scaffold")
@click.argument("name")
@click.option("--version", default="v1", show_default=True)
@click.option("--trigger-token", default=None, help="Override trigger token (default: cs_<name>_<version>)")
@click.option("--character-name", default=None, help="Display character name")
@click.option("--notes", default=None, help="Notes for the Soul File")
@click.option("--no-activate", is_flag=True, help="Don't set as ACTIVE")
def soul_create(
    name: str,
    version: str,
    trigger_token: str | None,
    character_name: str | None,
    notes: str | None,
    no_activate: bool,
) -> None:
    cfg = get_config()
    cfg.ensure_directories()
    loader = SoulLoader()
    try:
        path = loader.create_soul(
            name=name,
            version=version,
            trigger_token=trigger_token,
            character_name=character_name,
            activate=not no_activate,
            notes=notes,
        )
    except CentrumStudioError as e:
        click.echo(json.dumps(e.to_dict(), indent=2), err=True)
        sys.exit(1)
    click.echo(f"Created soul at: {path}")
    if not no_activate:
        click.echo(f"Activated: {name}/{version}")


@soul.command("activate", help="Set an existing soul/version as ACTIVE")
@click.argument("name")
@click.argument("version")
def soul_activate(name: str, version: str) -> None:
    cfg = get_config()
    cfg.ensure_directories()
    loader = SoulLoader()
    try:
        target = loader.activate(name, version)
    except CentrumStudioError as e:
        click.echo(json.dumps(e.to_dict(), indent=2), err=True)
        sys.exit(1)
    click.echo(f"ACTIVE -> {target}")


@soul.command("show", help="Show active Soul File manifest")
@click.option("--name", default=None, help="Soul name (default: ACTIVE_SOUL env)")
def soul_show(name: str | None) -> None:
    loader = SoulLoader()
    try:
        soul_obj, path = loader.load_with_paths(name)
    except CentrumStudioError as e:
        click.echo(json.dumps(e.to_dict(), indent=2), err=True)
        sys.exit(1)
    click.echo(json.dumps({"path": str(path), "soul": soul_obj.to_dict()}, indent=2, ensure_ascii=False))


def main() -> None:
    configure_logging()
    cli()


if __name__ == "__main__":
    main()
