# config.py

# your Telegram bot token
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Telegram user ID (integer) of the one admin allowed to rotate providers
BOT_OWNER_ID = 123456789

# list of URL‐shortener providers; you can add or remove entries here.
# Each provider must declare:
#   - name: arbitrary label
#   - type: one of "tinyurl" or "cuttly" (we implement those two)
#   - api_endpoint: full URL of the shortening endpoint
#   - api_key: (optional) your key for cuttly
SHORTENERS = [
    {
        "name": "TinyURL",
        "type": "tinyurl",
        "api_endpoint": "http://tinyurl.com/api-create.php",
    },
    {
        "name": "Cuttly",
        "type": "cuttly",
        "api_endpoint": "https://cutt.ly/api/api.php",
        "api_key": "YOUR_CUTTLY_API_KEY_HERE",
    },
]
