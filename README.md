# StampedeShield (Stark-x)

**Snapdragon Multiverse Hackathon · Qualcomm Bangalore · July 11–12, 2026**

> A pressure mat detects dangerous crowd compression, a Snapdragon NPU classifies the risk in under 40 milliseconds, and a marshal's phone vibrates red before the first person falls.

---

## 1. Problem Context
India hosts over 5,000 public gatherings of 10,000+ people annually. Crowd compression events (such as the 2024 Hathras tragedy or the 2013 Ratangarh temple tragedy) build up pressure waves for 60–90 seconds before they are visually identifiable by marshals.

StampedeShield is an offline-first, deployable, infrastructure-free system designed to detect crowd crush precursors in real time. 
- **Cost**: Under ₹8,000 per deployment.
- **Privacy**: Does not collect biometrics or camera video.
- **Offline Reliability**: Functions without cellular connectivity, making it resilient to cellular network congestion typical of massive crowds.

---

## 2. Multi-Device Architecture
StampedeShield is built using four distinct, non-interchangeable devices:

```
┌─────────────────┐      BLE      ┌───────────────────┐      BLE      ┌────────────────┐
│   Arduino UNO   ├──────────────►│ Snapdragon X PC   ├──────────────►│ Android Phone  │
│ (8 FSR Sensors) │ (JSON stream) │ (SPC Engine NPU)  │ (Risk Alert)  │ (Marshal App)  │
└─────────────────┘               └─────────┬─────────┘               └────────────────┘
                                            │
                                            │ Out-of-Distribution (Async)
                                            ▼
                                  ┌───────────────────┐
                                  │   Cloud AI 100    │
                                  │ (Recalibration)   │
                                  └───────────────────┘
```

1. **Arduino UNO Q (Pressure Mat)**: Reads 8 Force-Sensitive Resistors (FSRs) at 50Hz and streams zone-pressure vectors over BLE. If removed, the system goes blind.
2. **Snapdragon X Series PC (Inference Processor)**: Receives BLE stream, executes Statistical Process Control (SPC) risk classification on the Hexagon NPU via QNN / AI Hub in under 40ms. If removed, the risk score is never computed.
3. **Android Phone (Marshal Alert Screen)**: Receives alerts via BLE, updates display color (Green/Yellow/Red) and fires strong haptic vibration patterns. If removed, marshals are never notified.
4. **Qualcomm Cloud AI 100 (Adaptive Recalibration)**: Dynamically processes out-of-distribution pressure patterns and adjusts upper control limits (UCL) and alpha parameters asynchronously.

---

## 3. The SPC AI Algorithm
Instead of standard neural networks which lack crowd pressure training datasets, StampedeShield uses **Statistical Process Control (SPC)**:
- **Baseline Calibration**: System self-calibrates using the first 30 seconds of readings.
- **Dynamic Limits**: Computes Upper Control Limits ($UCL = \text{mean} + 3 \times \text{std}$) per sensor.
- **EWMA Smoothing**: Uses Exponentially Weighted Moving Averages (EWMA) with $\alpha = 0.3$ to filter transient noise while responding quickly to real spikes.
- **Out-of-Distribution (OOD)**: Computes Mahalanobis distance to identify novel crowd patterns and trigger asynchronous cloud calibration updates.

---

## 4. Repository Structure
```
Stark-x/
├── README.md                      # Project description and overview
├── SETUP.md                       # Setup and run commands
├── LICENSE                        # MIT License
├── arduino/
│   └── arduino_ble_fsr.ino        # Arduino BLE Mat firmware
├── pc/
│   ├── requirements.txt           # Python dependencies
│   ├── pc_main.py                 # PC BLE client & orchestrator
│   ├── spc_engine.py              # SPC Risk classification engine
│   ├── simulator.py               # Pressure mat simulator
│   ├── qnn_wrapper.py             # NPU wrap client interface
│   └── tests/
│       └── test_spc_engine.py     # 7 unit tests (100% pass target)
├── android/
│   └── app/
│       └── src/main/
│           ├── AndroidManifest.xml # Android BLE & Local network config
│           ├── java/com/stampedeshield/MainActivity.kt
│           └── res/layout/activity_main.xml
├── cloud/
│   ├── requirements.txt           # Flask dependencies
│   └── cloud_endpoint.py          # Adaptive calibration API server
└── docs/
    ├── demo_script.md             # 3-minute presentation script
    └── wiring_guide.md            # Hardware schematic & test script
```

---

## 5. Team Roles
*   **Hardware Lead (E1)**: Arduino firmware, FSR wiring, pressure mat construction.
*   **AI/ML Lead (E2)**: SPC engine implementation, threshold tuning, and unit testing.
*   **Mobile Lead (E3)**: Android BLE client, haptic alerts, and offline network support.
*   **Cloud + Docs (E4)**: Flask calibration APIs, presentation slide deck, and backups.
*   **Platform Lead (E5)**: QNN / AI Hub integration, BLE orchestration, and performance metrics.
