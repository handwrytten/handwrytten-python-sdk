"""The `handwrytten account` command group."""

import click

from handwrytten.cli.config import get_client, save_api_key, CONFIG_FILE
from handwrytten.cli.output import error, output_json_raw, success
from handwrytten.exceptions import HandwryttenError


@click.group()
def account():
    """Manage your Handwrytten account and credentials."""
    pass


@account.command("login")
@click.option(
    "--key",
    prompt="API key",
    hide_input=True,
    help="Your Handwrytten API key.",
)
@click.pass_context
def account_login(ctx, key):
    """Save your API key for future CLI sessions.

    \b
    Example:
      handwrytten account login
      handwrytten account login --key your_api_key_here
    """
    # Verify the key works
    ctx.obj["api_key"] = key
    client = get_client(ctx)
    try:
        user = client.auth.get_user()
    except HandwryttenError as e:
        error(f"Authentication failed: {e}")
        ctx.exit(1)

    save_api_key(key)

    name = " ".join(filter(None, [user.first_name, user.last_name])) or user.email or "unknown"
    success(f"Logged in as {name}")
    click.echo(f"  Key saved to {CONFIG_FILE}")


@account.command("whoami")
@click.pass_context
def account_whoami(ctx):
    """Show current account info.

    \b
    Example:
      handwrytten account whoami
    """
    client = get_client(ctx)
    try:
        user = client.auth.get_user()
    except HandwryttenError as e:
        error(str(e))
        ctx.exit(1)

    if ctx.obj.get("json"):
        output_json_raw(user)
    else:
        click.echo(f"  {click.style('ID:', bold=True)}      {user.id}")
        click.echo(f"  {click.style('Email:', bold=True)}   {user.email or '—'}")
        click.echo(f"  {click.style('Name:', bold=True)}    {user.first_name or ''} {user.last_name or ''}")
        if user.company:
            click.echo(f"  {click.style('Company:', bold=True)} {user.company}")
        if user.credits is not None:
            click.echo(f"  {click.style('Credits:', bold=True)} {user.credits}")


@account.command("logout")
def account_logout():
    """Remove saved API key."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        success("API key removed.")
    else:
        click.echo("  No saved credentials found.")
