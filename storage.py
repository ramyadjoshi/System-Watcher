import csv
import os
from datetime import datetime  # for timestamps

# os.path.dirname(__file__) gives the folder this script lives in
# os.path.join builds a proper Windows path automatically
CSV_FILE = os.path.join(os.path.dirname(__file__), 'metrics.csv')
ANOMALY_FILE = os.path.join(os.path.dirname(__file__), 'anomalies.csv')

# column headers for metrics CSV
HEADERS = ['timestamp', 'cpu', 'ram_percent', 'ram_used_mb', 'disk_percent', 'disk_free_gb']

# column headers for anomalies CSV — different structure, different file
ANOMALY_HEADERS = ['timestamp', 'severity', 'metric', 'value', 'message']

def init_csv():
    # creates metrics CSV with headers only if it doesn't exist yet
    # if it exists, leaves it alone — never overwrites old data
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
        print(f"[INFO] Created new metrics file: {CSV_FILE}")
    else:
        print(f"[INFO] Appending to existing metrics file: {CSV_FILE}")


def save_snapshot(cpu, ram, disk):
    # appends one new row to metrics CSV
    # 'a' mode = append, never overwrites
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow({
            'timestamp'   : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu'         : cpu,
            'ram_percent' : ram.percent,
            'ram_used_mb' : ram.used // (1024**2),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free // (1024**3)
        })
    print("[INFO] Snapshot saved to metrics CSV")


def init_anomaly_csv():
    # creates anomaly CSV with headers only if it doesn't exist yet
    if not os.path.exists(ANOMALY_FILE):
        with open(ANOMALY_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ANOMALY_HEADERS)
            writer.writeheader()
        print(f"[INFO] Created new anomaly file: {ANOMALY_FILE}")
    else:
        print(f"[INFO] Appending to existing anomaly file: {ANOMALY_FILE}")


def save_anomaly(severity, metric, value, message):
    # saves one anomaly row — only called when something is actually wrong
    with open(ANOMALY_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ANOMALY_HEADERS)
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'severity' : severity,
            'metric'   : metric,
            'value'    : value,
            'message'  : message
        })
    print(f"[INFO] Anomaly saved — {severity} on {metric}")