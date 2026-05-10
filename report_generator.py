"""
report_generator.py
────────────────────
Generates a professional system health report as a plain-text file.
Called only by app.py /api/report route.
Does NOT modify any existing project files.
"""

import psutil
import csv
import os
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────

def _read_csv(filepath, last_n=20):
    rows = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows[-last_n:]


def _status(value, warn_thresh, crit_thresh):
    if value >= crit_thresh:
        return "CRITICAL"
    if value >= warn_thresh:
        return "WARNING"
    return "OK"


def _bar(percent, width=30):
    filled = int(width * percent / 100)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {percent:.1f}%"


def _separator(char="═", width=60):
    return char * width


def _section(title):
    return f"\n{_separator()}\n  {title}\n{_separator()}"


# ── Core report builder ───────────────────────────────────────

def generate_report():
    """
    Collects live metrics + CSV history + anomaly log.
    Returns the full report as a string.
    """
    now        = datetime.now()
    ts_display = now.strftime("%Y-%m-%d %H:%M:%S")
    ts_file    = now.strftime("%Y%m%d_%H%M%S")

    base_dir      = os.path.dirname(os.path.abspath(__file__))
    metrics_file  = os.path.join(base_dir, "metrics.csv")
    anomaly_file  = os.path.join(base_dir, "anomalies.csv")

    # ── Live metrics ──────────────────────────────────────────
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage("C:\\")
    net   = psutil.net_io_counters()

    cpu_status  = _status(cpu,          75, 90)
    ram_status  = _status(ram.percent,  80, 90)
    disk_status = _status(disk.percent, 75, 90)

    # Overall health score — simple weighted average
    score_map  = {"OK": 100, "WARNING": 55, "CRITICAL": 10}
    health_score = int(
        score_map[cpu_status]  * 0.35 +
        score_map[ram_status]  * 0.45 +
        score_map[disk_status] * 0.20
    )
    if health_score >= 85:
        overall = "HEALTHY"
    elif health_score >= 55:
        overall = "DEGRADED"
    else:
        overall = "CRITICAL"

    # ── Top processes ─────────────────────────────────────────
    procs = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            ram_mb = proc.info["memory_info"].rss // (1024 ** 2)
            if ram_mb > 10:
                procs.append({
                    "name":   proc.info["name"],
                    "pid":    proc.info["pid"],
                    "ram_mb": ram_mb,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["ram_mb"], reverse=True)
    top_procs = procs[:10]

    # ── CSV history (last 10 readings) ────────────────────────
    history   = _read_csv(metrics_file, last_n=10)

    # ── Anomaly log (last 15) ─────────────────────────────────
    anomalies = _read_csv(anomaly_file, last_n=15)
    anomalies.reverse()  # newest first

    # ── Trend analysis from history ───────────────────────────
    ram_trend = "N/A"
    if len(history) >= 4:
        vals  = [float(r["ram_percent"]) for r in history]
        mid   = len(vals) // 2
        first = sum(vals[:mid]) / mid
        last_ = sum(vals[mid:]) / (len(vals) - mid)
        diff  = last_ - first
        if diff > 2:
            ram_trend = f"CLIMBING (+{diff:.1f}% over last {len(history)} readings)"
        elif diff < -2:
            ram_trend = f"FALLING ({diff:.1f}% over last {len(history)} readings)"
        else:
            ram_trend = f"STABLE (±{abs(diff):.1f}% over last {len(history)} readings)"

    # ── Count anomaly severity ────────────────────────────────
    crit_count = sum(1 for a in anomalies if a.get("severity") == "CRITICAL")
    warn_count = sum(1 for a in anomalies if a.get("severity") == "WARNING")

    # ── Recommendations ───────────────────────────────────────
    recs = []
    if ram_status == "CRITICAL":
        recs.append("► RAM is CRITICAL. Close unused applications immediately to prevent system hang.")
    elif ram_status == "WARNING":
        recs.append("► RAM is elevated. Monitor closely — restart heavy applications if it keeps climbing.")
    if "CLIMBING" in ram_trend:
        recs.append("► RAM trend is climbing. A process may be leaking memory. Restart suspect applications.")
    if cpu_status in ("WARNING", "CRITICAL"):
        recs.append(f"► CPU is {cpu_status}. Identify the highest-CPU process in Task Manager and close if not needed.")
    if disk_status in ("WARNING", "CRITICAL"):
        recs.append(f"► Disk is {disk_status}. Run Disk Cleanup and remove unused files from C:\\.")
    if top_procs and top_procs[0]["ram_mb"] > 500:
        p = top_procs[0]
        recs.append(f"► {p['name']} (PID {p['pid']}) is consuming {p['ram_mb']} MB — consider restarting it.")
    if crit_count > 3:
        recs.append(f"► {crit_count} CRITICAL anomalies recorded recently. Review anomaly log for details.")
    if not recs:
        recs.append("► System is healthy. No immediate action required.")

    # ══════════════════════════════════════════════════════════
    # BUILD REPORT TEXT
    # ══════════════════════════════════════════════════════════
    lines = []

    lines.append(_separator("═"))
    lines.append("  SYSWATCH — AUTOMATED SYSTEM HEALTH REPORT")
    lines.append(f"  Generated : {ts_display}")
    lines.append(f"  Platform  : Windows 11  |  Tool: SysWatch v1.0")
    lines.append(_separator("═"))

    # ── Section 1: System Summary ─────────────────────────────
    lines.append(_section("1. SYSTEM SUMMARY"))
    lines.append(f"  Overall Health Score : {health_score}/100  →  {overall}")
    lines.append(f"  Report Timestamp     : {ts_display}")
    lines.append(f"  Metrics History      : {len(history)} recent readings loaded")
    lines.append(f"  Anomaly Records      : {len(anomalies)} recent events ({crit_count} CRITICAL, {warn_count} WARNING)")
    lines.append(f"  Network (cumulative) : Sent {net.bytes_sent // (1024**2)} MB  |  Received {net.bytes_recv // (1024**2)} MB")

    # ── Section 2: Health Status ──────────────────────────────
    lines.append(_section("2. HEALTH STATUS"))
    lines.append(f"  CPU Usage   :  {_bar(cpu):<40}  [{cpu_status}]")
    lines.append(f"  RAM Usage   :  {_bar(ram.percent):<40}  [{ram_status}]")
    lines.append(f"    Used      :  {ram.used // (1024**2)} MB  /  {ram.total // (1024**2)} MB")
    lines.append(f"  Disk Usage  :  {_bar(disk.percent):<40}  [{disk_status}]")
    lines.append(f"    Free      :  {disk.free // (1024**3)} GB  free on C:\\")
    lines.append(f"  RAM Trend   :  {ram_trend}")

    # ── Section 3: Detected Issues ────────────────────────────
    lines.append(_section("3. DETECTED ISSUES (Recent Anomaly Log)"))
    if anomalies:
        lines.append(f"  {'Timestamp':<20}  {'Severity':<10}  {'Metric':<8}  {'Value':<8}  Message")
        lines.append("  " + "-" * 72)
        for a in anomalies:
            ts  = a.get("timestamp", "—")
            sev = a.get("severity", "—")
            met = a.get("metric", "—")
            val = a.get("value", "—")
            msg = a.get("message", "—")
            try:
                val_str = f"{float(val):.1f}%"
            except (ValueError, TypeError):
                val_str = str(val)
            lines.append(f"  {ts:<20}  {sev:<10}  {met:<8}  {val_str:<8}  {msg}")
    else:
        lines.append("  No anomalies recorded yet.")

    # ── Section 4: Performance Analysis ──────────────────────
    lines.append(_section("4. PERFORMANCE ANALYSIS"))
    lines.append("  TOP 10 PROCESSES BY RAM USAGE")
    lines.append(f"  {'Process Name':<35}  {'PID':<8}  RAM Usage")
    lines.append("  " + "-" * 58)
    for p in top_procs:
        bar_len = min(20, p["ram_mb"] // 50)
        bar_str = "█" * bar_len
        lines.append(f"  {p['name']:<35}  {str(p['pid']):<8}  {p['ram_mb']:>5} MB  {bar_str}")

    if history:
        lines.append("")
        lines.append("  HISTORICAL METRICS (last 10 readings)")
        lines.append(f"  {'Timestamp':<20}  {'CPU':>6}  {'RAM':>6}  {'Disk':>6}")
        lines.append("  " + "-" * 44)
        for r in history:
            lines.append(
                f"  {r.get('timestamp', '—'):<20}  "
                f"{float(r.get('cpu', 0)):>5.1f}%  "
                f"{float(r.get('ram_percent', 0)):>5.1f}%  "
                f"{float(r.get('disk_percent', 0)):>5.1f}%"
            )

    # ── Section 5: Recommendations ────────────────────────────
    lines.append(_section("5. RECOMMENDATIONS"))
    for rec in recs:
        lines.append(f"  {rec}")

    # Footer
    lines.append(f"\n{_separator('─')}")
    lines.append("  Report generated by SysWatch — AI System Intelligence")
    lines.append("  TCS XploreInnoQuest 2026  |  Presenter: Ramya Joshi")
    lines.append(_separator("─"))
    lines.append("")

    return "\n".join(lines), ts_file