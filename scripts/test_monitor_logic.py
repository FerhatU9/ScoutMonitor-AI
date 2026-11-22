

from monitor_logic import detect_change


# Fictional test cases
tests = [
    ("First snapshot", None, (1, 2),
     "WAITING_FOR_HISTORY"),

    ("Performance increased", (1, 2), (2, 3),
     "CHANGE_DETECTED"),

    ("No performance change", (2, 3), (2, 3),
     "NO_CHANGE"),

    ("Suspicious decrease", (2, 3), (1, 3),
     "REVIEW_DATA"),

    ("Missing assists", (1, 2), (2, None),
     "MISSING_STATS"),
]


# Check each scenario
for name, previous, current, expected in tests:
    result = detect_change(previous, current)

    assert result == expected, (
        f"{name}: expected {expected}, got {result}"
    )

    print(f"PASS: {name} -> {result}")

print("\nAll 5 monitoring tests passed!")
