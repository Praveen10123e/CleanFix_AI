"""Rule-based safe AV troubleshooting catalogue.

Provides non-invasive, safe troubleshooting workflows based on device category
and reported symptoms without requiring an external RAG engine or LLM.
"""

from typing import Any, Dict, List, Optional
from backend.app.models.enums import DeviceType

# -----------------------------------------------------------------------------
# SAFE TROUBLESHOOTING RULE CATALOGUE
# -----------------------------------------------------------------------------

TROUBLESHOOTING_CATALOGUE: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    DeviceType.PROJECTOR.value: {
        "no_image": [
            {
                "step_number": 1,
                "instruction": "Verify the projector power LED indicator on the chassis or wall controller. If amber, red, or blinking, press the power button once and wait 30 seconds for the lamp/laser ignition cycle.",
                "reason": "Commercial laser and lamp projectors require a timed cooling and warm-up sequence before displaying output.",
                "source_refs": {"rule_type": "POWER_CYCLE", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Check the AV Mute / Shutter toggle on the projector remote control or the wall touch panel. Ensure the physical lens shutter is slid completely open.",
                "reason": "AV Mute blanks the projection screen to black while keeping the projector running, often mistaken for no video output.",
                "source_refs": {"rule_type": "SHUTTER_CHECK", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "Ensure the HDMI cable is securely seated into your laptop and the wall/podium plate. On Windows, press Win + P and confirm 'Duplicate' or 'Extend' mode is selected.",
                "reason": "Operating system display output often defaults to 'PC screen only' when an external display is disconnected.",
                "source_refs": {"rule_type": "DISPLAY_OUTPUT_CHECK", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 4,
                "instruction": "If the status LED flashes red or an overheat/filter warning is visible, do not attempt to open the projector. Stop and escalate the issue to an AV technician.",
                "reason": "Internal thermal lockouts and lamp ballast faults require certified technician inspection.",
                "source_refs": {"rule_type": "SAFETY_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
        "no_signal": [
            {
                "step_number": 1,
                "instruction": "Check the input source selection on the room wall panel or projector remote. Switch between HDMI 1, HDMI 2, or PC input to match the connected cable.",
                "reason": "Projectors do not always auto-switch if another active input previously sent sync signals.",
                "source_refs": {"rule_type": "INPUT_SELECT", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Unplug the HDMI cable from both your computer and the podium wall box, inspect for bent pins, and firmly re-seat both ends.",
                "reason": "Loose HDMI pin connections interrupt the HDCP digital handshake.",
                "source_refs": {"rule_type": "CABLE_SEATING", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "On your laptop display settings, lower the refresh rate to 60Hz and resolution to 1920x1080 (1080p).",
                "reason": "Legacy matrix switchers or long conduit runs cannot sync with 4K or high refresh rate laptop signals.",
                "source_refs": {"rule_type": "RESOLUTION_SYNC", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 4,
                "instruction": "Try an alternate podium HDMI port or backup cable if available. If 'No Signal' persists, escalate to AV technician.",
                "reason": "In-wall transceivers, active optical cables, or switcher distribution amps may be faulty.",
                "source_refs": {"rule_type": "TECHNICIAN_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
        "default": [
            {
                "step_number": 1,
                "instruction": "Confirm the projector is powered on and the input source indicator matches the physical connection in the room.",
                "reason": "Verifies basic power and signal routing.",
                "source_refs": {"rule_type": "GENERAL_CHECK", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Check that the presenter laptop output is active (Win + P to Duplicate) and video cables are firmly plugged in.",
                "reason": "Resolves common loose cabling and display output toggles.",
                "source_refs": {"rule_type": "GENERAL_CABLE", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "Power cycle the room AV wall controller once. If problem persists, escalate to AV technician.",
                "reason": "Clears transient switcher buffer state.",
                "source_refs": {"rule_type": "GENERAL_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
    },
    DeviceType.MICROPHONE.value: {
        "no_sound": [
            {
                "step_number": 1,
                "instruction": "Check the physical power/mute switch on the microphone body. Ensure it is switched to ON (unmuted) and the green or amber indicator LED is lit.",
                "reason": "Microphone hardware switches are often left in the OFF or MUTE state between classes.",
                "source_refs": {"rule_type": "POWER_SWITCH", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Check the battery gauge on the microphone transmitter screen. If the indicator is low or blank, replace with two fresh AA batteries from the instructor desk.",
                "reason": "Depleted battery voltage is the primary cause of wireless transmitter shutdown.",
                "source_refs": {"rule_type": "BATTERY_REPLACEMENT", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "Inspect the wireless receiver in the rack: confirm the RF (Radio Frequency) sync light is solid blue or green and the AF (Audio Frequency) meter bounces when speaking.",
                "reason": "Confirms frequency pairing and capsule transduction before master room amplification.",
                "source_refs": {"rule_type": "RECEIVER_SYNC", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 4,
                "instruction": "Check the master room audio touch panel or volume knob on the podium. Ensure Master Mic volume is turned up to at least 50% and not muted.",
                "reason": "Podium master gain or DSP room mute blocks audio output to ceiling speakers.",
                "source_refs": {"rule_type": "MASTER_GAIN", "safety_level": "SAFE_NON_INVASIVE"},
            },
        ],
        "intermittent": [
            {
                "step_number": 1,
                "instruction": "Ensure direct line-of-sight between the wireless transmitter and the receiver antennas on the ceiling or wall. Avoid wrapping your hand around the antenna base.",
                "reason": "Human body tissue causes strong RF attenuation and packet loss in digital wireless systems.",
                "source_refs": {"rule_type": "LINE_OF_SIGHT", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Inspect the battery compartment springs for loose fit or corrosion. Tap the microphone gently to observe if audio cuts out.",
                "reason": "Weak battery contact pressure produces instantaneous dropouts when moving.",
                "source_refs": {"rule_type": "BATTERY_CONTACTS", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "If crackling or dropouts persist across the room, switch to a backup wired or handheld mic and escalate to technician.",
                "reason": "May indicate local RF frequency interference or a degraded wireless antenna distribution amplifier.",
                "source_refs": {"rule_type": "TECHNICIAN_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
        "default": [
            {
                "step_number": 1,
                "instruction": "Confirm the microphone is powered on with fresh batteries and the mute switch is disabled.",
                "reason": "Resolves common power and mute oversights.",
                "source_refs": {"rule_type": "GENERAL_MIC", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Check the master room audio slider on the podium wall controller to ensure volume is unmuted and at 50%.",
                "reason": "Verifies room audio routing.",
                "source_refs": {"rule_type": "GENERAL_GAIN", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "If sound is still not produced, escalate to the AV technician team for audio DSP diagnosis.",
                "reason": "System-level amplifier or mixer issue requires technician access.",
                "source_refs": {"rule_type": "GENERAL_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
    },
    DeviceType.SMART_BOARD.value: {
        "touch_not_working": [
            {
                "step_number": 1,
                "instruction": "Check the USB Touch cable connecting the classroom PC or presenter laptop to the interactive display. Ensure it is plugged into a USB 3.0 port.",
                "reason": "Touch digitizers operate over a dedicated USB HID connection independent of the HDMI video cable.",
                "source_refs": {"rule_type": "USB_TOUCH_CABLE", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Inspect the perimeter bezel of the smartboard for dust, marker debris, or obstructions. Wipe the optical/infrared sensor track gently with a clean dry microfiber cloth.",
                "reason": "Optical and IR touch frames register false touches or freeze when foreign objects block sensor pathways.",
                "source_refs": {"rule_type": "SENSOR_CLEAN", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "Open the SMART / ViewSonic driver icon in the Windows system tray and run the touch calibration or touch service restart utility.",
                "reason": "Recalibrates digitizer coordinate mapping and restarts hung background driver services.",
                "source_refs": {"rule_type": "DRIVER_CALIBRATION", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 4,
                "instruction": "Restart the smartboard using the front power standby button (hold 3 seconds, wait 10 seconds, press to power back on). If touch remains unresponsive, escalate to technician.",
                "reason": "Performs digitizer firmware cold reboot; hardware faults require technician service.",
                "source_refs": {"rule_type": "TECHNICIAN_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
        "display_not_working": [
            {
                "step_number": 1,
                "instruction": "Check the main AC rocker power switch located on the bottom or rear panel of the display. Ensure it is in the ON position and the front power LED is illuminated.",
                "reason": "Physical rocker switches are sometimes turned off during overnight maintenance.",
                "source_refs": {"rule_type": "AC_POWER_SWITCH", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Press the Power button on the front bezel or remote control. Confirm the brand logo displays on screen.",
                "reason": "Wakes display from deep energy-saving sleep mode.",
                "source_refs": {"rule_type": "STANDBY_WAKE", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "On the display on-screen menu, select the correct input channel (e.g. OPS Slot, HDMI 1, or Type-C) corresponding to your computer connection.",
                "reason": "Ensures the display is reading from the connected video port.",
                "source_refs": {"rule_type": "INPUT_SELECT", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 4,
                "instruction": "If the screen stays completely black or power LED blinks an error code, do not disassemble. Escalate immediately to an AV technician.",
                "reason": "Internal power supply or backlight failure requires bench repair by a qualified technician.",
                "source_refs": {"rule_type": "SAFETY_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
        "default": [
            {
                "step_number": 1,
                "instruction": "Verify the smartboard is powered on and the input source matches the connected instructor laptop or podium PC.",
                "reason": "Basic power and channel routing check.",
                "source_refs": {"rule_type": "GENERAL_DISPLAY", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 2,
                "instruction": "Check both the HDMI video cable and the USB touch cable between the computer and display.",
                "reason": "Ensures dual connectivity for video and touch.",
                "source_refs": {"rule_type": "GENERAL_CABLES", "safety_level": "SAFE_NON_INVASIVE"},
            },
            {
                "step_number": 3,
                "instruction": "Restart the display using the front standby button. If issue persists, escalate to technician.",
                "reason": "Resets onboard Android / display controller.",
                "source_refs": {"rule_type": "GENERAL_ESCALATION", "safety_level": "TECHNICIAN_ESCALATION"},
            },
        ],
    },
}


def get_troubleshooting_steps(device_type: str, symptom: str) -> List[Dict[str, Any]]:
    """Determine the sequence of safe troubleshooting steps for a device category and symptom."""
    dev_type_norm = device_type.strip().upper()
    symptom_norm = symptom.strip().lower()

    category_rules = TROUBLESHOOTING_CATALOGUE.get(dev_type_norm)
    if not category_rules:
        # Fallback to projector default if unknown category
        category_rules = TROUBLESHOOTING_CATALOGUE[DeviceType.PROJECTOR.value]

    # Keyword matching for specific problem types
    if dev_type_norm == DeviceType.PROJECTOR.value:
        if any(w in symptom_norm for w in ["signal", "detect", "handshake", "source", "input", "blue screen"]):
            return category_rules["no_signal"]
        return category_rules["no_image"]

    elif dev_type_norm == DeviceType.MICROPHONE.value:
        if any(w in symptom_norm for w in ["cut", "intermittent", "drop", "crackl", "static", "noise"]):
            return category_rules["intermittent"]
        return category_rules["no_sound"]

    elif dev_type_norm in (DeviceType.SMART_BOARD.value, DeviceType.DISPLAY.value):
        if any(w in symptom_norm for w in ["touch", "pen", "write", "finger", "calibrat"]):
            return category_rules["touch_not_working"]
        return category_rules["display_not_working"]

    return category_rules.get("default", category_rules[list(category_rules.keys())[0]])

