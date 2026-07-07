# Hardware Wiring Guide & Test Sketch

This guide details how to wire the force-sensitive resistors (FSRs) to the Arduino UNO Q and verify their functionality using a test script.

## Component Overview
- **8× Force-Sensitive Resistors (FSR-402 or similar)**: Flat sensors whose resistance drops when pressed.
- **8× 10kΩ Resistors**: Used as pull-downs to create voltage dividers.
- **Breadboard & Jumper Wires**: For connecting the sensors to the Arduino.
- **EVA Foam Sheet (30×60cm)**: The physical base for mounting the sensors.

---

## Wiring One FSR Sensor
Repeat this setup for each of the 8 sensors.

```
Arduino 5V  ────────────────────── FSR Leg 1
                                         │
                                    (FSR body)
                                         │
Arduino Ax  ───────────── FSR Leg 2 ─────┤
(A0 to A7)                               │
                                     10kΩ resistor (Pull-down)
                                         │
Arduino GND ─────────────────────────────┘
```

### Pin Connections Table
| Sensor Number | Analog Pin | 5V Connection | Ground Connection |
|:---:|:---:|:---:|:---:|
| 1 | **A0** | 5V Rail | GND via 10kΩ Resistor |
| 2 | **A1** | 5V Rail | GND via 10kΩ Resistor |
| 3 | **A2** | 5V Rail | GND via 10kΩ Resistor |
| 4 | **A3** | 5V Rail | GND via 10kΩ Resistor |
| 5 | **A4** | 5V Rail | GND via 10kΩ Resistor |
| 6 | **A5** | 5V Rail | GND via 10kΩ Resistor |
| 7 | **A6** | 5V Rail | GND via 10kΩ Resistor |
| 8 | **A7** | 5V Rail | GND via 10kΩ Resistor |

> [!WARNING]
> **Do not omit the 10kΩ pull-down resistors.** Without them, the analog pins will float, causing random noise and fake alerts.

---

## Calibration & Verification Sketch

Before flashing the final BLE firmware, flash this simple calibration sketch to verify that all 8 sensors are functioning and wired correctly.

```cpp
// FSR Sensor Calibration and Verification Sketch
// Upload this to the Arduino UNO Q first.

const int FSR_PINS[8] = {A0, A1, A2, A3, A4, A5, A6, A7};

void setup() {
    Serial.begin(9600);
    while (!Serial) {
        ; // Wait for serial port to connect
    }
    Serial.println("StampedeShield Mat - Sensor Calibration Test Started");
}

void loop() {
    for (int i = 0; i < 8; i++) {
        int val = analogRead(FSR_PINS[i]);
        Serial.print("A");
        Serial.print(i);
        Serial.print(":");
        Serial.print(val);
        Serial.print("\t");
    }
    Serial.println();
    delay(200); // Sample every 200ms for readability in serial monitor
}
```

### Expected Behavior in Serial Monitor:
- **No Pressure**: Sensor readings should hover between **0 and 40**.
- **Light Finger Press**: Readings should climb to **300 - 600**.
- **Heavy Foot Step / Compression**: Readings should climb to **800 - 1023**.
- **Troubleshooting**: If a sensor is stuck permanently at `0` or `1023`, double-check the 10kΩ resistor connections and ensure the FSR legs aren't shorting.
