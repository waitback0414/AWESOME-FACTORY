import streamlit as st
from PIL import Image

st.set_page_config(page_title="Streamlit App", page_icon=":shark:")

st.title("E-DOYUの回答率集計アプリ")
st.write("made by AWESOME FACTORY")

# 変換後の画像 URL
# image = Image.open("https://drive.google.com/uc?export=view&id=1t9PTUy89tBejKogE0ywbEkO75FEDdlpc")
# 画像のURL
image_url = "https://drive.google.com/thumbnail?id=1t9PTUy89tBejKogE0ywbEkO75FEDdlpc&sz=w1000"

# 画像を表示
st.image(image_url, use_container_width=True)
#https://drive.google.com/uc?export=download&id=


