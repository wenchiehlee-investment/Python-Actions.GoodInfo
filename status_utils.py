def classify_result_status(success, error_msg="", stock_id=None, parameter=None):
    """Classify a result without changing the legacy success column."""
    error_text = (error_msg or "").strip()

    if success:
        if "Unsupported Index" in error_text:
            return "unsupported", error_text
        return "success", ""

    rate_limit_markers = [
        "GoodInfo rate limited",
        "rate limited request",
        "瀏覽量異常",
        "暫時關閉服務",
        "適當調降程式查詢頻率",
    ]
    no_data_markers = [
        "No tables found",
        "HTML table fallback failed: No tables found",
        "No usable HTML data table found",
        "找不到可用資料表",
    ]
    export_markers = [
        "No new-style export select found",
        "No export select or data table found",
        "No export select or usable data table found",
        "No XLS download elements found",
        "未找到新式匯出選單",
        "未找到新式匯出選單或資料表",
        "未找到新式匯出選單或可用資料表",
        "未找到XLS下載元素",
    ]
    network_markers = [
        "Chrome network error",
        "Chrome 網路錯誤",
        "ERR_",
        "timeout",
        "超時",
    ]

    if any(marker in error_text for marker in rate_limit_markers):
        return "rate_limited", error_text
    if any(marker in error_text for marker in no_data_markers):
        return "no_data", error_text
    if any(marker in error_text for marker in export_markers):
        return "export_missing", error_text
    if any(marker in error_text for marker in network_markers):
        return "retryable_failed", error_text
    return "retryable_failed", error_text


def legacy_status_from_success(success_value):
    return "success" if str(success_value).lower() == "true" else "retryable_failed"
