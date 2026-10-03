# Claim audit

| Claim | Evidence | Source | Year / scope | Verified? | Risk | Required correction |
|---|---|---|---|---|---|
| 2030 industrial-water ambition | Official commitment page | Source register row 1 | 2030; group industrial purposes | Yes | Low | State scope: industrial purposes in factories |
| 56% 2025 industrial-water result | Official sustainability page | Source register row 2 | 2025; group industrial purposes | Yes | Low | Preserve year and scope |
| AquaFlux can reduce water demand | Synthetic model output only | `backend/server.py` | Synthetic scenarios only | No external validation | High | Say “modeled synthetic scenario” |
| Endpoint likely reached | Synthetic simulated process signal | `backend/server.py` | Synthetic signal only | No | High | Require validated procedure and human approval |
| Potentially reusable | Illustrative compatibility screen | `backend/server.py` | Illustrative stream only | No | High | State no reuse is approved |

Audit rule: no L’Oréal-specific operational claim is permitted unless it is in `source_register.md`.
