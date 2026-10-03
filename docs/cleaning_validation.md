# Adaptive cleaning simulation and validation boundary

## Implemented simulation — REAL code with SYNTHETIC_DATA

The server generates deterministic conductivity, turbidity, temperature and flow readings with noise. It can simulate normal operation, missing readings, a spike, and drift. Any invalid, missing, or drift-suspected critical reading produces `INSUFFICIENT DATA — HUMAN/VALIDATED PROCEDURE REQUIRED`.

## Endpoint behavior

The prototype's endpoint probability is a synthetic scenario signal, not a trained or validated ML model. It may say “Endpoint likely reached” only when the synthetic stream is valid. It never releases equipment. Automatic release is always false.

## Site validation needed

Plant-specific acceptance criteria, sampling plan, sensor calibration, cleaning validation, product-risk assessment, quality authority approval and human release procedure are required before an endpoint recommendation could influence operations.
