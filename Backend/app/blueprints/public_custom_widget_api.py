# app/blueprints/public_custom_widget_api.py
from flask import Blueprint, request, jsonify, make_response
from pathlib import Path

from chatbot_service import chatbot_service
from chatbot_status_manager import chatbot_status_manager
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager
from widget_registry import resolve_widget
from tenant_context import (
    set_user_data_dir, clear_user_data_dir,
    set_current_kb_id, clear_current_kb_id,
    set_current_tenant_id,
    set_widget_settings_override, clear_widget_settings_override,
    set_model_override, clear_model_override,  # NEW
)

public_custom_widget_api_bp = Blueprint("public_custom_widget_api", __name__)

def _match_origin(origin: str, widget) -> str | None:
    if not origin or not widget:
        return None
    allowed = widget.get("allowed_origins") or []
    # exact match only (keeps your existing security model)
    return origin if origin in allowed else None

def _corsify(resp, widget=None, status=200):
    """Attach CORS headers based on widget.allowed_origins and request Origin."""
    origin = request.headers.get("Origin")
    allow_origin = _match_origin(origin, widget)
    response = make_response(resp, status)
    if allow_origin:
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        # If you need cookies, also set:
        # response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

def _clamp_0_4(value):
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(4, v))

# Map UI "mode" to model ids
_MODE_TO_MODEL = {
    "lite": "gpt-4o-mini",
    "pro":  "gpt-4o",
}

@public_custom_widget_api_bp.route("/public/custom-widget/<widget_id>/chatbot", methods=["OPTIONS"])
def public_custom_chatbot_options(widget_id):
    widget = resolve_widget(widget_id)
    # Return an empty body (string), not a tuple
    return _corsify("", widget=widget, status=204)


@public_custom_widget_api_bp.route("/public/custom-widget/<widget_id>/chatbot", methods=["POST"])
def public_custom_chatbot(widget_id):
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id")

    # --- persona sliders (optional) ---
    tone   = _clamp_0_4(payload.get("tone"))
    humor  = _clamp_0_4(payload.get("humor"))
    brevity= _clamp_0_4(payload.get("brevity"))

    # --- model switch (optional) ---
    mode_raw  = (payload.get("mode") or "").strip().lower()   # "lite" | "pro"
    model_raw = (payload.get("model") or "").strip()          # "gpt-4o-mini" | "gpt-4o"
    chosen_model = None
    if model_raw in _MODE_TO_MODEL.values():
        chosen_model = model_raw
    elif mode_raw in _MODE_TO_MODEL:
        chosen_model = _MODE_TO_MODEL[mode_raw]

    widget = resolve_widget(widget_id)
    if not widget:
        return _corsify({"success": False, "error": "Widget not found"}, widget=None, status=404)

    # tenant context
    set_current_tenant_id(widget["tenant_id"])
    set_user_data_dir(Path(widget["user_data_dir"]))

    # per-request overrides
    overrides = {}
    if tone   is not None: overrides["tone"] = tone
    if humor  is not None: overrides["humor"] = humor
    if brevity is not None: overrides["brevity"] = brevity
    if overrides:
        set_widget_settings_override(overrides)

    if chosen_model:
        set_model_override(chosen_model)  # << apply model override just for this request

    try:
        if not message:
            return _corsify({"success": False, "error": "Message cannot be empty"}, widget=widget, status=400)

        if chatbot_status_manager.is_chatbot_stopped():
            return _corsify({
                "success": False,
                "error": chatbot_status_manager.get_stop_message(),
                "chatbot_stopped": True
            }, widget=widget, status=503)

        # 1) Ensure FIRST public interaction starts on "default"
        dialogue_storage = get_dialogue_storage()
        client_ip = ip_session_manager.get_client_ip()
        existing = dialogue_storage.get_session_by_ip(client_ip)
        if not existing:
            sid = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id="default",
                kb_name="База знаний по умолчанию"
            )
            chatbot_service.set_current_session_id(sid)

        # 2) __RESET__
        if message == "__RESET__":
            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id="default",
                kb_name="База знаний по умолчанию"
            )
            chatbot_service.set_current_session_id(new_session_id)
            return _corsify({
                "success": True,
                "response": "✅ Switched to default knowledge base (session-scoped).",
                "session_id": new_session_id
            }, widget=widget)

        # 3) KB password flow
        from kb_locator import find_kb_by_password_in_dir
        kb_id = find_kb_by_password_in_dir(Path(widget["user_data_dir"]), message)
        if kb_id:
            user_data_dir = Path(widget["user_data_dir"])
            kb_dir = user_data_dir / "knowledge_bases" / kb_id
            kb_name = kb_id
            kb_info_file = kb_dir / "kb_info.json"
            if kb_info_file.exists():
                import json
                info = json.loads(kb_info_file.read_text(encoding="utf-8"))
                kb_name = info.get("name", kb_id)

            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id=kb_id,
                kb_name=kb_name
            )
            chatbot_service.set_current_session_id(new_session_id)

            return _corsify({
                "success": True,
                "response": f"✅ Switched to knowledge base '{kb_name}' (session-scoped).",
                "session_id": new_session_id
            }, widget=widget)

        # 4) Normal chat
        response_text = chatbot_service.generate_response(message, session_id)
        return _corsify({
            "success": True,
            "response": response_text,
            "session_id": chatbot_service.get_current_session_id(),
            "model": chosen_model or "default"  # optional debug info
        }, widget=widget)

    finally:
        clear_model_override()              # << IMPORTANT: prevent leakage across requests
        clear_widget_settings_override()
        clear_user_data_dir()
        clear_current_kb_id()
