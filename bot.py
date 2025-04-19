# bot.py

import sqlite3
import threading
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import config

DB_PATH = "bot_data.db"
_LOCK = threading.Lock()


def init_db():
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # state table holds simple key/value pairs
        c.execute("""
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # links table stores each original→shortened mapping
        c.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_url TEXT,
                short_url TEXT
            )
        """)
        # ensure we have a current_index entry
        c.execute("INSERT OR IGNORE INTO state(key, value) VALUES(?, ?)",
                  ("current_index", "0"))
        conn.commit()


def get_current_index() -> int:
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM state WHERE key = ?", ("current_index",))
        row = c.fetchone()
        return int(row[0])


def set_current_index(idx: int):
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE state SET value = ? WHERE key = ?", (str(idx), "current_index"))
        conn.commit()


def rotate_provider():
    """Advance to the next shortener in config.SHORTENERS."""
    idx = get_current_index()
    idx = (idx + 1) % len(config.SHORTENERS)
    set_current_index(idx)
    return idx


def call_shortener(provider: dict, url: str) -> str:
    """Invoke a single provider; return shortened URL or raise."""
    if provider["type"] == "tinyurl":
        r = requests.get(provider["api_endpoint"], params={"url": url}, timeout=10)
        r.raise_for_status()
        return r.text.strip()
    elif provider["type"] == "cuttly":
        params = {
            "key": provider["api_key"],
            "short": url
        }
        r = requests.get(provider["api_endpoint"], params=params, timeout=10)
        data = r.json()
        info = data.get("url")
        if info and info.get("status") == 7:
            return info["shortLink"]
        raise RuntimeError(f"Cuttly error status {info.get('status')}")
    else:
        raise RuntimeError("Unsupported provider type")


def shorten_with_rotation(url: str) -> (str, dict):
    """Try shortening with current provider; on failure, rotate once and retry."""
    tried = 0
    n = len(config.SHORTENERS)
    while tried < n:
        idx = get_current_index()
        provider = config.SHORTENERS[idx]
        try:
            short = call_shortener(provider, url)
            return short, provider
        except Exception:
            # provider failed: rotate and try next
            rotate_provider()
            tried += 1
    raise RuntimeError("All shorteners failed")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me any URL with /shorten to get a short link.\n"
        "Example: /shorten https://example.com/page\n\n"
        "Owner can also run /rotate to switch providers and re-generate all old links."
    )


async def shorten(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.message.reply_text("❗️ Usage: /shorten <URL>")
    url = ctx.args[0]
    try:
        short, used = shorten_with_rotation(url)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ Could not shorten: {e}")

    # store in DB
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO links(user_id, original_url, short_url) VALUES(?,?,?)",
            (update.effective_user.id, url, short),
        )
        conn.commit()

    await update.message.reply_text(
        f"✅ Shortened via {used['name']}:\n{short}"
    )


async def rotate_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if user != config.BOT_OWNER_ID:
        return await update.message.reply_text("❌ You are not authorized.")
    new_idx = rotate_provider()
    provider = config.SHORTENERS[new_idx]

    # re-generate all links
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, original_url FROM links")
    rows = c.fetchall()
    updated = 0
    for link_id, orig in rows:
        try:
            short = call_shortener(provider, orig)
            c.execute("UPDATE links SET short_url = ? WHERE id = ?", (short, link_id))
            updated += 1
        except:
            pass
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🔄 Rotated to provider #{new_idx + 1} ({provider['name']}).\n"
        f"Re-shortened {updated} links."
    )


def main():
    init_db()
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shorten", shorten))
    app.add_handler(CommandHandler("rotate", rotate_all))

    app.run_polling()


if __name__ == "__main__":
    main()
