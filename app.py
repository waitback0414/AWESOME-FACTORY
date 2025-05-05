import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import gspread
from google.oauth2.service_account import Credentials

# ===JSONの確認====
st.write("Secrets keys available:", list(st.secrets.keys()))
st.write("Service account email (from secrets):", st.secrets["gcp_service_account"].get("client_email", "None"))


# === 設定 ===
SHEET_ID = "1LYYXhCwKNgxl5m6M97tGfeFD0ZjaPu1IJALCAUY1gc0"  # ← ご自身のスプレッドシートIDに置き換えてください
SHEET_NAME = "2025.01"  # ← タブ名

# === Google Sheets 認証処理 ===
@st.cache_resource
def connect_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return worksheet


# === データ読み込み＆書き込み関数 ===
def read_member_sheet():
    ws = connect_gsheet()
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # 1行目を列名に
    return df

def extract_pdf_data(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    data = []

    for page in doc:
        blocks = page.get_text("blocks")
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            lines = text.strip().split("\n")
            if not lines:
                continue

            name_candidate = lines[0].strip()
            if 300 <= x0 <= 320 and " " in name_candidate and "確認" not in name_candidate:
                entry = {"名前": name_candidate}
                if len(lines) > 1:
                    second_line = lines[1].strip()
                    if re.match(r'^\d{4}/\d{2}/\d{2}$', second_line):
                        entry["回答日"] = second_line
                    else:
                        entry["回答日"] = pd.NA
                else:
                    entry["回答日"] = pd.NA
                data.append(entry)
    doc.close()
    return pd.DataFrame(data)

# === Streamlit アプリ本体 ===
st.set_page_config(page_title="PDF照合アプリ", layout="wide")
st.title("📄 PDFとGoogle Sheetsの照合アプリ")

uploaded_pdf = st.file_uploader("PDFファイルをアップロード（名前＋回答日）", type="pdf")

if uploaded_pdf:
    try:
        df_pdf = extract_pdf_data(uploaded_pdf)
        st.subheader("🔍 抽出されたPDFデータ")
        st.dataframe(df_pdf)

        df_member = read_member_sheet()
        st.subheader("📋 Google Sheetsメンバー一覧")
        st.dataframe(df_member)

        # 名前で照合して所属付与
        df_merged = pd.merge(df_member, df_pdf, on="名前", how="left")

        # 所属別集計
        group_total = df_member.groupby("所属").size()
        group_answered = df_merged[df_merged["回答日"].notna()].groupby("所属").size()

        summary = pd.concat([
            group_total.rename("分母（人数）"),
            group_answered.rename("分子（回答あり）")
        ], axis=1).fillna(0)

        summary["分母（人数）"] = summary["分母（人数）"].astype(int)
        summary["分子（回答あり）"] = summary["分子（回答あり）"].astype(int)
        summary["回答率（%）"] = (summary["分子（回答あり）"] / summary["分母（人数）"] * 100).round(1)

        st.subheader("📊 所属別回答率")
        st.dataframe(summary)

        # ダウンロード
        csv_merged = df_merged.to_csv(index=False, encoding="utf-8-sig")
        csv_summary = summary.to_csv(index=True, encoding="utf-8-sig")

        st.download_button("📥 名前・回答日一覧をCSVでダウンロード", csv_merged, file_name="回答一覧.csv", mime="text/csv")
        st.download_button("📥 所属別集計をCSVでダウンロード", csv_summary, file_name="所属別集計.csv", mime="text/csv")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("PDFファイルをアップロードしてください。")
