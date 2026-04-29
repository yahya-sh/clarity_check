"""
services/qr_service.py — QR code image generation.

Converts a URL into a base64-encoded PNG data-URI suitable for embedding
directly in an HTML ``<img src="...">`` attribute.

No Flask or HTTP code lives here; the function is a pure transformation
from a URL string to a data-URI string.
"""
import io
import base64

import qrcode


def generate_qr_code(url: str) -> str:
    """
    Generate a QR code image for *url* and return it as a data-URI.

    The returned string has the form::

        data:image/png;base64,<base64-encoded PNG>

    and can be used directly as the ``src`` attribute of an ``<img>`` tag.

    Args:
        url: The URL to encode in the QR code.

    Returns:
        A ``data:image/png;base64,…`` string.
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_b64}"
