from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
FILES = {
    "homepage": PUBLIC / "index.html",
    "shared_navigation_and_footer": PUBLIC / "js" / "shared.js",
    "status": PUBLIC / "status.html",
    "disclosure": PUBLIC / "disclosure.html",
    "treasury_health": PUBLIC / "treasury-health.html",
    "chain_status": PUBLIC / "chain-status.html",
}
TEXT = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}


class PublicFinanceTruthTests(unittest.TestCase):
    def test_public_pages_do_not_promote_inactive_offers_or_unverified_finance_claims(self):
        forbidden_copy = (
            "IDO סופי דרך SLH Spark",
            "השתתף ב-IDO",
            "110.75M",
            "PancakeSwap V2 Live",
            "LP Lock מתוכנן (Q3 2026)",
            "20 / 150 BNB",
            "Revenue Share",
            "Dynamic Yield",
            "בית השקעות דיגיטלי",
            "Treasury multisig 1/1",
            "PinkSale",
            "MIDAO",
            "0x9DD8aF7Ac0f601CD473422311b2942DAE9D0BD09",
            "Staking • Variable Yield (4-12%)",
            "/ido.html",
            "/api/treasury/health",
        )
        for file_name, content in TEXT.items():
            with self.subTest(file=file_name):
                normalized = content.casefold()
                for phrase in forbidden_copy:
                    with self.subTest(phrase=phrase):
                        self.assertNotIn(phrase.casefold(), normalized)

    def test_homepage_routes_to_mini_app_and_canonical_live_status(self):
        home = TEXT["homepage"]
        self.assertIn("https://slh-cloud-bot-production.up.railway.app/mini-app-v4", home)
        self.assertIn("/status.html", home)
        self.assertIn("https://slh-cloud-bot-production.up.railway.app/api/public/site-status", home)

    def test_status_page_uses_canonical_endpoint_and_fails_closed_to_unknown(self):
        status = TEXT["status"]
        self.assertIn("https://slh-cloud-bot-production.up.railway.app/api/public/site-status", status)
        self.assertIn("UNKNOWN", status)
        self.assertIn("settlement", status)

    def test_disclosure_makes_inactive_public_funding_clear(self):
        disclosure = TEXT["disclosure"].casefold()
        self.assertIn("אין כרגע", disclosure)
        self.assertIn("ido", disclosure)
        self.assertIn("status.html", disclosure)

    def test_legacy_treasury_page_does_not_publish_a_separate_financial_source(self):
        legacy = TEXT["treasury_health"].casefold()
        self.assertIn("status.html", legacy)
        self.assertIn("noindex", legacy)


if __name__ == "__main__":
    unittest.main()
