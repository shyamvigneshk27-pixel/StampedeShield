# StampedeShield Setup and Execution Guide

This document contains step-by-step instructions to run, test, and deploy the StampedeShield system.

---

## 1. Local Simulation Mode (No Hardware Needed)

Use this mode to develop, test, and review the entire system before the hackathon.

### Prerequisites
- Python 3.11+
- Git

### Step 1: Clone and Install Dependencies
```bash
git clone https://github.com/shyamvigneshk27-pixel/Stark-x.git
cd Stark-x

# Install PC dependencies
pip install -r pc/requirements.txt
```

### Step 2: Start the Cloud Endpoint (Simulating Qualcomm Cloud AI 100)
In a separate terminal:
```bash
cd cloud
pip install -r requirements.txt
python cloud_endpoint.py
```
*Expected console output:*
`Cloud AI 100 calibration server on port 5000`

### Step 3: Run the PC Orchestrator in Simulation Mode
By default, `pc/pc_main.py` has `USE_SIMULATOR = True` enabled.
```bash
cd pc
python pc_main.py
```
*Expected behavior:*
- The simulator generates baseline sensor readings for the first 30 seconds (Warmup phase).
- Risk score increases to Alert (Yellow) and Critical (Red) states as simulated crowd pressure spikes.
- Out-of-Distribution pressure values trigger updates to the Flask server, returning recalibrated parameters.

---

## 2. Running Automated Tests

To ensure the SPC engine logic is functioning correctly and verify the edge mathematical computations:
```bash
cd pc
pytest tests/ -v
```
*Expected output:*
All 7 unit tests (warmup, stability, alert trigger, critical state, range checks, recalibration updates, partial spikes) must pass successfully.

---

## 3. Deployment with Real Hardware (Hackathon Day)

Follow these steps once you receive the physical devices at the hackathon.

### Step 1: Wiring the Pressure Mat
1. Reference the [docs/wiring_guide.md](file:///d:/StampedeShield/docs/wiring_guide.md) layout.
2. Wire the 8 Force-Sensitive Resistors (FSRs) to the Arduino analog pins (`A0` to `A7`) using 10kΩ pull-down resistors.
3. Build the protective foam mat structure.

### Step 2: Flash the Arduino Board
1. Open Arduino IDE 2.x.
2. Install the `ArduinoBLE` library via the Library Manager.
3. Select board `Arduino UNO Q`.
4. Open [arduino/arduino_ble_fsr.ino](file:///d:/StampedeShield/arduino/arduino_ble_fsr.ino) and upload the sketch.
5. Verify in Serial Monitor (9600 baud) that the board is advertising as `StampedeShield-Mat`.

### Step 3: Configure PC for Real BLE Mode
1. Ensure the Snapdragon PC Bluetooth adapter is turned on.
2. Open `pc/pc_main.py` and modify configuration variables:
   ```python
   USE_SIMULATOR = False
   CLOUD_URL     = "http://YOUR_CLOUD_AI_100_ENDPOINT/calibrate"
   ```
3. Run the orchestrator:
   ```bash
   python pc_main.py
   ```

### Step 4: Install and Run Android App
1. Open the `android` folder in Android Studio.
2. Connect your Android phone with developer options enabled, or run on an emulator.
3. Ensure Android permissions for Location and Bluetooth are accepted.
4. Build and install the APK.
5. Tap **Connect** inside the application to search for `StampedeShield-PC`.
