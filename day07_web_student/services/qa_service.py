from pathlib import Path
import pandas as pd

def answer_question(base_dir: Path, question: str) -> str:
    try:
        data_dir = base_dir / "data"
        metrics_df = pd.read_csv(data_dir / "overall_metrics.csv", encoding="utf-8-sig")
        category_df = pd.read_csv(data_dir / "category_analysis.csv", encoding="utf-8-sig")
        segment_df = pd.read_csv(data_dir / "segment_analysis.csv", encoding="utf-8-sig")

        metrics = dict(zip(metrics_df["指标"], metrics_df["数值"]))
        normalized = question.replace(" ", "").lower()

        # 1. 总用户数
        if any(word in normalized for word in ["多少用户", "用户数", "总用户"]):
            return f"数据集中共有{int(metrics['用户数']):,}名用户。"

        # 2. 整体流失率
        if "流失率" in normalized and not any(word in normalized for word in ["最高", "哪个"]):
            churn = metrics.get("流失率", 0)
            return f"平台整体流失率为 {churn:.1%}。"

        # 3. 哪个品类用户最多？
        if "品类" in normalized and "最多" in normalized and "用户" in normalized:
            max_row = category_df.loc[category_df["用户数"].idxmax()]
            cat = max_row["PreferedOrderCat"]
            users = max_row["用户数"]
            return f"用户数最多的偏好品类是「{cat}」，共 {int(users):,} 人。"

        # 4. 生命周期阶段风险最高（流失率最高）—— 直接使用实际列名
        if ("生命周期" in normalized or "阶段" in normalized or "tenure" in normalized) and ("风险" in normalized or "最高" in normalized):
            # 现在使用实际列名 TenureGroup, 流失率
            if "流失率" not in segment_df.columns or "TenureGroup" not in segment_df.columns:
                return "数据中缺少生命周期阶段或流失率列，请检查CSV列名。"
            # 确保流失率为数值
            segment_df["流失率"] = pd.to_numeric(segment_df["流失率"], errors='coerce')
            valid_df = segment_df.dropna(subset=["流失率"])
            if valid_df.empty:
                return "生命周期流失率数据为空。"
            max_row = valid_df.loc[valid_df["流失率"].idxmax()]
            stage = max_row["TenureGroup"]
            rate = max_row["流失率"]
            return f"流失率最高的生命周期阶段是「{stage}」，流失率为 {rate:.1%}，建议重点干预。"

        # 5. 流失率最高的品类
        if "流失率" in normalized and ("最高" in normalized or "哪个" in normalized):
            max_row = category_df.loc[category_df["流失率"].idxmax()]
            cat = max_row["PreferedOrderCat"]
            rate = max_row["流失率"]
            return f"流失率最高的偏好品类是「{cat}」，流失率为 {rate:.1%}。"

        # 6. 指定品类用户数
        if "品类" in normalized and ("用户" in normalized or "人数" in normalized):
            for cat in category_df["PreferedOrderCat"].unique():
                if cat.lower() in normalized:
                    row = category_df[category_df["PreferedOrderCat"] == cat]
                    if not row.empty:
                        users = row.iloc[0]["用户数"]
                        return f"偏好品类「{cat}」的用户数为 {int(users):,} 人。"
            return "未找到您提到的品类，请确认品类名称（如‘女装’、‘男装’等）。"

        # 7. 生命周期阶段列表（使用 TenureGroup 列）
        if "生命周期" in normalized or "阶段" in normalized or "tenure" in normalized:
            if "TenureGroup" not in segment_df.columns:
                return "数据中缺少生命周期阶段列。"
            if "最多" in normalized:
                # 找出用户数最多的阶段
                if "用户数" not in segment_df.columns:
                    return "数据中缺少用户数列。"
                max_row = segment_df.loc[segment_df["用户数"].idxmax()]
                stage = max_row["TenureGroup"]
                users = max_row["用户数"]
                return f"用户数最多的生命周期阶段是「{stage}」，共 {int(users):,} 人。"
            else:
                stages = segment_df["TenureGroup"].tolist()
                return f"系统追踪的生命周期阶段包括：{', '.join(stages)}。"

        # 8. 平均订单数
        if "订单" in normalized:
            avg_orders = metrics.get("平均订单数", 0)
            return f"平台平均订单数为 {avg_orders:.2f} 单/人。"

        return "抱歉，我暂时无法回答这个问题。请尝试询问总用户数、整体流失率、哪个品类用户最多、哪个生命周期阶段风险最高、指定品类用户数、生命周期阶段列表或平均订单数。"

    except Exception as e:
        print(f"[ERROR] 问答服务异常: {e}")
        return f"问答服务内部错误：{e}（请检查控制台详细报错）"