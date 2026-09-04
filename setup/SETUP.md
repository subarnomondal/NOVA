# ⚙️ CLIO Setup Guide

Welcome to CLIO! This guide will walk you through the complete setup process to get your Autonomous Local AI Desktop Assistant running smoothly.

---

## 🚀 Step 1: Install Dependencies

### For Windows Users (Easiest)
1. Open the **`setup`** folder.
2. Double-click the **`install.bat`** file.
3. The script will automatically open a command prompt and install all required Python libraries, Playwright web browsers (for web-reading skills), and media downloaded tools (like YT-DLP).
3. Wait for the terminal window to say "Setup Complete!"

### For Mac / Linux Users (Manual)
Open your terminal and run the following commands:
```bash
# 1. Install all python requirements
pip install -r requirements.txt

# 2. Install the Playwright headless browser for web skills
playwright install

# 3. Install the youtube downloader for music fetching
pip install yt-dlp
```

---

## 🔑 Step 2: Configure API Keys

CLIO uses cloud AI models (like Claude or LLaMA) as her brain to think and make decisions. We highly recommend using **OpenRouter** because it provides cheap and fast access to advanced models.

1. Go to your project folder and look for a file named `keys.example.json`.
2. Rename this file to **`keys.json`**.
3. Open `keys.json` in a text editor (like Notepad or VSCode).
4. Paste your API keys into the corresponding fields.

*Alternatively, the first time you run CLIO, she will generate a `userdata/config/settings.yaml` file where you can also safely paste your API keys.*

---

## 🎙️ Step 3: Configure Your Microphone (Optional)

If you plan on talking to CLIO via Voice Activity Detection (VAD) instead of typing:
1. Check your Windows Sound settings to make sure your default microphone is selected.
2. In the web interface, click the **Settings (Gear Icon)** in the top right.
3. Enable Voice Mode.

---

## ▶️ Step 4: Run the Assistant!

### On Windows
Simply double-click the **`run_clio.bat`** file. 
* This will launch the Python backend server.
* A web browser window will automatically pop up with the CLIO Cyberpunk Interface.

### On Mac / Linux
Open your terminal and run:
```bash
python desktop.py
```
Then, open your web browser and go to: `http://localhost:5000`

---

## 🐛 Troubleshooting

*   **Error: "Model not found" or 404**
    *   Make sure your `keys.json` has a valid API key, and that the selected model in `core/llm_manager.py` (like `google/gemini-2.0-flash-exp:free`) is active on OpenRouter. You can change this in the Web UI Settings panel.
*   **Error: "Playwright executable not found"**
    *   You forgot to install the browsers. Run `playwright install` in your terminal.
*   **Audio/Music doesn't play**
    *   Ensure `yt-dlp` is installed correctly, or try updating it by running `pip install -U yt-dlp`.

Enjoy your new autonomous desktop assistant!
