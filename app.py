import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import base64

st.set_page_config(page_title="物流作業進捗管理アプリ", layout="wide")

# -------------------------
# 背景設定
# -------------------------
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{data}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(255, 255, 255, 0.72);
            z-index: -1;
        }}

        html, body, [class*="css"] {{
            font-family: 'Yu Gothic UI', 'Meiryo', sans-serif;
            color: #333;
        }}

        .card {{
            background-color: rgba(255, 255, 255, 0.94);
            padding: 20px;
            border-radius: 18px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}

        h1, h2, h3 {{
            color: #1F4E79;
        }}

        section[data-testid="stSidebar"] {{
            background-color: rgba(245,248,252,0.88);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

BASE_DIR = Path(__file__).resolve().parent
bg_path = BASE_DIR / "assets" / "background.png"

if bg_path.exists():
    set_background(str(bg_path))
else:
    st.warning(f"背景画像が見つかりません: {bg_path}")

# -------------------------
# DB接続
# -------------------------
db_path = BASE_DIR / "logistics_tasks.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

# -------------------------
# テーブル作成
# -------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT,
    location TEXT,
    staff TEXT,
    priority TEXT,
    status TEXT,
    due_date TEXT,
    memo TEXT,
    created_at TEXT
)
""")
conn.commit()

# -------------------------
# サンプルデータ
# -------------------------
sample_tasks = [
    ("入荷検品", "川崎第一物流センター", "佐藤 太一", "高", "未着手", "2026-03-25", "午前中対応必須", "2026-03-24"),
    ("ピッキング", "海老名フルフィルメントセンター", "鈴木 健", "中", "作業中", "2026-03-26", "優先出荷案件あり", "2026-03-24"),
    ("梱包", "相模原ディストリビューションセンター", "高橋 翔", "低", "未着手", "2026-03-27", "", "2026-03-24"),
    ("出荷検品", "厚木ロジスティクスセンター", "田中 大輔", "高", "未着手", "2026-03-25", "ミス防止のダブルチェック実施", "2026-03-24"),
    ("棚入れ", "横浜ベイサイドセンター", "伊藤 恒一", "中", "完了", "2026-03-24", "", "2026-03-24"),
    ("仕分け", "川崎第二物流センター", "渡辺 拓也", "中", "作業中", "2026-03-25", "午後便対応", "2026-03-24"),
    ("返品処理", "海老名フルフィルメントセンター", "山本 恒一", "低", "保留", "2026-03-28", "確認待ち", "2026-03-24"),
    ("在庫棚卸", "厚木ロジスティクスセンター", "中村 翔太", "高", "未着手", "2026-03-29", "月末棚卸", "2026-03-24"),
    ("入荷受付", "横浜ベイサイドセンター", "小林 健太", "中", "完了", "2026-03-24", "", "2026-03-24"),
    ("出荷処理", "川崎第一物流センター", "加藤 翔", "高", "作業中", "2026-03-25", "当日出荷分", "2026-03-24"),
]

locations = [
    "川崎第一物流センター",
    "川崎第二物流センター",
    "海老名フルフィルメントセンター",
    "相模原ディストリビューションセンター",
    "厚木ロジスティクスセンター",
    "横浜ベイサイドセンター",
]

task_names = [
    "入荷受付",
    "入荷検品",
    "棚入れ",
    "ピッキング",
    "仕分け",
    "梱包",
    "出荷検品",
    "出荷処理",
    "返品処理",
    "在庫棚卸",
]

staff_names = [
    "佐藤 太一",
    "鈴木 健",
    "高橋 翔",
    "田中 大輔",
    "伊藤 恒一",
    "渡辺 拓也",
    "山本 恒一",
    "中村 翔太",
    "小林 健太",
    "加藤 翔",
]

priority_options = ["高", "中", "低"]
status_options = ["未着手", "作業中", "完了", "保留"]

# -------------------------
# 共通関数
# -------------------------
def load_tasks():
    return pd.read_sql("SELECT * FROM tasks ORDER BY id DESC", conn)

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

def style_task_df(df: pd.DataFrame):
    def row_style(row):
        styles = [""] * len(row)
        try:
            due = pd.to_datetime(row["due_date"]).date()
        except Exception:
            due = None

        if row["status"] == "完了":
            return ["background-color: #f2f2f2; color: #666;"] * len(row)

        if row["priority"] == "高":
            styles = ["background-color: #fff4e5;"] * len(row)

        if due and due < date.today() and row["status"] != "完了":
            styles = ["background-color: #fde2e1; color: #a61b1b; font-weight: bold;"] * len(row)

        return styles

    return df.style.apply(row_style, axis=1)

# -------------------------
# UI
# -------------------------
st.title("📦 物流作業進捗管理アプリ")

menu = st.sidebar.radio(
    "メニュー",
    ["ダッシュボード", "作業登録", "作業一覧", "分析"]
)

# -------------------------
# ダッシュボード
# -------------------------
if menu == "ダッシュボード":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if st.button("サンプルデータを追加"):
        existing = pd.read_sql("SELECT COUNT(*) as cnt FROM tasks", conn).iloc[0]["cnt"]
        if existing == 0:
            for task in sample_tasks:
                c.execute("""
                    INSERT INTO tasks (
                        task_name, location, staff, priority, status, due_date, memo, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, task)
            conn.commit()
            st.success("サンプルデータを追加しました✨")
        else:
            st.info("すでにデータが入っています。")

    tasks_df = load_tasks()

    total_count = len(tasks_df)
    incomplete_count = len(tasks_df[tasks_df["status"] != "完了"]) if not tasks_df.empty else 0
    overdue_count = 0
    today_count = 0

    if not tasks_df.empty:
        tmp_df = tasks_df.copy()
        tmp_df["due_date_dt"] = pd.to_datetime(tmp_df["due_date"], errors="coerce").dt.date
        overdue_count = len(tmp_df[(tmp_df["due_date_dt"] < date.today()) & (tmp_df["status"] != "完了")])
        today_count = len(tmp_df[tmp_df["due_date_dt"] == date.today()])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("作業総数", total_count)
    col2.metric("未完了数", incomplete_count)
    col3.metric("遅延数", overdue_count)
    col4.metric("今日の作業数", today_count)

    st.subheader("最近の作業")
    if tasks_df.empty:
        st.info("まだ作業データがありません。")
    else:
        recent_df = tasks_df[["id", "task_name", "location", "staff", "priority", "status", "due_date"]].head(8)
        st.dataframe(style_task_df(recent_df), use_container_width=True)

    st.subheader("遅延タスク")
    if tasks_df.empty:
        st.info("まだ作業データがありません。")
    else:
        tmp_df = tasks_df.copy()
        tmp_df["due_date_dt"] = pd.to_datetime(tmp_df["due_date"], errors="coerce").dt.date
        overdue_df = tmp_df[(tmp_df["due_date_dt"] < date.today()) & (tmp_df["status"] != "完了")]

        if overdue_df.empty:
            st.success("遅延タスクはありません。")
        else:
            st.dataframe(
                overdue_df[["id", "task_name", "location", "staff", "priority", "status", "due_date", "memo"]],
                use_container_width=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 作業登録
# -------------------------
elif menu == "作業登録":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    task_name = st.selectbox("作業名", task_names)
    location = st.selectbox("事業所", locations)
    staff = st.selectbox("担当者", staff_names)
    priority = st.selectbox("優先度", priority_options)
    status = st.selectbox("ステータス", status_options, index=0)
    due_date = st.date_input("期限", value=date.today())
    memo = st.text_area("メモ")

    if st.button("作業を登録"):
        c.execute("""
            INSERT INTO tasks (
                task_name, location, staff, priority, status, due_date, memo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_name,
            location,
            staff,
            priority,
            status,
            str(due_date),
            memo,
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        st.success("作業を登録しました✨")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 作業一覧
# -------------------------
elif menu == "作業一覧":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    tasks_df = load_tasks()

    keyword = st.text_input("検索", placeholder="作業名・担当者・メモで検索")
    location_filter = st.selectbox("事業所絞り込み", ["すべて"] + locations)
    status_filter = st.selectbox("ステータス絞り込み", ["すべて"] + status_options)
    priority_filter = st.selectbox("優先度絞り込み", ["すべて"] + priority_options)

    if tasks_df.empty:
        st.info("まだ作業データがありません。")
    else:
        filtered_df = tasks_df.copy()

        if keyword.strip():
            kw = keyword.strip()
            filtered_df = filtered_df[
                filtered_df["task_name"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["staff"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["memo"].astype(str).str.contains(kw, case=False, na=False)
            ]

        if location_filter != "すべて":
            filtered_df = filtered_df[filtered_df["location"] == location_filter]

        if status_filter != "すべて":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]

        if priority_filter != "すべて":
            filtered_df = filtered_df[filtered_df["priority"] == priority_filter]

        export_df = filtered_df[[
            "id", "task_name", "location", "staff", "priority", "status", "due_date", "memo", "created_at"
        ]].copy()

        st.download_button(
            label="作業一覧をCSVダウンロード",
            data=to_csv_bytes(export_df),
            file_name="logistics_tasks.csv",
            mime="text/csv"
        )

        st.dataframe(style_task_df(export_df), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 分析
# -------------------------
elif menu == "分析":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    tasks_df = load_tasks()

    if tasks_df.empty:
        st.info("まだ分析できるデータがありません。")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("事業所別件数")
            location_counts = tasks_df["location"].value_counts().reset_index()
            location_counts.columns = ["事業所", "件数"]
            st.dataframe(location_counts, use_container_width=True)

        with col2:
            st.subheader("ステータス別件数")
            status_counts = tasks_df["status"].value_counts().reset_index()
            status_counts.columns = ["ステータス", "件数"]
            st.dataframe(status_counts, use_container_width=True)

        with col3:
            st.subheader("優先度別件数")
            priority_counts = tasks_df["priority"].value_counts().reset_index()
            priority_counts.columns = ["優先度", "件数"]
            st.dataframe(priority_counts, use_container_width=True)

        st.subheader("作業名別件数")
        task_counts = tasks_df["task_name"].value_counts().reset_index()
        task_counts.columns = ["作業名", "件数"]
        st.dataframe(task_counts, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
