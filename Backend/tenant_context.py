# tenant_context.py
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

_current_user_data_dir: ContextVar[Optional[Path]] = ContextVar("current_user_data_dir", default=None)
_current_kb_id: ContextVar[Optional[str]] = ContextVar("current_kb_id", default=None)
_current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default="public-default")

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
