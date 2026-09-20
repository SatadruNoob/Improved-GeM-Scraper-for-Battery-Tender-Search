import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# -------------------------------------------------
# Resolve BASE directory (exe-aware)
# -------------------------------------------------
if getattr(sys, "frozen", False):
    INTERNAL_DIR = Path(sys._MEIPASS)
    sys.path.insert(0, str(INTERNAL_DIR))
    os.chdir(str(INTERNAL_DIR))
else:
    INTERNAL_DIR = Path(__file__).parent

# -------------------------------------------------
# Choose Python executable (prefer virtual environment)
# -------------------------------------------------
python_exe = sys.executable  # Default to current Python

# Try to use virtual environment Python if available
venv_python = INTERNAL_DIR / ".venv" / "Scripts" / "python.exe"
if venv_python.exists():
    python_exe = str(venv_python)
    print(f"Using virtual environment Python: {python_exe}")
else:
    print(f"Using system Python: {python_exe}")

# -------------------------------------------------
# Environment safety
# -------------------------------------------------
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
os.environ["STREAMLIT_BROWSER_SERVER_ADDRESS"] = ""

# Playwright bundled browsers
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(INTERNAL_DIR / "chromium")

# -------------------------------------------------
# Paths
# -------------------------------------------------
APP_PY = INTERNAL_DIR / "app.py"

if not APP_PY.exists():
    raise RuntimeError(f"app.py not found at: {APP_PY}")

# -------------------------------------------------
# Launch Streamlit
# -------------------------------------------------
if getattr(sys, "frozen", False):    # Prevent browser from opening
    import webbrowser
    webbrowser.open = lambda url: None    # In frozen mode, run streamlit directly to avoid subprocess issues
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    import streamlit.web.cli as cli
    original_argv = sys.argv[:]
    sys.argv = ["streamlit", "run", str(APP_PY), "--server.port=8501", "--server.headless=true"]
    try:
        cli.main()
    finally:
        sys.argv = original_argv
else:
    cmd = [
        python_exe,
        "-m",
        "streamlit",
        "run",
        str(APP_PY),
        "--server.port=8501",
        "--server.headless=true",
    ]

    # Run Streamlit in the foreground so the container's main process
    # remains Streamlit itself (prevents container from exiting).
    # Also allow logs to appear in container stdout/stderr.
    subprocess.run(
        cmd,
        cwd=str(INTERNAL_DIR),
    )

# In containerized or non-GUI environments we do not attempt to open a browser
# (launcher will block while Streamlit runs). If running locally and you want
# automatic browser opening, call Streamlit directly or add logic here.
