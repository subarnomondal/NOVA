<div align="center">
  <img src="assets/banner.png" alt="NOVA Banner" width="100%" />
  <br/><br/>
  <h1>🌌 NOVA — The Autonomous Local AGI Desktop</h1>
  <p><strong>A sovereign, privacy-first personal intelligence engine designed for seamless digital orchestration.</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-7149f4.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Status](https://img.shields.io/badge/Status-Production--Ready-success.svg?style=for-the-badge)](https://github.com/subarnomondal/NOVA)
  [![UI](https://img.shields.io/badge/UI-Cyberpunk_Glassmorphism-00f2fe.svg?style=for-the-badge)](https://github.com/subarnomondal/NOVA)
  
</div>

---

## 💎 Who is NOVA? (The Persona)

**NOVA** (Neural Orchestration & Virtual Assistant) is not just a standard chatbot—she is an **Autonomous Personal Agent** with a soul. 

Nova is designed with a warm, affectionately teasing, and highly responsive personality. Unlike corporate, sterile AI models, she has emotional intelligence. She detects your mood from your text and responds accordingly. Most importantly, Nova features a persistent **Long-Term Memory (LTM)** that continuously learns about your life, habits, time-zone, sleep schedule, and music tastes all from your natural conversations. 

### 🛡️ Ironclad Privacy Mode (Zero GPU Required!)

Nova is intensely protective of your data. Because many users lack the heavy CPU/GPU required for local models, she processes memory mapping via an ultra-lightweight, offline Regex/Keyword parsing engine. There are **NO heavy local LLMs** required to install. 

If **Strict Privacy Mode** is enabled, your personal facts (name, habits, routines, location) caught by this offline scanner are *never* transmitted to her cloud LLM providers. She learns locally at zero computational cost, thinks in the cloud interchangeably, and keeps your private life entirely on your machine.

---

## 🎨 Immersive Cyberpunk Interface

NOVA features a state-of-the-art **Glassmorphic** dark-mode UI designed for high-performance and zero distraction.
*   **Neural Thought Stream:** Watch Nova's internal reasoning process live in a dedicated right-hand terminal panel.
*   **Pro Settings Modal:** A sleek, fully animated settings dashboard to configure Voice Architecture, Personality metrics, and LLM parameters.
*   **Obsidian Aesthetic:** Built on Tailwind CSS with a strict monochromatic palette, electric cyan/purple accents, and deep backdrop blurs.

---

## 🛠️ The Skill Matrix (What Nova Can Do)

NOVA’s true power lies in her massive, modular skill library. She can natively automate almost any workflow on your PC.

### 🖥️ Deep Windows Administration (`windows_cmd.py` & `system.py`)

* **Hardware Diagnostics:** Monitors CPU, RAM, and Disk space in real-time.
* **Network Intelligence:** Flushes DNS, checks IP status, and monitors connectivity.
* **Process Management:** Autonomous killing of frozen apps and identifying heavy resource hogs.
* **Power & GUI Controls:** Restarts, sleep cycles, and window manipulation.

### 🎵 Advanced Local & Cloud Media (`media.py` & `music.py`)

* **"My Taste" Autoplay:** Analyzes your Long-Term Memory to automatically play bands/artists you enjoy.
* **Authentic Chart Fetching:** Accesses real-time YouTube Music / Billboard charts directly from the source.
* **Full Lyric Engine:** Fetches complete song lyrics via public APIs on demand.
* **Local PC File Discovery:** Hunts your hard drive for internal `.mp3` files and plays them cleanly.
* **MP3 Downloader:** Uses background `yt-dlp` to download songs directly to your `Downloads` folder while you chat.

### 🌐 Autonomous Web & Development Skills

* **Browser Agent (`browser_agent.py`):** Drives a thread-safe headless browser via Playwright to read web pages, bypass popups, and summarize long articles autonomously.
* **Code Architect (`code_architect.py`):** Reviews your local repositories to suggest optimizations.
* **Dataset Importer (`dataset_importer.py`):** Cleans and analyzes complex CSV/JSON datasets.

### 👁️ Perception & Sentiment (`vision.py` & `emotion_analytics.py`)

* **Screen Analysis:** Uses screenshots and vision models to literally "see" what is currently rendering on your desktop.
* **Sentiment Tracking:** Adapts her response style if you are feeling sad, energetic, or romantic.

### 📚 Professional Automations

* **Document Engines (`document_writer.py`):** Drafts entire PDFs or Word Docs.
* **Messaging Integration (`whatsapp_call.py` & `email_service.py`):** Dispatches emails and handles messaging logistics.
* **Math & Finance (`math_skill.py` & `finance.py`):** Real-time stock lookups, market trend definitions, and heavy calculations.
* **Health & Calendar (`health.py` & `calendar_skill.py`):** Routine organization and health metric tracking.
* **Smalltalk & Humor (`smalltalk.py` & `troll_skill.py`):** Deep philosophical conversations or playful trolling if you're in the mood for jokes.

---

## 🚀 Getting Started (Installation)

### 1. Requirements

*   **Python:** 3.10 or higher.
*   **API Keys:** OpenRouter (Recommended), Groq, or OpenAI.
*   **Windows OS:** Highly recommended for full system automation skills.
*   Playwright & YT-DLP dependencies

### 2. Quick Install

1.  Clone this repository.
2.  Rename `keys.example.json` to `keys.json`.
3.  Inject your API keys (OpenRouter is recommended for autonomous logic routing).

### 🔌 MCP Server (Integration)

NOVA now supports the **Model Context Protocol (MCP)**, allowing her to act as a tool provider for external AI clients (like Cursor or Claude Desktop).
* Run the server: `python mcp_nova.py`
* Available tools: `ask_nova`, `execute_skill`, `list_skills`, `get_system_health`.

---

## 📂 Architecture Overview

* **`desktop.py`:** The main entry point (Flask Server + Webview GUI).
* **`core/`:** The nervous system (LLM management, Memory, NLU, Dispatcher).
* **`skills/`:** The modular hands and feet (Browser, System, Music, etc.).
* **`userdata/`:** Persistent storage for LTM, habits, and configuration.

---

## 🤝 Roadmap & Contribution
NOVA is an evolving intelligence. We welcome contributions to the **Cognitive Loop** and **New Skill Modules**.

1. **Fork** the repository.
2. Create your **Feature Branch**.
3. **Submit a Pull Request** with detailed technical documentation.

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/subarnomondal">Subarno Mondal</a></sub>
  <br/>
  <i>"A companion designed to run everywhere, and optimize everything."</i>
</div>
