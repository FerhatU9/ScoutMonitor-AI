
def detect_change(previous, current):

    # Check whether we have current data
    if current is None:
        return "NO_DATA"

    goals, assists = current

    if goals is None or assists is None:
        return "MISSING_STATS"

    # Check whether earlier data exists
    if previous is None:
        return "WAITING_FOR_HISTORY"

    old_goals, old_assists = previous

    if old_goals is None or old_assists is None:
        return "MISSING_STATS"

    # Check for suspicious decreases
    if goals < old_goals or assists < old_assists:
        return "REVIEW_DATA"

    # Check for increases
    if goals > old_goals or assists > old_assists:
        return "CHANGE_DETECTED"

    return "NO_CHANGE"
