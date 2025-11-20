import random
from datetime import datetime

"""Utility helpers (text cleaning, etc.)."""

def clean_some_unicode_from_text(text: str) -> str:
    chars_to_remove = "\u061C"  # Arabic letter mark
    chars_to_remove += "\u200B\u200C\u200D"  # Zero-width space, non/ joiner
    chars_to_remove += "\u200E\u200F"  # LTR/RTL marks
    chars_to_remove += "\u202A\u202B\u202C\u202D\u202E"  # embeddings/overrides
    chars_to_remove += "\u2066\u2067\u2068\u2069"  # isolate controls
    chars_to_remove += "\uFEFF"  # zero-width no-break space
    return text.translate({ord(c): None for c in chars_to_remove})


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Sanitize a filename (without path). Keeps Unicode letters/digits, replaces unsafe chars.

    Windows reserved characters: < > : " / \ | ? * and control chars are replaced.
    Also trims whitespace and collapses repeats of the replacement.
    Falls back to 'file' if the cleaned base is empty or composed solely of replacement characters.
    """
    import re
    # Remove path components just in case
    base = name.split('/')[-1].split('\\')[-1]
    # Replace reserved characters
    base = re.sub(r'[<>:"/\\|?*]+', replacement, base)
    # Remove control characters
    base = re.sub(r'[\x00-\x1F\x7F]+', '', base)
    # Collapse multiple replacements
    base = re.sub(rf'{re.escape(replacement)}{{2,}}', replacement, base)
    # Strip leading/trailing dots and spaces (Windows quirk)
    base = base.strip(' .')
    # Fallback if empty or only replacement characters
    if not base or set(base) == {replacement}:
        base = 'file'
    return base[:200]  # limit length


def generate_positive_personal_message(recipient: str | None = None) -> str:
    """Generate a short upbeat personal message by composing multiple random parts.

    The message is built from: greeting + energy phrase + 2-3 shuffled boosts + closing.
    This creates large variety vs picking from a single list.
    """
    now = datetime.utcnow()
    hour = now.hour
    # Time-based greeting variants
    if hour < 6:
        tod = "early hours"
    elif hour < 12:
        tod = "morning"
    elif hour < 17:
        tod = "afternoon"
    else:
        tod = "evening"
    greetings = [
        f"Hey", f"Hi", f"Hello", f"Hey there", f"Greetings"
    ]
    if recipient:
        # Use part before @ for personalization if safe
        nick = recipient.split('@')[0][:25]
        nick = ''.join(ch for ch in nick if ch.isalnum() or ch in ('_', '-', '.'))
        if nick:
            greetings.append(f"Hi {nick}")
    greeting = random.choice(greetings) + f" — hope your {tod} is going well!"

    energy_phrases = [
        "May your focus feel light and steady today.",
        "Wishing you pockets of clarity and sparks of curiosity.",
        "Here's to smooth progress and zero friction moments.",
        "May momentum find you exactly when you need it.",
        "Let creative neurons fire in friendly sequence." ,
    ]
    energy = random.choice(energy_phrases)

    boosts_pool = [
        "A dash of calm", "a splash of motivation", "gentle sustained energy",
        "insight that arrives just in time", "solid breakthroughs", "refreshing mini-pauses",
        "nicely aligned priorities", "confident decisions", "quiet wins", "useful serendipity"
    ]
    random.shuffle(boosts_pool)
    boosts_selected = boosts_pool[: random.randint(2, 3)]
    # Compose boosts into a phrase
    if len(boosts_selected) == 1:
        boosts_phrase = boosts_selected[0]
    else:
        boosts_phrase = ", ".join(boosts_selected[:-1]) + f" and {boosts_selected[-1]}"
    boosts_sentence_starters = ["May you get", "Wishing you", "May today bring", "Here's to"]
    boosts_sentence = random.choice(boosts_sentence_starters) + f" {boosts_phrase}."

    closings = [
        "Keep going — you're doing great!", "Onward with good vibes!", "Have an excellent rest of your day!",
        "Sending a pulse of encouragement your way!", "Rooting for your progress!"
    ]
    closing = random.choice(closings)

    message = f"{greeting}\n{energy}\n{boosts_sentence}\n{closing}"
    return message

__all__ = [
    "clean_some_unicode_from_text",
    "sanitize_filename",
    "generate_positive_personal_message",
]
