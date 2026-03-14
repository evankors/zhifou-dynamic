from datetime import datetime, timedelta
import os
import sqlite3
import secrets
from werkzeug.utils import secure_filename

from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "academic_consult.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "teachers")
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".pdf"}
USE_POSTGRES = bool(os.getenv("DATABASE_URL"))

TEACHERS = {
    "zhang": {
        "slug": "zhang",
        "name": "张沐白",
        "title": "管理学｜教授｜北京大学",
        "school": "北京大学",
        "major": "管理学",
        "avatar": "avatars/zhang.png",
        "price": 69,
        "rating": "4.97",
        "answers": 221,
        "years": 12,
        "desc": "主要研究组织行为、领导力，主持多项国家级课题，在 SSCI / CSSCI 期刊发表论文 30 余篇。",
        "tags": ["组织行为", "领导力", "人力资源管理", "实证研究"],
    },
    "hu": {
        "slug": "hu",
        "name": "胡老师",
        "title": "管理学｜教授｜吉林大学",
        "school": "吉林大学",
        "major": "人力资源管理",
        "avatar": "avatars/li.png",
        "price": 129,
        "rating": "5.00",
        "answers": 59,
        "years": 8,
        "desc": "聚焦绩效管理与问卷方法论，长期指导硕博论文开题和实证模型设计。",
        "tags": ["绩效管理", "实证研究", "问卷设计"],
    },
    "wang": {
        "slug": "wang",
        "name": "王老师",
        "title": "管理学｜教授｜浙江大学",
        "school": "浙江大学",
        "major": "战略管理",
        "avatar": "avatars/wang.png",
        "price": 99,
        "rating": "4.92",
        "answers": 410,
        "years": 15,
        "desc": "擅长战略管理与案例研究，在理论建模与顶刊投稿辅导方面经验丰富。",
        "tags": ["战略管理", "案例研究", "理论建模"],
    },
    "xia": {
        "slug": "xia",
        "name": "夏老师",
        "title": "管理学｜教授｜南开大学",
        "school": "南开大学",
        "major": "会计学",
        "avatar": "avatars/xia.png",
        "price": 59,
        "rating": "5.00",
        "answers": 259,
        "years": 28,
        "desc": "专注会计与组织绩效评估，善于指导量化模型与实证论文结构搭建。",
        "tags": ["会计研究", "实证研究", "问卷设计"],
    },
    "zheng": {
        "slug": "zheng",
        "name": "郑老师",
        "title": "管理学｜教授｜华北理工大学",
        "school": "华北理工大学",
        "major": "组织与员工行为",
        "avatar": "avatars/zheng.png",
        "price": 59,
        "rating": "5.00",
        "answers": 95,
        "years": 18,
        "desc": "研究方向覆盖员工行为与组织绩效，提供论文选题到方法落地的全流程建议。",
        "tags": ["绩效管理", "组织行为", "问卷设计"],
    },
}

MAJORS = [
    {"slug": "management", "name": "管理学", "desc": "工商管理 / 人力资源 / 战略", "icon": "📊"},
    {"slug": "psychology", "name": "心理学", "desc": "社会心理 / 临床 / 组织行为", "icon": "🧠"},
    {"slug": "cs", "name": "计算机", "desc": "人工智能 / 数据 / 软件工程", "icon": "💻"},
    {"slug": "education", "name": "教育学", "desc": "高等教育 / 教育心理", "icon": "📚"},
    {"slug": "law", "name": "法学", "desc": "民商法 / 公法 / 经济法", "icon": "⚖️"},
    {"slug": "economics", "name": "经济学", "desc": "应用经济 / 金融 / 产业", "icon": "💰"},
    {"slug": "stats", "name": "统计 / 数学", "desc": "数理统计 / 计量方法", "icon": "📐"},
    {"slug": "life", "name": "生命科学", "desc": "生物 / 医学 / 遗传", "icon": "🧬"},
    {"slug": "engineering", "name": "工学", "desc": "机械 / 材料 / 自动化", "icon": "🛠️"},
]

FEATURE_PAGES = {
    "theory": {
        "title": "查理论",
        "subtitle": "经典与前沿理论",
        "description": "在这里浏览学科理论脉络、核心概念和代表性研究。",
        "theories": [
            {
                "name": "计划行为理论（Theory of Planned Behavior, TPB）",
                "summary": "由 Ajzen 提出，强调行为意向是行为最直接前因，意向受态度、主观规范和知觉行为控制共同影响。",
                "keywords": ["行为意向", "态度", "主观规范", "知觉行为控制"],
                "scenario": "常用于解释知识分享、绿色行为、技术采纳、健康行为等。",
            },
            {
                "name": "资源保存理论（Conservation of Resources, COR）",
                "summary": "由 Hobfoll 提出，认为个体会努力获取、维持并保护资源；资源丧失会引发压力，资源获得会促进积极状态。",
                "keywords": ["资源丧失", "资源获得", "压力反应", "资源投资"],
                "scenario": "常用于工作压力、倦怠、工作-家庭冲突、领导支持等研究。",
            },
            {
                "name": "社会交换理论（Social Exchange Theory, SET）",
                "summary": "强调组织情境中的互惠关系，员工会基于感知到的支持与公平做出回报性行为。",
                "keywords": ["互惠", "组织支持", "回报行为", "关系质量"],
                "scenario": "常用于组织承诺、离职倾向、组织公民行为等研究。",
            },
            {
                "name": "自我决定理论（Self-Determination Theory, SDT）",
                "summary": "强调自主、胜任、关系三种基本心理需求满足对内在动机和行为持续性的影响。",
                "keywords": ["自主需要", "胜任需要", "关系需要", "内在动机"],
                "scenario": "常用于学习投入、员工敬业、创新行为、教育心理研究。",
            },
            {
                "name": "信号理论（Signaling Theory）",
                "summary": "在信息不对称情境下，行为主体通过可信信号传递质量或意图，接收方据此判断并决策。",
                "keywords": ["信息不对称", "信号发送", "信号解读", "决策判断"],
                "scenario": "常用于招聘、品牌传播、资本市场、平台治理研究。",
            },
        ],
    },
    "experiment": {
        "title": "查实验",
        "subtitle": "实验设计与方法",
        "description": "在这里查看实验框架、变量设计、测量方式与分析流程。",
    },
    "school": {
        "title": "查学院",
        "subtitle": "院校与研究方向",
        "description": "在这里按学校、学院和方向筛选导师与研究团队。",
    },
    "paper": {
        "title": "查论文",
        "subtitle": "论文结构与投稿",
        "description": "在这里查看论文结构模板、投稿流程与审稿应对建议。",
    },
    "grammar": {
        "title": "查语法",
        "subtitle": "学术英语写作",
        "description": "在这里检查常见语法问题并优化学术表达准确性。",
    },
    "guide": {
        "title": "论文指南",
        "subtitle": "科研避坑指南",
        "description": "在这里查看选题、方法、数据到投稿的常见风险点。",
    },
    "video": {
        "title": "学术视频",
        "subtitle": "方法与经验分享",
        "description": "在这里观看研究方法、论文写作和答辩准备的讲解视频。",
    },
}

JOURNAL_PAGES = {
    "jcr-q1": {
        "title": "JCR Q1 期刊",
        "subtitle": "Journal Citation Reports 一区期刊（示例）",
        "journals": [
            "Academy of Management Journal",
            "Academy of Management Review",
            "Journal of Applied Psychology",
            "Journal of Management",
            "Strategic Management Journal",
            "Research Policy",
        ],
    },
    "jcr-q2": {
        "title": "JCR Q2 期刊",
        "subtitle": "Journal Citation Reports 二区期刊（示例）",
        "journals": [
            "Management Decision",
            "European Management Journal",
            "Journal of Organizational Behavior",
            "International Journal of Human Resource Management",
            "Asia Pacific Journal of Management",
            "Human Resource Management Journal",
        ],
    },
    "cas-1": {
        "title": "中科院1区期刊",
        "subtitle": "中科院分区 1 区（示例）",
        "journals": [
            "Journal of Cleaner Production",
            "Energy Economics",
            "Journal of Business Research",
            "Information & Management",
            "Decision Support Systems",
            "Computers in Human Behavior",
        ],
    },
    "cas-2": {
        "title": "中科院2区期刊",
        "subtitle": "中科院分区 2 区（示例）",
        "journals": [
            "Technology Analysis & Strategic Management",
            "Journal of Knowledge Management",
            "Service Industries Journal",
            "Quality & Quantity",
            "Baltic Journal of Management",
            "Chinese Management Studies",
        ],
    },
    "ssci": {
        "title": "SSCI来源期刊",
        "subtitle": "Social Sciences Citation Index（示例）",
        "journals": [
            "Human Relations",
            "Organization Studies",
            "Personnel Psychology",
            "Work and Occupations",
            "Public Administration Review",
            "Journal of Vocational Behavior",
        ],
    },
    "cssci": {
        "title": "CSSCI来源期刊",
        "subtitle": "中文社会科学引文索引（示例）",
        "journals": [
            "管理世界",
            "经济研究",
            "中国工业经济",
            "科研管理",
            "南开管理评论",
            "中国人口·资源与环境",
            "财贸经济",
            "会计研究",
        ],
    },
    "pku-core": {
        "title": "北大核心期刊",
        "subtitle": "中文核心期刊要目总览（示例）",
        "journals": [
            "管理评论",
            "经济管理",
            "预测",
            "软科学",
            "科学学与科学技术管理",
            "现代财经",
        ],
    },
}


def get_conn():
    if USE_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        db_url = os.getenv("DATABASE_URL")
        if db_url and "sslmode=" not in db_url:
            db_url = f"{db_url}{'&' if '?' in db_url else '?'}sslmode=require"
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_execute(conn, sql, params=()):
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def init_db() -> None:
    conn = get_conn()
    if USE_POSTGRES:
        db_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                phone TEXT UNIQUE NOT NULL,
                name TEXT,
                major TEXT,
                school TEXT,
                degree TEXT,
                grade TEXT,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        db_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS sms_codes (
                id SERIAL PRIMARY KEY,
                phone TEXT NOT NULL,
                code TEXT NOT NULL,
                purpose TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        db_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                phone TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                school TEXT NOT NULL,
                title TEXT NOT NULL,
                major TEXT NOT NULL,
                price INTEGER NOT NULL,
                bio TEXT,
                avatar_path TEXT,
                cert1_path TEXT,
                cert2_path TEXT,
                is_verified INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """,
        )
        db_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                teacher_id INTEGER,
                teacher_slug TEXT NOT NULL,
                question TEXT NOT NULL,
                image_name TEXT,
                pre_info TEXT,
                pre_summary TEXT,
                is_public INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                paid_at TEXT
            )
            """,
        )
        db_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        db_execute(conn, "DELETE FROM sms_codes WHERE expires_at < ?", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()
        return

    db_execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT,
            major TEXT,
            school TEXT,
            degree TEXT,
            grade TEXT,
            email TEXT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
    )
    db_execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS sms_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
    )
    db_execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            school TEXT NOT NULL,
            title TEXT NOT NULL,
            major TEXT NOT NULL,
            price INTEGER NOT NULL,
            bio TEXT,
            avatar_path TEXT,
            cert1_path TEXT,
            cert2_path TEXT,
            is_verified INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """,
    )
    db_execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            teacher_id INTEGER,
            teacher_slug TEXT NOT NULL,
            question TEXT NOT NULL,
            image_name TEXT,
            pre_info TEXT,
            pre_summary TEXT,
            is_public INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            paid_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
    )
    db_execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
        """,
    )
    # Lightweight schema migration for existing databases
    cols = {row["name"] for row in db_execute(conn, "PRAGMA table_info(users)")}
    if "name" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN name TEXT")
    if "major" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN major TEXT")
    if "school" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN school TEXT")
    if "degree" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN degree TEXT")
    if "grade" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN grade TEXT")
    if "email" not in cols:
        db_execute(conn, "ALTER TABLE users ADD COLUMN email TEXT")
    tcols = {row["name"] for row in db_execute(conn, "PRAGMA table_info(teachers)")}
    if "bio" not in tcols:
        db_execute(conn, "ALTER TABLE teachers ADD COLUMN bio TEXT")
    if "avatar_path" not in tcols:
        db_execute(conn, "ALTER TABLE teachers ADD COLUMN avatar_path TEXT")
    if "cert1_path" not in tcols:
        db_execute(conn, "ALTER TABLE teachers ADD COLUMN cert1_path TEXT")
    if "cert2_path" not in tcols:
        db_execute(conn, "ALTER TABLE teachers ADD COLUMN cert2_path TEXT")
    if "is_verified" not in tcols:
        db_execute(conn, "ALTER TABLE teachers ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
    order_cols = {row["name"] for row in db_execute(conn, "PRAGMA table_info(orders)")}
    if "teacher_id" not in order_cols:
        db_execute(conn, "ALTER TABLE orders ADD COLUMN teacher_id INTEGER")
    if "pre_info" not in order_cols:
        db_execute(conn, "ALTER TABLE orders ADD COLUMN pre_info TEXT")
    if "pre_summary" not in order_cols:
        db_execute(conn, "ALTER TABLE orders ADD COLUMN pre_summary TEXT")
    # messages table is append-only
    # cleanup expired codes occasionally
    db_execute(conn, "DELETE FROM sms_codes WHERE expires_at < ?", (datetime.now().isoformat(),))
    conn.commit()
    conn.close()


def get_teacher(slug: str):
    teacher = TEACHERS.get(slug)
    if not teacher:
        abort(404)
    return teacher


def get_order(order_id: int):
    conn = get_conn()
    order = db_execute(conn, "SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    return order


def get_teacher_by_id(teacher_id: int):
    conn = get_conn()
    row = db_execute(conn, "SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
    conn.close()
    return row


def build_teacher_view_from_order(order):
    if order["teacher_id"]:
        teacher_db = get_teacher_by_id(order["teacher_id"])
        if not teacher_db:
            return None
        return {
            "name": teacher_db["name"],
            "major": teacher_db["major"],
            "school": teacher_db["school"],
            "price": teacher_db["price"],
            "avatar": teacher_db["avatar_path"] or "avatars/teacher.png",
        }
    teacher = get_teacher(order["teacher_slug"])
    return {
        "name": teacher["name"],
        "major": teacher["major"],
        "school": teacher["school"],
        "price": teacher["price"],
        "avatar": teacher["avatar"],
    }


def get_approved_teachers():
    conn = get_conn()
    rows = db_execute(conn, 
        "SELECT * FROM teachers WHERE status = 'approved' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def save_teacher_upload(teacher_id: int, file_obj, kind: str) -> str | None:
    if not file_obj or not file_obj.filename:
        return None
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        return None
    safe_name = secure_filename(file_obj.filename)
    folder = os.path.join(UPLOAD_DIR, str(teacher_id))
    os.makedirs(folder, exist_ok=True)
    filename = f"{kind}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
    path = os.path.join(folder, filename)
    file_obj.save(path)
    rel_path = os.path.relpath(path, os.path.join(BASE_DIR, "static"))
    return rel_path.replace("\\", "/")


def get_teacher_applications():
    conn = get_conn()
    rows = db_execute(conn, 
        "SELECT * FROM teachers ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def update_teacher_status(teacher_id: int, status: str) -> None:
    conn = get_conn()
    db_execute(conn, "UPDATE teachers SET status = ? WHERE id = ?", (status, teacher_id))
    conn.commit()
    conn.close()


@app.route("/")
def index():
    query = (request.args.get("q") or "").strip()
    matched_teachers = []
    if query:
        for teacher in TEACHERS.values():
            haystack = " ".join(
                [
                    teacher["name"],
                    teacher["school"],
                    teacher["major"],
                    teacher["desc"],
                    " ".join(teacher["tags"]),
                ]
            )
            if query in haystack:
                matched_teachers.append(teacher)

    return render_template(
        "index.html",
        query=query,
        matched_teachers=matched_teachers,
        featured_teachers=[
            TEACHERS["zhang"],
            TEACHERS["hu"],
            TEACHERS["wang"],
            TEACHERS["xia"],
        ],
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    saved = False
    if request.method == "POST":
        phone = (request.form.get("phone") or "").strip()
        name = (request.form.get("name") or "").strip()
        major = (request.form.get("major") or "").strip()
        password = request.form.get("password") or ""
        code = (request.form.get("code") or "").strip()

        if not phone:
            message = "手机号不能为空"
        elif not code:
            message = "请输入验证码"
        elif not verify_code(phone, code, "register"):
            message = "验证码错误或已过期"
        else:
            conn = get_conn()
            existing = db_execute(conn, "SELECT id FROM users WHERE phone = ?", (phone,)).fetchone()
            if existing:
                message = "该手机号已注册"
            else:
                if not password:
                    password = secrets.token_urlsafe(16)
                db_execute(conn, 
                    "INSERT INTO users (phone, name, major, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        phone,
                        name,
                        major,
                        generate_password_hash(password),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                conn.close()
                return redirect(url_for("login", next="/"))
            conn.close()

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        account = (request.form.get("username") or request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        code = (request.form.get("code") or "").strip()

        conn = get_conn()
        user = db_execute(conn, "SELECT * FROM users WHERE phone = ?", (account,)).fetchone()
        teacher = db_execute(conn, "SELECT * FROM teachers WHERE phone = ?", (account,)).fetchone()
        conn.close()

        if code:
            if teacher:
                if teacher["status"] != "approved":
                    message = "老师账号未通过审核"
                elif not verify_code(account, code, "login"):
                    message = "验证码错误或已过期"
                else:
                    session["teacher_id"] = teacher["id"]
                    session["teacher_phone"] = teacher["phone"]
                    session["teacher_name"] = teacher["name"]
                    return redirect(url_for("index"))
            else:
                if not user:
                    message = "该手机号未注册"
                elif not verify_code(account, code, "login"):
                    message = "验证码错误或已过期"
                else:
                    session["user_id"] = user["id"]
                    session["user_phone"] = user["phone"]
                    session["user_name"] = user["name"] or ""
                    session["user_major"] = user["major"] or ""
                    return redirect(request.args.get("next") or url_for("index"))
        else:
            if teacher:
                message = "老师请使用验证码登录"
            elif not user or not check_password_hash(user["password_hash"], password):
                message = "账号或密码错误"
            else:
                session["user_id"] = user["id"]
                session["user_phone"] = user["phone"]
                session["user_name"] = user["name"] or ""
                session["user_major"] = user["major"] or ""
                return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def issue_code(phone: str, purpose: str) -> str:
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
    conn = get_conn()
    db_execute(conn, 
        "INSERT INTO sms_codes (phone, code, purpose, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (phone, code, purpose, expires_at, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return code


def verify_code(phone: str, code: str, purpose: str) -> bool:
    conn = get_conn()
    row = db_execute(conn, 
        """
        SELECT id, expires_at FROM sms_codes
        WHERE phone = ? AND code = ? AND purpose = ?
        ORDER BY id DESC LIMIT 1
        """,
        (phone, code, purpose),
    ).fetchone()
    if not row:
        conn.close()
        return False
    if row["expires_at"] < datetime.now().isoformat():
        conn.close()
        return False
    db_execute(conn, "DELETE FROM sms_codes WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return True


@app.route("/send-code", methods=["POST"])
def send_code():
    phone = (request.form.get("phone") or "").strip()
    purpose = (request.form.get("purpose") or "").strip()
    if not phone or purpose not in {"register", "login", "teacher_register", "teacher_login"}:
        return {"ok": False, "message": "参数错误"}, 400
    code = issue_code(phone, purpose)
    # demo only: return code directly
    return {"ok": True, "code": code}


@app.route("/register-teacher", methods=["GET", "POST"])
def register_teacher():
    message = ""
    if request.method == "POST":
        phone = (request.form.get("phone") or "").strip()
        name = (request.form.get("name") or "").strip()
        school = (request.form.get("school") or "").strip()
        title = (request.form.get("title") or "").strip()
        major = (request.form.get("major") or "").strip()
        price = (request.form.get("price") or "").strip()
        code = (request.form.get("code") or "").strip()

        if not all([phone, name, school, title, major, price]):
            message = "请完整填写信息"
        elif not code:
            message = "请输入验证码"
        elif not verify_code(phone, code, "teacher_register"):
            message = "验证码错误或已过期"
        else:
            try:
                price_val = int(price)
            except ValueError:
                message = "价格必须是数字"
            else:
                conn = get_conn()
                existing = db_execute(conn, "SELECT id FROM teachers WHERE phone = ?", (phone,)).fetchone()
                if existing:
                    message = "该手机号已提交过老师注册"
                else:
                    db_execute(conn, 
                        """
                        INSERT INTO teachers (phone, name, school, title, major, price, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                        """,
                        (phone, name, school, title, major, price_val, datetime.now().isoformat()),
                    )
                    conn.commit()
                    conn.close()
                    message = "提交成功，等待审核"
    return render_template("register_teacher.html", message=message, majors=MAJORS)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login", next="/profile"))
    conn = get_conn()
    saved = False
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        major = (request.form.get("major") or "").strip()
        school = (request.form.get("school") or "").strip()
        degree = (request.form.get("degree") or "").strip()
        grade = (request.form.get("grade") or "").strip()
        email = (request.form.get("email") or "").strip()
        db_execute(conn, 
            """
            UPDATE users
            SET name = ?, major = ?, school = ?, degree = ?, grade = ?, email = ?
            WHERE id = ?
            """,
            (name, major, school, degree, grade, email, user_id),
        )
        conn.commit()
        saved = True
    user = db_execute(conn, 
        "SELECT phone, name, major, school, degree, grade, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    created_at = user["created_at"]
    if created_at:
        try:
            created_at = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return render_template("profile.html", user=user, created_at=created_at, saved=saved)


@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():
    message = ""
    if request.method == "POST":
        phone = (request.form.get("phone") or "").strip()
        code = (request.form.get("code") or "").strip()
        if not phone or not code:
            message = "请输入手机号和验证码"
        else:
            conn = get_conn()
            teacher = db_execute(conn, "SELECT * FROM teachers WHERE phone = ?", (phone,)).fetchone()
            conn.close()
            if not teacher:
                message = "该手机号未提交老师注册"
            elif teacher["status"] != "approved":
                message = "审核未通过或尚未审核"
            elif not verify_code(phone, code, "teacher_login"):
                message = "验证码错误或已过期"
            else:
                session["teacher_id"] = teacher["id"]
                session["teacher_phone"] = teacher["phone"]
                session["teacher_name"] = teacher["name"]
                return redirect(url_for("teacher_center"))
    return render_template("teacher_login.html", message=message)


@app.route("/teacher-profile", methods=["GET", "POST"])
def teacher_profile_edit():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        return redirect(url_for("login", next="/teacher-profile"))
    conn = get_conn()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        school = (request.form.get("school") or "").strip()
        title = (request.form.get("title") or "").strip()
        major = (request.form.get("major") or "").strip()
        price = (request.form.get("price") or "").strip()
        bio = (request.form.get("bio") or "").strip()

        avatar = save_teacher_upload(teacher_id, request.files.get("avatar"), "avatar")
        cert1 = save_teacher_upload(teacher_id, request.files.get("cert1"), "cert1")
        cert2 = save_teacher_upload(teacher_id, request.files.get("cert2"), "cert2")

        try:
            price_val = int(price) if price else 0
        except ValueError:
            price_val = 0

        teacher = db_execute(conn, "SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
        new_avatar = avatar or teacher["avatar_path"]
        new_cert1 = cert1 or teacher["cert1_path"]
        new_cert2 = cert2 or teacher["cert2_path"]
        verified = 1 if (new_cert1 or new_cert2) else teacher["is_verified"]

        db_execute(conn, 
            """
            UPDATE teachers
            SET name = ?, school = ?, title = ?, major = ?, price = ?, bio = ?,
                avatar_path = ?, cert1_path = ?, cert2_path = ?, is_verified = ?
            WHERE id = ?
            """,
            (
                name or teacher["name"],
                school or teacher["school"],
                title or teacher["title"],
                major or teacher["major"],
                price_val or teacher["price"],
                bio,
                new_avatar,
                new_cert1,
                new_cert2,
                verified,
                teacher_id,
            ),
        )
        conn.commit()

    teacher = db_execute(conn, "SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
    conn.close()
    return render_template("teacher_profile_edit.html", teacher=teacher)


@app.route("/demo")
def demo_showcase():
    return render_template("demo_showcase.html")


@app.route("/metrics")
def metrics_showcase():
    return render_template("metrics_showcase.html")


@app.route("/rules")
def rules_showcase():
    return render_template("rules_showcase.html")


@app.route("/teacher-logout")
def teacher_logout():
    session.pop("teacher_id", None)
    session.pop("teacher_phone", None)
    session.pop("teacher_name", None)
    return redirect(url_for("index"))


@app.route("/teacher-admin")
def teacher_admin():
    rows = get_teacher_applications()
    pending = [t for t in rows if t["status"] == "pending"]
    approved = [t for t in rows if t["status"] == "approved"]
    rejected = [t for t in rows if t["status"] == "rejected"]
    return render_template(
        "teacher_admin.html",
        teachers=rows,
        pending_teachers=pending,
        approved_teachers=approved,
        rejected_teachers=rejected,
    )


@app.route("/teacher-admin/approve/<int:teacher_id>", methods=["POST"])
def teacher_admin_approve(teacher_id: int):
    update_teacher_status(teacher_id, "approved")
    return redirect(url_for("teacher_admin"))


@app.route("/teacher-admin/reject/<int:teacher_id>", methods=["POST"])
def teacher_admin_reject(teacher_id: int):
    update_teacher_status(teacher_id, "rejected")
    return redirect(url_for("teacher_admin"))


@app.route("/order-assign/<int:order_id>", methods=["POST"])
def order_assign(order_id: int):
    teacher_id = request.form.get("teacher_id")
    if not teacher_id:
        return redirect(url_for("teacher_admin"))
    conn = get_conn()
    db_execute(conn, "UPDATE orders SET teacher_id = ? WHERE id = ?", (int(teacher_id), order_id))
    conn.commit()
    conn.close()
    return redirect(url_for("teacher_admin"))


@app.route("/teacher-center")
def teacher_center():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        return redirect(url_for("login", next="/teacher-center"))
    teacher = get_teacher_by_id(teacher_id)
    conn = get_conn()
    rows = db_execute(conn, 
        """
        SELECT orders.id, orders.question, orders.status, orders.created_at,
               users.phone AS user_phone
        FROM orders
        LEFT JOIN users ON users.id = orders.user_id
        WHERE orders.teacher_id = ?
        ORDER BY orders.created_at DESC
        """,
        (teacher_id,),
    ).fetchall()
    conn.close()
    status_map = {
        "pending": "待处理",
        "paid": "已支付",
        "answered": "已回复",
        "completed": "已完成",
    }
    orders = []
    for row in rows:
        created_at = row["created_at"]
        if created_at:
            try:
                created_at = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass
        orders.append(
            {
                "id": row["id"],
                "question": row["question"],
                "status": status_map.get(row["status"], row["status"]),
                "created_at": created_at,
                "user_phone": row["user_phone"],
            }
        )
    return render_template("teacher_center.html", orders=orders, teacher=teacher)


@app.route("/my-questions")
def my_questions():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login", next="/my-questions"))
    conn = get_conn()
    rows = db_execute(conn, 
        """
        SELECT orders.id, orders.question, orders.status, orders.created_at,
               orders.pre_summary, teachers.name AS teacher_name
        FROM orders
        LEFT JOIN teachers ON teachers.id = orders.teacher_id
        WHERE orders.user_id = ?
        ORDER BY orders.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    status_map = {
        "pending": "待处理",
        "paid": "已支付",
        "answered": "已回复",
        "completed": "已完成",
    }
    questions = []
    for row in rows:
        created_at = row["created_at"]
        if created_at:
            try:
                created_at = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass
        questions.append(
            {
                "id": row["id"],
                "question": row["question"],
                "status": status_map.get(row["status"], row["status"]),
                "created_at": created_at,
                "teacher_name": row["teacher_name"] or "未指派",
                "pre_summary": row["pre_summary"],
            }
        )
    return render_template("my_questions.html", questions=questions)


@app.route("/ask-subject")
def ask_subject():
    return render_template("ask_subject.html", majors=MAJORS)

@app.route("/feature/<slug>")
def feature_page(slug):
    page = FEATURE_PAGES.get(slug)
    if not page:
        abort(404)
    return render_template("feature_page.html", page=page)

@app.route("/journals/<slug>")
def journals_page(slug):
    page = JOURNAL_PAGES.get(slug)
    if not page:
        abort(404)
    return render_template("journals_cssci.html", page=page, journals=page["journals"])


@app.route("/ask-teacher/<slug>")
def ask_teacher_by_major(slug):
    major = next((m for m in MAJORS if m["slug"] == slug), None)
    if not major:
        abort(404)
    conn = get_conn()
    teachers = db_execute(conn, 
        "SELECT * FROM teachers WHERE status = 'approved' AND major = ? ORDER BY created_at DESC",
        (major["name"],),
    ).fetchall()
    conn.close()
    return render_template(
        "ask_teacher_management.html",
        teachers=teachers,
        major_title=major["name"],
        major_desc=major["desc"],
    )


@app.route("/teacher/<name>")
def teacher_detail(name):
    teacher = get_teacher(name)
    return render_template("teacher.html", teacher=teacher)


@app.route("/teacher-profile/<int:teacher_id>")
def teacher_profile(teacher_id: int):
    teacher = get_teacher_by_id(teacher_id)
    if not teacher or teacher["status"] != "approved":
        abort(404)
    return render_template("teacher_profile.html", teacher=teacher)


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if not session.get("user_id"):
        return redirect(url_for("login", next=request.path))
    if request.method == "POST":
        teacher_slug = request.form.get("teacher") or "zhang"
        teacher_id = request.form.get("teacher_id")
        question = (request.form.get("question") or "").strip()
        image = request.files.get("image")
        image_name = image.filename if image and image.filename else None

        if not question:
            teacher = get_teacher(teacher_slug)
            return render_template("ask.html", teacher=teacher, message="请先填写问题内容")

        teacher = get_teacher(teacher_slug)
        conn = get_conn()
        cursor = db_execute(conn, 
            """
            INSERT INTO orders (user_id, teacher_id, teacher_slug, question, image_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.get("user_id"),
                int(teacher_id) if teacher_id else None,
                teacher["slug"],
                question,
                image_name,
                datetime.now().isoformat(),
            ),
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for("pay", order_id=order_id))

    teacher_id = request.args.get("teacher_id")
    if teacher_id:
        teacher_db = get_teacher_by_id(int(teacher_id))
        if not teacher_db or teacher_db["status"] != "approved":
            abort(404)
        return render_template("ask.html", teacher=teacher_db, message="", teacher_id=teacher_db["id"], is_db_teacher=True)

    teacher_slug = request.args.get("teacher") or "zhang"
    teacher = get_teacher(teacher_slug)
    return render_template("ask.html", teacher=teacher, message="")


@app.route("/pay", methods=["GET", "POST"])
def pay():
    order_id = request.args.get("order_id", type=int) or request.form.get("order_id", type=int)
    if not order_id:
        return redirect(url_for("ask_subject"))

    order = get_order(order_id)
    if not order:
        abort(404)

    teacher = build_teacher_view_from_order(order)
    if not teacher:
        abort(404)

    if request.method == "POST":
        conn = get_conn()
        db_execute(conn, 
            "UPDATE orders SET status = 'paid', paid_at = ? WHERE id = ?",
            (datetime.now().isoformat(), order_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("chat", order_id=order_id))

    return render_template("pay.html", order=order, teacher=teacher)


@app.route("/chat")
def chat():
    order_id = request.args.get("order_id", type=int)
    if not order_id:
        return redirect(url_for("ask_subject"))

    order = get_order(order_id)
    if not order:
        abort(404)

    teacher = build_teacher_view_from_order(order)
    if not teacher:
        abort(404)
    return render_template("chat.html", order=order, teacher=teacher, pre_summary=order["pre_summary"])


@app.route("/order-preinfo", methods=["POST"])
def order_preinfo():
    order_id = request.form.get("order_id", type=int)
    pre_info = request.form.get("pre_info") or ""
    pre_summary = request.form.get("pre_summary") or ""
    if not order_id:
        return {"ok": False, "message": "missing order_id"}, 400
    order = get_order(order_id)
    if not order:
        return {"ok": False, "message": "order not found"}, 404
    # only the student who owns the order can submit pre-info
    if session.get("user_id") and order["user_id"] and session.get("user_id") != order["user_id"]:
        return {"ok": False, "message": "forbidden"}, 403
    conn = get_conn()
    db_execute(conn, 
        "UPDATE orders SET pre_info = ?, pre_summary = ? WHERE id = ?",
        (pre_info, pre_summary, order_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.route("/messages", methods=["GET", "POST"])
def messages_api():
    if request.method == "POST":
        order_id = request.form.get("order_id", type=int)
        role = (request.form.get("role") or "").strip()
        content = (request.form.get("content") or "").strip()
        if not order_id or role not in {"student", "teacher"} or not content:
            return {"ok": False, "message": "invalid"}, 400
        order = get_order(order_id)
        if not order:
            return {"ok": False, "message": "order not found"}, 404
        # student can post only if owns the order
        if role == "student":
            if not session.get("user_id") or order["user_id"] != session.get("user_id"):
                return {"ok": False, "message": "forbidden"}, 403
        # teacher can post only if assigned
        if role == "teacher":
            if not session.get("teacher_id") or order["teacher_id"] != session.get("teacher_id"):
                return {"ok": False, "message": "forbidden"}, 403
        conn = get_conn()
        db_execute(conn, 
            "INSERT INTO messages (order_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (order_id, role, content, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return {"ok": True}

    order_id = request.args.get("order_id", type=int)
    if not order_id:
        return {"ok": False, "message": "missing order_id"}, 400
    order = get_order(order_id)
    if not order:
        return {"ok": False, "message": "order not found"}, 404
    # allow owner or assigned teacher to read
    if session.get("user_id") and order["user_id"] == session.get("user_id"):
        pass
    elif session.get("teacher_id") and order["teacher_id"] == session.get("teacher_id"):
        pass
    else:
        return {"ok": False, "message": "forbidden"}, 403
    conn = get_conn()
    rows = db_execute(conn, 
        "SELECT role, content, created_at FROM messages WHERE order_id = ? ORDER BY id ASC",
        (order_id,),
    ).fetchall()
    conn.close()
    data = []
    for r in rows:
        created_at = r["created_at"]
        try:
            created_at = datetime.fromisoformat(created_at).strftime("%H:%M")
        except ValueError:
            pass
        data.append({"role": r["role"], "content": r["content"], "created_at": created_at})
    return {"ok": True, "messages": data}


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
