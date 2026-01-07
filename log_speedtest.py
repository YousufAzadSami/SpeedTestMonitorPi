import os
import csv
import datetime
import speedtest
import time
import socket
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = BASE_DIR
LOG_FILE = os.path.join(LOG_DIR, "speedtest_log.csv")


def _internet_up(host="8.8.8.8", port=53, timeout=3):
    try:
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        return True
    except Exception:
        return False


def _do_speedtest():
    # Timestamp
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    # Run speedtest
    st = speedtest.Speedtest()
    server = st.get_best_server()
    download_bps = st.download()
    upload_bps = st.upload()
    ping_ms = st.results.ping

    server_name = server.get("host", "")
    server_sponsor = server.get("sponsor", "")
    server_country = server.get("country", "")

    # Convert to Mbps
    download_mbps = download_bps / 1_000_000
    upload_mbps = upload_bps / 1_000_000

    # Prepare row (append an error column, empty on success)
    row = [
        timestamp,
        round(ping_ms, 2),
        round(download_mbps, 2),
        round(upload_mbps, 2),
        server_name,
        server_sponsor,
        server_country,
        "",
    ]

    return row


def run_speedtest(max_attempts=3, initial_backoff=5):
    # Ensure directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Check if file exists (for header)
    file_exists = os.path.isfile(LOG_FILE)

    attempts = 0
    backoff = initial_backoff
    last_exc = None

    while attempts < max_attempts:
        attempts += 1

        if not _internet_up():
            last_exc = Exception("No network connectivity detected")
            print(f"Attempt {attempts}: network not available, retrying in {backoff}s")
            time.sleep(backoff)
            backoff *= 2
            continue

        try:
            row = _do_speedtest()

            # Write CSV
            with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(
                        [
                            "timestamp",
                            "ping_ms",
                            "download_mbps",
                            "upload_mbps",
                            "server_host",
                            "server_sponsor",
                            "server_country",
                            "error",
                        ]
                    )
                    file_exists = True
                writer.writerow(row)

            print("Logged:", row)
            return

        except Exception as e:
            last_exc = e
            print(f"Attempt {attempts}: speedtest failed: {e}\n{traceback.format_exc()}")
            time.sleep(backoff)
            backoff *= 2

    # If we reach here, all attempts failed — write an error row so you still have a record
    error_ts = datetime.datetime.now().isoformat(timespec="seconds")
    error_row = [error_ts, "", "", "", "", "", "", str(last_exc)]
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "ping_ms",
                    "download_mbps",
                    "upload_mbps",
                    "server_host",
                    "server_sponsor",
                    "server_country",
                    "error",
                ]
            )
        writer.writerow(error_row)

    print("Logged error row:", error_row)


if __name__ == "__main__":
    run_speedtest()
