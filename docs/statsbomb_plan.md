# StatsBomb Open Data — integration plan

Source: https://github.com/hudl/open-data

The official repository provides JSON for competitions, matches, events, lineups and (some matches) 360 data. A planned integration will read selected downloadable JSON files, inspect their actual fields, and save raw-source provenance. Do not assume all matches have 360 data or that attributes such as transfer values, preferred foot or recovery speed are available.

Steps after the synthetic validation milestone:
1. Select a small published match from a documented competition and season.
2. Download original JSON from the published repository with source URL, date and attribution.
3. Parse one match's events with Python into a safe, explicit data model.
4. Test required fields and missing values; never invent unavailable player attributes.
5. Store a small selected subset in PostgreSQL; build SQL queries and a FastAPI response.

Rights: Data is made public for research and genuine football analytics interest, with source attribution requested. A public repository is not automatic commercial/redistribution/API-LLM permission. Confirm legal terms and obtain written permission where needed before commercial use.
