import psutil
from storage import init_csv, save_snapshot, init_anomaly_csv, save_anomaly
from display import print_snapshot, print_processes
from advisor import get_advice


def run_snapshot(last_state):

    # ── METRICS COLLECTION ────────────────────────────────────────────────────

    # cpu_percent(interval=1) watches for 1 second before reporting
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')

    # print metrics as a rich table
    print_snapshot(cpu, ram, disk)

    # ── PROCESS LIST ──────────────────────────────────────────────────────────

    processes    = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info'])
    process_list = []

    for proc in processes:
        try:
            # rss = actual RAM physically used by this process in bytes
            ram_used_mb = proc.info['memory_info'].rss // (1024**2)
            if ram_used_mb > 10:
                process_list.append({
                    'name'  : proc.info['name'],
                    'pid'   : proc.info['pid'],
                    'ram_mb': ram_used_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # process closed or access blocked — skip it
            pass

    # sort highest RAM first
    process_list.sort(key=lambda x: x['ram_mb'], reverse=True)

    # print top 10 processes as a rich table
    print_processes(process_list[:10])

    # ── ANOMALY DETECTION ─────────────────────────────────────────────────────

    # determine current state for each metric
    if cpu > 90:
        current_cpu = 'CRITICAL'
    elif cpu > 75:
        current_cpu = 'WARNING'
    else:
        current_cpu = 'OK'

    if ram.percent > 90:
        current_ram = 'CRITICAL'
    elif ram.percent > 80:
        current_ram = 'WARNING'
    else:
        current_ram = 'OK'

    if disk.percent > 90:
        current_disk = 'CRITICAL'
    elif disk.percent > 75:
        current_disk = 'WARNING'
    else:
        current_disk = 'OK'

    # only save anomaly if state changed since last cycle
    print("\n=== Anomaly Detection ===")

    if current_cpu != last_state['cpu']:
        print(f"[{current_cpu}] CPU is at {cpu}%")
        if current_cpu != 'OK':
            save_anomaly(current_cpu, 'CPU', cpu, 'CPU state changed')
    else:
        print(f"[{current_cpu}] CPU is at {cpu}% — no state change")

    if current_ram != last_state['ram']:
        print(f"[{current_ram}] RAM is at {ram.percent}%")
        if current_ram != 'OK':
            save_anomaly(current_ram, 'RAM', ram.percent, 'RAM state changed')
    else:
        print(f"[{current_ram}] RAM is at {ram.percent}% — no state change")

    if current_disk != last_state['disk']:
        print(f"[{current_disk}] Disk is at {disk.percent}%")
        if current_disk != 'OK':
            save_anomaly(current_disk, 'DISK', disk.percent, 'Disk state changed')
    else:
        print(f"[{current_disk}] Disk is at {disk.percent}% — no state change")

    # ── ADVISOR ───────────────────────────────────────────────────────────────

    # build current state dictionary to pass to advisor
    current_state = {
        'cpu' : current_cpu,
        'ram' : current_ram,
        'disk': current_disk
    }

    # get advice based on current states and top processes
    suggestions = get_advice(current_state, process_list)

    print("\n=== Advisor ===")
    for suggestion in suggestions:
        print(f"→ {suggestion}")

    # ── SAVE SNAPSHOT ─────────────────────────────────────────────────────────

    # always save every reading regardless of anomaly state
    save_snapshot(cpu, ram, disk)

    # return updated state so monitor.py remembers it for next cycle
    return {
        'cpu' : current_cpu,
        'ram' : current_ram,
        'disk': current_disk
    }


# allows snapshot.py to be run directly for a one-time check
if __name__ == '__main__':
    init_csv()
    init_anomaly_csv()
    default_state = {'cpu': 'OK', 'ram': 'OK', 'disk': 'OK'}
    run_snapshot(default_state)