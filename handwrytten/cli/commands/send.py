"""The `handwrytten send` command — the star of the CLI."""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path
from typing import Any, Dict, List

import click

from handwrytten.cli.address_parser import normalize_csv_row, parse_address_string
from handwrytten.cli.config import get_client
from handwrytten.cli.output import error, info, output_json_raw, success, warn
from handwrytten.exceptions import HandwryttenError


@click.command()
@click.option("--card", "card_id", required=True, help="Card/stationery ID.")
@click.option("--font", "font_id", required=True, help="Handwriting font ID.")
@click.option(
    "--message", "-m",
    help='Message body. Use {{firstName}}, {{lastName}} for personalization. '
         'Pass "-" to read from stdin.',
)
@click.option(
    "--message-file",
    type=click.Path(exists=True),
    help="Read message body from a file.",
)
@click.option(
    "--to",
    "to_address",
    help='Recipient address: "Jane Doe, 123 Main St, Phoenix AZ 85001".',
)
@click.option(
    "--from", "from_address",
    help='Return address (same format as --to).',
)
@click.option(
    "--from-csv",
    type=click.Path(exists=True),
    help="Send to all recipients in a CSV file.",
)
@click.option("--gift-card", help="Gift card denomination ID to include.")
@click.option("--insert", help="Insert ID to include.")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be sent without actually sending.",
)
@click.pass_context
def send(
    ctx,
    card_id,
    font_id,
    message,
    message_file,
    to_address,
    from_address,
    from_csv,
    gift_card,
    insert,
    dry_run,
):
    """Send handwritten notes to one or more recipients.

    \b
    Examples:
      # Single note
      handwrytten send --card 123 --font 456 \\
          --message "Thanks for your business!" \\
          --to "Jane Doe, 123 Main St, Phoenix AZ 85001"

    \b
      # Batch from CSV with personalization
      handwrytten send --card 123 --font 456 \\
          --message "Hi {{firstName}}, thanks for being a customer!" \\
          --from-csv recipients.csv

    \b
      # Message from file, stdin piping
      echo "Thank you!" | handwrytten send --card 123 --font 456 \\
          --message - --to "Jane Doe, 123 Main St, Phoenix AZ 85001"
    """
    output_json = ctx.obj.get("json", False)
    quiet = ctx.obj.get("quiet", False)

    # Resolve message
    msg = _resolve_message(message, message_file)
    if not msg:
        error("A message is required. Use --message, --message-file, or pipe to stdin.")
        ctx.exit(1)

    # Resolve recipients
    recipients = _resolve_recipients(to_address, from_csv)
    if not recipients:
        error("At least one recipient is required. Use --to or --from-csv.")
        ctx.exit(1)

    # Resolve sender
    sender = None
    if from_address:
        try:
            sender = parse_address_string(from_address)
        except ValueError as e:
            error(f"Cannot parse --from address: {e}")
            ctx.exit(1)

    info(
        f"Sending {len(recipients)} note{'s' if len(recipients) != 1 else ''} "
        f"using card {card_id}, font {font_id}",
        quiet=quiet,
    )

    if dry_run:
        _print_dry_run(recipients, msg, card_id, font_id, sender, output_json)
        return

    client = get_client(ctx)
    sent = 0
    failed = 0
    results = []

    for i, recipient in enumerate(recipients, 1):
        personalized_msg = _personalize(msg, recipient)

        try:
            send_kwargs = {
                "card_id": card_id,
                "font": font_id,
                "message": personalized_msg,
                "recipient": recipient,
            }
            if sender:
                send_kwargs["sender"] = sender
            if gift_card:
                send_kwargs["denomination_id"] = int(gift_card)
            if insert:
                send_kwargs["insert_id"] = int(insert)

            result = client.orders.send(**send_kwargs)
            sent += 1
            results.append(result)

            if not output_json:
                name = f"{recipient.get('firstName', '')} {recipient.get('lastName', '')}".strip()
                order_id = result.get("id", result.get("order_id", "unknown"))
                success(f"[{i}/{len(recipients)}] Sent to {name} — order {order_id}")

        except HandwryttenError as e:
            failed += 1
            name = f"{recipient.get('firstName', '')} {recipient.get('lastName', '')}".strip()
            error(f"[{i}/{len(recipients)}] Failed for {name}: {e}")

    if output_json:
        output_json_raw(results)
    elif not quiet:
        click.echo()
        if failed == 0:
            success(f"All {sent} note{'s' if sent != 1 else ''} sent successfully!")
        else:
            warn(f"{sent} sent, {failed} failed out of {len(recipients)} total.")


def _resolve_message(message: str | None, message_file: str | None) -> str | None:
    """Get message from --message, --message-file, or stdin."""
    if message == "-":
        return sys.stdin.read().strip()
    if message:
        return message
    if message_file:
        return Path(message_file).read_text().strip()
    # Check if stdin has data (piped)
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return data
    return None


def _resolve_recipients(
    to_address: str | None,
    from_csv: str | None,
) -> List[Dict[str, str]]:
    """Build recipient list from --to or --from-csv."""
    recipients = []

    if to_address:
        try:
            recipients.append(parse_address_string(to_address))
        except ValueError as e:
            raise click.ClickException(f"Cannot parse --to address: {e}")

    if from_csv:
        csv_path = Path(from_csv)
        text = csv_path.read_text()

        # Auto-detect delimiter
        dialect = csv.Sniffer().sniff(text[:2048])
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)

        for row_num, row in enumerate(reader, 2):  # row 2 because header is row 1
            try:
                normalized = normalize_csv_row(row)
                # Validate required fields
                for field in ("firstName", "lastName", "street1", "city", "state", "zip"):
                    if field not in normalized or not normalized[field]:
                        raise ValueError(f"Missing required field '{field}'")
                recipients.append(normalized)
            except ValueError as e:
                raise click.ClickException(f"CSV row {row_num}: {e}")

    return recipients


def _personalize(message: str, recipient: Dict[str, str]) -> str:
    """Replace {{field}} placeholders with recipient values."""
    result = message
    for key, value in recipient.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


def _print_dry_run(
    recipients: List[Dict[str, str]],
    message: str,
    card_id: str,
    font_id: str,
    sender: Dict[str, str] | None,
    output_json: bool,
) -> None:
    """Show what would be sent in dry-run mode."""
    if output_json:
        import json

        data = []
        for r in recipients:
            data.append({
                "card_id": card_id,
                "font_id": font_id,
                "message": _personalize(message, r),
                "recipient": r,
                "sender": sender,
            })
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(click.style("\n  DRY RUN — nothing will be sent\n", fg="yellow", bold=True))
    for i, r in enumerate(recipients, 1):
        name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
        city_state = f"{r.get('city', '')}, {r.get('state', '')} {r.get('zip', '')}"
        personalized = _personalize(message, r)

        click.echo(f"  {click.style(f'[{i}]', bold=True)} {name}")
        click.echo(f"      {r.get('street1', '')}")
        if r.get("street2"):
            click.echo(f"      {r['street2']}")
        click.echo(f"      {city_state}")
        click.echo(f"      Message: {click.style(personalized[:80], dim=True)}")
        if len(personalized) > 80:
            click.echo(f"               {click.style('...', dim=True)}")
        click.echo()
