# Weighted Decision Matrix

Reuse this single matrix for every major choice in Phase 2.

## Criteria and weights

| Criterion | Weight | Rationale for weight |
|---|---|---|
| Security | 20 | Payment and trade data is high-value |
| Regulatory compliance and auditability | 20 | Non-compliance is existential |
| Scalability and resilience | 15 | Peak events, global traffic |
| Operability and skills fit | 15 | A small team must run it |
| Latency | 10 | Checkout-path decisions have tight budgets |
| Cost (build + run) | 10 | OSS reduces licence, not ops cost |
| Vendor lock-in and portability | 10 | Cloud-agnostic posture |
| **Total** | **100** | |

## Worked example — platform style

Scores 1–5. Weighted total is out of 500.

| Option | Sec (20) | Comp (20) | Scale (15) | Ops (15) | Lat (10) | Cost (10) | Lock-in (10) | **Weighted** |
|---|---|---|---|---|---|---|---|---|
| Modular monolith | 3 | 3 | 2 | 5 | 5 | 5 | 4 | **370** |
| Event-driven microservices | 4 | 4 | 5 | 3 | 4 | 3 | 4 | **405** |
| Fully serverless / managed | 4 | 3 | 5 | 4 | 3 | 3 | 1 | **365** |

## Sensitivity check

Re-run with **operability = 30** and **scale = 5**. If the winner flips, say so and give the condition:

> "If the team were two people, I'd start as a modular monolith and extract the fraud scorer first."

## Honesty point

Scores are judgement, not measurement. The matrix structures the argument and exposes assumptions; it does not replace thinking.