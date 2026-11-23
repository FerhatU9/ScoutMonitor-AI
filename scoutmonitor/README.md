# ScoutMonitor AI domain utilities

Reusable, side-effect-limited modules are maintained separately from HTTP routes and Streamlit entry points.

- `validation.py` validates fictional player records and rejects malformed CSV input and invalid statistics.
- `demo_catalog.py` loads verified demonstration records and implements filtering, sorting, and comparisons.

Unknown football statistics are represented as `None` rather than silently converted to zero. Missing metrics sort last for either sort direction.

The customer application should gradually move additional reusable monitoring logic into this package as functionality is verified, without changing the existing live report workflow unnecessarily.
