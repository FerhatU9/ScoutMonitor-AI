
from monitor_logic import detect_change


def create_alert(player_name, previous, current):

    # Use our existing, tested monitoring function
    status = detect_change(previous, current)

    # Only generate an alert when performance increases
    if status != "CHANGE_DETECTED":
        return None

    # Calculate the increases
    new_goals = current[0] - previous[0]
    new_assists = current[1] - previous[1]

    # Prepare a simple alert message
    message = (
        f"ALERT: {player_name} | "
        f"+{new_goals} goals | "
        f"+{new_assists} assists"
    )

    return message
