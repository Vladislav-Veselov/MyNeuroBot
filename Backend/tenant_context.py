# tenant_context.py
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, Dict

_current_user_data_dir: ContextVar[Optional[Path]] = ContextVar("current_user_data_dir", default=None)
_current_kb_id: ContextVar[Optional[str]] = ContextVar("current_kb_id", default=None)
_current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default="public-default")

# NEW: per-request widget persona override (tone/humor/brevity)
_current_widget_settings_override: ContextVar[Optional[Dict[str, int]]] = ContextVar(
    "current_widget_settings_override", default=None
)

# NEW: per-request model override
_current_model_override: ContextVar[Optional[str]] = ContextVar("current_model_override", default=None)

def set_user_data_dir(path: Path):
    _current_user_data_dir.set(Path(path))

def get_user_data_dir_override() -> Optional[Path]:
    return _current_user_data_dir.get()

def clear_user_data_dir():
    _current_user_data_dir.set(None)

def set_current_kb_id(kb_id: Optional[str]):
    _current_kb_id.set(kb_id)

def get_current_kb_id_override() -> Optional[str]:
    return _current_kb_id.get()

def clear_current_kb_id():
    _current_kb_id.set(None)

def set_current_tenant_id(tenant_id: str):
    _current_tenant_id.set(tenant_id)

def get_current_tenant_id() -> str:
    return _current_tenant_id.get()

# NEW: persona override helpers
def set_widget_settings_override(settings: Dict[str, int]):
    """
    Expected keys: tone, humor, brevity (0..4).
    """
    _current_widget_settings_override.set(settings or {})

def get_widget_settings_override() -> Optional[Dict[str, int]]:
    return _current_widget_settings_override.get()

def clear_widget_settings_override():
    _current_widget_settings_override.set(None)

# NEW: per-request model override
def set_model_override(model: Optional[str]):
    _current_model_override.set(model)

def get_model_override() -> Optional[str]:
    return _current_model_override.get()

def clear_model_override():
    _current_model_override.set(None)
