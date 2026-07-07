# Demo Script — 3 Minutes Word for Word

### Setup Before Judges Arrive

- Place the pressure mat on the edge of the table (so judges can physically step on it or press it with their hands).
- Arduino on the left, connected via USB to a power bank or powered USB hub.
- Snapdragon X PC in the center, screen showing the `pc_main.py` console with live risk scores visible.
- Android phone on a stand on the right, displaying the StampedeShield application screen.
- Slide deck open on a second screen or printed out.

---

### Word-for-Word Script (3 minutes)

**[0:00 – 0:20] Open with the problem**
> "In 2024, 121 people died in the Hathras stampede. In 2013, 115 died in Ratangarh. In both cases, the dangerous compression wave had been building up in the crowd for over 90 seconds before a single marshal saw it. StampedeShield detects it in under one second."

**[0:20 – 0:40] Introduce the system**
> "We built a four-device edge AI system where every device has a unique, non-interchangeable role. Remove any single device, and the system breaks in a different, provable way."
> *(Point to each device physically: pressure mat ➔ Arduino ➔ PC ➔ phone)*

**[0:40 – 1:00] Show normal state**
> "Right now, with no one on the mat, the zone is classified as Green (Safe). The risk score is sitting low at 12. Inference time on the Snapdragon X NPU is just 38 milliseconds. The core pipeline is completely offline, requiring zero cloud connectivity."

**[1:00 – 1:40] The demo moment**
> "Could one of you please step on or press down on the mat?"
> *(Judge presses or steps on the mat. Pressure increases. The PC console shows the risk climbing. The Android phone screen turns Yellow, then vibrates and turns Red as pressure spikes).*
> "That took under one second. Mat pressure ➔ Bluetooth ➔ Snapdragon NPU ➔ risk classification ➔ Android haptic alert. All computed on-device."

**[1:40 – 2:20] Multi-device proof**
> "Let me prove that every device is irreplaceable:
> - If I unplug the Arduino: The PC receives nothing. The system is blind.
> - If I kill the PC process: There is no NPU inference. The risk score is never computed.
> - If I put the phone in airplane mode: The alert is computed but marshals never see it.
> Three different failure modes, three unique hardware roles."

**[2:20 – 2:45] Edge-first and impact**
> "This system operates entirely offline. In massive Indian gatherings like the Kumbh Mela, where 400 million people gather and cellular networks saturate, cloud-based systems fail. StampedeShield keeps running. It costs under ₹8,000 to deploy, captures no biometric or video data, and is fully compliant with the DPDP Act."

**[2:45 – 3:00] Close**
> "Five engineers. Twenty-four hours. Fully MIT licensed, open-source, and live on GitHub."
> *(Show QR code pointing to https://github.com/shyamvigneshk27-pixel/Stark-x)*
