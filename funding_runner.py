import time
import subprocess

# =========================
# FUNDING AGENT LOOP
# =========================

while True:

    print("===================================")
    print("Running funding agent...")
    print("===================================")

    subprocess.run([
        "python",
        "funding_agent.py"
    ])

    print("===================================")
    print("Sleeping 15 minutes...")
    print("===================================")

    time.sleep(900)