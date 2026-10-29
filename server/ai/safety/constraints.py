"""Deterministic safety rules, hazard detection, and constraints for classroom AV equipment."""

import re


class SafetyHazardDetected(Exception):
    """Raised when an immediate safety hazard is identified in user reports."""
    def __init__(self, hazard_type: str, message: str):
        super().__init__(message)
        self.hazard_type = hazard_type
        self.message = message


# Critical hazards that require IMMEDIATE escalation and halting of self-service
HAZARD_PATTERNS = [
    (r"\b(smoke|smoking)\b", "smoke", "Smoke detected coming from the equipment."),
    (r"\b(spark|sparks|sparking)\b", "sparks", "Electrical sparking observed."),
    (r"\b(burning\s+(smell|odor)|smells?\s+like\s+burn)\b", "burning_odor", "Burning odor or overheating reported."),
    (r"\b(fire|flame|flames)\b", "fire", "Fire or active flames reported."),
    (r"\b(electric\s+shock|shocked|tingling\s+sensation)\b", "electric_shock", "Electric shock or tingling sensation upon touching equipment."),
    (r"\b(exposed\s+wires?|bare\s+wires?|frayed\s+cord|chewed\s+cable)\b", "exposed_wiring", "Exposed electrical conductors or damaged high-voltage cord."),
    (r"\b(water\s+damage|liquid\s+spill|water\s+leak|liquid\s+intrusion|spill(ed)?\s+.*?\b(water|liquid))\b", "liquid_damage", "Liquid intrusion or water spill into electronic chassis."),
    (r"\b(exploded|popped\s+loudly|loud\s+pop|burst\s+lamp)\b", "lamp_explosion", "Projector lamp explosion or component blowout."),
    (r"\b(shattered\s+glass|broken\s+screen\s+glass)\b", "shattered_glass", "Shattered optical glass or screen surface."),
    (r"\b(falling|loose\s+mount|hanging\s+by\s+wires?)\b", "structural_hazard", "Ceiling mount loose or equipment in danger of falling."),
]

# Prohibited actions that faculty should NEVER be instructed to perform
PROHIBITED_ACTION_KEYWORDS = [
    r"\bopen(\s+up)?\s+(the\s+)?(casing|cover|enclosure|housing|chassis|unit)\b",
    r"\bunscrew\b",
    r"\bremove\s+(the\s+)?(screws|lamp\s+cover|panel)\b",
    r"\breplace\s+(the\s+)?(lamp|bulb|ballast|fuse|circuit)\b",
    r"\btouch\s+(the\s+)?(bare\s+|internal\s+)?(wires?|terminals?|leads?|board|pcb)\b",
    r"\bdisassemble\b",
    r"\bbypass\s+(the\s+)?(safety|switch|interlock|ground)\b",
    r"\bclimb\s+(a\s+)?(ladder|chair|desk|table)\b",
    r"\bcut\s+(the\s+)?(wire|cable|cord)\b",
    r"\bsolder\b",
    r"\bhigh\s+voltage\b",
]

# Max attempts allowed before mandatory escalation
MAX_UNRESOLVED_STEPS = 5


def is_safety_hazard(text: str) -> tuple[str, str] | None:
    """
    Checks if the given text contains any critical safety hazard markers.
    Returns (hazard_type, message) or None if safe.
    """
    if not text:
        return None
    lower_text = text.lower()
    for pattern, hazard_type, message in HAZARD_PATTERNS:
        if re.search(pattern, lower_text):
            return hazard_type, message
    return None


def check_prohibited_actions(instruction_text: str) -> str | None:
    """
    Checks if an instruction contains prohibited physical actions.
    Returns matched prohibited action description or None if safe.
    """
    if not instruction_text:
        return None
    lower_text = instruction_text.lower()
    for pattern in PROHIBITED_ACTION_KEYWORDS:
        if re.search(pattern, lower_text):
            return f"Violates safety policy: matches prohibited action pattern '{pattern}'"
    return None
