import os
import subprocess
import platform

print("🚀 Starting CLIO Build Process (Cross-Platform)...")

# Install PyInstaller if missing
try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    subprocess.check_call(["pip", "install", "pyinstaller"])

# Define assets to include (web interface, skills, core logic)
separator = ";" if platform.system() == "Windows" else ":"
assets = [
    f"web{separator}web",
    f"skills{separator}skills",
    f"core{separator}core"
]

add_data_args = []
for asset in assets:
    add_data_args.extend(["--add-data", asset])

# Build the PyInstaller command
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onedir",       # Creates a directory with the executable (better for debugging/assets than onefile)
    "--windowed",     # Hides the terminal window (GUI only)
    "--name", "CLIO",
] + add_data_args + ["desktop.py"]

print(f"📦 Running Build Command: {' '.join(cmd)}")
subprocess.run(cmd)

print("✅ Build complete! You can find the compiled executable in the 'dist/CLIO' folder.")
print("Note: The 'userdata' folder will be generated automatically when you run the app.")
