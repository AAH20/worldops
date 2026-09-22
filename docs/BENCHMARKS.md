# Benchmark and economics protocol

## Baselines and gates

Compare WorldOps against first-fit, cheapest feasible-on-node, and the operator's existing scheduler policy on the **same frozen world snapshots and declared scenarios**. Publish full scenarios and failure cases, not only mean improvements. Distinguish a synthetic benchmark from a replay on historical operator data and from a live shadow study.

Hard gates: no unplaced priority job, GPU overcommit, rack power or cooling violation, violated network path/latency requirement, or execution without scoped authority. A plan that fails any hard gate is not saved by a better cost score.

For each workload class, report: accepted-plan rate, false-feasible rate on held-out failures, false-rejection rate, cost per SLO-compliant completed job, delivered GPU-hours per purchased GPU-hour, queue wait, planning latency, energy per completed job, canary/rollback success, and human review burden. Report these by site and by workload, not only as a global average.

For Laya/Jev/rules triage, use one human-labeled held-out corpus and identical questions; report accuracy, confusion matrix, Brier score, expected calibration error, abstention coverage, P50/P95 latency, hardware, and fully loaded cost. Model probabilities cannot waive hard controls.

## Unit economics

For a measured period:

```
delivered_unit_margin = (recognized revenue - attributable compute, network,
                         storage, energy, cooling and support cost)
                        / SLO-compliant completed units

verified_incremental_value = observed_margin_with_worldops
                             - matched_baseline_margin
                             - platform_and_operator_cost
                             - measured_incremental_incident_cost
```

Purchased-but-unused GPU-hours and avoided purchases are **capacity opportunity**, not cash savings unless invoices or capital plans confirm a reduction. Use a matched baseline or controlled rollout to estimate incremental value. Show uncertainty and exclude missing data from realized-value claims.

## Promotion stages

Synthetic pass -> historical replay with hidden outcomes -> prospective shadow mode -> approved canary -> multi-site study. Each stage must meet pre-registered safety and economic thresholds set with the operator. No universal performance or savings threshold is claimed by this repository.
