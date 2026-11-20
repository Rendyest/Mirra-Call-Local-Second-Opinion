import json

from model_client import MODEL_NAME, client, response_text


def validate_coaching(result):
    """Validate Qwen's coaching response."""

    required_fields = {
        "struggling": bool,
        "signal": str,
        "body_part": str,
        "severity": str,
        "cue_text": str,
        "ask_pain_check": bool,
        "safety_concern": bool,
    }

    if not isinstance(result, dict):
        raise ValueError("Coaching response must be a JSON object")

    for field, expected_type in required_fields.items():
        if field not in result:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(result[field], expected_type):
            raise ValueError(f"Invalid type for field: {field}")

    allowed_severities = {"none", "mild", "moderate", "high"}
    if result["severity"] not in allowed_severities:
        raise ValueError("Invalid severity value")
    if not result["cue_text"].strip():
        raise ValueError("Coaching cue cannot be empty")
    if len(result["cue_text"]) > 200:
        raise ValueError("Coaching cue is too long")
    return result


def generate_coaching(movement_data):
    """Generate a brief, safety-conscious movement coaching response."""
    prompt = f"""
You are the AI coaching component of Mirra Call,
an assistive rehabilitation system.

A person is performing a face-washing movement.

Movement observations:
{json.dumps(movement_data, indent=2)}

Your task:
1. Identify the observable movement difficulty.
2. Generate one short, supportive coaching cue.
3. Flag whether a pain check may be appropriate.
4. Flag any potential safety concern.

Important rules:
- Do not diagnose medical conditions.
- Do not claim the person is experiencing pain.
- Do not encourage pushing through pain.
- Do not recommend increasing movement intensity.
- Base your response only on the observations.
- If observations are insufficient, say so.
- Return valid JSON only, without markdown.

Return exactly these fields: struggling (boolean), signal (string),
body_part (string), severity (none, mild, moderate, or high),
cue_text (string, at most 200 characters), ask_pain_check (boolean),
and safety_concern (boolean).
"""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1200,
    )
    try:
        return validate_coaching(json.loads(response_text(response)))
    except json.JSONDecodeError as error:
        raise ValueError("Qwen returned invalid JSON") from error


if __name__ == "__main__":
    sample_movement = {
        "task": "face_washing",
        "elbow_angle": 70,
        "shoulder_elevation": 45,
        "struggle_signal": "stall",
        "stall_duration_seconds": 3,
    }
    print(f"Sending movement data to {MODEL_NAME}...")
    try:
        result = generate_coaching(sample_movement)
        print(f"\n{MODEL_NAME} coaching response:")
        print(json.dumps(result, indent=2))
    except Exception as error:
        print(f"\nError: {type(error).__name__}: {error}")