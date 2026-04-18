"""
Run this script WHILE a WhatsApp call is coming in.
It will print ALL open windows with their title, size, and position
so we can identify exactly which one is the call popup.
"""
import pygetwindow as gw
import time

print("Scanning all open windows...\n")
print(f"{'TITLE':<45} {'W':>6} {'H':>6} {'LEFT':>6} {'TOP':>6}")
print("-" * 75)

all_wins = gw.getAllWindows()
for win in all_wins:
    title = win.title[:44] if win.title else "(no title)"
    if win.width > 0 and win.height > 0:  # skip invisible/ghost windows
        marker = "  <-- SMALL POPUP?" if win.width < 600 and win.height < 500 else ""
        print(f"{title:<45} {win.width:>6} {win.height:>6} {win.left:>6} {win.top:>6}{marker}")

print("\n[INFO] Look for the WhatsApp call popup in the list above.")
print("[INFO] Any entry marked '<-- SMALL POPUP?' is a candidate.")
