
from alert_logic import create_alert

# All statistics below are fictional test data.

tests = [
    ("Increase", (1, 2), (2, 3),
     "ALERT: Test Player | +1 goals | +1 assists"),

    ("No change", (2, 3), (2, 3), None),

    ("No history", None, (1, 2), None),

    ("Decrease", (2, 3), (1, 3), None),

    ("Missing data", (1, 2), (2, None), None),
]

for name, previous, current, expected in tests:

    result = create_alert(
        "Test Player",
        previous,
        current
    )

    assert result == expected, (
        f"{name}: Expected {expected}, got {result}"
    )

    print(f"PASS: {name}")

    if result:
        print(result)

print("\nAll 5 alert tests passed!")
