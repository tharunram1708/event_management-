import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_ticket_email(email: str, ticket_number: str) -> None:
    settings = get_settings()
    logger.info(
        "Email notification queued from %s to %s for ticket %s",
        settings.email_from,
        email,
        ticket_number,
    )
