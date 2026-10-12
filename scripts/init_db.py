"""Initialize the local SQLite schema."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grievance_app import create_app  # noqa: E402
from grievance_app.extensions import db  # noqa: E402


app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables are ready.")
