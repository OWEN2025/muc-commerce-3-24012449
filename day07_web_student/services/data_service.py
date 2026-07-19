from pathlib import Path
import pandas as pd

def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")

def load_dashboard_data(base_dir: Path, selected_category: str = "全部") -> dict:
    data_dir = base_dir / "data"
    metrics_df = _read_csv(data_dir / "overall_metrics.csv")
    category_df = _read_csv(data_dir / "category_analysis.csv")
    segment_df = _read_csv(data_dir / "segment_analysis.csv")

    metric_map = dict(zip(metrics_df["指标"], metrics_df["数值"]))

    total_users = metric_map.get("用户数", 0)
    total_churned = metric_map.get("流失人数", 0)
    overall_churn_rate = metric_map.get("流失率", total_churned / total_users if total_users else 0)
    avg_orders = metric_map.get("平均订单数", category_df["平均订单数"].mean() if "平均订单数" in category_df else 0)
    metrics = [
        {"label": "总用户数", "value": f"{int(total_users):,}", "note": "人"},
        {"label": "流失用户", "value": f"{int(total_churned):,}", "note": "人"},
        {"label": "总体流失率", "value": f"{overall_churn_rate:.1%}", "note": ""},
        {"label": "平均订单数", "value": f"{avg_orders:.2f}", "note": "单/人"},
    ]

    categories = ["全部"] + category_df["PreferedOrderCat"].tolist()

    # 筛选
    if selected_category != "全部":
        table_df = category_df[category_df["PreferedOrderCat"] == selected_category].copy()
    else:
        table_df = category_df.copy()

    # 显示用的格式化表格
    display_df = table_df.rename(
        columns={
            "PreferedOrderCat": "偏好品类",
            "用户数": "用户数",
            "流失率": "流失率",
            "平均订单数": "平均订单数",
        }
    )[["偏好品类", "用户数", "流失率", "平均订单数"]]
    display_df["流失率"] = display_df["流失率"].map(lambda v: f"{v:.1%}")
    display_df["平均订单数"] = display_df["平均订单数"].map(lambda v: f"{v:.2f}")

    # 生命周期洞察（使用实际列名 TenureGroup）
    if "流失率" in segment_df.columns and "TenureGroup" in segment_df.columns:
        max_row = segment_df.loc[segment_df["流失率"].idxmax()]
        stage = max_row["TenureGroup"]
        rate = max_row["流失率"]
        insight = f"流失率最高的生命周期阶段为「{stage}」，流失率达 {rate:.1%}，建议重点干预。"
    else:
        insight = "当前数据无法计算生命周期风险观察。"

    # 导出用的原始记录：将 NaN 替换为空字符串，确保 CSV 写入不出错
    table_df_clean = table_df.fillna("")   # 关键修复
    export_records = table_df_clean.to_dict("records")

    return {
        "metrics": metrics,
        "categories": categories,
        "category_rows": display_df.to_dict("records"),
        "insight": insight,
        "export_records": export_records,
        "selected_category": selected_category,
    }