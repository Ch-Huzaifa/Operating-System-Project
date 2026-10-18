import html
import inspect
import time

import pandas as pd
import streamlit as st

from os_core import (
    STATES,
    create_process,
    get_available_actions,
    transition_process,
    fcfs,
    sjf,
    srtf,
    preemptive_priority,
    non_preemptive_priority,
    round_robin,
    multilevel_queue,
    multilevel_feedback_queue,
)

st.set_page_config(
    page_title="OS Lab · Interactive Simulator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Works on both old and new Streamlit versions (use_container_width vs width="stretch").
_STRETCH = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.button).parameters
    else {"use_container_width": True}
)

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------

CSS = """
<style>
.block-container{padding-top:1.2rem;max-width:1280px}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none}

.brand{display:flex;align-items:center;gap:.75rem}
.brand-logo{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,#4f46e5,#06b6d4);
  color:#fff;display:grid;place-items:center;font-weight:800;font-size:1.05rem;box-shadow:0 6px 16px rgba(79,70,229,.3)}
.brand-name{font-weight:800;font-size:1.2rem;color:#1e1b4b;line-height:1.1}
.brand-sub{font-size:.7rem;letter-spacing:.16em;color:#6b7280}

.page-title{margin:1.1rem 0 .3rem 0}
.page-title .tag{display:inline-block;font-size:.7rem;font-weight:700;letter-spacing:.14em;color:#4f46e5;
  background:#eef2ff;padding:.2rem .6rem;border-radius:999px}
.page-title h1{margin:.45rem 0 .1rem 0;font-size:2rem;color:#1e1b4b;padding:0}
.page-title p{margin:0;color:#6b7280}

.hero{background:linear-gradient(120deg,#312e81,#4f46e5 55%,#06b6d4);color:#fff;border-radius:22px;
  padding:2.4rem 2.2rem;margin:1rem 0 1.2rem 0;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;
  background:rgba(255,255,255,.12)}
.hero .tag{font-size:.7rem;letter-spacing:.18em;font-weight:700;opacity:.85}
.hero h1{color:#fff;margin:.4rem 0 .3rem 0;font-size:2.4rem;padding:0}
.hero p{margin:0;opacity:.9;max-width:560px}

.stat-card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:1rem 1.2rem;
  box-shadow:0 2px 8px rgba(15,23,42,.04)}
.stat-card span{display:block;font-size:.72rem;letter-spacing:.1em;color:#6b7280;font-weight:600}
.stat-card b{font-size:1.7rem;color:#1e1b4b}
.stat-card.accent b{color:#4f46e5}

.mod-card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:1.1rem 1.2rem;height:100%}
.mod-card h4{margin:0 0 .3rem 0;color:#1e1b4b}
.mod-card p{margin:0;color:#6b7280;font-size:.92rem}

.lifecycle{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin:.2rem 0 .4rem 0}
.life-node{padding:.35rem .8rem;border-radius:999px;color:#fff;font-size:.78rem;font-weight:700;letter-spacing:.05em}
.life-arrow{color:#9ca3af;font-weight:700}
.life-note{font-size:.82rem;color:#6b7280;margin-top:.2rem}

.clock-card{background:#1e1b4b;color:#fff;border-radius:14px;padding:.55rem 1rem;text-align:center}
.clock-card span{display:block;font-size:.65rem;letter-spacing:.16em;opacity:.7}
.clock-card b{font-size:1.5rem}

.kanban{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:.7rem;margin:.6rem 0 1rem 0;overflow-x:auto}
.kcol{background:#f1f0ea;border-radius:14px;padding:.6rem;min-height:130px}
.khead{display:flex;justify-content:space-between;align-items:center;font-size:.72rem;font-weight:800;
  letter-spacing:.1em;color:#374151;border-bottom:3px solid;padding-bottom:.4rem;margin-bottom:.5rem}
.khead b{background:#fff;border-radius:999px;padding:0 .5rem}
.kcard{background:#fff;border-radius:10px;padding:.5rem .6rem;margin-bottom:.45rem;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kcard .kid{font-weight:800;color:#1e1b4b;font-size:.9rem}
.kcard .kname{color:#6b7280;font-size:.78rem;word-break:break-word}
.kbar{height:6px;background:#e5e7eb;border-radius:99px;margin-top:.4rem;overflow:hidden}
.kbar i{display:block;height:100%;background:linear-gradient(90deg,#4f46e5,#06b6d4)}
.kmeta{font-size:.7rem;color:#9ca3af;margin-top:.2rem}
.kempty{color:#b8b5a8;font-size:.8rem;text-align:center;padding:.8rem 0}

.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.3rem 0 .6rem 0}
.chip{border-radius:999px;padding:.2rem .7rem;font-size:.78rem;font-weight:700;color:#fff}

.pcb{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:.4rem 1rem}
.pcb-row{display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px dashed #e5e7eb;font-size:.9rem}
.pcb-row:last-child{border-bottom:none}
.pcb-row span{color:#6b7280}
.pcb-row b{color:#1e1b4b;text-align:right}

.gantt-wrap{overflow-x:auto;padding:.6rem .2rem 1.6rem .2rem;background:#fff;border:1px solid #e5e7eb;border-radius:14px}
.gantt{display:flex;min-width:100%;padding:0 1.4rem 0 .6rem}
.g-col{position:relative}
.g-cell{height:50px;display:grid;place-items:center;color:#fff;font-weight:800;font-size:.9rem;
  border-right:2px solid #fff;border-radius:6px}
.g-idle{background:repeating-linear-gradient(45deg,#e5e7eb,#e5e7eb 6px,#f3f4f6 6px,#f3f4f6 12px);color:#9ca3af;font-size:.7rem}
.g-tick{position:absolute;top:56px;left:-2px;font-size:.75rem;color:#4b5563;font-weight:600}
.g-tick.end{left:auto;right:-6px}

.splash{max-width:420px;margin:12vh auto 1rem auto;text-align:center;background:#fff;border-radius:22px;
  padding:2.2rem 1.5rem;box-shadow:0 20px 50px rgba(79,70,229,.15)}
.ring{width:64px;height:64px;margin:0 auto 1rem auto;border-radius:50%;border:5px solid #e0e7ff;border-top-color:#4f46e5;
  animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.splash h2{margin:0;color:#1e1b4b;letter-spacing:.12em}
.splash p{margin:.3rem 0 0 0;color:#6b7280;font-size:.9rem}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def md(text: str):
    """Render single-line-joined HTML (avoids markdown code-block issues)."""
    st.markdown("".join(line.strip() for line in text.strip().splitlines()), unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x))


STATE_COLORS = {
    "New": "#64748b",
    "Ready": "#d97706",
    "Running": "#16a34a",
    "Waiting": "#7c3aed",
    "Terminated": "#be123c",
}

GANTT_PALETTE = [
    "#4f46e5", "#0891b2", "#d97706", "#16a34a", "#db2777", "#7c3aed",
    "#ea580c", "#0d9488", "#2563eb", "#ca8a04", "#9333ea", "#dc2626",
]


# --------------------------------------------------------------------------
# Startup splash (once per browser session)
# --------------------------------------------------------------------------

def show_startup_splash():
    if st.session_state.get("startup_seen", False):
        return
    holder = st.empty()
    holder.markdown(
        '<div class="splash"><div class="ring"></div><h2>OS LAB</h2>'
        "<p>Setting up your interactive learning environment…</p></div>",
        unsafe_allow_html=True,
    )
    progress = st.progress(0, text="Booting simulator...")
    for value, message in [
        (22, "Loading core interface..."),
        (48, "Initializing process manager..."),
        (73, "Preparing scheduling modules..."),
        (100, "System ready."),
    ]:
        progress.progress(value, text=message)
        time.sleep(0.22)
    time.sleep(0.25)
    progress.empty()
    holder.empty()
    st.session_state.startup_seen = True


show_startup_splash()


# --------------------------------------------------------------------------
# Top bar + navigation
# --------------------------------------------------------------------------

SECTIONS = ["Home", "Processes", "CPU Scheduling", "Process Synchronization"]

brand_col, nav_col = st.columns([1.1, 2.6], vertical_alignment="center")
with brand_col:
    md(
        """
        <div class="brand">
          <div class="brand-logo">OS</div>
          <div><div class="brand-name">OS Lab</div><div class="brand-sub">INTERACTIVE SIMULATOR</div></div>
        </div>
        """
    )
with nav_col:
    section = st.radio(
        "Navigation",
        SECTIONS,
        horizontal=True,
        key="main_navigation",
        label_visibility="collapsed",
    )
st.divider()


def page_title(tag: str, title: str, subtitle: str):
    md(
        f"""
        <div class="page-title"><span class="tag">{tag}</span>
        <h1>{title}</h1><p>{subtitle}</p></div>
        """
    )


# --------------------------------------------------------------------------
# HOME
# --------------------------------------------------------------------------

def render_home():
    md(
        """
        <div class="hero">
          <div class="tag">INTERACTIVE LEARNING PLATFORM</div>
          <h1>Operating System Lab</h1>
          <p>Explore process management and CPU scheduling through hands-on simulations.</p>
        </div>
        """
    )
    a, b, c = st.columns(3)
    with a:
        md('<div class="stat-card"><span>AVAILABLE MODULES</span><b>2</b></div>')
    with b:
        md('<div class="stat-card"><span>CPU ALGORITHMS</span><b>7</b></div>')
    with c:
        md('<div class="stat-card accent"><span>NEXT MODULE</span><b>Synchronization</b></div>')
    st.write("")
    m1, m2 = st.columns(2)
    with m1:
        md(
            '<div class="mod-card"><h4>🧩 Processes</h4><p>Create processes, step through the '
            "lifecycle manually or let Auto Run drive the CPU.</p></div>"
        )
    with m2:
        md(
            '<div class="mod-card"><h4>⏱️ CPU Scheduling</h4><p>Run FCFS, SJF, SRTF, Priority, '
            "Round Robin, MLQ and MLFQ and read the Gantt chart.</p></div>"
        )
    st.write("")
    st.info("Choose **Processes** to explore process states, or **CPU Scheduling** to run an algorithm.")


# --------------------------------------------------------------------------
# PROCESSES
# --------------------------------------------------------------------------

def advance_process():
    """Advance the educational FCFS-style process lifecycle by one tick."""
    items = st.session_state.os_processes
    if not items:
        return

    new_process = next((p for p in items if p["state"] == "New"), None)
    if new_process:
        transition_process(new_process, "admit")
        st.session_state.process_clock += 1
        return

    running = next((p for p in items if p["state"] == "Running"), None)
    if running:
        transition_process(running, "execute_unit")
        st.session_state.process_clock += 1
        return

    ready = next((p for p in items if p["state"] == "Ready"), None)
    if ready:
        transition_process(ready, "dispatch")
        st.session_state.process_clock += 1
        return

    st.session_state.process_auto_run = False


def apply_manual_action(process, action):
    items = st.session_state.os_processes
    if action == "dispatch" and any(p["state"] == "Running" for p in items):
        st.session_state.flash = ("warning", "CPU is busy. Preempt or finish the running process first.")
        return
    transition_process(process, action)


def lifecycle_html() -> str:
    parts = []
    nodes = [("NEW", "New"), ("READY", "Ready"), ("RUNNING", "Running"), ("TERMINATED", "Terminated")]
    for i, (label, state) in enumerate(nodes):
        if i:
            parts.append('<span class="life-arrow">→</span>')
        parts.append(f'<span class="life-node" style="background:{STATE_COLORS[state]}">{label}</span>')
    return (
        f'<div class="lifecycle">{"".join(parts)}</div>'
        '<div class="life-note">Running → Waiting on an I/O request · Waiting → Ready when I/O completes</div>'
    )


def board_html(items) -> str:
    cols = []
    for state in STATES:
        cards = [p for p in items if p["state"] == state]
        body = ""
        for p in cards:
            burst = max(1, p["burst_time"])
            pct = int((burst - p["remaining_time"]) / burst * 100)
            body += (
                f'<div class="kcard"><div class="kid">{esc(p["pid"])}</div>'
                f'<div class="kname">{esc(p["name"])}</div>'
                f'<div class="kbar"><i style="width:{pct}%"></i></div>'
                f'<div class="kmeta">{p["remaining_time"]} / {p["burst_time"]} left</div></div>'
            )
        if not body:
            body = '<div class="kempty">empty</div>'
        cols.append(
            f'<div class="kcol"><div class="khead" style="border-color:{STATE_COLORS[state]}">'
            f"<span>{state.upper()}</span><b>{len(cards)}</b></div>{body}</div>"
        )
    return f'<div class="kanban">{"".join(cols)}</div>'


ACTION_LABELS = {
    "admit": "Admit to Ready",
    "dispatch": "Dispatch to Running",
    "execute_unit": "Execute 1 CPU Unit",
    "request_io": "Request I/O",
    "complete_io": "Complete I/O",
    "preempt": "Preempt to Ready",
    "terminate": "Terminate Process",
}


def render_processes():
    page_title(
        "PROCESS MANAGEMENT",
        "Processes &amp; States",
        "Manage multiple processes with manual stepping and automatic execution.",
    )

    for key, default in [
        ("os_processes", []),
        ("next_pid", 1),
        ("process_auto_run", False),
        ("process_clock", 0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    flash = st.session_state.pop("flash", None)
    if flash:
        getattr(st, flash[0])(flash[1])

    top_left, top_right = st.columns([1, 1.15], gap="large")

    with top_left:
        with st.form("create_process_form", clear_on_submit=True):
            st.markdown("#### Create a process")
            process_name = st.text_input("Process name", placeholder="e.g. Browser")
            process_burst = st.number_input("CPU burst time", min_value=1, max_value=999, value=5, step=1)
            create_clicked = st.form_submit_button("＋ Create Process", type="primary", **_STRETCH)

    with top_right:
        st.markdown("#### Process lifecycle")
        md(lifecycle_html())

    if create_clicked:
        pid = f"P{st.session_state.next_pid}"
        st.session_state.os_processes.append(
            create_process(pid, process_name.strip() or pid, int(process_burst))
        )
        st.session_state.next_pid += 1
        st.session_state.process_auto_run = False
        st.session_state.flash = ("success", f"{pid} created successfully in New state.")
        st.rerun()

    auto = st.session_state.process_auto_run

    # The fragment only ticks every second while Auto Run is active.
    @st.fragment(run_every=1.0 if auto else None)
    def process_dashboard():
        items = st.session_state.os_processes

        st.markdown("#### Simulation controls")
        clock_c, a, b, c = st.columns([1.1, 1, 1, 1], vertical_alignment="center")

        with clock_c:
            md(f'<div class="clock-card"><span>CLOCK</span><b>{st.session_state.process_clock}</b></div>')
        with a:
            if st.button("⏭️ Next Step", disabled=not items, **_STRETCH):
                st.session_state.process_auto_run = False
                advance_process()
                st.rerun(scope="app")
        with b:
            if st.button(
                "▶️ Auto Run",
                type="primary",
                disabled=(
                    not items
                    or st.session_state.process_auto_run
                    or all(p["state"] in ("Terminated", "Waiting") for p in items)
                ),
                **_STRETCH,
            ):
                st.session_state.process_auto_run = True
                st.rerun(scope="app")
        with c:
            if st.button("⏸️ Pause", disabled=not st.session_state.process_auto_run, **_STRETCH):
                st.session_state.process_auto_run = False
                st.rerun(scope="app")

        # Automatic simulation: one tick per fragment refresh.
        if st.session_state.process_auto_run:
            advance_process()
            items = st.session_state.os_processes
            if not any(p["state"] in ("New", "Ready", "Running") for p in items):
                st.session_state.process_auto_run = False
                st.rerun(scope="app")  # re-create the fragment without the timer

        if st.session_state.process_auto_run:
            st.info("Auto Run is active. Use Pause to stop the simulation.")
        elif items:
            st.caption("Paused. Use Next Step or Auto Run to continue.")

        if not items:
            st.info("Create your first process above to start.")
            return

        running = next((p for p in items if p["state"] == "Running"), None)
        if running:
            st.success(f"CPU is executing: {running['pid']} · {running['name']}")
        else:
            st.info("CPU is idle. A Ready process can be dispatched.")

        st.markdown("#### State board")
        md(board_html(items))

        left, right = st.columns([1.5, 1], gap="large")

        with left:
            st.markdown("#### Live process table")
            rows = [
                {
                    "PID": p["pid"],
                    "Name": p["name"],
                    "State": p["state"],
                    "CPU Burst": p["burst_time"],
                    "Remaining": p["remaining_time"],
                    "Last Transition": p["last_transition"],
                }
                for p in items
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, **_STRETCH)

            st.markdown("#### Process state summary")
            chips = "".join(
                f'<span class="chip" style="background:{STATE_COLORS[s]}">{s}: '
                f'{sum(p["state"] == s for p in items)}</span>'
                for s in STATES
            )
            md(f'<div class="chips">{chips}</div>')

        with right:
            st.markdown("#### Individual process controls")
            selected_pid = st.selectbox(
                "Select process",
                options=[p["pid"] for p in items],
                format_func=lambda pid: next(
                    f'{p["pid"]} · {p["name"]} ({p["state"]})' for p in items if p["pid"] == pid
                ),
                key="process_selected_pid",
            )
            selected = next(p for p in items if p["pid"] == selected_pid)

            actions = get_available_actions(selected["state"])
            if actions:
                for action in actions:
                    if st.button(
                        ACTION_LABELS[action],
                        key=f"manual_{selected_pid}_{action}",
                        **_STRETCH,
                    ):
                        st.session_state.process_auto_run = False
                        apply_manual_action(selected, action)
                        st.rerun(scope="app")
            else:
                st.info("This process has terminated.")

            st.markdown("#### Process Control Block")
            md(
                f"""
                <div class="pcb">
                  <div class="pcb-row"><span>PID</span><b>{esc(selected["pid"])}</b></div>
                  <div class="pcb-row"><span>Name</span><b>{esc(selected["name"])}</b></div>
                  <div class="pcb-row"><span>State</span><b style="color:{STATE_COLORS[selected["state"]]}">{selected["state"]}</b></div>
                  <div class="pcb-row"><span>CPU Burst</span><b>{selected["burst_time"]}</b></div>
                  <div class="pcb-row"><span>Remaining</span><b>{selected["remaining_time"]}</b></div>
                  <div class="pcb-row"><span>Last Transition</span><b>{esc(selected["last_transition"])}</b></div>
                </div>
                """
            )

        st.divider()
        if st.button("🗑️ Reset All Processes", type="secondary"):
            st.session_state.process_auto_run = False
            st.session_state.os_processes = []
            st.session_state.next_pid = 1
            st.session_state.process_clock = 0
            st.session_state.pop("process_selected_pid", None)
            st.rerun(scope="app")

    process_dashboard()


# --------------------------------------------------------------------------
# PROCESS SYNCHRONIZATION
# --------------------------------------------------------------------------

def render_sync():
    page_title("CONCURRENCY", "Process Synchronization", "This module is reserved for a future development phase.")
    st.info("This module is reserved for the next development phase.")


# --------------------------------------------------------------------------
# CPU SCHEDULING
# --------------------------------------------------------------------------

ALGO_OPTIONS = {
    "Preemptive": [
        "SRTF (Preemptive SJF)",
        "Priority Scheduling",
        "Round Robin (RR)",
        "Multilevel Queue (MLQ)",
        "Multilevel Feedback Queue (MLFQ)",
    ],
    "Non-Preemptive": ["FCFS", "SJF", "Priority Scheduling"],
}

ALGO_INFO = {
    "SRTF (Preemptive SJF)": "The process with the shortest remaining CPU time runs first.",
    "Priority Scheduling": "The process with the highest priority runs first. Smaller priority number means higher priority.",
    "Round Robin (RR)": "Each ready process receives a fixed time quantum in turn.",
    "FCFS": "Processes run in order of arrival.",
    "SJF": "The available process with the shortest burst time runs first.",
    "Multilevel Queue (MLQ)": "Processes are assigned to fixed queues, each with its own priority. "
    "(Q1: RR quantum 2, Q2: RR quantum 4, Q3: FCFS; higher queue preempts lower.)",
    "Multilevel Feedback Queue (MLFQ)": "Processes start in their given queue and move down when they use up a full "
    "time quantum. (Q1: RR quantum 2, Q2: RR quantum 4, Q3: FCFS.)",
}


def default_table(n: int, use_priority: bool, use_queue: bool) -> pd.DataFrame:
    data = {
        "Process": [f"P{i + 1}" for i in range(n)],
        "Arrival Time": [0] + [i for i in range(1, n)],
        "Burst Time": [5, 3, 8, 2][:n] if n <= 4 else [5] + [3 for _ in range(n - 1)],
    }
    if use_priority:
        data["Priority"] = [2, 1, 3, 2][:n] if n <= 4 else [2 for _ in range(n)]
    if use_queue:
        data["Queue"] = [1, 2, 1, 3][:n] if n <= 4 else [1 + (i % 3) for i in range(n)]
    return pd.DataFrame(data)


def build_processes(edited: pd.DataFrame, use_priority: bool, use_queue: bool) -> list[dict]:
    if edited["Process"].isnull().any() or (edited["Process"].astype(str).str.strip() == "").any():
        raise ValueError("Process name cannot be empty.")
    if edited["Process"].astype(str).str.strip().duplicated().any():
        raise ValueError("Process names must be unique.")
    if edited[["Arrival Time", "Burst Time"]].isnull().any().any():
        raise ValueError("Arrival Time and Burst Time cannot be empty.")
    if (edited["Arrival Time"] < 0).any():
        raise ValueError("Arrival Time cannot be negative.")
    if (edited["Burst Time"] <= 0).any():
        raise ValueError("Burst Time must be greater than zero.")
    if use_priority and edited["Priority"].isnull().any():
        raise ValueError("Priority cannot be empty.")
    if use_queue and edited["Queue"].isnull().any():
        raise ValueError("Queue cannot be empty.")

    numeric_cols = ["Arrival Time", "Burst Time"] + (["Priority"] if use_priority else []) + (["Queue"] if use_queue else [])
    for col in numeric_cols:
        if (edited[col] % 1 != 0).any():
            raise ValueError(f"{col} must contain whole numbers only.")

    processes = []
    for _, row in edited.iterrows():
        p = {"pid": str(row["Process"]).strip(), "at": int(row["Arrival Time"]), "bt": int(row["Burst Time"])}
        if use_priority:
            p["priority"] = int(row["Priority"])
        if use_queue:
            q = int(row["Queue"])
            if q not in (1, 2, 3):
                raise ValueError("Queue must be 1, 2, or 3.")
            p["queue"] = q
        processes.append(p)
    return processes


def run_algorithm(mode, algorithm, processes, quantum):
    if algorithm == "FCFS":
        return fcfs(processes)
    if algorithm == "SJF":
        return sjf(processes)
    if algorithm == "SRTF (Preemptive SJF)":
        return srtf(processes)
    if algorithm == "Priority Scheduling" and mode == "Preemptive":
        return preemptive_priority(processes)
    if algorithm == "Priority Scheduling":
        return non_preemptive_priority(processes)
    if algorithm == "Multilevel Queue (MLQ)":
        return multilevel_queue(processes)
    if algorithm == "Multilevel Feedback Queue (MLFQ)":
        return multilevel_feedback_queue(processes)
    return round_robin(processes, int(quantum))


def gantt_html(blocks, colors) -> str:
    cols = []
    last = len(blocks) - 1
    for i, b in enumerate(blocks):
        dur = b["end"] - b["start"]
        if b["pid"] == "IDLE":
            cell = '<div class="g-cell g-idle">IDLE</div>'
        else:
            cell = f'<div class="g-cell" style="background:{colors[b["pid"]]}">{esc(b["pid"])}</div>'
        ticks = f'<span class="g-tick">{b["start"]}</span>'
        if i == last:
            ticks += f'<span class="g-tick end">{b["end"]}</span>'
        cols.append(f'<div class="g-col" style="flex:{dur} 0 48px">{cell}{ticks}</div>')
    return f'<div class="gantt-wrap"><div class="gantt">{"".join(cols)}</div></div>'


def render_scheduling():
    page_title(
        "CPU MANAGEMENT",
        "CPU Scheduling",
        "Choose a scheduling type, enter process details, and calculate the results.",
    )

    left, right = st.columns([1, 2.2], gap="large")

    with left:
        st.markdown("#### 1 · Configure")
        mode = st.radio("Scheduling type", ["Preemptive", "Non-Preemptive"], horizontal=True)
        algorithm = st.selectbox("Choose algorithm", ALGO_OPTIONS[mode])
        st.caption(ALGO_INFO[algorithm])
        n = st.number_input("Number of processes", min_value=1, max_value=12, value=4, step=1)
        quantum = None
        if algorithm == "Round Robin (RR)":
            quantum = st.number_input("Time Quantum", min_value=1, value=2, step=1)

    use_priority = algorithm == "Priority Scheduling"
    use_queue = algorithm in ("Multilevel Queue (MLQ)", "Multilevel Feedback Queue (MLFQ)")

    with right:
        with st.form("process_form"):
            st.markdown("#### 2 · Process input")
            edited = st.data_editor(
                default_table(int(n), use_priority, use_queue),
                num_rows="fixed",
                key=f"editor_{n}_{mode}_{algorithm}",
                **_STRETCH,
            )
            submitted = st.form_submit_button("▶ Calculate Schedule", type="primary", **_STRETCH)

    if submitted:
        try:
            processes = build_processes(edited, use_priority, use_queue)
            result = run_algorithm(mode, algorithm, processes, quantum)
            df = pd.DataFrame(result["rows"])

            st.success("Scheduling completed successfully.")

            m1, m2, m3 = st.columns(3)
            m1.metric("Average Waiting Time", f"{df['WT'].mean():.2f}")
            m2.metric("Average Turnaround Time", f"{df['TAT'].mean():.2f}")
            m3.metric("Average Response Time", f"{df['RT'].mean():.2f}")

            st.markdown("#### Gantt Chart")
            colors = {pid: GANTT_PALETTE[i % len(GANTT_PALETTE)] for i, pid in enumerate(df["Process"])}
            md(gantt_html(result["gantt"], colors))

            st.markdown("#### Process Results")
            st.dataframe(df, hide_index=True, **_STRETCH)
        except Exception as e:
            st.error(f"Please check your inputs: {e}")

    with st.expander("Formula reference"):
        st.markdown(
            """
- **Turnaround Time (TAT) = Completion Time (CT) − Arrival Time (AT)**
- **Waiting Time (WT) = Turnaround Time (TAT) − Burst Time (BT)**
- **Response Time (RT) = First Start Time − Arrival Time (AT)**
- **Priority:** smaller priority number means higher priority.
"""
        )


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------

if section == "Home":
    render_home()
elif section == "Processes":
    render_processes()
elif section == "Process Synchronization":
    render_sync()
else:
    render_scheduling()
