import base64
import io
import secrets

import qrcode


def generate_ticket_number() -> str:
    return f"EVT-{secrets.token_hex(6).upper()}"


def make_qr_code_base64(ticket_number: str) -> str:
    image = qrcode.make(ticket_number)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
