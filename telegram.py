import json
import re
import requests
import threading
from queue import Queue

# Load configuration from config.json
with open("telegram.json", "r") as f:
    config = json.load(f)

# Retrieve Telegram configuration values
TOKEN = config["telegram"]["token"]
GROUP_CHAT_ID = config["telegram"]["group_chat_id"]
PRIVATE_CHAT_ID = config["telegram"]["private_chat_id"]

# Create a thread-safe queue
message_queue = Queue()


def send_notification(exchange, account, message, filter = True):
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

        cleaned_message = f"{ex_logo} {exchange.capitalize()} {cleaned_text}"

        if account.startswith("cpt_"):
            send_channel(cleaned_message)
        else:
            send_private(cleaned_message)

    except Exception as e:
        send_private(
            f"{ex_logo} {exchange.capitalize()} Exception new notification, message {e}"
        )


def remove_extra_spaces(text):
    return re.sub(r"\s+", " ", text)


def send_channel(message):
    # Put the message into the queue
    message_queue.put(("channel", message))


def send_private(error_message):
    # Put the message into the queue
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


# Start the message sending thread
sending_thread = threading.Thread(target=send_message_worker, daemon=True)
sending_thread.start()
