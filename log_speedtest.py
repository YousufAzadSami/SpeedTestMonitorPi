import os
import csv
import datetime
import speedtest
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = BASE_DIR
LOG_FILE = os.path.join(LOG_DIR, "speedtest_log.csv")


def run_speedtest():
    # Timestamp
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    # Run speedtest
    st = speedtest.Speedtest(secure=True)
    st.get_servers()
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

    # Prepare row
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

    # Ensure directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Check if file exists (for header)
    file_exists = os.path.isfile(LOG_FILE)

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
        writer.writerow(row)

    print("Logged:", row)


def log_error(error_msg):
    """Log a failed attempt to the CSV."""
    os.makedirs(LOG_DIR, exist_ok=True)
    file_exists = os.path.isfile(LOG_FILE)
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    error_row = [timestamp, "", "", "", "", "", "", error_msg]

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

    print("Logged error:", error_row)


if __name__ == "__main__":
    max_attempts = 5
    backoff = 10
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            run_speedtest()
            break
        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                print(f"Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed.")
                log_error(last_error)
