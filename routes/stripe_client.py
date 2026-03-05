import os
import json
import urllib.request
import stripe


def _get_stripe_credentials():
    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME", "")
    repl_id = os.environ.get("REPL_IDENTITY", "")
    web_renewal = os.environ.get("WEB_REPL_RENEWAL", "")

    if repl_id:
        token = "repl " + repl_id
    elif web_renewal:
        token = "depl " + web_renewal
    else:
        raise RuntimeError("Stripe credentials unavailable: no Replit token found")

    is_production = os.environ.get("REPLIT_DEPLOYMENT") == "1"
    env = "production" if is_production else "development"

    url = f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=stripe&environment={env}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "X-Replit-Token": token})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())

    items = data.get("items", [])
    if not items:
        raise RuntimeError("Stripe connection not found in Replit connectors")

    settings = items[0].get("settings", {})
    return settings.get("publishable", ""), settings.get("secret", "")


def get_stripe_client():
    _, secret_key = _get_stripe_credentials()
    stripe.api_key = secret_key
    return stripe


def get_publishable_key():
    pub_key, _ = _get_stripe_credentials()
    return pub_key
