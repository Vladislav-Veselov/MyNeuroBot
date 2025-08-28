# widget_registry.py
import json
from pathlib import Path
from typing import Optional, Dict, Any

WIDGETS_FILE = Path(__file__).resolve().parent / "widgets.json"

def resolve_widget(widget_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns:
    {
      "tenant_id": "acme",
      "user_data_dir": "/srv/app/userdata/acme",
      "allowed_origins": ["https://www.acme.com"]
    }
    """
    if not WIDGETS_FILE.exists():
        return None
    data = json.loads(WIDGETS_FILE.read_text(encoding="utf-8"))
    return data.get(widget_id)
