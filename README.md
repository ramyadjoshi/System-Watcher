# 🤖 SysWatch — AI Powered System Intelligence

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=30&pause=1000&color=00F7FF&center=true&vCenter=true&width=700&lines=AI-Powered+System+Monitoring;Real-Time+Anomaly+Detection;RAG-Based+System+Advisor;Know+Your+System+Before+It+Fails" />

<br>

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge\&logo=flask)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-purple?style=for-the-badge)
![Windows](https://img.shields.io/badge/Platform-Windows_11-0078D6?style=for-the-badge\&logo=windows)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br><br>

<img width="850" src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,100:8b5cf6&height=220&section=header&text=SysWatch&fontSize=55&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI%20Powered%20System%20Monitoring%20and%20Analysis&descAlignY=58" />

</div>

---

# 📌 Overview

SysWatch is an intelligent real-time monitoring system that combines:

* ⚡ Live system monitoring
* 🧠 AI-powered advisory insights
* 📈 Trend analysis
* 🚨 Smart anomaly detection
* 🔍 Software issue detection
* 💬 RAG-based AI assistant

Instead of only displaying CPU/RAM numbers, SysWatch explains:

> **What is happening, why it is happening, and what to do next.**

---

# ✨ Core Features

<div align="center">

| Feature                 | Description                                                   |
| ----------------------- | ------------------------------------------------------------- |
| 📊 Real-Time Dashboard  | Live CPU, RAM, Disk, Network monitoring                       |
| 🚨 Smart Alerts         | Detects warnings and critical state transitions               |
| 🧠 AI Advisor           | Generates human-readable optimization suggestions             |
| 📈 Historical Analysis  | Tracks metrics over time using CSV storage                    |
| 🔍 Software Detection   | Detects memory leaks, thread explosions, suspicious processes |
| 💬 AI Chat              | RAG-powered contextual assistant using system history         |
| ⚡ Fast APIs             | Flask backend with optimized routes and caching               |
| 🧪 Evaluation Framework | Precision, Recall, F1, Latency benchmarking                   |

</div>

---

# 🖼️ System Preview

## 🏠 Landing Page

<img width="100%" src="https://dummyimage.com/1200x600/0f172a/ffffff&text=Add+Your+Landing+Page+Screenshot+Here" />

## 📊 Monitoring Dashboard

<img width="100%" src="https://dummyimage.com/1200x600/111827/ffffff&text=Add+Dashboard+Screenshot+Here" />

## 📈 History Analytics

<img width="100%" src="https://dummyimage.com/1200x600/1e293b/ffffff&text=Add+Graphs+Screenshot+Here" />

## 💬 AI Advisor

<img width="100%" src="https://dummyimage.com/1200x600/172554/ffffff&text=Add+AI+Advisor+Screenshot+Here" />

---

# 🧠 Architecture

```text
sys_watcher/
│
├── app.py                  # Flask backend and APIs
├── snapshot.py             # System metrics collection
├── advisor.py              # AI advisory engine
├── software_detector.py    # Software issue detection
├── storage.py              # CSV storage utilities
├── monitor.py              # Terminal monitoring mode
│
├── templates/
│   └── index.html          # Frontend dashboard
│
├── evaluation/
│   ├── evaluate.py         # Evaluation framework
│   └── test_cases.json     # Ground truth cases
│
├── metrics.csv
├── anomalies.csv
├── .env
└── README.md
```

---

# 🚀 Quick Start

## 1️⃣ Clone Repository

```bash
git clone https://github.com/ramyadjoshi/System-Watcher.git
cd System-Watcher
```

---

## 2️⃣ Install Dependencies

```bash
pip install flask psutil python-dotenv requests rich
```

---

## 3️⃣ Add Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

---

## 4️⃣ Run Application

```bash
python app.py
```

Open browser:

```text
http://127.0.0.1:5000
```

---

# 🌐 API Endpoints

| Endpoint         | Purpose                     |
| ---------------- | --------------------------- |
| `/api/metrics`   | Live CPU/RAM/Disk metrics   |
| `/api/processes` | Top RAM-consuming processes |
| `/api/network`   | Network statistics          |
| `/api/history`   | Historical CSV data         |
| `/api/anomalies` | Logged anomaly events       |
| `/api/advisor`   | AI-generated system advice  |
| `/api/chat`      | RAG-based AI assistant      |

---

# 📊 Evaluation Metrics

SysWatch includes an evaluation framework for measuring:

* ✅ Precision
* ✅ Recall
* ✅ F1 Score
* ✅ Latency
* ✅ Advisor relevance

## 📈 Latest Results

```text
Precision : 1.0000
Recall    : 1.0000
F1 Score  : 1.0000

Average Latency : 269ms
Advisor Relevance : 0.56
```

---

# 🛠️ Tech Stack

<div align="center">

| Layer         | Technology          |
| ------------- | ------------------- |
| Backend       | Flask + Python      |
| Monitoring    | psutil              |
| AI            | Groq + Llama 3.1    |
| Frontend      | HTML/CSS/JavaScript |
| Visualization | Chart.js            |
| Terminal UI   | Rich                |
| Storage       | CSV                 |

</div>

---

# 🔍 Detection Capabilities

```text
🔴 Critical CPU spikes
🟡 High RAM consumption
🔴 Disk nearing full capacity
🟡 Memory leak suspects
🔴 Handle leaks
🟡 Thread explosions
🔴 Suspicious process locations
```

---

# 🔐 Security

* ✅ Runs locally
* ✅ Environment variables protected via `.env`
* ✅ No telemetry
* ✅ Read-only monitoring
* ✅ Sensitive files excluded using `.gitignore`

---

# 🗺️ Future Improvements

* [ ] Predictive crash analysis
* [ ] Email/desktop notifications
* [ ] Docker deployment
* [ ] Multi-machine monitoring
* [ ] PDF system reports
* [ ] ML-based anomaly prediction

---

# 👩‍💻 Author

<div align="center">

## Ramya Dattaraj Joshi

### Software Engineer • AI Systems Enthusiast

Built as part of advanced system intelligence and GenAI experimentation.

<br>

<a href="https://github.com/ramyadjoshi">
<img src="https://img.shields.io/badge/GitHub-ramyadjoshi-181717?style=for-the-badge&logo=github" />
</a>

</div>

---

<div align="center">

## ⭐ If you found SysWatch interesting, consider starring the repository.

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:8b5cf6,100:06b6d4&height=120&section=footer" />

</div>
