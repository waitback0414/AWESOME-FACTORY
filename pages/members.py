import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# スプレッドシート情報
SHEET_ID = "あなたのスプレッドシートID"  # URLの「/d/」と「/edit」の間
SHEET_NAME = "シート1"  # タブ名

# 認証情報（ローカル or Cloud）
@st.cache_resource
def connect_gsheet():
    try:
        # Streamlit Cloud用：secrets から読み込み
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
    except Exception:
        # ローカル用：ファイルから読み込み
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return worksheet

def read_member_sheet():
    ws = connect_gsheet()
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # ヘッダー行から DataFrame
    return df

def update_member_sheet(df):
    ws = connect_gsheet()
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# ================================
# Streamlit UI
# ================================
st.set_page_config(page_title="メンバー管理（Google Sheets連携）", layout="wide")
st.title("👥 メンバー一覧（Google Sheets 連携）")

df = read_member_sheet()

tab1, tab2 = st.tabs(["✏️ 編集する", "📄 並び替えて見る"])

with tab1:
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Google Sheets に保存"):
        update_member_sheet(edited_df)
        st.success("Google Sheets に保存しました。")

with tab2:
    st.dataframe(df, use_container_width=True)
