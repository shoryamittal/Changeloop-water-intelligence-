# Architecture

```mermaid
flowchart TD
 Q[Synthetic batch queue] --> B[Changeover burden rules]
 B --> O[Sequence optimizer]
 O --> I[Incremental impact ledger]
 S[Synthetic sensor stream] --> G[Signal quality gate]
 G --> H[Human + validated-procedure gate]
 H --> I
 R[Illustrative recovery stream] --> W[Compatibility screen]
 W --> I
 I --> A[Audit trail and UI]
```

The local server implements this path using a deterministic demo seed. It is a real executable prototype. The input data and plant behaviors are simulated. Any future connection to MES, historian, LIMS, treatment controls, or identity service is target integration architecture only. See `data_model.md` for implemented and target persistence boundaries.
