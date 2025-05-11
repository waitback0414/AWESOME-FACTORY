# import streamlit as st
# import pandas as pd
# import gspread
# from google.oauth2.service_account import Credentials

# # スプレッドシート情報
# SHEET_ID = "1LYYXhCwKNgxl5m6M97tGfeFD0ZjaPu1IJALCAUY1gc0"  # ← ご自身のスプレッドシートIDに置き換えてください
# SHEET_NAME = "2025.01"  # ← タブ名


# # 認証情報（ローカル or Cloud）
# @st.cache_resource
# def connect_gsheet():
#     try:
#         # Streamlit Cloud用：secrets から読み込み
#         creds = Credentials.from_service_account_info(
#             st.secrets["gcp_service_account"],
#             scopes=["https://www.googleapis.com/auth/spreadsheets",
#                     "https://www.googleapis.com/auth/drive"]
#         )
#     except Exception:
#         # ローカル用：ファイルから読み込み
#         creds = Credentials.from_service_account_file(
#             "service_account.json",
#             scopes=["https://www.googleapis.com/auth/spreadsheets",
#                     "https://www.googleapis.com/auth/drive"]
#         )
#     client = gspread.authorize(creds)
#     worksheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
#     return worksheet

# def read_member_sheet():
#     ws = connect_gsheet()
#     data = ws.get_all_values()
#     df = pd.DataFrame(data[1:], columns=data[0])  # ヘッダー行から DataFrame
#     return df

# def update_member_sheet(df):
#     ws = connect_gsheet()
#     ws.clear()
#     ws.update([df.columns.values.tolist()] + df.values.tolist())

# # ================================
# # Streamlit UI
# # ================================
# st.set_page_config(page_title="メンバー管理（Google Sheets連携）", layout="wide")
# st.title("👥 メンバー一覧（Google Sheets 連携）")

# df = read_member_sheet()

# tab1, tab2 = st.tabs(["✏️ 編集する", "📄 並び替えて見る"])

# with tab1:
#     edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
#     if st.button("💾 Google Sheets に保存"):
#         update_member_sheet(edited_df)
#         st.success("Google Sheets に保存しました。")

# with tab2:
#     st.dataframe(df, use_container_width=True)



import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
import io
from google.cloud import vision

# ===JSONの確認====
# ✅ 必ず一番最初に書く！
st.set_page_config(page_title="PDF照合アプリ", layout="wide")

# ✅ その後に確認コードを書く。グーグル認証確認用
#st.write("Secrets keys available:", list(st.secrets.keys()))
#st.write("Service account email (from secrets):", st.secrets["gcp_service_account"].get("client_email", "None"))


# === 設定 ===
SHEET_ID = "1LYYXhCwKNgxl5m6M97tGfeFD0ZjaPu1IJALCAUY1gc0"  # ← ご自身のスプレッドシートIDに置き換えてください
SHEET_NAME = "2025.01"  # ← タブ名
MEMBER_SHEET_ID = "1LYYXhCwKNgxl5m6M97tGfeFD0ZjaPu1IJALCAUY1gc0"
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

@st.cache_resource
def get_gspread_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def list_sheet_names():
    client = get_gspread_client()
    spreadsheet = client.open_by_key(MEMBER_SHEET_ID)
    return [s.title for s in spreadsheet.worksheets()]


# === データ読み込み＆書き込み関数 ===
# ✅ デバッグ用に追加
#try:
#    ws = connect_gsheet()
#    st.success("✅ Google Sheets 認証成功")
#except Exception as e:
#    st.error(f"❌ Google Sheets 認証エラー: {e}")



# def read_member_sheet():
#     ws = connect_gsheet()
#     data = ws.get_all_values()
#     df = pd.DataFrame(data[1:], columns=data[0])  # 1行目を列名に
#     return df
def read_member_sheet(sheet_name):
    client = get_gspread_client()
    ws = client.open_by_key(MEMBER_SHEET_ID).worksheet(sheet_name)
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # ヘッダーあり
    return df


from google.cloud import vision
import io



# === OCR関数 ===
def detect_attendance_text(img_region):
    img_bytes_io = io.BytesIO()
    img_region.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    client = vision.ImageAnnotatorClient.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    image = vision.Image(content=img_bytes)
    response = client.text_detection(image=image)

    if response.error.message:
        return "エラー"

    text = response.text_annotations[0].description if response.text_annotations else ""

    if "出席" in text:
        return "出席"
    elif "欠席" in text:
        return "欠席"
    elif "未回答" in text:
        return "未回答"
    else:
        return "未検出"



# def extract_pdf_data(uploaded_file):
#     doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
#     data = []

#     for page in doc:
#         blocks = page.get_text("blocks")
#         for block in blocks:
#             x0, y0, x1, y1, text, *_ = block
#             lines = text.strip().split("\n")
#             if not lines:
#                 continue

#             name_candidate = lines[0].strip()
#             if 300 <= x0 <= 320 and " " in name_candidate and "確認" not in name_candidate:
#                 entry = {"名前": name_candidate}
#                 if len(lines) > 1:
#                     second_line = lines[1].strip()
#                     if re.match(r'^\d{4}/\d{2}/\d{2}$', second_line):
#                         entry["回答日"] = second_line
#                     else:
#                         entry["回答日"] = pd.NA
#                 else:
#                     entry["回答日"] = pd.NA
#                 data.append(entry)
#     doc.close()
#     return pd.DataFrame(data)

# def extract_pdf_data(uploaded_file):
#     import re
#     doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
#     data = []

#     for page in doc:
#         blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, ...)

#         for block in blocks:
#             x0, y0, x1, y1, text, *_ = block
#             lines = text.strip().split("\n")
#             if not lines:
#                 continue

#             name_candidate = lines[0].strip()

#             # ✅ 名前候補：x0が300〜320にあり、空白を含む（姓と名）
#             if 300 <= x0 <= 320 and " " in name_candidate:
#                 entry = {"名前": name_candidate}

#                 # 回答日：2行目に日付がある場合
#                 if len(lines) > 1:
#                     second_line = lines[1].strip()
#                     if re.match(r'^\d{4}/\d{2}/\d{2}$', second_line):
#                         entry["回答日"] = second_line
#                     else:
#                         entry["回答日"] = pd.NA
#                 else:
#                     entry["回答日"] = pd.NA

#                 # 出席情報：x0 - 150（≒150〜170）あたりにある同じy位置の文字をチェック
#                 status_x_range = (x0 - 155, x0 - 145)  # 例: 145〜155
#                 matched_status = "未検出"

#                 for s_block in blocks:
#                     sx0, sy0, sx1, sy1, s_text, *_ = s_block
#                     if status_x_range[0] <= sx0 <= status_x_range[1] and abs(sy0 - y0) < 5:
#                         if "出席" in s_text:
#                             matched_status = "出席"
#                         elif "欠席" in s_text:
#                             matched_status = "欠席"
#                         elif "未回答" in s_text:
#                             matched_status = "未回答"
#                         break

#                 entry["出席情報"] = matched_status
#                 data.append(entry)

#     doc.close()
#     return pd.DataFrame(data)



# === PDF処理関数 ===
def extract_pdf_data(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    records = []

    for page_index, page in enumerate(doc):
        blocks = page.get_text("blocks")
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            lines = text.strip().split("\n")
            if not lines:
                continue

            name_candidate = lines[0].strip()

            if 300 <= x0 <= 340 and " " in name_candidate:
                entry = {"名前": name_candidate}

                # 回答日
                if len(lines) > 1 and re.match(r'^\d{4}/\d{2}/\d{2}$', lines[1].strip()):
                    entry["回答日"] = lines[1].strip()
                else:
                    entry["回答日"] = pd.NA

                # 出席画像部分をcrop
                crop_left = max(x0 - 150, 0)
                crop_right = x0 - 50
                crop_box = (crop_left, y0, crop_right, y1)
                cropped_img = img.crop(crop_box)

                # OCRで出席情報抽出
                entry["出席情報"] = detect_attendance_text(cropped_img)
                records.append(entry)

    doc.close()
    return pd.DataFrame(records)



# === Streamlit アプリ本体 ===
# st.set_page_config(page_title="PDF照合アプリ", layout="wide")
st.title("📄 PDFとGoogle Sheetsの照合アプリ")

# プルダウンでメンバーシートを選択
sheet_names = list_sheet_names()
selected_sheet = st.selectbox("メンバーシートを選択", sheet_names)


uploaded_pdf = st.file_uploader("PDFファイルをアップロード（名前＋回答日）", type="pdf")

if uploaded_pdf:
    try:
        df_pdf = extract_pdf_data(uploaded_pdf)
        st.subheader("🔍 抽出されたPDFデータ")
        st.dataframe(df_pdf)

        df_member = read_member_sheet(selected_sheet)
        st.subheader("📋 Google Sheetsメンバー一覧")
        st.dataframe(df_member)

        # 名前で照合して所属付与
        
        # df_merged = pd.merge(df_member, df_pdf, on="名前", how="left")
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
        csv_download = df_pdf.to_csv(index=False, encoding="utf-8-sig")
        csv_merged = df_merged.to_csv(index=False, encoding="utf-8-sig")
        csv_summary = summary.to_csv(index=True, encoding="utf-8-sig")


        st.download_button("📥 名前・回答日一覧をCSVでダウンロード", csv_merged, file_name="回答一覧.csv", mime="text/csv")
        st.download_button("📥 所属別集計をCSVでダウンロード", csv_summary, file_name="所属別集計.csv", mime="text/csv")
        st.download_button("📥 抽出結果をCSVでダウンロード", csv_download, file_name="抽出結果.csv", mime="text/csv")


    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("PDFファイルをアップロードしてください。")
