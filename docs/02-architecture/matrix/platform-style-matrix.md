# Decision Matrix Applied: Platform Style

Using the Phase 0 weights (Sec 20, Comp 20, Scale 15, Ops 15, Lat 10, Cost 10, Lock-in 10), scores 1–5.

| Option | Sec | Comp | Scale | Ops | Lat | Cost | Lock | **Total /500** |
|---|---|---|---|---|---|---|---|---|
| Modular monolith | 3 | 3 | 2 | 5 | 5 | 5 | 4 | **365** |
| Domain services + event backbone | 4 | 4 | 5 | 3 | 4 | 3 | 4 | **390** |
| Fully serverless / managed | 4 | 3 | 5 | 4 | 3 | 3 | 1 | **345** |

*Working for the middle row:* 80 + 80 + 75 + 45 + 40 + 30 + 40 = 390.

## Sensitivity run

Weights: Ops 30, Scale 5, Cost 5; others unchanged.

| Option | Weighted |
|---|---|
| Modular monolith | **395** |
| Domain services | 370 |
| Serverless | 340 |

**The winner flips.** The decision is sensitive to team capacity.

## What to say

> "The decision is sensitive to team capacity. If operability dominates, a modular monolith wins. I chose domain services because residency isolation, independent scaling of the fraud scorer, and blast-radius containment are structural requirements — but I limited the design to about eight deployable services, not dozens. If the team were two people, I'd start as a modular monolith with enforced module boundaries and extract the scorer first."

## Why not serverless

Scores well on operability, but lock-in is the biggest loss, and it conflicts with the cloud-agnostic constraint and the Fabric/Kafka toolset.