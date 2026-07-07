// MainActivity.kt
// Android BLE client for StampedeShield.
// Connects to Snapdragon PC, displays risk score as coloured screen.
// Development: test on Android Studio emulator with mock JSON.
// Hackathon day: install via ADB on real Android phone.

package com.stampedeshield

import android.Manifest
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.*
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import org.json.JSONObject
import java.util.UUID

class MainActivity : AppCompatActivity() {

    // ── BLE Configuration ──────────────────────────────────────────────────
    companion object {
        const val PC_DEVICE_NAME    = "StampedeShield-PC"
        const val SERVICE_UUID_STR  = "0000180d-0000-1000-8000-00805f9b34fb"
        const val ALERT_CHAR_UUID   = "00002a38-0000-1000-8000-00805f9b34fb"
        const val CCCD_UUID         = "00002902-0000-1000-8000-00805f9b34fb"
        const val PERMISSIONS_CODE  = 1001
    }

    // ── UI ─────────────────────────────────────────────────────────────────
    private lateinit var rootLayout:     FrameLayout
    private lateinit var riskTextView:   TextView
    private lateinit var statusTextView: TextView
    private lateinit var connectButton:  Button
    private lateinit var vibrator:       Vibrator

    // ── BLE State ──────────────────────────────────────────────────────────
    private var gatt:        BluetoothGatt? = null
    private var leScanner:   BluetoothLeScanner? = null
    private var isConnected: Boolean = false

    // ── Lifecycle ──────────────────────────────────────────────────────────
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        rootLayout     = findViewById(R.id.rootLayout)
        riskTextView   = findViewById(R.id.riskText)
        statusTextView = findViewById(R.id.statusText)
        connectButton  = findViewById(R.id.connectBtn)
        vibrator       = getSystemService(VIBRATOR_SERVICE) as Vibrator

        updateUI(risk = 0, alert = false, critical = false)
        statusTextView.text = "Not connected"

        connectButton.setOnClickListener {
            if (isConnected) disconnect() else startScan()
        }

        requestBlePermissions()
    }

    // ── BLE Scan ───────────────────────────────────────────────────────────
    private fun startScan() {
        val adapter = (getSystemService(BLUETOOTH_SERVICE) as BluetoothManager).adapter
        if (adapter == null || !adapter.isEnabled) {
            statusTextView.text = "Bluetooth is OFF"
            return
        }
        statusTextView.text = "Scanning..."
        leScanner = adapter.bluetoothLeScanner
        val filter   = ScanFilter.Builder().setDeviceName(PC_DEVICE_NAME).build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        leScanner?.startScan(listOf(filter), settings, scanCallback)
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            leScanner?.stopScan(this)
            statusTextView.text = "Connecting to PC..."
            result.device.connectGatt(
                this@MainActivity, false, gattCallback, BluetoothDevice.TRANSPORT_LE
            )
        }
        override fun onScanFailed(errorCode: Int) {
            statusTextView.text = "Scan failed (error $errorCode)"
        }
    }

    // ── GATT Callbacks ─────────────────────────────────────────────────────
    private val gattCallback = object : BluetoothGattCallback() {

        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            gatt = g
            runOnUiThread {
                when (newState) {
                    BluetoothProfile.STATE_CONNECTED -> {
                        isConnected = true
                        statusTextView.text = "Connected — discovering services..."
                        connectButton.text  = "Disconnect"
                        g.discoverServices()
                    }
                    BluetoothProfile.STATE_DISCONNECTED -> {
                        isConnected = false
                        statusTextView.text = "Disconnected"
                        connectButton.text  = "Connect"
                        updateUI(0, false, false)
                    }
                }
            }
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) return
            val service = g.getService(UUID.fromString(SERVICE_UUID_STR)) ?: run {
                runOnUiThread { statusTextView.text = "Service not found on PC" }
                return
            }
            val char = service.getCharacteristic(UUID.fromString(ALERT_CHAR_UUID)) ?: return

            g.setCharacteristicNotification(char, true)
            val descriptor = char.getDescriptor(UUID.fromString(CCCD_UUID))
            descriptor?.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            descriptor?.let { g.writeDescriptor(it) }

            runOnUiThread { statusTextView.text = "Receiving alerts ✓" }
        }

        override fun onCharacteristicChanged(
            g: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            val payload = String(characteristic.value ?: return)
            try {
                val json     = JSONObject(payload)
                val risk     = json.getInt("risk")
                val alert    = json.getBoolean("alert")
                val critical = json.optBoolean("critical", false)
                runOnUiThread { updateUI(risk, alert, critical) }
            } catch (_: Exception) { /* Silently ignore malformed packets */ }
        }
    }

    // ── UI Update ──────────────────────────────────────────────────────────
    private fun updateUI(risk: Int, alert: Boolean, critical: Boolean) {
        val (bg, label) = when {
            critical -> Color.parseColor("#F44336") to "⚠ CRITICAL — Evacuate now"
            alert    -> Color.parseColor("#FF9800") to "⚡ ALERT — Redirect crowd"
            else     -> Color.parseColor("#4CAF50") to "✓ Safe"
        }
        rootLayout.setBackgroundColor(bg)
        riskTextView.text = "Risk: $risk / 100\n$label"
        riskTextView.setTextColor(Color.WHITE)

        if (critical && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(
                VibrationEffect.createWaveform(longArrayOf(0L, 400L, 200L, 400L), -1)
            )
        } else if (alert && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(250L, 180))
        }
    }

    // ── Disconnect ─────────────────────────────────────────────────────────
    private fun disconnect() {
        gatt?.close(); gatt = null
        isConnected         = false
        statusTextView.text = "Disconnected"
        connectButton.text  = "Connect"
    }

    override fun onDestroy() { super.onDestroy(); disconnect() }

    // ── Permissions ────────────────────────────────────────────────────────
    private fun requestBlePermissions() {
        val required = buildList {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                add(Manifest.permission.BLUETOOTH_SCAN)
                add(Manifest.permission.BLUETOOTH_CONNECT)
            }
            add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        val missing = required.filter {
            ActivityCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty())
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), PERMISSIONS_CODE)
    }
}
