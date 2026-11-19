
from datetime import date

from langgraph.graph import StateGraph, START, END

from scout_monitoring_graph import (
    ScoutState,
    assess_change,
    choose_next_step,
    prepare_summary,
    prepare_alert_draft,
)

# 1. Build a test graph using our real functions
# We skip the database and provide fictional snapshots.

workflow = StateGraph(ScoutState)

workflow.add_node("check_change", assess_change)
workflow.add_node("create_summary", prepare_summary)
workflow.add_node("create_alert_draft", prepare_alert_draft)

workflow.add_edge(START, "check_change")

workflow.add_conditional_edges(
    "check_change",
    choose_next_step,
    {
        "alert": "create_alert_draft",
        "summary": "create_summary",
    },
)

workflow.add_edge("create_summary", END)
workflow.add_edge("create_alert_draft", END)

graph = workflow.compile()


# 2. Define fictional test scenarios
# Snapshots are ordered newest first.

tests = [
    (
        "No previous history",
        [(date(2026, 11, 15), 1, 2)],
        "WAITING_FOR_HISTORY",
        False,
    ),
    (
        "Performance increased",
        [
            (date(2026, 11, 16), 2, 3),
            (date(2026, 11, 15), 1, 2),
        ],
        "CHANGE_DETECTED",
        True,
    ),
    (
        "No performance change",
        [
            (date(2026, 11, 16), 1, 2),
            (date(2026, 11, 15), 1, 2),
        ],
        "NO_CHANGE",
        False,
    ),
    (
        "Suspicious decrease",
        [
            (date(2026, 11, 16), 0, 2),
            (date(2026, 11, 15), 1, 2),
        ],
        "REVIEW_DATA",
        False,
    ),
    (
        "Missing statistics",
        [
            (date(2026, 11, 16), None, 2),
            (date(2026, 11, 15), 1, 2),
        ],
        "MISSING_STATS",
        False,
    ),
]


# 3. Run every test through LangGraph
for name, snapshots, expected_status, expect_alert in tests:

    result = graph.invoke({
        "player_id": 82032,
        "team_id": 85,
        "season_id": 27897,
        "snapshots": snapshots,
    })

    assert result["status"] == expected_status

    summary = result["summary"]

    if expect_alert:
        assert "PERFORMANCE ALERT" in summary
        assert "Additional goals: 1" in summary
        assert "Additional assists: 1" in summary
    else:
        assert "PERFORMANCE ALERT" not in summary

    print(f"PASS: {name} -> {result['status']}")


print("\nAll 5 LangGraph routing tests passed!")
