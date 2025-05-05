import streamlit as st
from PIL import Image

st.set_page_config(page_title="Streamlit App", page_icon=":shark:")

st.title("E-DOYUの回答率集計アプリ")
st.write("made by AWESOME FACTORY")

# 変換後の画像 URL
image = Image.open("https://drive.google.com/uc?export=view&id=1t9PTUy89tBejKogE0ywbEkO75FEDdlpc")
#https://drive.google.com/uc?export=download&id=
# 画像を表示
# 修正後（推奨）
st.image(image, use_container_width=True)

