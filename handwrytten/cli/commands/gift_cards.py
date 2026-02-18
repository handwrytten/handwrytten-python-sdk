"""The `handwrytten gift-cards` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group("gift-cards")
def gift_cards():
    """Browse gift cards."""
    pass


@gift_cards.command("list")
@click.pass_context
def gift_cards_list(ctx):
    """List available gift cards."""
    client = get_client(ctx)
    try:
        items = client.gift_cards.list()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["id", "title", "amount"],
            headers=["ID", "Title", "Amount"],
        )
