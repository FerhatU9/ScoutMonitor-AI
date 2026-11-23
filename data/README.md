# Demonstration football data

`fictional_players.csv` contains **20 completely fictional player profiles** used to verify data validation, filtering, sorting, and comparisons.

The records have synthetic IDs (`SYN001`–`SYN020`), invented league names, and made-up statistics. They do not represent actual players, clubs, or licensed football-provider information.

**Missing metrics must remain missing:** an empty cell means the source did not supply a value, not that a player recorded zero. The data-validation and API tests assert this behavior.

The published GitHub Pages website includes a copy of these records in `docs/assets/players.csv`; `.github/workflows/website.yml` verifies that the two datasets match.

Do not use these numbers in real scouting decisions or describe them as verified sports data.
