import os
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({
        "project": "Hostly Python Demo API",
        "message": "Python backend is running",
        "endpoints": {
            "GET /api/health": "Check whether the API is running",
            "GET /api/info": "Get information about this demo",
            "GET /api/schedule?quantum=2": "Run the sample Round Robin schedule",
            "POST /api/schedule": "Run Round Robin with your own processes"
        }
    })


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "hostly-python-api"})


@app.get("/api/info")
def info():
    return jsonify({
        "name": "Round Robin CPU Scheduler API",
        "technology": "Python + Flask",
        "description": "A small demo API that simulates Round Robin CPU scheduling.",
        "note": "For simplicity, all processes are assumed to arrive at time zero."
    })


def run_round_robin(processes, quantum):
    remaining = {process["pid"]: process["burst_time"] for process in processes}
    burst_times = {process["pid"]: process["burst_time"] for process in processes}
    queue = [process["pid"] for process in processes]
    current_time = 0
    execution_order = []
    timeline = []
    completion_time = {}

    while queue:
        pid = queue.pop(0)
        start_time = current_time
        run_time = min(quantum, remaining[pid])
        current_time += run_time
        remaining[pid] -= run_time

        execution_order.append(pid)
        timeline.append({"process": pid, "start": start_time, "end": current_time})

        if remaining[pid] > 0:
            queue.append(pid)
        else:
            completion_time[pid] = current_time

    turnaround_time = dict(completion_time)
    waiting_time = {
        pid: turnaround_time[pid] - burst_times[pid]
        for pid in burst_times
    }

    return {
        "algorithm": "Round Robin",
        "time_quantum": quantum,
        "execution_order": execution_order,
        "timeline": timeline,
        "completion_time": completion_time,
        "turnaround_time": turnaround_time,
        "waiting_time": waiting_time,
        "average_waiting_time": round(sum(waiting_time.values()) / len(waiting_time), 2),
        "average_turnaround_time": round(sum(turnaround_time.values()) / len(turnaround_time), 2)
    }


def validate_schedule_input(data):
    if not isinstance(data, dict):
        return None, None, "Send a JSON object containing 'quantum' and 'processes'."

    quantum = data.get("quantum", 2)
    if isinstance(quantum, bool) or not isinstance(quantum, int) or quantum <= 0:
        return None, None, "'quantum' must be a positive integer."

    processes = data.get("processes")
    if not isinstance(processes, list) or not processes:
        return None, None, "'processes' must be a non-empty list."

    cleaned_processes = []
    seen_pids = set()
    for index, process in enumerate(processes, start=1):
        if not isinstance(process, dict):
            return None, None, f"Process {index} must be a JSON object."

        pid = process.get("pid", f"P{index}")
        burst_time = process.get("burst_time")

        if not isinstance(pid, str) or not pid.strip():
            return None, None, f"Process {index} needs a non-empty string 'pid'."
        if pid in seen_pids:
            return None, None, "Each process 'pid' must be unique."
        if isinstance(burst_time, bool) or not isinstance(burst_time, int) or burst_time <= 0:
            return None, None, f"Process {pid}: 'burst_time' must be a positive integer."

        seen_pids.add(pid)
        cleaned_processes.append({"pid": pid, "burst_time": burst_time})

    return cleaned_processes, quantum, None


@app.route("/api/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "GET":
        try:
            quantum = int(request.args.get("quantum", "2"))
        except ValueError:
            return jsonify({"error": "'quantum' must be a positive integer."}), 400

        if quantum <= 0:
            return jsonify({"error": "'quantum' must be a positive integer."}), 400

        processes = [
            {"pid": "P1", "burst_time": 5},
            {"pid": "P2", "burst_time": 3},
            {"pid": "P3", "burst_time": 1}
        ]
    else:
        data = request.get_json(silent=True)
        processes, quantum, error = validate_schedule_input(data)
        if error:
            return jsonify({"error": error}), 400

    return jsonify(run_round_robin(processes, quantum))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
