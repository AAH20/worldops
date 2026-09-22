"""Reproducible, explicitly synthetic AI factory fixture."""


def make_factory(rack_count: int = 20, nodes_per_rack: int = 10) -> dict:
    if rack_count < 4 or nodes_per_rack < 2:
        raise ValueError("factory requires at least four racks and two nodes per rack")
    racks = []
    nodes = []
    for r in range(rack_count):
        rack_id = f"rack-{r:02d}"
        racks.append({
            "id": rack_id,
            "power_limit_w": 35000,
            "cooling_limit_w": 34000,
            "base_draw_w": 25500 if r == 0 else 23000 + (r % 3) * 300,
            "energy_usd_per_kwh": 0.11 + (r % 4) * 0.01,
        })
        for i in range(nodes_per_rack):
            nodes.append({
                "id": f"node-{r:02d}-{i:02d}",
                "rack": rack_id,
                "gpus": 8,
                "used_gpus": 0,
                "gpu_power_w": 650,
                "cost_usd_per_gpu_hour": round(1.60 + r * 0.025 + i * 0.003, 3),
                "data_latency_ms": 1.5 if r < 2 else 2.5 + (r % 4) * 0.4,
                "healthy_paths": 2 if r < 2 else 3,
            })
    return {
        "fixture_kind": "synthetic_not_measured",
        "racks": racks,
        "nodes": nodes,
        "jobs": [
            {"id": "customer-inference", "gpus": 8, "priority": 3, "max_data_latency_ms": 5.0,
             "min_healthy_paths": 2, "value_usd_per_hour": 35.0},
            {"id": "model-training", "gpus": 8, "priority": 2, "max_data_latency_ms": 8.0,
             "min_healthy_paths": 2, "value_usd_per_hour": 26.0},
            {"id": "batch-embeddings", "gpus": 4, "priority": 1, "max_data_latency_ms": 12.0,
             "min_healthy_paths": 1, "value_usd_per_hour": 10.0},
        ],
        "scenarios": [
            {"id": "cooling-derate", "cooling_derate_w": {"rack-00": 5000, "rack-01": 3000}},
            {"id": "fabric-degradation", "extra_latency_ms": {"rack-00": 5, "rack-01": 4},
             "path_loss": {"rack-00": 1, "rack-01": 1}},
        ],
    }
