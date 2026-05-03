from __future__ import annotations

import json
import unittest

from void_codon_library import (
    all_codons,
    codon_chain,
    export_catalog,
    get_codon,
    get_lbn_codons,
    get_platform_codons,
)


class CatalogTests(unittest.TestCase):
    def test_platform_lookup_returns_real_codon(self) -> None:
        adriana = get_codon("adriana", library="platform")

        self.assertIsNotNone(adriana)
        assert adriana is not None
        self.assertEqual(adriana.codon, "ψ·Ψ·◆")
        self.assertEqual(adriana.label, "ADRIANA")

    def test_band_filter_and_chain(self) -> None:
        mid_band = get_platform_codons(band="mid")

        self.assertEqual(len(mid_band), 6)
        self.assertEqual(
            codon_chain("chronicle", "adriana", "session_seal"),
            "α·Ω·⟐ -> ψ·Ψ·◆ -> τ·Ω·⟐",
        )

    def test_lbn_catalog_and_export(self) -> None:
        lbn = get_lbn_codons()
        payload = json.loads(export_catalog(pretty=False))

        self.assertEqual(len(lbn), 10)
        self.assertEqual(len(all_codons()), 25)
        self.assertTrue(any(entry["codon"] == "B-kk-S" for entry in payload))


if __name__ == "__main__":
    unittest.main()
