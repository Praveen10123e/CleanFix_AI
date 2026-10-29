"""Approved Diagnostic Action Registry for classroom AV equipment.

Defines permitted low-risk actions per device category. Actions not registered here
cannot be recommended by the diagnostic engine.
"""


from pydantic import BaseModel, Field

from server.ai.diagnosis.models import SafetyLevel


class ApprovedAction(BaseModel):
    """Definition of a verified, low-risk diagnostic action."""
    action_id: str = Field(description="Unique action registry identifier")
    device_type: str = Field(description="Target device type (projector, microphone, smart_board)")
    category: str = Field(description="Action category (e.g. source_selection, cable_check)")
    title: str = Field(description="Short human-readable title")
    instruction: str = Field(description="Clear, non-technical instruction for faculty")
    reason: str = Field(description="Rationale explaining why this step is necessary")
    expected_observation: str = Field(description="What the user should observe if successful")
    safety_level: SafetyLevel = Field(default=SafetyLevel.LOW)
    requires_confirmation: bool = Field(default=True)
    priority: int = Field(default=10, description="Default sequence priority (lower = earlier)")


# Pre-approved action catalog strictly vetted for faculty self-service
ACTION_REGISTRY: dict[str, ApprovedAction] = {
    # --- Projector Actions ---
    "PROJ_SOURCE_SEARCH": ApprovedAction(
        action_id="PROJ_SOURCE_SEARCH",
        device_type="projector",
        category="source_selection",
        title="Check Projector Input Source",
        instruction="Press the 'Source Search' or 'Input' button on the projector remote control or the wall control panel until HDMI 1 is selected.",
        reason="When a laptop is connected, the projector may still be listening to an inactive input port, displaying a 'No Signal' screen.",
        expected_observation="The projector switches to the correct port and your laptop desktop or presentation appears.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=1,
    ),
    "PROJ_LAPTOP_DUPLICATE_DISPLAY": ApprovedAction(
        action_id="PROJ_LAPTOP_DUPLICATE_DISPLAY",
        device_type="projector",
        category="device_settings",
        title="Configure Laptop Display Output",
        instruction="On your laptop, press Windows Key + P and select 'Duplicate' (or on macOS, open System Settings > Displays and select 'Mirror').",
        reason="Laptops frequently disable external display output when newly connected to conserve battery or maintain privacy.",
        expected_observation="The laptop screen output is mirrored onto the projector screen.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=2,
    ),
    "PROJ_CHECK_HDMI_CABLE_RESEAT": ApprovedAction(
        action_id="PROJ_CHECK_HDMI_CABLE_RESEAT",
        device_type="projector",
        category="cable_connection",
        title="Reseat Accessible Video Cable",
        instruction="Unplug the HDMI or display cable from your laptop and the desk/wall plate, check that no pins are bent, and plug both ends back in firmly.",
        reason="A slightly loose HDMI connection can cause digital handshake failure, producing a blue screen, snow, or 'No Signal'.",
        expected_observation="The connection handshakes and video immediately transmits to the display.",
        safety_level=SafetyLevel.MEDIUM,
        requires_confirmation=True,
        priority=3,
    ),
    "PROJ_CHECK_POWER_LED": ApprovedAction(
        action_id="PROJ_CHECK_POWER_LED",
        device_type="projector",
        category="power_verification",
        title="Inspect Power Status LED",
        instruction="Look at the projector power indicator light on the projector body or wall control plate and note if it is solid blue/green or flashing amber/red.",
        reason="A flashing warning light indicates a cooling cycle, lamp alert, or overheating protection rather than an input issue.",
        expected_observation="The power light is solid blue or green, indicating normal operating status.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=4,
    ),
    "PROJ_CHECK_LENS_SHUTTER": ApprovedAction(
        action_id="PROJ_CHECK_LENS_SHUTTER",
        device_type="projector",
        category="device_settings",
        title="Check Lens Cover or A/V Mute",
        instruction="Check if the physical lens shutter on the front of the projector is slid open, and press the 'A/V Mute' button on the remote to ensure blanking is off.",
        reason="An engaged A/V Mute or closed lens shutter blocks projection even while the projector lamp is fully powered.",
        expected_observation="The projector light beam projects clearly onto the classroom screen.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=5,
    ),
    "PROJ_POWER_CYCLE_REMOTE": ApprovedAction(
        action_id="PROJ_POWER_CYCLE_REMOTE",
        device_type="projector",
        category="power_verification",
        title="Soft Power Cycle via Remote",
        instruction="Press the Power button on the remote control to put the projector into standby, wait 30 seconds for the fan cycle, then press Power to turn it back on.",
        reason="A soft power cycle resets internal digital EDID handshake buffers without risking electrical hazards.",
        expected_observation="The projector reboots cleanly and redetects the laptop signal.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=6,
    ),

    # --- Microphone Actions ---
    "MIC_CHECK_MUTE_SWITCH": ApprovedAction(
        action_id="MIC_CHECK_MUTE_SWITCH",
        device_type="microphone",
        category="device_settings",
        title="Verify Microphone Power & Mute Switch",
        instruction="Check the physical power switch on the microphone body. Ensure it is switched to 'ON' and not set to 'MUTE' or 'STANDBY'.",
        reason="Microphone switches commonly have a middle 'Mute' detent that leaves the device powered on but silences audio output.",
        expected_observation="The microphone status light turns solid green and your voice amplifies through the classroom speakers.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=1,
    ),
    "MIC_CHECK_BATTERY_LED": ApprovedAction(
        action_id="MIC_CHECK_BATTERY_LED",
        device_type="microphone",
        category="power_verification",
        title="Inspect Microphone Battery Indicator",
        instruction="Look at the battery icon or LED indicator on the microphone handle/pack. If the LED is red or unlit, the battery is depleted.",
        reason="Depleted transmitter batteries prevent the microphone from transmitting RF audio to the classroom receiver.",
        expected_observation="The battery indicator shows green or at least 2 bars of remaining charge.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=2,
    ),
    "MIC_REPLACE_AA_BATTERIES": ApprovedAction(
        action_id="MIC_REPLACE_AA_BATTERIES",
        device_type="microphone",
        category="device_settings",
        title="Replace Microphone Batteries",
        instruction="Slide open the external battery compartment at the base of the microphone, replace the two AA batteries with fresh ones from the podium drawer, and close the lid.",
        reason="Weak batteries cause audio dropouts, distortion, or complete lack of transmission.",
        expected_observation="The microphone powers on immediately with a solid green battery indicator.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=3,
    ),
    "MIC_CHECK_ROOM_VOLUME": ApprovedAction(
        action_id="MIC_CHECK_ROOM_VOLUME",
        device_type="microphone",
        category="device_settings",
        title="Check Podium Audio Volume Control",
        instruction="Locate the master volume knob or touchscreen slider on the instructor podium and ensure the 'Wireless Mic' volume is raised and not muted.",
        reason="The microphone may be transmitting properly while the classroom amplifier or podium mixer channel is muted.",
        expected_observation="Microphone audio is clearly audible throughout the room.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=4,
    ),
    "MIC_CHECK_RECEIVER_POWER": ApprovedAction(
        action_id="MIC_CHECK_RECEIVER_POWER",
        device_type="microphone",
        category="power_verification",
        title="Inspect AV Rack Receiver Unit",
        instruction="Look at the wireless receiver mounted in the podium rack. Verify that its front panel LCD screen is lit and the RF signal meter illuminates when speaking.",
        reason="If the receiver has lost AC power or has been switched off, no audio will route to the room amplifiers.",
        expected_observation="The receiver display is illuminated and the RF/Audio LED meters bounce in response to your voice.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=5,
    ),
    "MIC_VERIFY_FREQUENCY_SYNC": ApprovedAction(
        action_id="MIC_VERIFY_FREQUENCY_SYNC",
        device_type="microphone",
        category="device_settings",
        title="Verify Frequency/Channel Match",
        instruction="Compare the Group and Channel numbers displayed on the microphone body with the numbers shown on the receiver front panel.",
        reason="If the microphone and receiver are on different channels, the receiver will not decode the wireless signal.",
        expected_observation="Both channel numbers match identically and the RF meter lights up.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=6,
    ),

    # --- Smart Board Actions ---
    "SMART_CHECK_USB_TOUCH_CABLE": ApprovedAction(
        action_id="SMART_CHECK_USB_TOUCH_CABLE",
        device_type="smart_board",
        category="cable_connection",
        title="Check USB Touch Cable Connection",
        instruction="Verify that the USB cable (Type-A to Type-B or USB-C touch cable) is securely plugged into both your laptop and the interactive board wall plate.",
        reason="Video (HDMI) and interactive touch (USB) run through separate cables. A loose USB cable allows video display but disables touch input.",
        expected_observation="Your laptop chimes for new USB device connection and the board begins responding to touch.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=1,
    ),
    "SMART_CHECK_TOUCH_POWER": ApprovedAction(
        action_id="SMART_CHECK_TOUCH_POWER",
        device_type="smart_board",
        category="power_verification",
        title="Check Smart Board Power Indicator",
        instruction="Press the power button on the bottom-right bezel of the smart board to verify the interactive frame is powered on.",
        reason="Some interactive flat panels have an independent power switch for the Android/touch controller distinct from the display backlight.",
        expected_observation="The smart board indicator changes to solid white/green and touch sensors activate.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=2,
    ),
    "SMART_CHECK_TOUCH_LOCK": ApprovedAction(
        action_id="SMART_CHECK_TOUCH_LOCK",
        device_type="smart_board",
        category="device_settings",
        title="Verify Touch Lock Button",
        instruction="Check the physical control bar on the front bezel to ensure the 'Touch Freeze' or 'Touch Lock' icon is not illuminated.",
        reason="The Touch Lock feature intentionally disables touch interaction to prevent accidental palm marks during presentations.",
        expected_observation="Touch Lock is toggled off and the screen responds immediately to finger contact.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=3,
    ),
    "SMART_TEST_FINGER_TOUCH": ApprovedAction(
        action_id="SMART_TEST_FINGER_TOUCH",
        device_type="smart_board",
        category="device_settings",
        title="Test Finger vs. Stylus Touch",
        instruction="Touch the screen directly with your index finger. If your finger moves the cursor but the stylus does not, the stylus battery or nib needs replacement.",
        reason="Distinguishes between a board-wide touch sensor failure and a dead active stylus pen.",
        expected_observation="Cursor moves with finger touch, isolating the problem to the stylus pen.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=4,
    ),
    "SMART_RESTART_SMART_SERVICE": ApprovedAction(
        action_id="SMART_RESTART_SMART_SERVICE",
        device_type="smart_board",
        category="software_check",
        title="Restart Interactive Touch Software",
        instruction="On your laptop, locate the interactive touch icon (e.g. SMART Ink or Touch Service) in the system tray, right-click, and select 'Restart Service'.",
        reason="The background touch driver service can occasionally become unresponsive after a sleep or hibernate cycle.",
        expected_observation="The touch driver reconnects and touch interaction resumes immediately.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=5,
    ),
    "SMART_LAUNCH_CALIBRATION": ApprovedAction(
        action_id="SMART_LAUNCH_CALIBRATION",
        device_type="smart_board",
        category="software_check",
        title="Run Touch Calibration Tool",
        instruction="Open the SMART Settings or Windows Tablet PC Settings on your laptop, click 'Calibrate', and touch each crosshair on the screen.",
        reason="Coordinate drift can cause touch inputs to register several inches away from the actual contact point.",
        expected_observation="The cursor aligns accurately under your fingertip or stylus tip.",
        safety_level=SafetyLevel.LOW,
        requires_confirmation=True,
        priority=6,
    ),
}


def get_approved_action(action_id: str) -> ApprovedAction | None:
    """Retrieve an approved action by ID."""
    return ACTION_REGISTRY.get(action_id)


def get_approved_actions_for_device(device_type: str) -> list[ApprovedAction]:
    """Retrieve all approved actions for a given device type, ordered by priority."""
    actions = [a for a in ACTION_REGISTRY.values() if a.device_type == device_type]
    actions.sort(key=lambda x: x.priority)
    return actions

