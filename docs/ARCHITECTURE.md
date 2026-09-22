# Architecture and authority boundaries

The v0.1 kernel has four functions: validate world input, generate candidates, replay normal and named failure scenarios, and issue an advisory receipt. A world contains racks, nodes, jobs and scenarios. Rack base draw is an input; each placed GPU adds its stated incremental power draw. Power and cooling have separate limits. Node data latency and healthy paths are checked against job requirements in each scenario. Cost is listed GPU-hour charge plus incremental GPU energy at the rack tariff.

The model deliberately does not infer unprovided dependencies, calculate reliability probabilities, operate facilities, or promise that a passing placement is safe in reality. Data from an actual operator must carry observation time, measurement source, unit, precision, owner, residency classification and permission to use. Missing or stale critical data should block recommendation in a future live adapter.

## Proposed system components

| Component | Contract | Acceptance evidence |
| --- | --- | --- |
| Ingestion | Read-only adapters to NetBox, Redfish, OpenConfig, DCGM, OpenTelemetry and schedulers | Replayable source snapshots and unit normalization |
| World state | Time-versioned topology, capacities, dependencies and provenance; Iceberg is an optional analytical store | Point-in-time reconstruction and freshness tests |
| Context | Retrieve runbooks and prior incidents; GraphRAG/Obsidian/Cognee are optional context sources | Citation accuracy and stale-context rejection |
| Typed triage | Rules baseline, Laya or Jev under the same event/answer schema | Held-out accuracy, Brier/ECE, abstention, latency and cost |
| Scenario engine | Discrete failure and derating events | Measured prediction error on historical incidents |
| Optimizer | Hard feasibility then economic objective | Optimality gap, constraint violations, planning latency |
| Workflow | Durable proposal/review/canary/verify state; LangGraph is a candidate | Idempotency and crash/recovery tests |
| Authority | Agent Trust Fabric plus operator IAM/PAM; deterministic final gate | No action without scoped, current authorization |
| Governance | GRC Claw evidence mapping and retention | Independently reviewable decision and outcome receipts |

Specialist agents may propose candidate explanations and scenarios. They are not a quorum that can overrule a hard constraint, change a power system, or assign privileges. The default state of every v0.1 receipt is `ADVISORY_ONLY_NOT_AUTHORIZED`.

## OSS and commercial boundary

Keep public: schemas, synthetic datasets, replay/benchmark code, rules baseline, adapter interface, safety contract and scorecards. Sell: customer-specific integration and calibration, operational support, large-estate optimization, verified economic reporting, enterprise workflow and service levels. Customer infrastructure topology, credentials, contracts and incident histories remain customer-controlled.
