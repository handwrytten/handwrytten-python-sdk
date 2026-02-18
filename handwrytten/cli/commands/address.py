"""The `handwrytten address` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group()
def address():
    """Look up countries and states."""
    pass


@address.command("countries")
@click.pass_context
def address_countries(ctx):
    """List supported countries."""
    client = get_client(ctx)
    try:
        items = client.address_book.countries()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["code", "name"],
            headers=["Code", "Country"],
        )


@address.command("states")
@click.option("--country", default="US", help="Country code (default: US).")
@click.pass_context
def address_states(ctx, country):
    """List states/provinces for a country.

    \b
    Examples:
      handwrytten address states
      handwrytten address states --country CA
    """
    client = get_client(ctx)
    try:
        items = client.address_book.states(country)
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["code", "name"],
            headers=["Code", "State"],
        )
