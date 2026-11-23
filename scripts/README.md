# Local monitoring and reporting tools

This directory contains the existing Streamlit application and command-line utilities for scouting, data inspection, report validation, and manually controlled football-data collection.

**Primary local dashboard:** `review_dashboard.py`. Start it from the repository root with the Streamlit command in the [main README](../README.md).

**Graph orchestration:** `scout_monitoring_graph.py`, `scout_structured_graph.py`, and `scout_llm_graph.py` manage local monitoring and AI-assisted reports.

**Review and persistence:** `report_storage.py`, `report_validation.py`, and `review_actions.py` support fact checks, persistence, and human review.

**Collection and diagnostics:** other scripts inspect player records, examine licensed-provider responses when credentials are configured, and operate on local PostgreSQL records.

These are development utilities rather than public multi-user endpoints. Some scripts use configured PostgreSQL credentials and optional Sportmonks/Gemini API keys; review their behavior and database target before executing. Never run them against important customer data without isolation, backup, and authorization checks.

The Streamlit dashboard is not yet tenant-isolated. It must not be hosted publicly as a customer-facing application.
