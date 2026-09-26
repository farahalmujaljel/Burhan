"""Print the API's OpenAPI schema as JSON (used to generate frontend TypeScript types).

Usage (from backend/):  python scripts/export_openapi.py > ../frontend/openapi.json
Builds the app with defaults and no .env, so no secrets or running services are needed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

if __name__ == "__main__":
    app = create_app(Settings(_env_file=None, embedding_backend="hashing"))
    json.dump(app.openapi(), sys.stdout, indent=2)
