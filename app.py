# app.py
# Streamlit "stage clear" UX state machine demo
# - Shows ONLY map + overlay particles for exactly 3 seconds on clear
# - Then auto-transitions to a centered YES/NO modal
# - No balloons / no confetti / no other rich effects

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

import streamlit as st


# ----------------------------
# State model
# ----------------------------

@dataclass
class StageClearFX:
    """Transient 'clear FX' state.

    mission_key: identifier of the mission that was cleared
    started_at: monotonic timestamp (seconds)
    duration: effect duration (seconds)
    """
    mission_key: str
    started_at: float
    duration: float = 3.0

    def elapsed(self) -> float:
        return time.monotonic() - float(self.started_at)

    def is_active(self) -> bool:
        return self.elapsed() < float(self.duration)


def _get_fx() -> Optional[StageClearFX]:
    raw = st.session_state.get("stage_clear_fx")
    if not raw:
        return None
    try:
        return StageClearFX(
            mission_key=str(raw["mission_key"]),
            started_at=float(raw["started_at"]),
            duration=float(raw.get("duration", 3.0)),
        )
    except Exception:
        # Defensive: if state is corrupted, reset safely.
        st.session_state["stage_clear_fx"] = None
        return None


def _set_fx(fx: Optional[StageClearFX]) -> None:
    st.session_state["stage_clear_fx"] = (asdict(fx) if fx else None)


def _ensure_session_defaults() -> None:
    st.session_state.setdefault("mission_key", "M-001")
    st.session_state.setdefault("stage_index", 1)
    st.session_state.setdefault("stage_clear_fx", None)           # dict or None
    st.session_state.setdefault("stage_clear_modal", False)       # bool


# ----------------------------
# UI helpers
# ----------------------------

def _inject_base_css() -> None:
    """Global CSS. Keep it stable and minimal."""
    st.markdown(
        """
        <style>
        /* Remove default padding a bit for a 'game' feel */
        .block-container { padding-top: 1.5rem; }

        /* Map container */
        .map-wrap {
            position: relative;
            width: 100%;
            height: 520px;
            border-radius: 18px;
            overflow: hidden;
            background: radial-gradient(circle at 30% 25%, #25324a 0%, #111827 55%, #0b1020 100%);
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 12px 40px rgba(0,0,0,0.35);
        }

        /* Fake "map" grid */
        .map-grid {
            position: absolute;
            inset: 0;
            background-image:
              linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
            background-size: 44px 44px;
            opacity: 0.6;
            mix-blend-mode: screen;
        }

        /* Marker */
        .marker {
            position: absolute;
            left: 68%;
            top: 38%;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: 0 0 0 10px rgba(255,255,255,0.07), 0 0 28px rgba(255,255,255,0.55);
            transform: translate(-50%, -50%);
        }

        /* Particles overlay */
        .fx-overlay {
            position: absolute;
            inset: 0;
            pointer-events: none;
            overflow: hidden;
        }

        .spark {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.9);
            filter: blur(0.2px);
            animation: floatUp 3s linear forwards;
            opacity: 0;
        }

        @keyframes floatUp {
            0%   { transform: translateY(40px) scale(0.7); opacity: 0; }
            12%  { opacity: 0.95; }
            70%  { opacity: 0.75; }
            100% { transform: translateY(-520px) scale(1.35); opacity: 0; }
        }

        /* Center modal */
        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.55);
            z-index: 9998;
        }
        .modal-card {
            position: fixed;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: min(520px, calc(100vw - 48px));
            background: rgba(17,24,39,0.95);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px;
            padding: 22px 20px 18px 20px;
            z-index: 9999;
            box-shadow: 0 18px 60px rgba(0,0,0,0.55);
        }
        .modal-title {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 6px;
            color: rgba(255,255,255,0.95);
        }
        .modal-sub {
            font-size: 0.95rem;
            margin-bottom: 14px;
            color: rgba(255,255,255,0.78);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_map() -> None:
    """Map placeholder."""
    st.markdown(
        """
        <div class="map-wrap">
          <div class="map-grid"></div>
          <div class="marker"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_particles_overlay(seed: int = 7) -> None:
    """Render 'overlay particles' as pure HTML/CSS.

    This intentionally avoids canvas dependencies for stability.
    """
    # Deterministic-ish pattern from seed
    # We generate a fixed set of "sparks" with staggered delays.
    # The overlay is visible for 3 seconds because we only render it during FX.
    sparks_html = []
    # 26 sparks feels visible but not too heavy
    for i in range(26):
        left = (seed * (i * 37 + 13) * 0.013) % 100
        delay = (i * 0.06) % 0.9
        size = 6 + (i % 5) * 2
        blur = 0.0 + (i % 4) * 0.2
        alpha = 0.55 + (i % 6) * 0.07
        sparks_html.append(
            f"""
            <div class="spark" style="
              left: {left:.2f}%;
              bottom: -12px;
              width: {size}px; height: {size}px;
              filter: blur({blur}px);
              background: rgba(255,255,255,{alpha:.2f});
              animation-delay: {delay:.2f}s;
            "></div>
            """
        )

    st.markdown(
        f"""
        <div class="fx-overlay">
          {''.join(sparks_html)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_center_modal(title: str, subtitle: str) -> None:
    """Center modal wrapper (HTML only). Buttons are rendered via Streamlit below."""
    st.markdown(
        f"""
        <div class="modal-backdrop"></div>
        <div class="modal-card">
          <div class="modal-title">{title}</div>
          <div class="modal-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------
# State machine transitions
# ----------------------------

def _start_stage_clear(mission_key: str) -> None:
    _set_fx(StageClearFX(mission_key=mission_key, started_at=time.monotonic(), duration=3.0))
    st.session_state["stage_clear_modal"] = False


def _tick_state_machine() -> None:
    """Advance state machine based on time."""
    fx = _get_fx()
    if fx and (not fx.is_active()):
        # After 3 seconds, auto switch to modal, and clear fx state.
        _set_fx(None)
        st.session_state["stage_clear_modal"] = True


def _go_next_stage() -> None:
    st.session_state["stage_index"] = int(st.session_state.get("stage_index", 1)) + 1
    st.session_state["mission_key"] = f"M-{st.session_state['stage_index']:03d}"
    st.session_state["stage_clear_modal"] = False


def _return_to_map() -> None:
    st.session_state["stage_clear_modal"] = False


# ----------------------------
# App
# ----------------------------

def main() -> None:
    st.set_page_config(page_title="Stage Clear UX State Machine", layout="centered")
    _ensure_session_defaults()
    _inject_base_css()

    # Always tick transitions first (so UI reflects the latest state)
    _tick_state_machine()

    fx = _get_fx()
    modal = bool(st.session_state.get("stage_clear_modal", False))

    # CASE A) FX active: show ONLY "map + overlay particles" for 3 seconds
    if fx and fx.is_active():
        # Auto-refresh while FX is active, so the transition to modal happens without user interaction.
        st.autorefresh(interval=200, key="fx_refresh")  # ms
        _render_map()
        _render_particles_overlay(seed=hash(fx.mission_key) & 0xFFFF)
        return

    # CASE B) Modal active: map in background + centered modal (YES/NO)
    if modal:
        # We keep the map visible, but no other "rich" effects.
        _render_map()

        # Modal chrome (HTML)
        stage_idx = int(st.session_state.get("stage_index", 1))
        _render_center_modal(
            title=f"Stage {stage_idx} Cleared",
            subtitle="Go to the next stage?",
        )

        # Buttons under the modal card:
        # Streamlit buttons can't be placed inside arbitrary HTML reliably,
        # so we render them right after and rely on the fixed-position modal overlay above.
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.write("")
        with col2:
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("YES", use_container_width=True):
                    _go_next_stage()
                    st.rerun()
            with c_no:
                if st.button("NO", use_container_width=True):
                    _return_to_map()
                    st.rerun()
        with col3:
            st.write("")
        return

    # CASE C) Normal map state (not FX, not modal)
    st.title("Map")
    st.caption("Demo of a 'clear-only state machine': FX for 3 seconds → centered modal (YES/NO).")
    _render_map()

    # Normal UI controls (hidden during FX, absent during modal)
    st.divider()
    left, right = st.columns([1, 1])
    with left:
        st.write(f"**Current mission_key:** `{st.session_state['mission_key']}`")
        st.write(f"**Stage:** {int(st.session_state['stage_index'])}")
    with right:
        if st.button("Simulate Stage Clear", type="primary", use_container_width=True):
            _start_stage_clear(st.session_state["mission_key"])
            st.rerun()

    st.info(
        "Design notes:\n"
        "- During FX: ONLY map + particles are rendered.\n"
        "- After exactly 3 seconds: automatically switches to stage_clear_modal=True.\n"
        "- Modal: fixed-position centered overlay with YES/NO.\n"
        "- No balloons/confetti effects are used."
    )


if __name__ == "__main__":
    main()
