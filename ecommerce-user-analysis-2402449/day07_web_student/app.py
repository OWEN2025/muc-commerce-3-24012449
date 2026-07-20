from functools import wraps
from pathlib import Path
import csv
import io
import traceback

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, Response
import pandas as pd

from services.data_service import load_dashboard_data
from services.qa_service import answer_question

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "day07-classroom-demo-key"


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "username" not in session:
            flash("请先登录后再访问数据看板。", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/")
def index():
    return redirect(url_for("dashboard") if "username" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "student" and password == "day07":
            session["username"] = username
            flash("登录成功，欢迎进入电商用户分析系统。", "success")
            return redirect(url_for("dashboard"))
        flash("账号或密码错误。演示账号：student / day07", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("你已安全退出。", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    category = request.args.get("category", "全部")
    dashboard_data = load_dashboard_data(BASE_DIR, category)
    return render_template(
        "dashboard.html",
        username=session["username"],
        **dashboard_data,
    )


@app.route("/assistant")
@login_required
def assistant():
    return render_template("assistant.html", username=session["username"])


@app.route("/api/ask", methods=["POST"])
@login_required
def ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    if not question:
        return jsonify({"ok": False, "answer": "请输入一个与项目数据有关的问题。"}), 400
    return jsonify({"ok": True, "answer": answer_question(BASE_DIR, question)})


# ========== 必选拓展 A：导出 CSV（修复中文乱码） ==========
@app.route("/api/export")
@login_required
def export_csv():
    try:
        category = request.args.get("category", "全部")
        data_dir = BASE_DIR / "data"
        df = pd.read_csv(data_dir / "category_analysis.csv", encoding="utf-8-sig")
        
        if category != "全部":
            df = df[df["PreferedOrderCat"] == category]
        
        df = df.fillna("").astype(str)
        records = df.to_dict("records")
        
        if not records:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["无数据"])
            content = output.getvalue().encode("utf-8-sig")
            return Response(
                content,
                mimetype="text/csv; charset=utf-8-sig",
                headers={"Content-Disposition": f"attachment;filename=export_{category}.csv"}
            )
        
        fieldnames = list(records[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)
        # 添加 BOM 让 Excel 识别 UTF-8
        content = output.getvalue().encode("utf-8-sig")
        return Response(
            content,
            mimetype="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment;filename=export_{category}.csv"}
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        return f"导出失败：{e}\n{error_detail}", 500


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)