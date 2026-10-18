"""Core logic for the OS Lab simulator.

Contains
  1. the process state machine (New -> Ready -> Running -> Waiting -> Terminated)
  2. all CPU scheduling algorithms

Every scheduling function takes a list of dicts:
    {"pid": str, "at": int, "bt": int, "priority": int (optional), "queue": int (optional)}
and returns:
    {"gantt": [{"pid", "start", "end"}, ...], "rows": [{"Process", "AT", "BT", ..., "CT", "TAT", "WT", "RT"}, ...]}
Idle CPU time is shown in the Gantt chart with the pid "IDLE".
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Process state machine
# --------------------------------------------------------------------------

STATES = ["New", "Ready", "Running", "Waiting", "Terminated"]

# state -> {action: next_state}. next_state None means "decided at run time".
_TRANSITIONS = {
    "New": {"admit": "Ready"},
    "Ready": {"dispatch": "Running", "terminate": "Terminated"},
    "Running": {
        "execute_unit": None,
        "request_io": "Waiting",
        "preempt": "Ready",
        "terminate": "Terminated",
    },
    "Waiting": {"complete_io": "Ready", "terminate": "Terminated"},
    "Terminated": {},
}


def create_process(pid: str, name: str, burst: int) -> dict:
    return {
        "pid": pid,
        "name": name,
        "state": "New",
        "burst_time": int(burst),
        "remaining_time": int(burst),
        "last_transition": "Created",
    }


def get_available_actions(state: str) -> list[str]:
    return list(_TRANSITIONS.get(state, {}).keys())


def transition_process(process: dict, action: str) -> dict:
    old = process["state"]
    if action not in _TRANSITIONS.get(old, {}):
        raise ValueError(f"Action '{action}' is not allowed in state {old}.")

    if action == "execute_unit":
        process["remaining_time"] = max(0, process["remaining_time"] - 1)
        if process["remaining_time"] == 0:
            process["state"] = "Terminated"
            process["last_transition"] = "Running → Terminated (burst complete)"
        else:
            process["last_transition"] = "Executed 1 CPU unit"
        return process

    new = _TRANSITIONS[old][action]
    process["state"] = new
    process["last_transition"] = f"{old} → {new}"
    return process


# --------------------------------------------------------------------------
# Scheduling helpers
# --------------------------------------------------------------------------

class _Gantt:
    def __init__(self):
        self.blocks: list[dict] = []

    def add(self, pid, start, end):
        if end <= start:
            return
        last = self.blocks[-1] if self.blocks else None
        if last and last["pid"] == pid and last["end"] == start:
            last["end"] = end
        else:
            self.blocks.append({"pid": pid, "start": start, "end": end})


def _prep(processes):
    return [
        {
            "pid": p["pid"],
            "at": p["at"],
            "bt": p["bt"],
            "priority": p.get("priority"),
            "queue": p.get("queue"),
            "idx": i,
            "rem": p["bt"],
            "start": None,
            "ct": None,
        }
        for i, p in enumerate(processes)
    ]


def _result(procs, gantt):
    rows = []
    for p in procs:
        tat = p["ct"] - p["at"]
        row = {"Process": p["pid"], "AT": p["at"], "BT": p["bt"]}
        if p["priority"] is not None:
            row["Priority"] = p["priority"]
        if p["queue"] is not None:
            row["Queue"] = p["queue"]
        row.update(
            {
                "CT": p["ct"],
                "TAT": tat,
                "WT": tat - p["bt"],
                "RT": p["start"] - p["at"],
            }
        )
        rows.append(row)
    return {"gantt": gantt.blocks, "rows": rows}


# --------------------------------------------------------------------------
# Non-preemptive algorithms
# --------------------------------------------------------------------------

def _non_preemptive(processes, keyfn):
    procs = _prep(processes)
    g = _Gantt()
    t, done, n = 0, 0, len(procs)
    while done < n:
        avail = [p for p in procs if p["ct"] is None and p["at"] <= t]
        if not avail:
            nxt = min(p["at"] for p in procs if p["ct"] is None)
            g.add("IDLE", t, nxt)
            t = nxt
            continue
        p = min(avail, key=keyfn)
        p["start"] = t
        g.add(p["pid"], t, t + p["bt"])
        t += p["bt"]
        p["rem"] = 0
        p["ct"] = t
        done += 1
    return _result(procs, g)


def fcfs(processes):
    return _non_preemptive(processes, lambda p: (p["at"], p["idx"]))


def sjf(processes):
    return _non_preemptive(processes, lambda p: (p["bt"], p["at"], p["idx"]))


def non_preemptive_priority(processes):
    return _non_preemptive(
        processes, lambda p: (p["priority"], p["at"], p["idx"])
    )


# --------------------------------------------------------------------------
# Preemptive algorithms (decision every time unit)
# --------------------------------------------------------------------------

def _preemptive(processes, primary):
    procs = _prep(processes)
    g = _Gantt()
    t, done, n = 0, 0, len(procs)
    current = None
    while done < n:
        avail = [p for p in procs if p["ct"] is None and p["at"] <= t]
        if not avail:
            nxt = min(p["at"] for p in procs if p["ct"] is None)
            g.add("IDLE", t, nxt)
            t = nxt
            current = None
            continue
        pick = min(
            avail,
            key=lambda p: (
                primary(p),
                0 if p is current else 1,  # avoid needless switching on ties
                p["at"],
                p["idx"],
            ),
        )
        if pick["start"] is None:
            pick["start"] = t
        g.add(pick["pid"], t, t + 1)
        pick["rem"] -= 1
        t += 1
        if pick["rem"] == 0:
            pick["ct"] = t
            done += 1
            current = None
        else:
            current = pick
    return _result(procs, g)


def srtf(processes):
    return _preemptive(processes, lambda p: p["rem"])


def preemptive_priority(processes):
    return _preemptive(processes, lambda p: p["priority"])


# --------------------------------------------------------------------------
# Round Robin
# --------------------------------------------------------------------------

def round_robin(processes, quantum: int):
    procs = _prep(processes)
    g = _Gantt()
    n = len(procs)
    pending = sorted(procs, key=lambda p: (p["at"], p["idx"]))
    ptr = 0
    queue: list[dict] = []
    t, done = 0, 0

    def admit(now):
        nonlocal ptr
        while ptr < n and pending[ptr]["at"] <= now:
            queue.append(pending[ptr])
            ptr += 1

    while done < n:
        admit(t)
        if not queue:
            nxt = pending[ptr]["at"]
            g.add("IDLE", t, nxt)
            t = nxt
            continue
        p = queue.pop(0)
        if p["start"] is None:
            p["start"] = t
        run = min(quantum, p["rem"])
        g.add(p["pid"], t, t + run)
        t += run
        p["rem"] -= run
        admit(t)  # new arrivals queue up before the preempted process
        if p["rem"] > 0:
            queue.append(p)
        else:
            p["ct"] = t
            done += 1
    return _result(procs, g)


# --------------------------------------------------------------------------
# Multilevel Queue / Multilevel Feedback Queue
#   Queue 1 : Round Robin, quantum 2   (highest priority)
#   Queue 2 : Round Robin, quantum 4
#   Queue 3 : FCFS                     (lowest priority)
#   A process in a higher queue always preempts a lower queue.
#   MLQ  : a process stays in its assigned queue.
#   MLFQ : a process that uses its full quantum is demoted one level.
# --------------------------------------------------------------------------

QUEUE_QUANTUM = {1: 2, 2: 4, 3: None}


def _multilevel(processes, feedback: bool):
    procs = _prep(processes)
    g = _Gantt()
    n = len(procs)
    level = {p["idx"]: p["queue"] for p in procs}
    queues = {1: [], 2: [], 3: []}
    pending = sorted(procs, key=lambda p: (p["at"], p["idx"]))
    ptr = 0
    t, done = 0, 0
    cur, used = None, 0

    def admit(now):
        nonlocal ptr
        while ptr < n and pending[ptr]["at"] <= now:
            queues[level[pending[ptr]["idx"]]].append(pending[ptr])
            ptr += 1

    while done < n:
        admit(t)
        top = next((k for k in (1, 2, 3) if queues[k]), None)

        # a higher queue became non-empty -> preempt the running process
        if cur is not None and top is not None and top < level[cur["idx"]]:
            queues[level[cur["idx"]]].append(cur)
            cur, used = None, 0

        if cur is None:
            if top is None:
                nxt = pending[ptr]["at"]
                g.add("IDLE", t, nxt)
                t = nxt
                continue
            cur = queues[top].pop(0)
            used = 0

        if cur["start"] is None:
            cur["start"] = t
        g.add(cur["pid"], t, t + 1)
        cur["rem"] -= 1
        t += 1
        used += 1

        if cur["rem"] == 0:
            cur["ct"] = t
            done += 1
            cur, used = None, 0
        else:
            q = QUEUE_QUANTUM[level[cur["idx"]]]
            if q is not None and used >= q:
                admit(t)
                if feedback and level[cur["idx"]] < 3:
                    level[cur["idx"]] += 1
                queues[level[cur["idx"]]].append(cur)
                cur, used = None, 0

    return _result(procs, g)


def multilevel_queue(processes):
    return _multilevel(processes, feedback=False)


def multilevel_feedback_queue(processes):
    return _multilevel(processes, feedback=True)
