"""Source descriptions for ScoutMonitor AI observations.

A database name only identifies the fictional demonstration database; it does
not establish provenance for records in any other database.
"""


def observation_source_description(database_name: str | None) -> str:
    if database_name == "scoutmonitor_demo":
        return "Fictional demonstration data"
    return "Stored football observations (provider not independently verified)"
