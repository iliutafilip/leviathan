import json
import os
import shutil
import sys
import gzip
from datetime import datetime
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

LOG_DIR = "logs"
BASE_LOG_FILE_NAME = "leviathan"
LOG_FILE = os.path.join(LOG_DIR, f"{BASE_LOG_FILE_NAME}.log")
MAX_LOG_SIZE = 1024 * 1024 * 100 # 100MB

os.makedirs(LOG_DIR, exist_ok=True)

load_dotenv()

ELK_ENABLED = os.getenv("ELK_ENABLED", "false").lower() == "true"
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
INDEX_NAME = "leviathan-logs"

es = None
if ELK_ENABLED:
    try:
        es = Elasticsearch(ES_HOST)
    except Exception as e:
        print(f"[LOGGER] Elasticsearch connection failed: {e}")
        ELK_ENABLED = False

def rotate_log():
    """
    Rotates and compresses the existing log file when it exceeds the size limit.
    """
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_log_name = os.path.join(LOG_DIR, f"{BASE_LOG_FILE_NAME}_{timestamp}.log")

        shutil.move(LOG_FILE, new_log_name)

        with open(new_log_name, "rb") as f_in, gzip.open(f"{new_log_name}.gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        os.remove(new_log_name)

        print(f"[LOGGER] Rotated and compressed log to: {new_log_name}.gz")


def log_event(event_id: str,
              session_id: str,
              src_ip: str = None,
              src_port: int = None,
              dst_ip: str = None,
              dst_port: int = None,
              protocol: str = None,
              username: str = None,
              password: str = None,
              command: str = None,
              message: str = None,
              response: str = None,
              ) -> None:
    """
    Logs an event in JSON format.

    :param event_id: event type ("session_start", "login_attempt", ...)
    :param session_id: session ID
    :param src_ip: source IP address
    :param src_port: source port
    :param dst_ip: destination IP address
    :param dst_port: destination port
    :param protocol: used protocol
    :param username: username used for logging in
    :param password: password used for logging in
    :param command: input command
    :param message: message
    :param response: LLM response
    """

    rotate_log()

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_id,
        "session_id": session_id,
        "src_ip": src_ip
    }

    if src_port is not None:
        log_entry["src_port"] = src_port
    if dst_ip is not None:
        log_entry["dst_ip"] = dst_ip
    if dst_port is not None:
        log_entry["dst_port"] = dst_port
    if protocol is not None:
        log_entry["protocol"] = protocol
    if username is not None:
        log_entry["username"] = username
    if password is not None:
        log_entry["password"] = password
    if command is not None:
        log_entry["command"] = command
    if message is not None:
        log_entry["message"] = message
    if response is not None:
        log_entry["response"] = response

    log_json = json.dumps(log_entry)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_json + "\n")

    print(log_json, file=sys.stdout)

    send_to_elasticsearch(log_entry)


def send_to_elasticsearch(log_entry: dict):
    if not ELK_ENABLED or es is None:
        return
    try:
        print(f"[LOGGER] Sending to Elasticsearch: {log_entry}")
        es.index(index=INDEX_NAME, document=log_entry)
    except Exception as e:
        print(f"[LOGGER] Failed to send log to Elasticsearch: {e}")


def clear_log_file():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
