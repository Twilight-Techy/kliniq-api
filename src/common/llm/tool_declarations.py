# src/common/llm/tool_declarations.py
"""Gemini native function declarations for Kliniq tools."""

from google.genai import types


GEMINI_TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="request_appointment",
            description=(
                "Request an appointment for the patient. Use when: "
                "the patient asks to book an appointment, the patient describes "
                "concerning symptoms that need medical attention, or you recommend "
                "the patient see a doctor."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "reason": types.Schema(
                        type=types.Type.STRING,
                        description="Description of why the appointment is needed",
                    ),
                    "urgency": types.Schema(
                        type=types.Type.STRING,
                        description="Urgency level: 'low', 'normal', or 'urgent'",
                        enum=["low", "normal", "urgent"],
                    ),
                    "department": types.Schema(
                        type=types.Type.STRING,
                        description=(
                            "Suggested department, e.g. 'General Practice', "
                            "'Cardiology', 'Emergency'"
                        ),
                    ),
                },
                required=["reason", "urgency"],
            ),
        ),
        types.FunctionDeclaration(
            name="create_triage",
            description=(
                "Create a triage case to document the patient's symptoms. Use when: "
                "the patient describes symptoms you want to document, or the patient "
                "needs symptoms assessed for urgency."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symptoms": types.Schema(
                        type=types.Type.STRING,
                        description="Description of the patient's symptoms",
                    ),
                    "urgency_level": types.Schema(
                        type=types.Type.STRING,
                        description="Urgency level: 'low', 'medium', or 'high'",
                        enum=["low", "medium", "high"],
                    ),
                    "notes": types.Schema(
                        type=types.Type.STRING,
                        description="Additional observations or recommendations",
                    ),
                },
                required=["symptoms", "urgency_level"],
            ),
        ),
    ]
)
