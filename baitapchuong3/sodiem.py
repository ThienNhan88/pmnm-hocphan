"""Ứng dụng Sổ điểm lớp học - Bài tập tổng hợp Chương 3."""
import math

from flask import Flask, abort, jsonify, make_response, redirect, request, url_for
from markupsafe import escape

app = Flask(__name__)
app.json.ensure_ascii = False  # JSON hiển thị tiếng Việt có dấu
app.json.sort_keys = False     # giữ nguyên thứ tự khoá

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A",
                   "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A",
                   "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B",
                   "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B",
                   "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A",
                   "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C",
                   "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


# ---------------------------------------------------------------- Hàm phụ
def average(scores):
    """Trung bình cộng làm tròn 2 chữ số; dict rỗng -> None."""
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    """Xếp loại theo điểm trung bình."""
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    """Dict tóm tắt của một sinh viên (giả định mssv đã tồn tại)."""
    s = STUDENTS[mssv]
    avg = average(s["scores"])
    return {
        "mssv": mssv,
        "name": s["name"],
        "lop": s["lop"],
        "scores": dict(s["scores"]),
        "average": avg,
        "rank": rank(avg),
    }


CSS = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:0 auto;padding:16px;color:#222}
nav{padding:8px 0;border-bottom:2px solid #1d4ed8;margin-bottom:16px}
nav a{margin-right:6px;color:#1d4ed8;text-decoration:none;font-weight:600}
table{border-collapse:collapse;width:100%;margin:12px 0}
th,td{border:1px solid #ccc;padding:6px 10px;text-align:left}
th{background:#eff4ff}
.filter a{margin-right:10px}
"""


def layout(title, body):
    """Trang HTML hoàn chỉnh. title được escape, body chèn nguyên văn."""
    return (
        "<!doctype html>\n"
        '<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{escape(title)} - Sổ điểm</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        "<nav>"
        f'<a href="{url_for("home")}">Trang chủ</a> · '
        f'<a href="{url_for("student_list")}">Sinh viên</a> · '
        f'<a href="{url_for("search")}">Tìm kiếm</a>'
        "</nav>\n"
        f"<main>\n{body}\n</main>\n</body>\n</html>\n"
    )


# =============================================================== PHẦN 1
# ------------------------------------------------ Câu 1. Trang chủ
@app.route("/")
def home():
    n_sv = len(STUDENTS)
    n_lop = len({s["lop"] for s in STUDENTS.values()})
    body = (
        "<h1>Sổ điểm lớp học</h1>\n"
        f"<p>Tổng số sinh viên: <strong>{n_sv}</strong></p>\n"
        f"<p>Số lớp: <strong>{n_lop}</strong></p>\n"
        "<ul>\n"
        f'<li><a href="{url_for("student_list")}">Danh sách sinh viên</a></li>\n'
        f'<li><a href="{url_for("api_students")}">API JSON danh sách sinh viên</a></li>\n'
        "</ul>"
    )
    return layout("Trang chủ", body)


# ------------------------------------------------ Câu 2. Danh sách + lọc
@app.route("/students")
def student_list():
    lop = request.args.get("lop", "").strip()
    classes = sorted({s["lop"] for s in STUDENTS.values()})

    # Thanh lọc lấy từ dữ liệu, không viết cứng
    links = [f'<a href="{url_for("student_list")}">Tất cả</a>']
    for c in classes:
        links.append(f'<a href="{url_for("student_list", lop=c)}">{escape(c)}</a>')
    filter_bar = '<p class="filter">' + " | ".join(links) + "</p>"

    rows = []
    for mssv, s in STUDENTS.items():
        if lop and s["lop"].lower() != lop.lower():
            continue
        info = student_summary(mssv)
        avg = "—" if info["average"] is None else f'{info["average"]:.2f}'
        link = url_for("student_detail", mssv=mssv)
        rows.append(
            "<tr>"
            f'<td><a href="{link}">{escape(mssv)}</a></td>'
            f'<td>{escape(info["name"])}</td>'
            f'<td>{escape(info["lop"])}</td>'
            f"<td>{escape(avg)}</td>"
            f'<td>{escape(info["rank"])}</td>'
            "</tr>"
        )

    if rows:
        table = (
            "<table>\n<tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th>"
            "<th>Điểm TB</th><th>Xếp loại</th></tr>\n"
            + "\n".join(rows) + "\n</table>"
        )
    else:
        table = "<p>Không có sinh viên phù hợp.</p>"

    return layout("Danh sách sinh viên", f"<h1>Danh sách sinh viên</h1>\n{filter_bar}\n{table}")


# ------------------------------------------------ Câu 3. Chi tiết
@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    info = student_summary(mssv)
    avg = "—" if info["average"] is None else f'{info["average"]:.2f}'

    if info["scores"]:
        score_rows = "\n".join(
            f"<tr><td>{escape(course)}</td><td>{escape(score)}</td></tr>"
            for course, score in info["scores"].items()
        )
        scores_html = (
            "<table>\n<tr><th>Học phần</th><th>Điểm</th></tr>\n"
            f"{score_rows}\n</table>"
        )
    else:
        scores_html = "<p>Chưa có điểm học phần nào.</p>"

    lop_link = url_for("student_list", lop=info["lop"])
    export_link = url_for("export_scores", mssv=mssv)
    short_link = url_for("short_link", mssv=mssv)
    body = (
        f'<h1>{escape(info["name"])}</h1>\n'
        f'<p>MSSV: <strong>{escape(mssv)}</strong></p>\n'
        f'<p>Lớp: <a href="{lop_link}">{escape(info["lop"])}</a></p>\n'
        f"<p>Điểm trung bình: <strong>{escape(avg)}</strong></p>\n"
        f'<p>Xếp loại: <strong>{escape(info["rank"])}</strong></p>\n'
        f"<h2>Bảng điểm</h2>\n{scores_html}\n"
        f'<p><a href="{export_link}">Tải bảng điểm (CSV)</a></p>\n'
        f'<p>Link rút gọn: <a href="{short_link}">{escape(short_link)}</a></p>'
    )
    return layout(info["name"], body)


# ------------------------------------------------ Câu 4. Link rút gọn
@app.route("/sv/<mssv>")
def short_link(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)


# ------------------------------------------------ Câu 5. Xuất CSV
@app.route("/students/<mssv>/export")
def export_scores(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    lines = ["hoc_phan,diem"]
    for course, score in STUDENTS[mssv]["scores"].items():
        lines.append(f"{course},{score}")
    resp = make_response("\n".join(lines) + "\n")
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return resp


# ------------------------------------------------ Câu 6. Tìm kiếm an toàn
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    # q xuất hiện trong thuộc tính value => escape (đổi cả dấu ")
    form = (
        f'<form method="get" action="{url_for("search")}">\n'
        f'<input type="text" name="q" value="{escape(q)}" placeholder="Họ tên hoặc MSSV">\n'
        "<button type=\"submit\">Tìm</button>\n</form>"
    )
    result_html = ""
    if q:
        key = q.lower()
        found = [
            mssv for mssv, s in STUDENTS.items()
            if key in s["name"].lower() or key in mssv.lower()
        ]
        items = "\n".join(
            f'<li><a href="{url_for("student_detail", mssv=m)}">{escape(m)}</a>'
            f' - {escape(STUDENTS[m]["name"])}</li>'
            for m in found
        )
        result_html = (
            f"<p>Tìm thấy {len(found)} kết quả cho “{escape(q)}”</p>\n"
            f"<ul>\n{items}\n</ul>"
        )
    return layout("Tìm kiếm", f"<h1>Tìm kiếm sinh viên</h1>\n{form}\n{result_html}")


# =============================================================== PHẦN 2
def get_student_or_404(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return STUDENTS[mssv]


def parse_number(raw, name):
    """Chuyển chuỗi thành số hữu hạn, sai kiểu -> 400."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        abort(400, description=f"Tham số {name} phải là một số.")
    if not math.isfinite(value):
        abort(400, description=f"Tham số {name} phải là một số hữu hạn.")
    return value


# ------------------------------------------------ Câu 7. API đọc dữ liệu
@app.route("/api/students")
def api_students():
    lop = request.args.get("lop", "").strip()
    raw_min = request.args.get("min_avg")  # None = thiếu tham số
    min_avg = None
    if raw_min is not None:                # có tham số -> phải đúng kiểu, sai là 400
        min_avg = parse_number(raw_min, "min_avg")

    result = []
    for mssv, s in STUDENTS.items():
        if lop and s["lop"].lower() != lop.lower():
            continue
        info = student_summary(mssv)
        if min_avg is not None and (info["average"] is None or info["average"] < min_avg):
            continue
        result.append(info)
    return jsonify(result)


@app.route("/api/students/<mssv>")
def api_student(mssv):
    get_student_or_404(mssv)
    return jsonify(student_summary(mssv))


# ------------------------------------------------ Câu 8. API điểm một học phần
@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE"])
def api_score(mssv, course):
    scores = get_student_or_404(mssv)["scores"]
    course = course.upper()

    if request.method == "GET":
        if course not in scores:  # điểm 0 vẫn hợp lệ nên kiểm tra bằng "in"
            abort(404, description=f"Sinh viên {mssv} chưa có điểm học phần {course}.")
        return jsonify({"mssv": mssv, "course": course, "score": scores[course]})

    if request.method == "PUT":
        raw = request.args.get("score")
        if raw is None:
            abort(400, description="Thiếu tham số score.")
        score = parse_number(raw, "score")
        if not 0 <= score <= 10:
            abort(400, description="Điểm phải nằm trong khoảng [0, 10].")
        created = course not in scores
        scores[course] = score
        resp = jsonify({
            "mssv": mssv,
            "course": course,
            "score": score,
            "average": average(scores),
        })
        if created:
            resp.status_code = 201
            resp.headers["Location"] = url_for("api_score", mssv=mssv, course=course)
        return resp

    # DELETE
    if course not in scores:
        abort(404, description=f"Sinh viên {mssv} chưa có điểm học phần {course}.")
    del scores[course]
    return "", 204


# =============================================================== PHẦN 3
ERROR_TITLES = {
    400: "Dữ liệu không hợp lệ",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ",
}


# ------------------------------------------------ Câu 9. Trang lỗi thống nhất
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    code = error.code
    title = ERROR_TITLES[code]
    detail = error.description

    if request.path.startswith("/api/"):
        resp = jsonify({"error": title, "detail": detail})
    else:
        body = (
            f"<h1>Lỗi {code}: {escape(title)}</h1>\n"
            f"<p>{escape(detail)}</p>\n"
            f'<p><a href="{url_for("home")}">Về trang chủ</a></p>'
        )
        resp = make_response(layout(f"Lỗi {code}", body))

    resp.status_code = code  # luôn trả đúng mã lỗi, không để Flask trả 200
    if code == 405 and getattr(error, "valid_methods", None):
        resp.headers["Allow"] = ", ".join(error.valid_methods)
    return resp
