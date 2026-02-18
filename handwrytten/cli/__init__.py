"""
Handwrytten CLI
~~~~~~~~~~~~~~~

Send real handwritten notes from the command line.

    $ handwrytten send --card 123 --font 456 --message "Thanks!" \\
          --to "Jane Doe, 123 Main St, Phoenix AZ 85001"

    $ handwrytten cards list
    $ handwrytten fonts list
    $ handwrytten orders get abc123
    $ handwrytten send --from-csv recipients.csv --card 123 --font 456
"""

import click

from handwrytten.cli.config import load_api_key
from handwrytten.cli.commands.send import send
from handwrytten.cli.commands.cards import cards
from handwrytten.cli.commands.fonts import fonts
from handwrytten.cli.commands.orders import orders
from handwrytten.cli.commands.gift_cards import gift_cards
from handwrytten.cli.commands.inserts import inserts
from handwrytten.cli.commands.account import account
from handwrytten.cli.commands.address import address


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--api-key",
    envvar="HANDWRYTTEN_API_KEY",
    help="API key (or set HANDWRYTTEN_API_KEY env var).",
)
@click.option(
    "--base-url",
    envvar="HANDWRYTTEN_BASE_URL",
    default=None,
    help="Override the API base URL.",
)
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output.")
@click.version_option(package_name="handwrytten")
@click.pass_context
def cli(ctx, api_key, base_url, output_json, quiet):
    """Handwrytten — send real handwritten notes from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key or load_api_key()
    ctx.obj["base_url"] = base_url
    ctx.obj["json"] = output_json
    ctx.obj["quiet"] = quiet


# Register command groups
cli.add_command(send)
cli.add_command(cards)
cli.add_command(fonts)
cli.add_command(orders)
cli.add_command(gift_cards)
cli.add_command(inserts)
cli.add_command(account)
cli.add_command(address)


def main():
    cli()


if __name__ == "__main__":
    main()
