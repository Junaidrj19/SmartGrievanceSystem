"""Seed fictional development accounts and sample grievances."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grievance_app import create_app  # noqa: E402
from grievance_app.seed import seed_demo_data  # noqa: E402


app = create_app()

with app.app_context():
    counts = seed_demo_data()
    print(
        "Demo data ready: "
        f"{counts['departments']} departments, "
        f"{counts['users']} users, "
        f"{counts['grievances']} grievances."
    )
