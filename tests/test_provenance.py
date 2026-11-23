"""Protect against misleading football-data provenance labels."""

import unittest

from scripts.monitor_logic import observation_source_description


class TestProvenanceDescriptions(unittest.TestCase):
    def test_fictional_demo_database_is_identified(self):
        self.assertEqual(
            observation_source_description("scoutmonitor_demo"),
            "Fictional demonstration data",
        )

    def test_other_database_is_not_assumed_to_be_sportmonks(self):
        self.assertEqual(
            observation_source_description("scoutmonitor_db"),
            "Stored football observations (provider not independently verified)",
        )

    def test_missing_database_name_is_not_assumed_to_be_real_data(self):
        self.assertEqual(
            observation_source_description(None),
            "Stored football observations (provider not independently verified)",
        )


if __name__ == "__main__":
    unittest.main()
