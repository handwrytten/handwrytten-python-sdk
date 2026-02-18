"""The `handwrytten inserts` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group()
def inserts():
    """Browse card inserts."""
    pass


@inserts.command("list")
@click.pass_context
def inserts_list(ctx):
    """List available inserts."""
    client = get_client(ctx)
    try:
        items = client.inserts.list()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["id", "title"],
            headers=["ID", "Title"],
        )
