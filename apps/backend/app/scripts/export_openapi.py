"""Export the FastAPI app's OpenAPI schema to the shared api-spec package.

This is the single source of truth consumed by Kubb to generate the typed
frontend API client. Run via: `uv run python -m app.scripts.export_openapi`.
"""

import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parents[4] / "packages" / "api-spec" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote OpenAPI spec to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
