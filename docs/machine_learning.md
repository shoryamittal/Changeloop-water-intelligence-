# Model development and monitoring

**Current state: ARCHITECTED.** The prototype does not claim a trained production endpoint model or performance metrics. Its signal curve is synthetic, and the safety logic is deliberately rule-led.

ML becomes justified only after a controlled pilot has ground truth from validated cleaning acceptance. Then the process should use a temporal train / validation / test split, compare an interpretable baseline against any learned model, report precision, recall, F1, calibration and confusion matrix for the defined endpoint task, and report missing-data handling explicitly.

Monitor data availability, invalid-signal rate, distribution shift, post-release prediction error and operator override rate. On degradation or low confidence, flag the model and use the validated procedure.
