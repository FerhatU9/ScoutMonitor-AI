
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 1. Find project folders
project_folder = Path(__file__).resolve().parent.parent
scripts_folder = project_folder / "scripts"
logs_folder = project_folder / "logs"

# Create the logs folder if it doesn't exist
logs_folder.mkdir(exist_ok=True)

log_file = logs_folder / "daily_monitor.log"

# 2. Print a message and save it to our log file
def log_message(message):
    print(message, flush=True)

    with log_file.open("a", encoding="utf-8") as file:
        file.write(message + "\n")


# 3. List the programs in the correct order
steps = [
    ("Collect football statistics", "save_player_stats.py"),
    ("Monitor player performance", "monitor_player.py"),
]

log_message("\n" + "=" * 45)
log_message(f"Started: {datetime.now().astimezone()}")
log_message("Starting ScoutMonitor AI...")

# 4. Run each program
for step_name, filename in steps:

    log_message(f"\nStep: {step_name}")

    script_path = scripts_folder / filename

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_folder,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Save the program's output
    if result.stdout:
        log_message(result.stdout.rstrip())

    if result.stderr:
        log_message("Error output:\n" + result.stderr.rstrip())

    # Stop if a program failed
    if result.returncode != 0:
        log_message(f"FAILED: {step_name}")
        raise SystemExit(1)

    log_message(f"Completed: {step_name}")

log_message("\nScoutMonitor AI daily workflow completed!")
log_message(f"Finished: {datetime.now().astimezone()}")
