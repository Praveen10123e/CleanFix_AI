"""Adaptive question selector for CleanFix AI.

Selects targeted questions that reduce diagnostic uncertainty, asking one question
at a time and avoiding questions already answered in the session history.
"""


from server.ai.diagnosis.models import (
    DeviceType,
    DiagnosticQuestion,
    NormalizedSymptom,
    QuestionInputType,
    SessionContext,
)


class QuestionSelector:
    """Selects targeted, low-friction diagnostic questions."""

    @classmethod
    def select_question(
        cls,
        session_context: SessionContext,
        normalized: NormalizedSymptom,
    ) -> DiagnosticQuestion | None:
        """
        Evaluates session context and returns the most useful unasked question.
        Returns None if no further clarifying question is needed before recommending a step.
        """
        answered_qids = {q.question_id for q in session_context.previous_questions}
        device_type = session_context.device_type or normalized.device_type

        # Device-specific question candidate trees
        if device_type == DeviceType.PROJECTOR.value:
            candidates = cls._projector_questions(normalized)
        elif device_type == DeviceType.MICROPHONE.value:
            candidates = cls._microphone_questions(normalized)
        elif device_type == DeviceType.SMART_BOARD.value:
            candidates = cls._smart_board_questions(normalized)
        else:
            candidates = []

        # Find first question not yet asked
        for question in candidates:
            if question.question_id not in answered_qids:
                return question

        return None

    @classmethod
    def _projector_questions(cls, normalized: NormalizedSymptom) -> list[DiagnosticQuestion]:
        standard_opts = ["Yes", "No", "Not sure", "Unable to perform"]

        questions = [
            DiagnosticQuestion(
                question_id="Q_PROJ_POWER_LIGHT",
                text="Is the projector's power light solid blue/green, or is it flashing / off?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=["Solid blue or green", "Flashing orange/red", "Completely unlit", "Cannot see ceiling unit"],
            ),
            DiagnosticQuestion(
                question_id="Q_PROJ_LAPTOP_OS",
                text="What type of laptop are you connecting?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=["Windows Laptop", "Apple Mac / MacBook", "Chromebook / Linux", "Not sure"],
            ),
            DiagnosticQuestion(
                question_id="Q_PROJ_CABLE_TYPE",
                text="Are you connected using a physical HDMI cable plugged into the wall/desk plate?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=standard_opts,
            ),
        ]
        return questions

    @classmethod
    def _microphone_questions(cls, normalized: NormalizedSymptom) -> list[DiagnosticQuestion]:
        standard_opts = ["Yes", "No", "Not sure", "Unable to perform"]

        questions = [
            DiagnosticQuestion(
                question_id="Q_MIC_SWITCH_STATE",
                text="Is the switch on the microphone currently toggled to 'ON' (not Mute or Off)?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=standard_opts,
            ),
            DiagnosticQuestion(
                question_id="Q_MIC_BATTERY_LIGHT",
                text="Is the battery light on the microphone glowing green?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=["Solid green", "Red or flashing", "Completely dark", "Not sure"],
            ),
            DiagnosticQuestion(
                question_id="Q_MIC_PODIUM_VOLUME",
                text="Is the classroom master volume or 'Wireless Mic' volume turned up on the podium?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=standard_opts,
            ),
        ]
        return questions

    @classmethod
    def _smart_board_questions(cls, normalized: NormalizedSymptom) -> list[DiagnosticQuestion]:
        standard_opts = ["Yes", "No", "Not sure", "Unable to perform"]

        questions = [
            DiagnosticQuestion(
                question_id="Q_SMART_FINGER_VS_PEN",
                text="Does the screen respond when you touch it directly with your bare finger?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=["Yes, finger works but stylus does not", "No, neither finger nor stylus works", "Not sure"],
            ),
            DiagnosticQuestion(
                question_id="Q_SMART_USB_CONNECTED",
                text="Is the separate USB touch cable (USB-A to USB-B) plugged into your laptop?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=standard_opts,
            ),
            DiagnosticQuestion(
                question_id="Q_SMART_IMAGE_VISIBLE",
                text="Can you clearly see your laptop screen projected onto the smart board?",
                input_type=QuestionInputType.SINGLE_CHOICE,
                options=standard_opts,
            ),
        ]
        return questions

