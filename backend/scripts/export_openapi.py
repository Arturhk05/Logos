"""Write the API contract to frontend/openapi.json, from which the frontend generates its types."""

import json
from pathlib import Path

from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def main() -> None:
    schema = create_app().openapi()
    # Sorted keys and LF on every OS keep the file stable, so CI can diff it.
    OUTPUT.write_text(json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
