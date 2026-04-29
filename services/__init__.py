"""
services/ — Application service layer.

This package holds business logic that sits between the route handlers
(HTTP boundary) and the repositories (data-access boundary).  Each
module is focused on a single responsibility:

    :mod:`services.pin_service`  — PIN code generation and lifecycle.
    :mod:`services.qr_service`   — QR code image generation.
    :mod:`services.run_service`  — Orchestrates the full run/session lifecycle.
"""
