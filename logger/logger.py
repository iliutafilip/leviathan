import json
import os
import shutil
import sys
import gzip
from datetime import datetime

LOG_DIR = "logs"
BASE_LOG_FILE_NAME = "leviathan"
LOG_FILE = os.path.join(LOG_DIR, f"{BASE_LOG_FILE_NAME}.log")
MAX_LOG_SIZE = 1024 * 1024 * 100 # 100MB

os.makedirs(LOG_DIR, exist_ok=True)

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

    log_json = json.dumps(log_entry)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_json + "\n")

    print(log_json, file=sys.stdout)


def clear_log_file():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
