# config.py

# your Telegram bot token
BOT_TOKEN = "8016813542:AAEsZiP5WAiwU00X2MxpPV4oxt8fqIiiQ7M"

# Telegram user ID (integer) of the one admin allowed to rotate providers
BOT_OWNER_ID = 23810894

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
        "name": "Cuty",
        "type": "cuty",
        "api_endpoint": "https://api.cuty.io/full",
        "api_key": "d4c29e41cfee332e563a5904d",
    },
]
