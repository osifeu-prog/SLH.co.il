from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "public" / "index.html").read_text(encoding="utf-8")


class PublicHomepageTruthTests(unittest.TestCase):
    def test_homepage_does_not_promote_inactive_ido_or_unverified_finance_claims(self):
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
        )
        normalized = HOME.casefold()
        for phrase in forbidden_copy:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.casefold(), normalized)

    def test_homepage_links_users_to_primary_mini_app_and_truth_page(self):
        self.assertIn("https://slh-cloud-bot-production.up.railway.app/mini-app-v4", HOME)
        self.assertIn("/status.html", HOME)


if __name__ == "__main__":
    unittest.main()
