import psutil
import os
import csv
from datetime import datetime

METRICS_FILE = os.path.join(os.path.dirname(__file__), 'metrics.csv')

def get_process_details():
    # collects detailed per-process data for software bug detection
    process_data = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent',
                                      'memory_info', 'num_handles', 'num_threads',
                                      'create_time']):
        try:
            ram_mb      = proc.info['memory_info'].rss // (1024**2)
            create_time = proc.info['create_time']
            uptime_mins = (datetime.now().timestamp() - create_time) / 60

            process_data.append({
                'pid'         : proc.info['pid'],
                'name'        : proc.info['name'],
                'status'      : proc.info['status'],
                'cpu_percent' : proc.info['cpu_percent'],
                'ram_mb'      : ram_mb,
                'num_handles' : proc.info['num_handles'] or 0,
                'num_threads' : proc.info['num_threads'] or 0,
                'uptime_mins' : round(uptime_mins, 1)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return process_data


def detect_zombie_processes(process_data):
    # zombie = process that has finished but not been cleaned up by parent
    # status will be 'zombie' — classic software bug
    zombies = [p for p in process_data if p['status'] == 'zombie']
    return zombies


# Windows system processes that legitimately have high handle counts
SYSTEM_PROCESS_WHITELIST = {
    'system', 'svchost.exe', 'lsass.exe', 'services.exe',
    'csrss.exe', 'wininit.exe', 'smss.exe', 'registry'
}

def detect_handle_leaks(process_data, threshold=3000):
    leakers = [
        p for p in process_data
        if p['num_handles'] > threshold
        and p['name'].lower() not in SYSTEM_PROCESS_WHITELIST
    ]
    return leakers
# def detect_handle_leaks(process_data, threshold=3000):
#     # a process with too many open handles is leaking resources
#     # normal processes have under 1000 handles
#     # above 3000 is a strong signal of a handle leak
#     leakers = [p for p in process_data if p['num_handles'] > threshold]
#     return leakers


def detect_thread_explosion(process_data, threshold=100):
    # a process with hundreds of threads is likely buggy
    # normal apps have under 50 threads
    exploded = [p for p in process_data if p['num_threads'] > threshold]
    return exploded


def detect_runaway_cpu(process_data, threshold=80):
    # a single process eating more than 80% CPU is a runaway process
    runaways = [p for p in process_data if p['cpu_percent'] > threshold]
    return runaways


def detect_memory_leak_processes(process_data, ram_threshold=500, uptime_threshold=30):
    # a process that has been running for more than 30 minutes
    # AND consuming more than 500MB is a memory leak candidate
    suspects = [
        p for p in process_data
        if p['ram_mb'] > ram_threshold and p['uptime_mins'] > uptime_threshold
    ]
    return suspects


def detect_high_thread_cpu(process_data):
    # process with both high threads AND high CPU — thread thrashing
    suspects = [
        p for p in process_data
        if p['num_threads'] > 50 and p['cpu_percent'] > 30
    ]
    return suspects


def run_software_detection():
    # runs all software bug checks and returns list of findings
    findings = []
    process_data = get_process_details()

    # ── ZOMBIE PROCESSES ──
    zombies = detect_zombie_processes(process_data)
    for z in zombies:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'WARNING',
            'title'  : f"Zombie process detected: {z['name']}",
            'detail' : f"PID {z['pid']} has finished but was not cleaned up by its parent process. "
                       f"This is a software bug in the parent application. "
                       f"Restarting the parent application will clear it."
        })

    # ── HANDLE LEAKS ──
    leakers = detect_handle_leaks(process_data)
    for p in leakers:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'CRITICAL',
            'title'  : f"Handle leak detected: {p['name']}",
            'detail' : f"PID {p['pid']} has {p['num_handles']} open handles — "
                       f"far above normal. This process is leaking system resources. "
                       f"Restart {p['name']} to recover handles."
        })

    # ── THREAD EXPLOSION ──
    exploded = detect_thread_explosion(process_data)
    for p in exploded:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'WARNING',
            'title'  : f"Thread explosion: {p['name']}",
            'detail' : f"PID {p['pid']} has spawned {p['num_threads']} threads. "
                       f"Normal applications use under 50. "
                       f"This suggests a thread management bug. Restart {p['name']}."
        })

    # ── RUNAWAY CPU ──
    runaways = detect_runaway_cpu(process_data)
    for p in runaways:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'CRITICAL',
            'title'  : f"Runaway process: {p['name']}",
            'detail' : f"PID {p['pid']} is consuming {p['cpu_percent']}% CPU — "
                       f"this is a runaway process. It may be stuck in an infinite loop. "
                       f"Force close {p['name']} immediately."
        })

    # ── MEMORY LEAK SUSPECTS ──
    suspects = detect_memory_leak_processes(process_data)
    for p in suspects:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'WARNING',
            'title'  : f"Memory leak suspect: {p['name']}",
            'detail' : f"PID {p['pid']} has been running for {p['uptime_mins']} minutes "
                       f"and is consuming {p['ram_mb']}MB. "
                       f"Long-running processes with high RAM often indicate memory leaks. "
                       f"Restart {p['name']} if performance degrades."
        })

    # ── THREAD THRASHING ──
    thrashing = detect_high_thread_cpu(process_data)
    for p in thrashing:
        findings.append({
            'type'   : 'SOFTWARE',
            'level'  : 'WARNING',
            'title'  : f"Thread thrashing: {p['name']}",
            'detail' : f"PID {p['pid']} has {p['num_threads']} threads "
                       f"and {p['cpu_percent']}% CPU usage simultaneously. "
                       f"Threads are competing for CPU — likely a concurrency bug."
        })
    # ── SUSPICIOUS PROCESSES ──
    suspicious = detect_suspicious_processes(process_data)
    findings.extend(suspicious)   

    return findings

def detect_suspicious_processes(process_data):
    # detects processes running from suspicious locations
    # or with no verified publisher — lightweight security check
    suspicious = []
    suspicious_paths = ['\\temp\\', '\\tmp\\', '\\appdata\\local\\temp\\',
                        '\\downloads\\', '\\public\\']

    for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
        try:
            exe = proc.info.get('exe') or ''
            exe_lower = exe.lower()
            for path in suspicious_paths:
                if path in exe_lower:
                    suspicious.append({
                        'type'   : 'SECURITY',
                        'level'  : 'CRITICAL',
                        'title'  : f"Suspicious process location: {proc.info['name']}",
                        'detail' : f"PID {proc.info['pid']} is running from {exe} — "
                                   f"legitimate software rarely runs from temp folders. "
                                   f"This could indicate malware. Investigate immediately."
                    })
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return suspicious