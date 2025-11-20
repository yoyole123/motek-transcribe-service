from transcriber.utils import generate_positive_personal_message


def test_generate_positive_personal_message_basic_structure():
    msg = generate_positive_personal_message("alice@example.com")
    lines = msg.splitlines()
    # Expect at least 3 lines (greeting, energy, boosts, maybe closing -> 4)
    assert len(lines) >= 3
    # Greeting line should mention time of day phrase or have a dash
    assert any(token in lines[0].lower() for token in ["morning", "afternoon", "evening", "early hours"]) or "—" in lines[0]


def test_generate_positive_personal_message_variation_and_personalization():
    msgs = [generate_positive_personal_message("alice@example.com") for _ in range(6)]
    # Ensure variation (extremely unlikely all identical). Allow small chance; require >1 unique.
    assert len(set(msgs)) > 1
    # At least one greeting line should include the derived nickname 'alice'
    assert any(m.splitlines()[0].lower().count("alice") for m in msgs)


