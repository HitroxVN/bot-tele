import os
import random
import string
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz
import threading

# Flask app setup
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render!"

# Telegram bot functions
def generate_random_email():
    """Generate a random email address."""
    domain = "gmail.com"
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{username}@{domain}"

def register_and_login():
    """Register and login to fast4g.vn, returning the subscription link or an error message."""
    # Register
    register_url = "https://fast4g.vn/api/v1/passport/auth/register"
    email = generate_random_email()
    password = email
    payload = {
        "email": email,
        "password": password,
        "password_confirmation": password,
        "agree_terms": True
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        register_response = requests.post(register_url, json=payload, headers=headers)
        if register_response.status_code == 200:
            login_url = "https://fast4g.vn/api/v1/passport/auth/login"
            login_payload = {"email": email, "password": password}
            login_response = requests.post(login_url, json=login_payload, headers=headers)
            if login_response.status_code == 200:
                login_data = login_response.json()
                if "data" in login_data:
                    token = login_data['data']['token']
                    subscription_link = f"https://fast4g.vn/api/v1/client/subscribe?token={token}"
                    return subscription_link
        return "Hãy thử lại sau!"
    except Exception as e:
        return "Hãy thử lại sau!"

async def send_subscription_link(context: ContextTypes.DEFAULT_TYPE):
    """Send a new subscription link to the user."""
    chat_id = context.job.data
    link = register_and_login()
    await context.bot.send_message(chat_id=chat_id, text=link)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    chat_id = update.effective_chat.id
    link = register_and_login()
    await update.message.reply_text(link)

    # Schedule daily job at 00:00 (UTC+7)
    timezone = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(timezone)
    next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delay = (next_run - now).total_seconds()
    context.job_queue.run_repeating(send_subscription_link, interval=86400, first=delay, data=chat_id)

async def create_new_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /taolink command."""
    chat_id = update.effective_chat.id
    link = register_and_login()
    message = f"Link data 4G VPN của bạn:\n{link}"
    await update.message.reply_text(message)

def run_bot():
    """Run the Telegram bot."""
    token = "7826087010:AAFLg7oBWQenOgIlFbCbtYKKZs-QH_B663I"
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("taolink", create_new_link))

    application.run_polling()

if __name__ == "__main__":
    # Run Flask in a separate thread
    port = int(os.environ.get("PORT", 443))  # Lấy cổng từ biến môi trường
    threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": port, "use_reloader": False}).start()

    # Run the Telegram bot
    run_bot()
