# 0004. OmniJev-4B (MSO1) Runtime Selection and Model Weights

We decided to adopt the `OmniJev` repository (`tinnel123666888/OmniJev`) jointly developed by the Institute of Automation, Chinese Academy of Sciences (CASIA), Beijing Zhongguancun Academy, and Zevo on the RTX 3090 cluster node.

For model weights, we selected `OmniJev-4B` (LoRA adapter `tinnel123/OmniJev` on `Qwen/Qwen3.5-4B` backbone) using the `mso.infer.MSO1` zero-token single-forward-pass inference engine. This parameter scale provides maximum spatial blind-spot cognition and posture reasoning while maintaining a steady-state forward-pass latency benchmark of ~107ms for real-time 10 FPS CCTV safety arbitration.

Four core decision probe primitives are bound to full-frame CCTV evaluation:
- `Noul`: Binary calibrated collision likelihood.
- `Choice` (`worker_awareness`): Worker attention and evasion distribution.
- `Choice` (`worker_hazard_behavior`): Non-compliant high-risk worker behavior identification.
- `Score`: Continuous operational hazard severity (0–3).
