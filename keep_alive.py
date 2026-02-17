import asyncio
import threading
from flask import Flask

app = Flask(__name__)

PING_INTERVAL = 300


@app.route("/")
def index():
    return "VOID ENGINE — Active", 200


@app.route("/ping")
def ping():
    return "pong", 200


async def _pulse_loop():
    import urllib.request
    import urllib.error

    await asyncio.sleep(10)
    while True:
        try:
            urllib.request.urlopen("http://0.0.0.0:8099/ping", timeout=5)
        except (urllib.error.URLError, OSError):
            pass
        await asyncio.sleep(PING_INTERVAL)


def _run_flask():
    app.run(host="0.0.0.0", port=8099, use_reloader=False)


def start_pulse():
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    loop = asyncio.new_event_loop()
    pulse_thread = threading.Thread(
        target=loop.run_until_complete,
        args=(_pulse_loop(),),
        daemon=True,
    )
    pulse_thread.start()

    print("  [VOID] Stealth Pulse active on port 8099 (ping every 5 min)")
    return flask_thread, pulse_thread
