# pc_main.py
# Runs on the Snapdragon X PC.
# Receives BLE pressure data from Arduino, runs SPC inference on NPU,
# sends risk alerts to Android phone over BLE.
#
# Before hackathon: USE_SIMULATOR = True  (no hardware needed)
# Hackathon day:    USE_SIMULATOR = False (real Arduino via BLE)

import asyncio
import json
import os
import time

import requests
from bleak import BleakClient, BleakScanner

from spc_engine import CrushRiskEngine, SPCConfig

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
USE_SIMULATOR        = True   # ← Set False on hackathon day
ARDUINO_NAME         = "StampedeShield-Mat"
ANDROID_NAME         = "StampedeShield-Phone"
PRESSURE_CHAR_UUID   = "00002a37-0000-1000-8000-00805f9b34fb"
ALERT_CHAR_UUID      = "00002a38-0000-1000-8000-00805f9b34fb"
CLOUD_URL            = os.getenv("CLOUD_URL", "http://localhost:5000/calibrate")
CLOUD_SYNC_MIN_SEC   = 60    # Minimum seconds between cloud syncs

# ─── STATE ────────────────────────────────────────────────────────────────────
engine          = CrushRiskEngine(config=SPCConfig(alpha=0.3, ucl_sigma=3.0, warmup_samples=30))
last_cloud_sync = 0.0
android_gatt:   BleakClient = None  # type: ignore


# ─── INFERENCE CALLBACK ───────────────────────────────────────────────────────
async def on_pressure_packet(sender, data: bytearray) -> None:
    """Fires every 20ms when Arduino sends a BLE notification."""
    global last_cloud_sync

    # Parse packet
    try:
        packet         = json.loads(data.decode("utf-8"))
        pressure_vals  = packet["p"]   # list of 8 ints
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as exc:
        print(f"[WARN] Malformed packet: {exc}")
        return

    # ── SPC inference (on NPU via QNN on hackathon day) ──────────────────────
    t0        = time.perf_counter()
    result    = engine.update(pressure_vals)
    latency   = (time.perf_counter() - t0) * 1000

    # ── Console dashboard ─────────────────────────────────────────────────────
    if result["warmup"]:
        print(f"[WARMUP {result['sample']:02d}/30] Calibrating baseline...")
        return

    status = ("CRITICAL" if result["critical"]
              else "ALERT   " if result["alert"]
              else "SAFE    ")
    print(
        f"[{latency:5.1f}ms] Risk={result['risk']:3d} | {status} | "
        f"violations={result['violations']} | OOD={result['ood']}"
    )

    # ── Send alert to Android phone ───────────────────────────────────────────
    if android_gatt and android_gatt.is_connected:
        alert_bytes = json.dumps({
            "risk":     result["risk"],
            "alert":    result["alert"],
            "critical": result["critical"]
        }).encode("utf-8")
        try:
            await android_gatt.write_gatt_char(ALERT_CHAR_UUID, alert_bytes, response=False)
        except Exception as exc:
            print(f"[WARN] Android write failed: {exc}")

    # ── Cloud AI 100 async sync (only on OOD, rate-limited) ──────────────────
    now = time.time()
    if result["ood"] and (now - last_cloud_sync) > CLOUD_SYNC_MIN_SEC:
        asyncio.create_task(_cloud_sync(pressure_vals, result))


async def _cloud_sync(sensors: list, result: dict) -> None:
    """POST anonymised pattern to Cloud AI 100 and apply returned weights."""
    global last_cloud_sync
    try:
        resp = requests.post(
            CLOUD_URL,
            json={"sensors": sensors, "risk": result["risk"], "timestamp": time.time()},
            timeout=5
        )
        resp.raise_for_status()
        weights = resp.json()
        engine.recalibrate(weights)
        last_cloud_sync = time.time()
        print(f"[CLOUD] Recalibrated → sigma={weights.get('ucl_sigma')} alpha={weights.get('alpha')}")
    except Exception as exc:
        # Cloud failure is non-critical — edge inference continues unchanged
        print(f"[CLOUD] Sync skipped (non-critical): {exc}")


# ─── SIMULATOR MODE ───────────────────────────────────────────────────────────
async def run_simulator() -> None:
    """Generates fake Arduino data. Use before hackathon day."""
    from simulator import generate_pressure_stream
    print("=" * 62)
    print("  StampedeShield - SIMULATOR MODE (no hardware needed)")
    print("  Phases: Calm(0-30s) -> Building(30-60s) -> Crush(60-75s)")
    print("=" * 62)
    await generate_pressure_stream(on_pressure_packet)


# ─── HARDWARE MODE ────────────────────────────────────────────────────────────
async def run_hardware() -> None:
    """Connect to real Arduino and Android via BLE. Hackathon day only."""
    global android_gatt
    print(f"Scanning for '{ARDUINO_NAME}'...")
    arduino = await BleakScanner.find_device_by_name(ARDUINO_NAME, timeout=20.0)
    if arduino is None:
        raise RuntimeError(
            f"'{ARDUINO_NAME}' not found. "
            "Check: (1) Arduino powered on, (2) BLE firmware flashed, "
            "(3) PC Bluetooth enabled."
        )

    print(f"Found Arduino at {arduino.address}")

    # Also try to connect to Android phone
    print(f"Scanning for '{ANDROID_NAME}'...")
    android_dev = await BleakScanner.find_device_by_name(ANDROID_NAME, timeout=10.0)
    if android_dev:
        android_gatt = BleakClient(android_dev)
        await android_gatt.connect()
        print(f"Connected to Android at {android_dev.address}")
    else:
        print(f"[WARN] Android not found — alerts will not be sent to phone")

    async with BleakClient(arduino) as client:
        print("Connected to Arduino ✓")
        await client.start_notify(PRESSURE_CHAR_UUID, on_pressure_packet)
        print("Receiving pressure data... (Ctrl+C to stop)")
        try:
            while True:
                await asyncio.sleep(1.0)
        finally:
            if android_gatt and android_gatt.is_connected:
                await android_gatt.disconnect()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
async def main() -> None:
    if USE_SIMULATOR:
        await run_simulator()
    else:
        await run_hardware()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown.")
