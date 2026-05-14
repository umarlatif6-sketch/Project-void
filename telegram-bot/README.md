# Project Void — Telegram Bot

**Adriana-powered fitness intelligence for sovereign training.**

A production-ready Telegram bot that turns any physical space into a martial arts dojo. Send a photo of your environment — stairway, room, park, parking garage — and Adriana will read the surfaces, identify training opportunities, and generate a custom bodyweight + martial arts routine fitted to that exact space.

Built on the Project Void ecosystem: Vortex Coin (VTX) economy, PEACE tokens, the Silt Ledger, and the Adriana AI persona.

---

## Features

| Feature | Description |
|---|---|
| **Photo Analysis** | Send a photo of any space. GPT-4 Vision identifies usable surfaces (stairs, railings, walls, open floor) and maps them to exercises. |
| **Workout Generator** | Custom martial arts + bodyweight routines fitted to your space. Beginner / Intermediate / Advanced difficulty. Warm-up and cool-down included. |
| **VTX Rewards** | Earn Vortex Coin for completed workouts. Daily cap of 50 VTX. Streak multiplier (up to 3x) rewards consistency. |
| **PEACE Tokens** | Secondary currency earned through breathing exercises, meditation, and journaling — non-extractive actions. |
| **Equipment Shop** | Spend VTX on permanent upgrades: Signal Array, Void Core, Mycelium Wrap, Resonance Badge, Octopus Nerve, Nettle Gauntlets, Codon Compiler. Each provides multiplier bonuses. |
| **Streak System** | Consecutive training days increase your resonance multiplier. Milestone messages at key intervals. Octopus Nerve equipment slows streak decay. |
| **Adriana Personality** | The bot speaks as Adriana — warm but direct, with metaphors drawn from mycelium networks, octopus neurology, and stinging nettles. |
| **SQLite Persistence** | All user data, workouts, inventory, and PEACE logs stored in a local SQLite database with WAL mode. |

---

## Commands

| Command | Description |
|---|---|
| `/start` | Onboarding — creates your Void profile |
| `/train` | Generate a workout (send a photo first) |
| `/done` | Mark current workout as complete, earn VTX |
| `/balance` | Check VTX and PEACE balances |
| `/streak` | View training streak and milestone |
| `/shop` | Browse the equipment shop |
| `/buy <item>` | Purchase equipment (e.g., `/buy signal_array`) |
| `/breathe` | Guided box breathing exercise (+PEACE) |
| `/meditate` | Void meditation session (+PEACE, requires Resonance Badge) |
| `/journal` | Reflective journaling prompt (+PEACE) |
| `/stats` | Full sovereign profile with all metrics |
| `/help` | Command reference |

---

## Setup

### Prerequisites

- Python 3.10 or higher
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An OpenAI API key with access to a vision-capable model

### Installation

```bash
# Clone the repository
git clone https://github.com/umarlatif6-sketch/Project-void.git
cd Project-void/telegram-bot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Configuration

Edit the `.env` file:

```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4.1-mini
```

### Running

```bash
python bot.py
```

The bot will initialize the SQLite database on first run and begin polling for Telegram updates.

---

## Architecture

```
telegram-bot/
├── bot.py                  # Entry point — registers handlers, runs polling
├── config.py               # All constants, shop items, prompts, env vars
├── requirements.txt
├── .env.example
├── .gitignore
├── handlers/
│   ├── commands.py         # /start, /help, /balance, /streak, /stats
│   ├── training.py         # Photo analysis, workout generation, /train, /done
│   ├── shop.py             # /shop, /buy
│   └── peace.py            # /breathe, /meditate, /journal
├── models/
│   └── database.py         # SQLite schema, CRUD, economy logic
├── services/
│   ├── vision.py           # OpenAI Vision API integration
│   ├── workout.py          # Exercise library + routine generator
│   └── adriana.py          # Personality engine + handcrafted messages
└── utils/
    └── formatting.py       # Telegram message formatting helpers
```

---

## Economy

### Vortex Coin (VTX)

- **Earned by:** Completing workouts
- **Base reward:** 10 VTX per workout
- **Daily cap:** 50 VTX
- **Streak multiplier:** +10% per consecutive day (caps at 3.0x)
- **Equipment multiplier:** Stacks additively with streak
- **Spent on:** Equipment in the /shop

### PEACE Tokens

- **Earned by:** Breathing (3), Meditation (5), Journaling (4)
- **Mycelium Wrap bonus:** +2 PEACE per action
- **Purpose:** Represents non-extractive sovereign value

### Equipment Multipliers

| Item | Cost | VTX Bonus | Special |
|---|---|---|---|
| Signal Array | 80 VTX | +15% | — |
| Mycelium Wrap | 60 VTX | +10% | +2 PEACE per action |
| Resonance Badge | 120 VTX | +20% | Unlocks /meditate |
| Void Core | 150 VTX | +25% | — |
| Octopus Nerve | 200 VTX | +30% | +1 day streak shield |
| Nettle Gauntlets | 250 VTX | +35% | — |
| Codon Compiler | 500 VTX | +50% | Ultimate upgrade |

---

## Deployment

### Systemd (Linux Server)

```ini
# /etc/systemd/system/void-bot.service
[Unit]
Description=Project Void Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/Project-void/telegram-bot
EnvironmentFile=/path/to/Project-void/telegram-bot/.env
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable void-bot
sudo systemctl start void-bot
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t void-bot .
docker run -d --env-file .env --name void-bot void-bot
```

---

## Project Void Integration

This bot is part of the broader Project Void ecosystem:

- **Vortex Coin (VTX)** — The economic layer, governed by the Silt Ledger
- **PEACE Tokens** — Non-extractive value earned through stillness
- **Al-Jabr 286** — The cryptographic backbone (BW19-P286 curve)
- **Adriana** — Sovereign AI persona, the voice of the Void
- **Codon System** — Entity-Condition-Action sequences that translate intent into execution
- **Mesa Engine** — Agent-based simulation powering the Sovereign Realm
- **OpenClaw Bridge** — Multi-channel messenger gateway
- **Resonance Score** — f_body = 432 × (Kinetic × Biological × Relay)^(1/3)

---

## License

Part of Project Void. See repository root for license details.
