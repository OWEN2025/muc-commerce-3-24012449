from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_NOTEBOOKS = [
    "notebooks/day03_pandas_product_analysis.ipynb",
    "notebooks/day04_pm_user_cleaning_project.ipynb",
    "notebooks/day05_pm_student_project.ipynb",
]

REQUIRED_OUTPUTS = [
    "output/day03_analysis/category_summary.csv",
    "output/day03_analysis/province_summary.csv",
    "output/day04_project/ecommerce_customer_cleaned.csv",
    "output/day04_project/data_quality_before.csv",
    "output/day04_project/data_quality_after.csv",
    "output/day04_project/cleaning_log.csv",
    "output/day04_project/outlier_report.csv",
    "output/day04_project/business_rule_report.csv",
    "output/day05_analysis/overall_metrics.csv",
    "output/day05_analysis/segment_analysis.csv",
    "output/day05_analysis/cross_analysis.csv",
]


def check_notebook(relative_path):
    path = ROOT / relative_path
    if not path.exists():
        return False, "文件不存在"

    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"JSON读取失败：{exc}"

    if nb.get("nbformat") != 4:
        return False, "不是nbformat 4"
    if not nb.get("cells"):
        return False, "没有单元格"

    error_outputs = []
    for index, cell in enumerate(nb["cells"]):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                error_outputs.append(index)

    if error_outputs:
        return False, f"存在错误输出单元格：{error_outputs}"

    return True, f"cells={len(nb['cells'])}"


def check_csv(relative_path):
    path = ROOT / relative_path
    if not path.exists():
        return False, "文件不存在"

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return False, f"CSV读取失败：{exc}"

    unnamed = [col for col in df.columns if str(col).startswith("Unnamed")]
    if unnamed:
        return False, f"包含多余索引列：{unnamed}"
    if df.empty:
        return False, "CSV为空"

    return True, f"shape={df.shape}"


def main():
    rows = []

    for path in REQUIRED_NOTEBOOKS:
        passed, note = check_notebook(path)
        rows.append({"类型": "Notebook", "文件": path, "通过": passed, "说明": note})

    for path in REQUIRED_OUTPUTS:
        passed, note = check_csv(path)
        rows.append({"类型": "CSV", "文件": path, "通过": passed, "说明": note})

    report = pd.DataFrame(rows)
    print(report.to_string(index=False))

    missing_or_failed = report.loc[~report["通过"]]
    print("\n通过：", int(report["通过"].sum()), "/", len(report))

    if not missing_or_failed.empty:
        raise SystemExit("提交检查未通过，请完成或修正以上文件。")

    print("提交结构检查通过。请继续人工复核代码、指标和结论。")


if __name__ == "__main__":
    main()
