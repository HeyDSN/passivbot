import json
import re
import requests
import threading
import os
from queue import Queue
import logging

# Initialize configuration variables with default values
TOKEN = None
GROUP_CHAT_ID = None
PRIVATE_CHAT_ID = None
message_queue = None
TELEGRAM_ENABLED = False

# Try to load configuration from telegram.json
try:
    if os.path.exists("telegram.json"):
        with open("telegram.json", "r") as f:
            config = json.load(f)

        # Retrieve Telegram configuration values
        TOKEN = config.get("telegram", {}).get("token")
        GROUP_CHAT_ID = config.get("telegram", {}).get("group_chat_id")
        PRIVATE_CHAT_ID = config.get("telegram", {}).get("private_chat_id")
        
        # Only enable telegram if all required values are present
        if TOKEN and (GROUP_CHAT_ID or PRIVATE_CHAT_ID):
            # Create a thread-safe queue
            message_queue = Queue()
            TELEGRAM_ENABLED = True
            logging.info("Telegram notifications enabled")
        else:
            logging.info("Telegram configuration incomplete, notifications disabled")
    else:
        logging.info("No telegram.json found, notifications disabled")
except Exception as e:
    logging.info(f"Error loading Telegram configuration: {e}, notifications disabled")


def send_notification(exchange, account, message, filter = True):
    # Do nothing if Telegram is not enabled
    if not TELEGRAM_ENABLED:
        return
    
    try:
        if exchange == "binance":
            ex_logo = "🟡"
        elif exchange == "bybit":
            ex_logo = "🟠"
        else:
            ex_logo = "🔰"

        if filter:
            cleaned_text = remove_extra_spaces(message)
        else:
            cleaned_text = message

        cleaned_message = f"{ex_logo} {exchange.capitalize()}: {cleaned_text}"

        if account.startswith("cpt_"):
            send_channel(cleaned_message)
        else:
            send_private(cleaned_message)

    except Exception as e:
        # Only try to send error message if Telegram is enabled
        try:
            if TELEGRAM_ENABLED:
                send_private(
                    f"{ex_logo} {exchange.capitalize()} Exception new notification, message {e}"
                )
        except:
            # Silently fail if even the error notification fails
            pass


def remove_extra_spaces(text):
    return re.sub(r"\s+", " ", text)


def send_channel(message):
    # Put the message into the queue if enabled
    if TELEGRAM_ENABLED and message_queue is not None:
        message_queue.put(("channel", message))


def send_private(error_message):
    # Put the message into the queue if enabled
    if TELEGRAM_ENABLED and message_queue is not None:
        message_queue.put(("private", error_message))


def send_message_worker():
    while True:
        # Get the next message from the queue
        message_type, message = message_queue.get()

        # Determine the appropriate chat ID
        chat_id = GROUP_CHAT_ID if message_type == "channel" else PRIVATE_CHAT_ID

        # Send the message
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"parse_mode": "HTML", "chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)

        # Mark the message as done in the queue
        message_queue.task_done()


# Start the message sending thread only if Telegram is enabled
if TELEGRAM_ENABLED and message_queue is not None:
    sending_thread = threading.Thread(target=send_message_worker, daemon=True)
    sending_thread.start()
