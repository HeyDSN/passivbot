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
        logging.info(f"Telegram notifications disabled, not sending: {message}")
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
        logging.info(f"Preparing to send Telegram notification: {cleaned_message}")

        if account.startswith("cpt_"):
            logging.info(f"Sending to channel: {GROUP_CHAT_ID}")
            send_channel(cleaned_message)
        else:
            logging.info(f"Sending to private: {PRIVATE_CHAT_ID}")
            send_private(cleaned_message)

    except Exception as e:
        # Log the exception
        logging.error(f"Error sending Telegram notification: {e}")
        # Only try to send error message if Telegram is enabled
        try:
            if TELEGRAM_ENABLED:
                send_private(
                    f"{ex_logo} {exchange.capitalize()} Exception new notification, message {e}"
                )
        except Exception as inner_e:
            # Log the inner exception
            logging.error(f"Error sending Telegram error notification: {inner_e}")


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
        try:
            # Get the next message from the queue
            message_type, message = message_queue.get()

            # Determine the appropriate chat ID
            chat_id = GROUP_CHAT_ID if message_type == "channel" else PRIVATE_CHAT_ID
            logging.info(f"Worker processing message type: {message_type}, chat_id: {chat_id}")

            # Send the message
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"parse_mode": "HTML", "chat_id": chat_id, "text": message}
            logging.info(f"Sending request to Telegram API: {url}")
            response = requests.post(url, data=data)
            
            # Log the response
            if response.status_code == 200:
                logging.info(f"Telegram API response success: {response.status_code}")
            else:
                logging.error(f"Telegram API error: {response.status_code}, {response.text}")

            # Mark the message as done in the queue
            message_queue.task_done()
        except Exception as e:
            logging.error(f"Error in send_message_worker: {e}")
            # Continue the loop even if there's an error
            continue


# Start the message sending thread only if Telegram is enabled
if TELEGRAM_ENABLED and message_queue is not None:
    sending_thread = threading.Thread(target=send_message_worker, daemon=True)
    sending_thread.start()
