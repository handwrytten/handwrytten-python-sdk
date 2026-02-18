"""The `handwrytten orders` command group."""

import click

from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, output_json_raw, print_table
from handwrytten.exceptions import HandwryttenError


@click.group()
def orders():
    """View and manage orders."""
    pass


@orders.command("list")
@click.option("--page", default=1, help="Page number.")
@click.option("--per-page", default=20, help="Results per page.")
@click.pass_context
def orders_list(ctx, page, per_page):
    """List recent orders.

    \b
    Examples:
      handwrytten orders list
      handwrytten orders list --page 2 --per-page 10
    """
    client = get_client(ctx)
    try:
        items = client.orders.list(page=page, per_page=per_page)
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(items)
    else:
        print_table(
            items,
            columns=["id", "status", "created_at", "tracking_number"],
            headers=["Order ID", "Status", "Created", "Tracking"],
        )


@orders.command("get")
@click.argument("order_id")
@click.pass_context
def orders_get(ctx, order_id):
    """Show details for a specific order.

    \b
    Example:
      handwrytten orders get abc123
    """
    client = get_client(ctx)
    try:
        order = client.orders.get(order_id)
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(order)
    else:
        click.echo(f"  {click.style('Order ID:', bold=True)}  {order.id}")
        click.echo(f"  {click.style('Status:', bold=True)}    {order.status or '—'}")
        click.echo(f"  {click.style('Created:', bold=True)}   {order.created_at or '—'}")
        click.echo(f"  {click.style('Tracking:', bold=True)}  {order.tracking_number or '—'}")
        if order.message:
            click.echo(f"  {click.style('Message:', bold=True)}   {order.message[:100]}")
