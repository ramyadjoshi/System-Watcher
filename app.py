from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template, request
import psutil
import csv
import os
import time as time_module
from storage import init_csv, init_anomaly_csv
from advisor import get_advice

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════
# CACHE LAYER — prevents repeated expensive reads every request
# ══════════════════════════════════════════════════════════════

# History CSV cache — re-reads file only every 10 seconds
_history_cache = {'data': [], 'time': 0}

def get_cached_history():
    global _history_cache
    now = time_module.time()
    if now - _history_cache['time'] > 10:
        rows = []
        metrics_file = os.path.join(os.path.dirname(__file__), 'metrics.csv')
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        _history_cache['data'] = rows[-100:]
        _history_cache['time'] = now
    return _history_cache['data']

# Software detection cache — re-runs every 30 seconds (expensive psutil calls)
_software_cache = {'data': [], 'time': 0}

def get_cached_software_findings():
    global _software_cache
    now = time_module.time()
    if now - _software_cache['time'] > 30:
        try:
            from software_detector import run_software_detection
            _software_cache['data'] = run_software_detection()
            _software_cache['time'] = now
        except Exception as e:
            print(f"Software detection error: {e}")
            _software_cache['data'] = []
    return _software_cache['data']

# Network cache — stores last reading to compute per-second delta
_net_cache = {'bytes_sent': 0, 'bytes_recv': 0, 'time': 0}

def get_network_speed():
    global _net_cache
    now   = time_module.time()
    net   = psutil.net_io_counters()
    sent  = net.bytes_sent
    recv  = net.bytes_recv

    if _net_cache['time'] == 0:
        # First call — store baseline, return zeros
        _net_cache = {'bytes_sent': sent, 'bytes_recv': recv, 'time': now}
        return 0.0, 0.0

    elapsed   = now - _net_cache['time']
    sent_kb   = round((sent - _net_cache['bytes_sent']) / 1024 / max(elapsed, 0.1), 1)
    recv_kb   = round((recv - _net_cache['bytes_recv']) / 1024 / max(elapsed, 0.1), 1)
    _net_cache = {'bytes_sent': sent, 'bytes_recv': recv, 'time': now}
    return max(0.0, sent_kb), max(0.0, recv_kb)

# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    return jsonify({
        'cpu'          : cpu,
        'ram_percent'  : ram.percent,
        'ram_used_mb'  : ram.used // (1024**2),
        'ram_total_mb' : ram.total // (1024**2),
        'disk_percent' : disk.percent,
        'disk_free_gb' : disk.free // (1024**3)
    })

@app.route('/api/network')
def get_network():
    # Returns per-second KB/s based on delta from last call
    sent_kb, recv_kb = get_network_speed()
    return jsonify({
        'sent_kb': sent_kb,
        'recv_kb': recv_kb
    })

@app.route('/api/processes')
def get_processes():
    processes    = psutil.process_iter(['pid', 'name', 'memory_info'])
    process_list = []
    for proc in processes:
        try:
            ram_mb = proc.info['memory_info'].rss // (1024**2)
            if ram_mb > 10:
                process_list.append({
                    'name'  : proc.info['name'],
                    'pid'   : proc.info['pid'],
                    'ram_mb': ram_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    process_list.sort(key=lambda x: x['ram_mb'], reverse=True)
    return jsonify(process_list[:10])

@app.route('/api/advisor')
def get_advisor():
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')

    current_state = {
        'cpu' : 'CRITICAL' if cpu > 90 else 'WARNING' if cpu > 75 else 'OK',
        'ram' : 'CRITICAL' if ram.percent > 90 else 'WARNING' if ram.percent > 80 else 'OK',
        'disk': 'CRITICAL' if disk.percent > 90 else 'WARNING' if disk.percent > 75 else 'OK'
    }

    processes    = psutil.process_iter(['pid', 'name', 'memory_info'])
    process_list = []
    for proc in processes:
        try:
            ram_mb = proc.info['memory_info'].rss // (1024**2)
            if ram_mb > 10:
                process_list.append({
                    'name'  : proc.info['name'],
                    'pid'   : proc.info['pid'],
                    'ram_mb': ram_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    process_list.sort(key=lambda x: x['ram_mb'], reverse=True)

    suggestions = get_advice(current_state, process_list)
    severity    = current_state['ram'] if current_state['ram'] != 'OK' else current_state['cpu']
    return jsonify([{
        'message': s['msg'],
        'severity': s['level'],
        'type'   : s['type']
    } for s in suggestions])

@app.route('/api/anomalies')
def get_anomalies():
    anomalies    = []
    anomaly_file = os.path.join(os.path.dirname(__file__), 'anomalies.csv')
    if os.path.exists(anomaly_file):
        with open(anomaly_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                anomalies.append(row)
    anomalies.reverse()
    return jsonify(anomalies)

@app.route('/api/history')
def get_history():
    # Uses cache — reads CSV only every 10 seconds, not on every request
    return jsonify(get_cached_history())

@app.route('/api/chat', methods=['POST'])
def chat():
    import requests as req

    user_message = request.json.get('message', '')
    api_key      = os.getenv('GROQ_API_KEY')

    if not api_key:
        return jsonify({'reply': 'Error: GROQ_API_KEY not found in .env file.'})

    # Live metrics
    cpu  = psutil.cpu_percent(interval=0.5)  # reduced from 1s to 0.5s
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')

    # Top 5 processes only — keeps prompt small
    processes    = psutil.process_iter(['pid', 'name', 'memory_info'])
    process_list = []
    for proc in processes:
        try:
            ram_mb = proc.info['memory_info'].rss // (1024**2)
            if ram_mb > 10:
                process_list.append(f"{proc.info['name']}({ram_mb}MB)")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    process_list.sort(key=lambda x: int(x.split('(')[1].replace('MB)','')), reverse=True)
    top_processes = ', '.join(process_list[:5])

    # Use CACHED history — last 10 rows only for AI context (keeps prompt small = faster response)
    cached = get_cached_history()
    recent_rows = cached[-10:]
    history_summary = ' | '.join([
        f"{r['timestamp'].split(' ')[1]} CPU:{r['cpu']}% RAM:{r['ram_percent']}%"
        for r in recent_rows
    ])

    # Compact system prompt — shorter = faster Groq response
    system_prompt = f"""You are SysWatch AI, a system health advisor.
LIVE: CPU={cpu}% RAM={ram.percent}%({ram.used//(1024**2)}MB/{ram.total//(1024**2)}MB) Disk={disk.percent}%({disk.free//(1024**3)}GB free)
TOP PROCESSES: {top_processes}
RECENT HISTORY: {history_summary}
Answer concisely and specifically using only this data. Be direct and actionable."""

    try:
        response = req.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type' : 'application/json'
            },
            json={
                'model'      : 'llama-3.1-8b-instant',  # fastest Groq model
                'messages'   : [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_message}
                ],
                'max_tokens' : 300,   # reduced from 500 — shorter = faster
                'temperature': 0.3,   # lower = more focused, less computation
                'stream'     : False
            },
            timeout=30  # 30 second hard timeout
        )

        data = response.json()

        if 'choices' not in data:
            err_msg = data.get('error', {}).get('message', str(data))
            return jsonify({'reply': f'Groq API error: {err_msg}'})

        reply = data['choices'][0]['message']['content']
        return jsonify({'reply': reply})

    except req.exceptions.Timeout:
        return jsonify({'reply': 'Request timed out. Groq free tier may be rate-limited. Please wait a moment and try again.'})
    except Exception as e:
        return jsonify({'reply': f'Connection error: {str(e)}'})

if __name__ == '__main__':
    # Prime the network cache on startup so first reading is accurate
    get_network_speed()
    time_module.sleep(1)
    get_network_speed()

    init_csv()
    init_anomaly_csv()
    app.run(debug=True)