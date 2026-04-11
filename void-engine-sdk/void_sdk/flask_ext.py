"""
VOID Flask Extension — init_app pattern
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Attach VoidSDK to a Flask app using the standard init_app pattern.
After init, access the SDK via flask.g.void or current_app.void_sdk.

Usage:
    from flask import Flask
    from void_sdk.flask_ext import VoidFlask

    app = Flask(__name__)
    void = VoidFlask()
    void.init_app(app, license_key="your-key")

    @app.route("/encode", methods=["POST"])
    def encode():
        from flask import request, g
        result = g.void.track(
            entity=f"user:{request.remote_addr}",
            condition="frequency:432hz",
            action="encode",
            codon="voidecho",
            meta={"chars": len(request.json.get("message", ""))}
        )
        # ... rest of your handler
        return {"ok": True, "digest": result["digest"]}
"""

from typing import TYPE_CHECKING

from flask import Flask, g, current_app
from void_sdk.core import VoidSDK

if TYPE_CHECKING:
    from flask import Flask as FlaskType


class VoidFlask:
    """
    Flask extension wrapper for VoidSDK.

    Provides per-request SDK access via flask.g.void.
    The SDK instance is shared at the app level (thread-safe reads;
    the memory layer handles its own connection-per-write safety).
    """

    def __init__(self, app: Flask | None = None, **sdk_kwargs):
        self._sdk: VoidSDK | None = None
        self._kwargs = sdk_kwargs
        if app is not None:
            self.init_app(app, **sdk_kwargs)

    def init_app(self, app: Flask, license_key: str | None = None, **kwargs):
        sdk_kwargs = {**self._kwargs, **kwargs}
        if license_key:
            sdk_kwargs["license_key"] = license_key

        sdk = VoidSDK(**sdk_kwargs)
        app.void_sdk = sdk  # type: ignore[attr-defined]

        @app.before_request
        def _attach_void():
            g.void = current_app.void_sdk  # type: ignore[attr-defined]

        app.extensions = getattr(app, "extensions", {})
        app.extensions["void_sdk"] = sdk

    @property
    def sdk(self) -> VoidSDK:
        return current_app.void_sdk  # type: ignore[attr-defined]
