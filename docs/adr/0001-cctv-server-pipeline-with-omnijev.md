# 0001. Architecture Shift to Server-Side CCTV Pipeline with OmniJev System 1

We have decided to replace the edge-device architecture (MaixCAM Pro + STM32) with a server-side pipeline that ingests fixed CCTV feeds, runs YOLO for spatial perception, and leverages OmniJev for single-pass System 1 risk decision probes.

This eliminates hardware procurement and cross-compilation risks while solving the high-mounted CCTV false-alarm problem through calibrated probability reasoning instead of autoregressive slow-thinking models.
