import unittest

from status_utils import classify_result_status

try:
    from GetGoodInfo import save_largest_html_table_as_xls
except ModuleNotFoundError as exc:
    save_largest_html_table_as_xls = None
    GETGOODINFO_IMPORT_ERROR = exc
else:
    GETGOODINFO_IMPORT_ERROR = None


class FakeDriver:
    page_source = """
    <html><body>
    您的瀏覽量異常, 已影響網站速度, 目前暫時關閉服務, 請稍後再重新使用
    若您是使用程式大量下載本網站資料, 請適當調降程式查詢頻率
    </body></html>
    """
    current_url = "https://goodinfo.tw/tw/ShowMarginChart.asp?STOCK_ID=2330"
    title = "Goodinfo!台灣股市資訊網"


class ChallengeDriver:
    page_source = """
    <html><head><title>Just a moment...</title></head>
    <body>Checking if the site connection is secure</body></html>
    """
    current_url = "https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=2330"
    title = "Just a moment..."


class RateLimitStatusTest(unittest.TestCase):
    @unittest.skipIf(
        save_largest_html_table_as_xls is None,
        f"GetGoodInfo dependencies unavailable: {GETGOODINFO_IMPORT_ERROR}",
    )
    def test_goodinfo_rate_limit_page_is_not_no_data(self):
        result = save_largest_html_table_as_xls(FakeDriver(), "/tmp/unused.xls")

        self.assertEqual(result, "rate_limited")

    def test_rate_limit_error_is_classified_separately(self):
        status, reason = classify_result_status(
            False,
            "GoodInfo rate limited request / 瀏覽量異常",
            stock_id="2330",
            parameter="13",
        )

        self.assertEqual(status, "rate_limited")
        self.assertIn("瀏覽量異常", reason)

    @unittest.skipIf(
        save_largest_html_table_as_xls is None,
        f"GetGoodInfo dependencies unavailable: {GETGOODINFO_IMPORT_ERROR}",
    )
    def test_anti_bot_challenge_page_is_rate_limited(self):
        result = save_largest_html_table_as_xls(ChallengeDriver(), "/tmp/unused.xls")

        self.assertEqual(result, "rate_limited")

    def test_anti_bot_challenge_error_is_rate_limited(self):
        status, reason = classify_result_status(
            False,
            "Timeout title: Just a moment... / GoodInfo anti-bot challenge",
            stock_id="2330",
            parameter="8",
        )

        self.assertEqual(status, "rate_limited")
        self.assertIn("Just a moment", reason)


if __name__ == "__main__":
    unittest.main()
