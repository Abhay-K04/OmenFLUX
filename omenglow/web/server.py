"""
OmenGlow Web Studio Backend Server
Lightweight, high-performance Flask API serving the next-generation Cyberpunk RGB Studio.
"""

import json
import logging
import os
import queue
import sys
import threading
import time

if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass
from typing import Dict, List, Optional, Tuple
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from ..hardware.shared_memory import SharedMemoryLighting
from ..hardware.handover import OlsHandoverManager, ControlOwner
from ..effects.engine import AnimationEngine, EffectType, parse_effect_type
from ..profiles.manager import Profile, ProfileManager
from ..state import StateManager

# Silence standard werkzeug HTTP request logs for ultra-clean console output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

base_dir = getattr(sys, '_MEIPASS', None)
if base_dir:
    candidate_static = [
        os.path.join(base_dir, "omenglow", "web", "static"),
        os.path.join(base_dir, "static"),
    ]
    static_dir = next((d for d in candidate_static if os.path.exists(d)), os.path.abspath(os.path.join(os.path.dirname(__file__), "static")))
    candidate_tmpl = [
        os.path.join(base_dir, "omenglow", "web", "templates"),
        os.path.join(base_dir, "templates"),
    ]
    template_dir = next((d for d in candidate_tmpl if os.path.exists(d)), os.path.abspath(os.path.join(os.path.dirname(__file__), "templates")))
else:
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))

app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
CORS(app)

# Global State & Controllers
shm = SharedMemoryLighting()
profiles_mgr = ProfileManager()
state_mgr = StateManager()

# Event queues for Server-Sent Events (SSE)
sse_subscribers: List[queue.Queue] = []
sse_lock = threading.Lock()
latest_colors: List[Tuple[int, int, int]] = [(255, 0, 80), (0, 200, 255), (140, 0, 255), (0, 255, 170)]

class AppState:
    def __init__(self):
        self.last_heartbeat: float = time.time() + 15.0  # 15s initial grace period for browser to open
        self.should_exit: bool = False

app_state = AppState()


def on_handover_state_changed(owner: ControlOwner):
    broadcast_sse({"type": "owner", "owner": owner.value})


handover = OlsHandoverManager(on_state_changed=on_handover_state_changed)


def on_engine_frame(colors: List[Tuple[int, int, int]]):
    global latest_colors
    latest_colors = colors
    broadcast_sse({"type": "frame", "colors": colors})


engine = AnimationEngine(shm=shm, on_frame=on_engine_frame)


def broadcast_sse(data: dict):
    payload = f"data: {json.dumps(data)}\n\n"
    with sse_lock:
        dead = []
        for q in sse_subscribers:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for d in dead:
            if d in sse_subscribers:
                sse_subscribers.remove(d)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    app_state.last_heartbeat = time.time()
    return jsonify({"status": "alive"})


@app.route("/api/exit", methods=["POST"])
@app.route("/api/app/quit", methods=["POST"])
def api_exit():
    app_state.should_exit = True
    return jsonify({"status": "exiting"})


@app.route("/api/status")
def get_status():
    all_profiles_data = profiles_mgr.get_all_profiles_data()
    all_profiles = [p["name"] for p in all_profiles_data]
    active_colors = shm.read_current_colors() or engine.zone_colors

    return jsonify({
        "owner": handover.current_owner.value,
        "ols_running": handover.is_ols_running(),
        "ols_pid": handover.get_ols_pid(),
        "ols_helper": handover.is_helper_running(),
        "effect": engine.effect.value,
        "speed": engine.speed,
        "brightness": engine.brightness,
        "zone_colors": engine.zone_colors,
        "live_colors": latest_colors,
        "profiles": all_profiles,
        "profiles_data": all_profiles_data,
        "active_profile": state_mgr.state.get("active_profile", ""),
        "autostart": state_mgr.is_autostart_registered(),
        "effects_list": [e.value for e in EffectType if e != EffectType.APEX_OVERDRIVE],
    })


@app.route("/api/settings/autostart", methods=["GET", "POST"])
def api_autostart():
    if request.method == "POST":
        data = request.json or {}
        enabled = bool(data.get("enabled", True))
        success = state_mgr.set_autostart(enabled)
        return jsonify({"success": success, "autostart": state_mgr.is_autostart_registered()})
    return jsonify({"autostart": state_mgr.is_autostart_registered()})


@app.route("/api/handover/take", methods=["POST"])
def handover_take():
    success = handover.take_control()
    if success:
        engine.resume()
    state_mgr.save_state({"owner": "OmenFLUX"})
    broadcast_sse({
        "type": "owner",
        "owner": handover.current_owner.value,
        "ols_pid": handover.get_ols_pid(),
        "ols_running": handover.is_ols_running()
    })
    return jsonify({
        "success": success,
        "owner": handover.current_owner.value,
        "ols_pid": handover.get_ols_pid(),
        "ols_running": handover.is_ols_running(),
    })


@app.route("/api/handover/release", methods=["POST"])
def handover_release():
    engine.pause()
    success = handover.handover_to_ols()
    state_mgr.save_state({"owner": "OMEN Light Studio"})
    broadcast_sse({
        "type": "owner",
        "owner": handover.current_owner.value,
        "ols_pid": handover.get_ols_pid(),
        "ols_running": handover.is_ols_running()
    })
    return jsonify({
        "success": success,
        "owner": handover.current_owner.value,
        "ols_pid": handover.get_ols_pid(),
        "ols_running": handover.is_ols_running(),
    })


@app.route("/api/color/zone", methods=["POST"])
def set_zone_color():
    data = request.json or {}
    zone = int(data.get("zone", 0))
    r = int(data.get("r", 255))
    g = int(data.get("g", 255))
    b = int(data.get("b", 255))

    engine.set_zone_color(zone, (r, g, b))
    if handover.current_owner != ControlOwner.OMENPULSE:
        handover.take_control()
        engine.resume()

    state_mgr.save_state({"zone_colors": engine.zone_colors, "owner": "OmenPulse"})
    return jsonify({"success": True, "zone_colors": engine.zone_colors})


@app.route("/api/color/all", methods=["POST"])
def set_all_colors():
    data = request.json or {}
    colors = data.get("colors", [])
    if colors and len(colors) >= 4:
        parsed = [(int(c[0]), int(c[1]), int(c[2])) for c in colors[:4]]
        engine.set_all_colors(parsed)
        if handover.current_owner != ControlOwner.OMENPULSE:
            handover.take_control()
            engine.resume()

        state_mgr.save_state({"zone_colors": engine.zone_colors, "owner": "OmenPulse"})
        return jsonify({"success": True, "zone_colors": engine.zone_colors})
    return jsonify({"success": False, "error": "Invalid colors payload"}), 400


@app.route("/api/reactive/trigger", methods=["POST"])
def api_reactive_trigger():
    data = request.json or {}
    zone = int(data.get("zone", 0))
    engine.trigger_key_press(zone)
    return jsonify({"success": True, "zone": zone})


@app.route("/api/effect", methods=["POST"])
def set_effect():
    data = request.json or {}
    if "effect" in data:
        eff = parse_effect_type(data["effect"])
        engine.set_effect(eff)

    if "speed" in data:
        engine.speed = max(0.1, min(5.0, float(data["speed"])))

    if "brightness" in data:
        engine.brightness = max(0.0, min(1.0, float(data["brightness"])))

    if handover.current_owner != ControlOwner.OMENPULSE:
        handover.take_control()
        engine.resume()

    state_mgr.save_state({
        "effect": engine.effect.value,
        "speed": engine.speed,
        "brightness": engine.brightness,
        "owner": "OmenPulse"
    })
    return jsonify({
        "success": True,
        "effect": engine.effect.value,
        "speed": engine.speed,
        "brightness": engine.brightness,
    })


@app.route("/api/profile/load", methods=["POST"])
def load_profile():
    data = request.json or {}
    name = data.get("name", "")
    profile = profiles_mgr.load_profile(name)
    if not profile:
        return jsonify({"success": False, "error": "Profile not found"}), 404

    engine.set_all_colors(profile.zone_colors)
    engine.set_effect(parse_effect_type(profile.effect))
    engine.speed = profile.speed
    engine.brightness = profile.brightness

    if handover.current_owner != ControlOwner.OMENPULSE:
        handover.take_control()
        engine.resume()

    state_mgr.save_state({
        "active_profile": name,
        "effect": engine.effect.value,
        "speed": engine.speed,
        "brightness": engine.brightness,
        "zone_colors": engine.zone_colors,
        "owner": "OmenPulse"
    })
    return jsonify({
        "success": True,
        "profile": profile.to_dict(),
    })


@app.route("/api/profile/save", methods=["POST"])
def save_profile():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "Name required"}), 400

    profile = Profile(
        name=name,
        effect=engine.effect.value,
        speed=engine.speed,
        brightness=engine.brightness,
        zone_colors=engine.zone_colors,
    )
    profiles_mgr.save_profile(profile)
    return jsonify({
        "success": True,
        "profile": profile.to_dict(),
        "profiles": profiles_mgr.list_profiles(),
        "profiles_data": profiles_mgr.get_all_profiles_data()
    })


@app.route("/api/profile/delete", methods=["POST"])
def delete_profile():
    data = request.json or {}
    name = data.get("name", "")
    deleted = profiles_mgr.delete_profile(name)
    return jsonify({
        "success": deleted,
        "profiles": profiles_mgr.list_profiles(),
        "profiles_data": profiles_mgr.get_all_profiles_data()
    })


@app.route("/api/stream")
def sse_stream():
    """Server-Sent Events pushing live 35-60 FPS frames and status changes to browser."""
    q = queue.Queue(maxsize=10)
    with sse_lock:
        sse_subscribers.append(q)

    def event_stream():
        # Send initial full status payload
        initial_status = {
            "type": "init",
            "owner": handover.current_owner.value,
            "ols_running": handover.is_ols_running(),
            "effect": engine.effect.value,
            "speed": engine.speed,
            "brightness": engine.brightness,
            "zone_colors": engine.zone_colors,
            "live_colors": latest_colors,
        }
        yield f"data: {json.dumps(initial_status)}\n\n"

        try:
            while True:
                data = q.get()
                yield data
        except GeneratorExit:
            with sse_lock:
                if q in sse_subscribers:
                    sse_subscribers.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


def start_server(port: int = 54321):
    """Start background animation engine, restore options chosen before shutdown, and launch Flask server."""
    # 1. Restore saved zone colors
    saved_colors = state_mgr.state.get("zone_colors")
    if saved_colors and len(saved_colors) == 4:
        engine.set_all_colors([(int(c[0]), int(c[1]), int(c[2])) for c in saved_colors])

    # 2. Restore saved effect
    saved_effect = state_mgr.state.get("effect", "Static")
    for e in EffectType:
        if e.value == saved_effect:
            engine.effect = e
            break

    # 3. Restore saved speed & brightness
    engine.speed = float(state_mgr.state.get("speed", 1.0))
    engine.brightness = float(state_mgr.state.get("brightness", 1.0))

    engine.start()

    # 4. Restore control ownership (defaults to OmenFLUX from the start)
    saved_owner = state_mgr.state.get("owner", "OmenFLUX")
    if saved_owner in ("OmenFLUX", "OmenPulse", "OmenGlow"):
        # Hardware WMI BIOS pre-initialization (if elevated) to prevent static freeze on cold boot
        try:
            from ..hardware.wmi_bios import WmiBiosLighting
            wmi = WmiBiosLighting()
            if wmi.is_available() and saved_colors:
                wmi.set_zone_colors([(int(c[0]), int(c[1]), int(c[2])) for c in saved_colors])
        except Exception:
            pass

        handover.take_control()
        engine.resume()
    else:
        engine.pause()
        handover.handover_to_ols()

    # 5. Sync autostart on Windows boot if user configured it
    if state_mgr.state.get("autostart", False):
        state_mgr.set_autostart(True)
    else:
        state_mgr.set_autostart(False)

    app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


def stop_server():
    """Clean exit."""
    engine.stop()
    handover.handover_to_ols()
    shm.close()
