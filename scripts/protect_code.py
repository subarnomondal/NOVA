"""
Code Protection Script for NOVA
Obfuscates core modules to prevent unauthorized access
"""

import os
import shutil
import py_compile
from pathlib import Path

def protect_nova():
    print(" NOVA Code Protection System")
    print("=" * 50)
    
    # Files to protect
    core_files = [
        "core/llm_manager.py",
        "core/key_manager.py",
        "core/user_profile.py",
        "core/drl_system.py",
        "core/assistant.py",
        "desktop.py"
    ]
    
    # Create protected directory
    protected_dir = "protected"
    if os.path.exists(protected_dir):
        shutil.rmtree(protected_dir)
    os.makedirs(protected_dir)
    os.makedirs(f"{protected_dir}/core", exist_ok=True)
    
    print("\n Compiling to bytecode (.pyc)...")
    
    for file_path in core_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Skipping {file_path} (not found)")
            continue
            
        try:
            # Compile to .pyc (bytecode)
            compiled_path = py_compile.compile(file_path, doraise=True)
            
            # Move to protected directory
            if "core/" in file_path:
                dest = f"{protected_dir}/core/{Path(file_path).stem}.pyc"
            else:
                dest = f"{protected_dir}/{Path(file_path).stem}.pyc"
            
            shutil.copy(compiled_path, dest)
            print(f"✅ Protected: {file_path} → {dest}")
            
        except Exception as e:
            print(f"❌ Failed to protect {file_path}: {e}")
    
    # Copy non-sensitive files as-is
    print("\n Copying configuration files...")
    copy_files = [
        "config/settings.yaml",
        "requirements.txt",
        "run_nova.bat"
    ]
    
    for file_path in copy_files:
        if os.path.exists(file_path):
            if "/" in file_path:
                os.makedirs(f"{protected_dir}/{Path(file_path).parent}", exist_ok=True)
            shutil.copy(file_path, f"{protected_dir}/{file_path}")
            print(f" Copied: {file_path}")
    
    # Create README
    with open(f"{protected_dir}/README.txt", "w") as f:
        f.write("""NOVA - Protected Distribution
================================

This is a protected version of NOVA.
Core modules are compiled to bytecode (.pyc) to prevent unauthorized modification.

To run:
1. Install dependencies: pip install -r requirements.txt
2. Add your API keys to keys.json
3. Run: python desktop.pyc

Note: Source code is not included in this distribution.
For licensing inquiries, contact the developer.
""")
    
    print("\n" + "=" * 50)
    print("✅ Protection Complete!")
    print(f" Protected files are in: ./{protected_dir}/")
    print("\n⚠️  IMPORTANT:")
    print("   - .pyc files are bytecode (harder to reverse)")
    print("   - For stronger protection, use PyArmor (commercial)")
    print("   - Never share your keys.json file!")

if __name__ == "__main__":
    protect_nova()
