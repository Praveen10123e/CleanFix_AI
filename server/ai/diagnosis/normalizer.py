"""Symptom Normalizer for CleanFix AI.

Translates natural-language faculty descriptions into structured interpretations
while preserving original text and treating hypotheses as candidate causes, not
confirmed diagnoses.
"""

from server.ai.diagnosis.models import DeviceType, NormalizedSymptom


class SymptomNormalizer:
    """Parses natural-language AV issue descriptions into candidate structured diagnostics."""

    @classmethod
    def normalize(cls, raw_symptom: str, device_type_hint: str = "projector") -> NormalizedSymptom:
        """
        Normalizes natural language symptom into candidate category, status, and causes.
        """
        text = raw_symptom.strip()
        lower_text = text.lower()

        # Inferred or confirmed device type
        device_type = cls._resolve_device_type(lower_text, device_type_hint)

        if device_type == DeviceType.PROJECTOR.value:
            category, status, causes, missing_info = cls._normalize_projector(lower_text)
        elif device_type == DeviceType.MICROPHONE.value:
            category, status, causes, missing_info = cls._normalize_microphone(lower_text)
        elif device_type == DeviceType.SMART_BOARD.value:
            category, status, causes, missing_info = cls._normalize_smart_board(lower_text)
        else:
            category = "unknown_device_issue"
            status = "Unspecified device issue reported."
            causes = ["Device context not matched"]
            missing_info = ["Confirmed device category", "Active symptoms"]

        return NormalizedSymptom(
            device_type=device_type,
            symptom_category=category,
            observed_status=status,
            probable_causes=causes,
            missing_information=missing_info,
            original_symptom=text,
        )

    @classmethod
    def _resolve_device_type(cls, lower_text: str, hint: str) -> str:
        """Resolves device type using explicit hint or keyword matches."""
        if hint in [d.value for d in DeviceType]:
            return hint
        if any(w in lower_text for w in ["projector", "projection", "screen display", "hdmi", "no signal"]):
            return DeviceType.PROJECTOR.value
        if any(w in lower_text for w in ["mic", "microphone", "sound", "voice", "audio", "speakers"]):
            return DeviceType.MICROPHONE.value
        if any(w in lower_text for w in ["smart board", "smartboard", "interactive display", "touch", "stylus", "pen"]):
            return DeviceType.SMART_BOARD.value
        return DeviceType.PROJECTOR.value

    @classmethod
    def _normalize_projector(cls, text: str) -> tuple[str, str, list[str], list[str]]:
        if "no signal" in text or "blue screen" in text or "blank screen" in text or "not showing" in text:
            category = "no_signal"
            status = "Projector appears powered on, but displays 'No Signal' or blank screen."
            causes = [
                "Projector input source set to incorrect port (e.g. HDMI 2 instead of HDMI 1)",
                "Laptop display projection disabled (Windows key + P not set to Duplicate)",
                "Loose or disconnected HDMI/video cable at desk or wall plate",
                "Laptop output resolution unsupported or display driver sleeping",
            ]
            missing_info = [
                "Current input source selected on projector",
                "Laptop operating system and display projection setting",
                "Physical cable connection status",
            ]
        elif "no power" in text or "won't turn on" in text or "dead" in text or "unlit" in text:
            category = "no_power"
            status = "Projector does not power on or status LED is completely unlit."
            causes = [
                "Master wall power switch turned off",
                "AC power cord disconnected from ceiling/wall box",
                "Remote control batteries depleted",
            ]
            missing_info = ["Wall switch status", "Power indicator LED color"]
        elif "blurry" in text or "fuzzy" in text or "out of focus" in text:
            category = "poor_image_quality"
            status = "Image is projecting but is blurry or misaligned."
            causes = ["Manual focus ring out of adjustment", "Incorrect laptop display resolution"]
            missing_info = ["Focus ring adjustment attempted", "Laptop output resolution"]
        else:
            category = "general_projection_issue"
            status = f"Reported projector anomaly: {text}"
            causes = ["Input mismatch or video handshake delay"]
            missing_info = ["Projector power LED state", "Input source selection"]

        return category, status, causes, missing_info

    @classmethod
    def _normalize_microphone(cls, text: str) -> tuple[str, str, list[str], list[str]]:
        if "no sound" in text or "silent" in text or "can't hear" in text or "not working" in text:
            category = "no_audio"
            status = "Microphone is in use, but no audio is heard through classroom speakers."
            causes = [
                "Microphone physical switch set to Mute or Standby",
                "Microphone transmitter batteries depleted or low",
                "Podium/wall master volume muted or set to zero",
                "Wireless receiver unit unpowered or channel desynchronized",
            ]
            missing_info = [
                "Physical mute switch position",
                "Battery indicator LED color",
                "Podium master volume level",
            ]
        elif "static" in text or "crackling" in text or "distortion" in text:
            category = "audio_distortion"
            status = "Microphone produces static, crackling, or distorted sound."
            causes = [
                "Weak transmitter batteries",
                "RF interference from nearby wireless equipment",
                "Gain/volume set too high causing clipping",
            ]
            missing_info = ["Battery level", "Mic gain setting"]
        else:
            category = "general_microphone_issue"
            status = f"Reported microphone anomaly: {text}"
            causes = ["Mute engaged or battery depleted"]
            missing_info = ["Mute switch state", "Receiver RF meter activity"]

        return category, status, causes, missing_info

    @classmethod
    def _normalize_smart_board(cls, text: str) -> tuple[str, str, list[str], list[str]]:
        if "touch" in text or "pen" in text or "stylus" in text or "unresponsive" in text:
            category = "touch_unresponsive"
            status = "Display shows computer image, but touch/pen interaction does not respond."
            causes = [
                "USB touch cable (Type-A to Type-B) disconnected from laptop or wall plate",
                "Touch lock / freeze toggle enabled on front bezel",
                "Interactive display touch service crashed or stopped on laptop",
                "Stylus battery depleted (if finger touch works)",
            ]
            missing_info = [
                "USB touch cable connection status",
                "Whether finger touch responds vs. stylus only",
                "Touch lock LED state on bezel",
            ]
        elif "calibrat" in text or "offset" in text or "misaligned" in text:
            category = "touch_calibration"
            status = "Touch registers in incorrect screen position."
            causes = ["Touch coordinate calibration drift", "Display scaling mismatch"]
            missing_info = ["Touch calibration tool executed", "Laptop display scaling %"]
        else:
            category = "general_smart_board_issue"
            status = f"Reported interactive display anomaly: {text}"
            causes = ["USB touch disconnected or driver inactive"]
            missing_info = ["USB touch cable connection", "Touch frame power light"]

        return category, status, causes, missing_info

