"""Typed event triage. Model output never grants infrastructure authority."""

from __future__ import annotations

from typing import Any, Protocol


class DecisionPort(Protocol):
    def triage(self, event: dict[str, Any]) -> dict[str, Any]: ...


class RulesTriage:
    """Reproducible baseline for Laya/Jev comparisons."""

    def triage(self, event: dict[str, Any]) -> dict[str, Any]:
        signal = str(event.get("signal", "")).lower()
        if any(word in signal for word in ("cooling", "thermal", "temperature")):
            route = "facility"
        elif any(word in signal for word in ("fabric", "network", "latency", "packet")):
            route = "network"
        elif any(word in signal for word in ("gpu", "cuda", "memory")):
            route = "compute"
        else:
            route = "human_review"
        return {"route": route, "engine": "rules-v1", "authority": "TRIAGE_ONLY"}


class LayaTriage:
    """Optional local Laya adapter; domain accuracy and calibration are unverified."""

    def __init__(self, router: Any | None = None):
        if router is None:
            try:
                from laya import Router
            except ImportError as exc:
                raise RuntimeError("Install and review Laya separately to use this optional adapter") from exc
            router = Router(preload=False)
        self.router = router

    def triage(self, event: dict[str, Any]) -> dict[str, Any]:
        questions = {
            "route": {
                "type": "choice",
                "instructions": "Which infrastructure specialist should inspect this event?",
                "criteria": {
                    "facility": "power or cooling equipment",
                    "network": "fabric, packet transport or network latency",
                    "compute": "GPU, accelerator or host compute",
                    "human_review": "insufficient evidence or other cause",
                },
            }
        }
        raw = self.router.predict(event, questions)
        answer = raw["answers"]["route"]
        route = answer["choice"]
        if route not in questions["route"]["criteria"]:
            route = "human_review"
        return {
            "route": route,
            "engine": "laya-unvalidated",
            "raw_confidence": answer.get("confidence"),
            "routing": raw.get("routing"),
            "authority": "TRIAGE_ONLY",
            "calibration": "not_established_for_worldops",
        }
