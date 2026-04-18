<div align="center">
  <img src="assets/banner.png" alt="NOVA Banner" width="100%" />
  <br/><br/>
  <h1>🌌 NOVA — The Autonomous Local AGI Desktop</h1>
  <p><strong>A sovereign, privacy-first personal intelligence engine designed for seamless digital orchestration.</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-7149f4.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Status](https://img.shields.io/badge/Status-Production--Ready-success.svg?style=for-the-badge)](https://github.com/subarnomondal/NOVA)
  
</div>

---

## 💎 The Vision
**NOVA** (Neural Orchestration & Virtual Assistant) is not just a chatbot—it is an **Autonomous Personal Agent**. Designed with a privacy-first philosophy, NOVA operates as a localized "Brain" that manages system architecture, explores the web, and automates professional workflows directly from your desktop. 

### 🛡️ Why NOVA?
- **Privacy-First**: Your data stays local. Interactions and logs are stored on your machine.
- **Autonomous Reasoning**: Uses a sophisticated cognitive loop (Observation → Thought → Action) to solve multi-step problems without supervision.
- **Zero-Latency Orchestration**: Optimized Python core for instant response times and low resource overhead.
- **Unlimited Extensibility**: A modular "Skill" architecture allows developers to build and plug in new capabilities in minutes.

---

## 🛠️ Integrated Capabilities (The Skill Matrix)

NOVA’s power is derived from its modular skill system, spanning across four primary domains:

### ⚡ System & Infrastructure
*   **Deep OS Integration**: Native control of Windows/System parameters, hardware monitoring, and media transport.
*   **Code Architect**: A specialized module for analyzing local codebases and generating architectural improvements.
*   **Automated Productivity**: Intelligent reminder systems and professional document generation (PDF/DOCX).

### 🌐 Autonomous Web Intelligence
*   **Web Agent**: A Playwright-powered autonomous browser that can "see" and interact with any website.
*   **Cognitive Search**: Multi-source research via DuckDuckGo and Wikipedia with synthesized summarization.
*   **Mail & Messaging**: Enterprise-grade automation for Email, WhatsApp, and Messenger.

### 👁️ Perception & Vision
*   **Proactive Vision**: Real-time screen analysis and image understanding via advanced OCR and Vision-LLM integration.
*   **Emotion Analytics**: Context-aware interactions driven by sentiment detection within conversations.

---

## 🚀 Deployment Guide

### Prerequisites
*   Python 3.10 or higher
*   Windows OS (for full system integration)
*   Playwright dependencies

### installation
```powershell
# Clone the repository
git clone https://github.com/subarnomondal/NOVA.git
cd NOVA

# Initialize environment & dependencies
pip install -r requirements.txt
playwright install
```

### Configuration
1.  Navigate to `userdata/keys.example.json`.
2.  Rename to `keys.json`.
3.  Inject your API keys (Gemini, OpenRouter, or Groq handles most heavy lifting).

---

## 📂 Architecture Overview

*   `/core/` — **The Central Nervous System**: Handles Memory (KV), LLM Routing, Vision Management, and NLU Parsing.
*   `/skills/` — **The Front-line Workers**: Indpendent Python modules that provide specific capabilities.
*   `/web/` — **The Dashboard**: A sleek, Glassmorphism-inspired Three.js interface for desktop interaction.
*   `/userdata/` — **The Vault**: Securely stores your local context, logs, and encrypted keys.

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
