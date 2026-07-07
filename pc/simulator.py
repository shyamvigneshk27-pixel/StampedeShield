# simulator.py
# Replaces the Arduino+FSR mat during pre-hackathon development.
# Generates realistic fake pressure data through three phases:
#   Phase 1 (0–30s):  calm crowd, values 50–150
#   Phase 2 (30–60s): crowd builds, values 200–600
#   Phase 3 (60–75s): crush event, values 700–1023
#   Phase 4 (75–90s): recovery, values 50–150 (then loops)
#
# Usage: this is imported and called by pc_main.py when USE_SIMULATOR=True

import asyncio
import json
import time
import random


async def generate_pressure_stream(callback):
    """
    Indefinitely generates simulated pressure packets and calls callback().
    callback receives (sender=None, data=bytearray) matching BLE callback signature.
    """
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > 90:
            start = time.time()
            elapsed = 0.0

        # Phase-based pressure generation
        if elapsed < 30:
            base, noise = 80, 40          # Calm baseline
        elif elapsed < 60:
            progress = (elapsed - 30) / 30
            base     = int(80 + progress * 500)
            noise    = 80                 # Building crowd
        elif elapsed < 75:
            base, noise = 800, 200        # Crush event
        else:
            base, noise = 80, 40          # Recovery

        # Spatial variation: edge sensors feel less pressure than centre sensors
        edge_weights = [0.6, 0.8, 0.8, 1.0, 1.0, 0.8, 0.8, 0.6]
        readings = [
            max(0, min(1023, int(base * w + random.randint(-noise, noise))))
            for w in edge_weights
        ]

        packet = json.dumps({
            "t": int(time.time() * 1000),
            "z": "A",
            "p": readings,
            "s": sum(readings)
        }).encode("utf-8")

        await callback(None, bytearray(packet))
        await asyncio.sleep(0.02)  # 50 Hz — matches real Arduino sample rate
