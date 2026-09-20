# file: check_dependencies.py

REQUIRED_LIBS = {
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "streamlit": "streamlit",
    "playwright": "playwright",
}

missing = []

for module, name in REQUIRED_LIBS.items():
    try:
        __import__(module)
    except ImportError:
        missing.append(name)

if missing:
    raise RuntimeError(
        "Missing required libraries: "
        + ", ".join(missing)
        + "\nInstall them using: pip install -r requirements.txt"
    )
else:
    print("[✓] All required dependencies are installed")
