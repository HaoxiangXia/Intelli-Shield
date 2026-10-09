# 0005. YOLO26 Nano (yolo26n) Perception Engine Selection

We decided to upgrade the perception engine from YOLO11n to Ultralytics YOLO26 Nano (`yolo26n.pt`).

YOLO26 introduces native NMS-free dual-head inference, removes DFL latency bottlenecks, and provides edge-first CPU optimizations. On the local Intel Celeron G6900 benchmark, it achieves ~5.2 FPS end-to-end on full video frames without requiring an external GPU.
