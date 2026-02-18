"""The `handwrytten fonts` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group()
def fonts():
    """Browse handwriting styles."""
    pass


@fonts.command("list")
@click.pass_context
def fonts_list(ctx):
    """List available handwriting fonts.

    \b
    Examples:
      handwrytten fonts list
      handwrytten fonts list --json
    """
    client = get_client(ctx)
    try:
        items = client.fonts.list()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["id", "name", "preview_url"],
            headers=["ID", "Name", "Preview URL"],
        )
