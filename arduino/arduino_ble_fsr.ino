// arduino_ble_fsr.ino
// Runs on Arduino UNO Q.
// Reads 8 FSR pressure sensors at 50Hz and broadcasts JSON over BLE.
//
// WIRING (repeat for each of the 8 sensors):
//   Arduino 5V  ──►  FSR leg 1
//   FSR leg 2   ──►  Arduino Ax pin  AND  10kΩ resistor
//   10kΩ        ──►  Arduino GND
// (The 10kΩ pull-down resistor is mandatory — without it you get random values)
//
// BEFORE FLASHING: Verify in Arduino IDE that board = "Arduino UNO Q"
// and that ArduinoBLE library is installed via Library Manager.

#include <ArduinoBLE.h>

// ─── CONFIGURATION ────────────────────────────────────────────────────────────
const int   FSR_PINS[8]  = {A0, A1, A2, A3, A4, A5, A6, A7};
const int   SAMPLE_MS    = 20;         // 50 Hz = 1000ms / 50 = 20ms interval
const char* DEVICE_NAME  = "StampedeShield-Mat";
const char* ZONE_NAME    = "A";

// ─── BLE SERVICE ──────────────────────────────────────────────────────────────
// Service UUID 180D = "Heart Rate" service (reused for sensor data)
BLEService pressureService("180D");

// Characteristic UUID 2A37 = value characteristic, notify + read, max 128 bytes
BLEStringCharacteristic pressureChar(
    "00002a37-0000-1000-8000-00805f9b34fb",
    BLENotify | BLERead,
    128
);

// ─── SETUP ────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(9600);
    pinMode(LED_BUILTIN, OUTPUT);

    if (!BLE.begin()) {
        // BLE failed to start — blink fast forever as error indicator
        Serial.println("[ERROR] BLE.begin() failed. Check board selection in IDE.");
        while (true) {
            digitalWrite(LED_BUILTIN, HIGH); delay(150);
            digitalWrite(LED_BUILTIN, LOW);  delay(150);
        }
    }

    BLE.setLocalName(DEVICE_NAME);
    BLE.setAdvertisedService(pressureService);
    pressureService.addCharacteristic(pressureChar);
    BLE.addService(pressureService);
    BLE.advertise();

    Serial.print("[OK] Advertising as: ");
    Serial.println(DEVICE_NAME);
    Serial.println("[INFO] Waiting for PC connection...");
}

// ─── MAIN LOOP ────────────────────────────────────────────────────────────────
void loop() {
    BLEDevice central = BLE.central();

    if (central) {
        Serial.print("[CONNECTED] Central address: ");
        Serial.println(central.address());
        digitalWrite(LED_BUILTIN, HIGH);   // LED on = connected

        while (central.connected()) {
            pressureChar.writeValue(buildPacket());
            delay(SAMPLE_MS);
        }

        // Re-advertise immediately after disconnect
        Serial.println("[DISCONNECTED] Re-advertising...");
        digitalWrite(LED_BUILTIN, LOW);
        BLE.advertise();
    }
}

// ─── PACKET BUILDER ───────────────────────────────────────────────────────────
String buildPacket() {
    int vals[8];
    int total = 0;

    for (int i = 0; i < 8; i++) {
        vals[i]  = analogRead(FSR_PINS[i]);
        total   += vals[i];
    }

    // Output: {"t":12345,"z":"A","p":[v0,v1,v2,v3,v4,v5,v6,v7],"s":total}
    String pkt = "{\"t\":";
    pkt += millis();
    pkt += ",\"z\":\"";
    pkt += ZONE_NAME;
    pkt += "\",\"p\":[";
    for (int i = 0; i < 8; i++) {
        pkt += vals[i];
        if (i < 7) pkt += ",";
    }
    pkt += "],\"s\":";
    pkt += total;
    pkt += "}";
    return pkt;
}
