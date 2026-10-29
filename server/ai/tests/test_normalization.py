"""Tests for symptom normalization across projectors, microphones, and smart boards."""

from server.ai.diagnosis.models import DeviceType
from server.ai.diagnosis.normalizer import SymptomNormalizer


def test_normalize_projector_no_signal():
    raw = "The projector is on and has a blue light, but my laptop screen isn't showing and says No Signal."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="projector")

    assert norm.device_type == DeviceType.PROJECTOR.value
    assert norm.symptom_category == "no_signal"
    assert norm.original_symptom == raw
    assert len(norm.probable_causes) >= 2
    assert any("source" in c.lower() or "input" in c.lower() for c in norm.probable_causes)
    assert len(norm.missing_information) >= 1


def test_normalize_projector_no_power():
    raw = "The projector won't turn on at all, power light is completely unlit."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="projector")

    assert norm.symptom_category == "no_power"
    assert "power" in norm.observed_status.lower()


def test_normalize_microphone_no_sound():
    raw = "Microphone is turned on but no sound is coming through the speakers."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="microphone")

    assert norm.device_type == DeviceType.MICROPHONE.value
    assert norm.symptom_category == "no_audio"
    assert any("mute" in c.lower() or "batter" in c.lower() for c in norm.probable_causes)
    assert any("mute" in m.lower() for m in norm.missing_information)


def test_normalize_microphone_static():
    raw = "The mic makes a loud crackling static whenever the speaker moves."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="microphone")

    assert norm.symptom_category == "audio_distortion"


def test_normalize_smart_board_unresponsive_touch():
    raw = "The board shows my desktop screen, but touching the screen with finger or stylus does nothing."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="smart_board")

    assert norm.device_type == DeviceType.SMART_BOARD.value
    assert norm.symptom_category == "touch_unresponsive"
    assert any("usb" in c.lower() for c in norm.probable_causes)


def test_normalize_preserves_original_text():
    raw = "Weird blue screen popping up on projector in room 302."
    norm = SymptomNormalizer.normalize(raw, device_type_hint="projector")

    assert norm.original_symptom == raw

