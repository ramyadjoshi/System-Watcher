# def get_advice(current_state, process_list):
#     # advice is a list of strings — one string per suggestion
#     # we append to it based on what's wrong, then return it
#     advice = []

#     # ── RAM ADVICE ────────────────────────────────────────────────────────────

#     if current_state['ram'] in ('CRITICAL', 'WARNING'):
#         # process_list is already sorted highest RAM first
#         # so index 0 is always the biggest offender
#         top_process = process_list[0]['name']
#         top_ram     = process_list[0]['ram_mb']

#         if top_process == 'chrome.exe':
#             advice.append(
#                 f"Chrome is consuming {top_ram}MB — your biggest RAM offender. "
#                 "Close unused tabs, or restart Chrome completely to free memory."
#             )
#         elif top_process == 'Code.exe':
#             advice.append(
#                 f"VS Code is consuming {top_ram}MB across multiple processes. "
#                 "Close unused editor windows and disable heavy extensions."
#             )
#         elif top_process == 'MsMpEng.exe':
#             advice.append(
#                 f"Windows Defender is consuming {top_ram}MB — it is actively scanning. "
#                 "This is temporary and should settle. "
#                 "If persistent, add your project folder to exclusions."
#             )
#         else:
#             advice.append(
#                 f"{top_process} is consuming {top_ram}MB — the highest RAM process. "
#                 "Consider restarting it if it is not essential right now."
#             )

#         # general RAM advice regardless of which process is top
#         if current_state['ram'] == 'CRITICAL':
#             advice.append(
#                 "RAM is in CRITICAL state. "
#                 "Close any applications you are not actively using immediately."
#             )
#         elif current_state['ram'] == 'WARNING':
#             advice.append(
#                 "RAM is running high. "
#                 "Monitor closely — if it keeps climbing, restart heavy applications."
#             )

#     # ── CPU ADVICE ────────────────────────────────────────────────────────────

#     if current_state['cpu'] == 'CRITICAL':
#         advice.append(
#             "CPU is under critical load. "
#             "Check Task Manager for runaway processes and close what you can."
#         )
#     elif current_state['cpu'] == 'WARNING':
#         advice.append(
#             "CPU is getting high. "
#             "Avoid opening new heavy applications until it settles."
#         )

#     # ── DISK ADVICE ───────────────────────────────────────────────────────────

#     if current_state['disk'] == 'CRITICAL':
#         advice.append(
#             "Disk is almost full. "
#             "Run Disk Cleanup immediately and delete files you no longer need."
#         )
#     elif current_state['disk'] == 'WARNING':
#         advice.append(
#             "Disk is getting full. "
#             "Consider cleaning up downloads, temp files, or uninstalling unused programs."
#         )

#     # ── ALL OK ────────────────────────────────────────────────────────────────

#     # if nothing was added to advice, everything is fine
#     if not advice:
#         advice.append("System looks healthy. No action needed right now.")

#     return advice
# --------------------------------------------------------------------------------------
import csv
import os
from software_detector import run_software_detection

METRICS_FILE = os.path.join(os.path.dirname(__file__), 'metrics.csv')


def load_recent_metrics(n=10):
    rows = []
    if not os.path.exists(METRICS_FILE):
        return rows
    with open(METRICS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows[-n:]


def detect_ram_trend(rows):
    if len(rows) < 3:
        return 'stable'
    values      = [float(r['ram_percent']) for r in rows]
    mid         = len(values) // 2
    first_half  = sum(values[:mid]) / mid
    second_half = sum(values[mid:]) / (len(values) - mid)
    diff = second_half - first_half
    if diff > 2.0:   return 'climbing'
    if diff < -2.0:  return 'falling'
    return 'stable'


def detect_sustained_high(rows, threshold=85, consecutive=5):
    if len(rows) < consecutive:
        return False
    return all(float(r['ram_percent']) > threshold for r in rows[-consecutive:])


def detect_ram_spike(rows):
    if len(rows) < 2:
        return False
    values = [float(r['ram_percent']) for r in rows]
    for i in range(1, len(values)):
        if values[i] - values[i-1] > 5.0:
            return True
    return False


def detect_cpu_trend(rows):
    if len(rows) < 3:
        return 'stable'
    values      = [float(r['cpu']) for r in rows]
    mid         = len(values) // 2
    first_half  = sum(values[:mid]) / mid
    second_half = sum(values[mid:]) / (len(values) - mid)
    diff = second_half - first_half
    if diff > 5.0:   return 'climbing'
    if diff < -5.0:  return 'falling'
    return 'stable'


def detect_disk_growing(rows):
    if len(rows) < 2:
        return False
    return float(rows[-1]['disk_percent']) > float(rows[0]['disk_percent'])


def get_advice(current_state, process_list):
    advice   = []
    recent   = load_recent_metrics(n=10)

    # ── HARDWARE — RAM ────────────────────────────────────────────────────────
    if current_state['ram'] in ('CRITICAL', 'WARNING'):
        ram_trend = detect_ram_trend(recent)
        sustained = detect_sustained_high(recent)
        spike     = detect_ram_spike(recent)

        if ram_trend == 'climbing':
            advice.append({
                'type' : 'HARDWARE',
                'level': current_state['ram'],
                'msg'  : f"RAM has been climbing steadily over the last {len(recent)} readings. "
                         "This is a sustained increase, not a spike. "
                         "A process may be leaking memory gradually."
            })
        elif ram_trend == 'falling':
            advice.append({
                'type' : 'HARDWARE',
                'level': 'OK',
                'msg'  : "RAM was high but is now falling. Pressure is easing."
            })
        elif sustained:
            advice.append({
                'type' : 'HARDWARE',
                'level': current_state['ram'],
                'msg'  : f"RAM has been above 85% for {len(recent)} consecutive readings. "
                         "Your system is under sustained memory pressure."
            })

        if spike:
            advice.append({
                'type' : 'HARDWARE',
                'level': 'WARNING',
                'msg'  : "A sudden RAM spike was detected. Something consumed large memory quickly. "
                         "Check which application was recently opened."
            })

        if process_list:
            top = process_list[0]
            advice.append({
                'type' : 'HARDWARE',
                'level': current_state['ram'],
                'msg'  : f"Highest RAM consumer: {top['name']} at {top['ram_mb']}MB "
                         f"(PID {top['pid']}). Closing it will free the most memory."
            })

        if current_state['ram'] == 'CRITICAL':
            advice.append({
                'type' : 'HARDWARE',
                'level': 'CRITICAL',
                'msg'  : "RAM is CRITICAL. System may become unresponsive. Close applications immediately."
            })

    # ── HARDWARE — CPU ────────────────────────────────────────────────────────
    if current_state['cpu'] in ('CRITICAL', 'WARNING'):
        cpu_trend = detect_cpu_trend(recent)
        if cpu_trend == 'climbing':
            advice.append({
                'type' : 'HARDWARE',
                'level': current_state['cpu'],
                'msg'  : "CPU usage has been climbing. A background process may be ramping up."
            })
        elif current_state['cpu'] == 'CRITICAL':
            advice.append({
                'type' : 'HARDWARE',
                'level': 'CRITICAL',
                'msg'  : "CPU is under critical load. Find the highest CPU process and close it."
            })
        else:
            advice.append({
                'type' : 'HARDWARE',
                'level': 'WARNING',
                'msg'  : "CPU is elevated. Avoid opening new heavy applications."
            })

    # ── HARDWARE — DISK ───────────────────────────────────────────────────────
    if current_state['disk'] in ('CRITICAL', 'WARNING'):
        growing = detect_disk_growing(recent)
        if current_state['disk'] == 'CRITICAL':
            advice.append({
                'type' : 'HARDWARE',
                'level': 'CRITICAL',
                'msg'  : "Disk is almost full. Run Disk Cleanup immediately."
            })
        elif growing:
            advice.append({
                'type' : 'HARDWARE',
                'level': 'WARNING',
                'msg'  : f"Disk usage is growing. Something is writing to disk. "
                         "Check downloads folder and temp files."
            })
        else:
            advice.append({
                'type' : 'HARDWARE',
                'level': 'WARNING',
                'msg'  : "Disk usage is in WARNING range but stable. Clean up when convenient."
            })

    # ── SOFTWARE BUG DETECTION ────────────────────────────────────────────────
    # software_findings = run_software_detection()
    # for finding in software_findings:
    #     advice.append({
    #         'type' : 'SOFTWARE',
    #         'level': finding['level'],
    #         'msg'  : f"{finding['title']} — {finding['detail']}"
    #     })
    # ── SOFTWARE BUG DETECTION ── use cached results for speed
    # imported here to avoid circular imports
    from app import get_cached_software_findings
    software_findings = get_cached_software_findings()
    for finding in software_findings:
        advice.append({
            'type' : finding['type'],
            'level': finding['level'],
            'msg'  : f"{finding['title']} — {finding['detail']}"
        })

    # ── ALL OK ────────────────────────────────────────────────────────────────
    if not advice:
        ram_trend = detect_ram_trend(recent) if recent else 'stable'
        if ram_trend == 'climbing':
            advice.append({
                'type' : 'HARDWARE',
                'level': 'OK',
                'msg'  : "System looks OK but RAM has been quietly climbing. Keep an eye on it."
            })
        else:
            advice.append({
                'type' : 'HARDWARE',
                'level': 'OK',
                'msg'  : "System is healthy. All metrics within normal range."
            })

    return advice