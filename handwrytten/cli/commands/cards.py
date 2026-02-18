"""The `handwrytten cards` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group()
def cards():
    """Browse card and stationery templates."""
    pass


@cards.command("list")
@click.option("--limit", "-n", default=50, help="Max cards to show.")
@click.pass_context
def cards_list(ctx, limit):
    """List available cards.

    \b
    Examples:
      handwrytten cards list
      handwrytten cards list --json
      handwrytten cards list -n 10
    """
    client = get_client(ctx)
    try:
        items = client.cards.list()[:limit]
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["id", "title", "category"],
            headers=["ID", "Title", "Category"],
        )


@cards.command("get")
@click.argument("card_id")
@click.pass_context
def cards_get(ctx, card_id):
    """Show details for a specific card.

    \b
    Example:
      handwrytten cards get 12345
    """
    client = get_client(ctx)
    try:
        card = client.cards.get(card_id)
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(card)
    else:
        click.echo(f"  {click.style('ID:', bold=True)}       {card.id}")
        click.echo(f"  {click.style('Title:', bold=True)}    {card.title}")
        click.echo(f"  {click.style('Category:', bold=True)} {card.category or '—'}")
        if card.image_url:
            click.echo(f"  {click.style('Image:', bold=True)}    {card.image_url}")


@cards.command("categories")
@click.pass_context
def cards_categories(ctx):
    """List available card categories."""
    client = get_client(ctx)
    try:
        cats = client.cards.categories()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(cats)
    else:
        for cat in cats:
            if isinstance(cat, dict):
                click.echo(f"  {cat.get('name', cat.get('id', cat))}")
            else:
                click.echo(f"  {cat}")
