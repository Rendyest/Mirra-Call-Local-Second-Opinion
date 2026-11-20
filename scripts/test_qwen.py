from model_client import MODEL_NAME, client

print(f"Connecting to {MODEL_NAME}...")

try:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": (
                "List three observable signs that someone is struggling "
                "with a face-washing movement. Keep your answer brief."
            ),
        }],
        max_tokens=1000,
    )
    print(f"\n{MODEL_NAME} response:")
    print(response.choices[0].message.content)
    print("\n--- FULL API RESPONSE ---")
    print(response.model_dump_json(indent=2))
except Exception as error:
    print(f"\nAPI request failed: {type(error).__name__}")
    print(str(error))