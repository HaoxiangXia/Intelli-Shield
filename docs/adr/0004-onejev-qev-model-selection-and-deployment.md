# 0004. OneJev (qev) Runtime Selection and Model Weights

We decided to adopt the official `OmniJev/OneJev` repository and `qev` runtime package from TypeSafe AI on the RTX 3090 cluster node.

For model weights, we selected `OmniJev/PlayJev-0.8B` as the primary engine for millisecond-level (30-40ms) System 1 risk decisions, with `OmniJev/OneJev-9B` retained as an option for offline comparative analysis.

Three core question primitives are bound to full-frame CCTV evaluation:
- `Noul`: Binary calibrated collision likelihood.
- `Choice`: Worker attention and evasion distribution.
- `Score`: Continuous operational hazard severity (0-3).
