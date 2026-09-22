"""Deterministic, advisory-only cross-domain placement kernel."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

VERSION = "worldops-placement-v0.1"


def canonical_digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def validate(world: dict[str, Any]) -> None:
    if not isinstance(world, dict):
        raise ValueError("world must be an object")
    for key in ("racks", "nodes", "jobs", "scenarios"):
        if not isinstance(world.get(key), list) or not world[key]:
            raise ValueError(f"{key} must be a nonempty array")
    if len(world["nodes"]) > 10000 or len(world["jobs"]) > 1000:
        raise ValueError("world exceeds v0.1 work budget")
    for key in ("racks", "nodes", "jobs", "scenarios"):
        ids = [item.get("id") for item in world[key]]
        if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"{key} IDs must be unique nonempty strings")
    racks = {r["id"] for r in world["racks"]}
    for rack in world["racks"]:
        for key in ("power_limit_w", "cooling_limit_w", "base_draw_w", "energy_usd_per_kwh"):
            _number(rack, key, minimum=0)
        if rack["base_draw_w"] > min(rack["power_limit_w"], rack["cooling_limit_w"]):
            raise ValueError(f"rack {rack['id']} starts beyond facility limit")
    for node in world["nodes"]:
        if node.get("rack") not in racks:
            raise ValueError(f"node {node['id']} has unknown rack")
        for key in ("gpus", "used_gpus", "gpu_power_w", "cost_usd_per_gpu_hour", "data_latency_ms", "healthy_paths"):
            _number(node, key, minimum=0)
        if node["used_gpus"] > node["gpus"]:
            raise ValueError(f"node {node['id']} overcommitted")
    for job in world["jobs"]:
        for key in ("gpus", "max_data_latency_ms", "min_healthy_paths", "value_usd_per_hour"):
            _number(job, key, minimum=0)
        if job["gpus"] <= 0:
            raise ValueError("job GPU demand must be positive")
    for scenario in world["scenarios"]:
        for field in ("power_derate_w", "cooling_derate_w", "extra_latency_ms", "path_loss"):
            values = scenario.get(field, {})
            if not isinstance(values, dict) or any(k not in racks for k in values):
                raise ValueError(f"scenario {scenario['id']} has invalid {field} rack")
            if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in values.values()):
                raise ValueError(f"scenario {scenario['id']} has invalid {field} value")
        if any(x not in {n["id"] for n in world["nodes"]} for x in scenario.get("failed_nodes", [])):
            raise ValueError(f"scenario {scenario['id']} names unknown failed node")


def _number(obj: dict[str, Any], key: str, minimum: float) -> None:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        raise ValueError(f"{key} must be a number >= {minimum}")


def evaluate(world: dict[str, Any], placements: dict[str, str]) -> dict[str, Any]:
    """Evaluate one complete plan in normal and declared contingency states."""
    validate(world)
    racks = {r["id"]: r for r in world["racks"]}
    nodes = {n["id"]: n for n in world["nodes"]}
    jobs = {j["id"]: j for j in world["jobs"]}
    violations: list[dict[str, str]] = []
    additions = {n: 0 for n in nodes}
    watts = {r: racks[r]["base_draw_w"] for r in racks}
    hourly_cost = 0.0
    latency_total = 0.0
    for job_id, job in jobs.items():
        node_id = placements.get(job_id)
        if node_id not in nodes:
            violations.append({"scenario": "base", "job": job_id, "constraint": "unplaced"})
            continue
        node = nodes[node_id]
        rack_id = node["rack"]
        additions[node_id] += job["gpus"]
        watts[rack_id] += job["gpus"] * node["gpu_power_w"]
        hourly_cost += job["gpus"] * node["cost_usd_per_gpu_hour"]
        hourly_cost += job["gpus"] * node["gpu_power_w"] / 1000 * racks[rack_id]["energy_usd_per_kwh"]
        latency_total += node["data_latency_ms"]
    for node_id, added in additions.items():
        node = nodes[node_id]
        if node["used_gpus"] + added > node["gpus"]:
            violations.append({"scenario": "base", "node": node_id, "constraint": "gpu_capacity"})
    for scenario in [{"id": "base"}, *world["scenarios"]]:
        scenario_id = scenario["id"]
        for rack_id, draw in watts.items():
            rack = racks[rack_id]
            if draw > rack["power_limit_w"] - scenario.get("power_derate_w", {}).get(rack_id, 0):
                violations.append({"scenario": scenario_id, "rack": rack_id, "constraint": "power"})
            if draw > rack["cooling_limit_w"] - scenario.get("cooling_derate_w", {}).get(rack_id, 0):
                violations.append({"scenario": scenario_id, "rack": rack_id, "constraint": "cooling"})
        for job_id, node_id in placements.items():
            if job_id not in jobs or node_id not in nodes:
                continue
            node, job = nodes[node_id], jobs[job_id]
            rack_id = node["rack"]
            if node_id in scenario.get("failed_nodes", []):
                violations.append({"scenario": scenario_id, "job": job_id, "constraint": "node_failure"})
            latency = node["data_latency_ms"] + scenario.get("extra_latency_ms", {}).get(rack_id, 0)
            if latency > job["max_data_latency_ms"]:
                violations.append({"scenario": scenario_id, "job": job_id, "constraint": "data_latency"})
            paths = node["healthy_paths"] - scenario.get("path_loss", {}).get(rack_id, 0)
            if paths < job["min_healthy_paths"]:
                violations.append({"scenario": scenario_id, "job": job_id, "constraint": "network_paths"})
    return {
        "feasible": not violations,
        "violations": violations,
        "hourly_cost_usd": round(hourly_cost, 4),
        "mean_base_latency_ms": round(latency_total / len(jobs), 4),
        "delivered_value_usd_per_hour": round(sum(j["value_usd_per_hour"] for j in jobs.values()) if not violations else 0, 4),
    }


def plan(world: dict[str, Any], strategy: str = "worldops") -> dict[str, Any]:
    """Compare candidate placements. Greedy v0.1 is explicit, not globally optimal."""
    validate(world)
    if strategy not in {"worldops", "first_fit", "cheapest"}:
        raise ValueError("unknown strategy")
    placements: dict[str, str] = {}
    jobs = sorted(world["jobs"], key=lambda j: (-j.get("priority", 0), j["id"]))
    nodes = sorted(world["nodes"], key=lambda n: n["id"])
    rejected: list[dict[str, str]] = []
    for job in jobs:
        candidates: list[tuple[float, str]] = []
        pool = nodes if strategy != "cheapest" else sorted(nodes, key=lambda n: (n["cost_usd_per_gpu_hour"], n["id"]))
        for node in pool:
            trial = {**placements, job["id"]: node["id"]}
            if strategy == "worldops":
                # During construction, only placed jobs are evaluated. Other jobs are assigned
                # after the next iteration; a temporary world avoids false "unplaced" failures.
                partial = deepcopy(world)
                partial["jobs"] = [j for j in jobs if j["id"] in trial]
                result = evaluate(partial, trial)
                if not result["feasible"]:
                    rejected.append({"job": job["id"], "node": node["id"], "reason": result["violations"][0]["constraint"]})
                    continue
                score = result["hourly_cost_usd"] + result["mean_base_latency_ms"] * 0.005
            else:
                # Baselines apply only local GPU capacity and ignore shared facility/network risks.
                occupied = sum(j["gpus"] for j in jobs if placements.get(j["id"]) == node["id"])
                if node["used_gpus"] + occupied + job["gpus"] > node["gpus"]:
                    continue
                score = node["cost_usd_per_gpu_hour"] if strategy == "cheapest" else 0
            candidates.append((score, node["id"]))
            if strategy == "first_fit":
                break
        if candidates:
            placements[job["id"]] = min(candidates)[1]
    evaluation = evaluate(world, placements)
    receipt = {
        "schema_version": "1",
        "engine_version": VERSION,
        "world_digest": canonical_digest(world),
        "strategy": strategy,
        "authority": "ADVISORY_ONLY_NOT_AUTHORIZED",
        "assurance": "synthetic_scenarios_only",
        "placements": placements,
        "evaluation": evaluation,
        "candidate_rejections": len(rejected),
        "rejection_examples": rejected[:12],
        "limitations": ["greedy search; no global optimality guarantee", "declared scenarios only", "no live telemetry or actuation"],
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    return receipt
