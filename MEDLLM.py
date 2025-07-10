import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components
from streamlit_chat import message
# 讀取 API 金鑰
load_dotenv()
GOOGLE_API_KEY = 'AIzaSyBgMdKfVDl7MO-bE3IY2EnLc_1t7pWkoUw'



# 初始化模型（文字模型與影像模型分開）
text_model = genai.GenerativeModel("gemini-2.5-flash")
vision_model = genai.GenerativeModel("gemini-2.5-pro")
chat = text_model.start_chat()


# === Session state 初始化 ===
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_images" not in st.session_state:
    st.session_state.pending_images = []

# === 頁面與樣式設定 ===
st.set_page_config(page_title="AI 醫療問診與影像助理", page_icon="💊")
st.markdown("""
    <style>
    .element-container:has(.chat-message) {
        padding: 4px 16px;
    }
    .stChatMessage {
        max-width: 90%;
    }
    </style>
""", unsafe_allow_html=True)
st.title("💊 台灣 AI 醫療問診與影像助理")

# === 上傳圖片區 ===
uploaded_images = st.file_uploader("📎 上傳醫學影像（可多張）", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_images:
    st.session_state.pending_images = uploaded_images

# === 顯示歷史訊息 ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("images"):
            for img in msg["images"]:
                st.image(img, use_column_width=True)

# === 輸入欄：固定在底部 ===
user_input = st.chat_input("請輸入症狀描述，可搭配圖片")

# === Gemini 回應邏輯 ===
if user_input or st.session_state.pending_images:
    # 顯示使用者訊息
    st.chat_message("user").markdown(user_input or "（僅附圖）")
    if st.session_state.pending_images:
        for img in st.session_state.pending_images:
            st.image(img, use_column_width=True)

    # 儲存使用者訊息
    st.session_state.messages.append({
        "role": "user",
        "content": user_input or "（僅附圖）",
        "images": st.session_state.pending_images
    })

    # Gemini 分析
    full_reply = ""
    try:
        if st.session_state.pending_images:
            for idx, img_file in enumerate(st.session_state.pending_images):
                img = Image.open(img_file)
                prompt = f"""
你是一位台灣的專業醫療影像診斷 AI 助理，請判讀第 {idx+1} 張醫學影像的異常情況，
推測可能的病灶或疾病（如肺炎、腫瘤、骨折等），並結合症狀描述分析。
禁止使用簡體與「僅供參考」等語句。
症狀描述：{user_input if user_input else "（無輸入）"}
""".strip()
                result = vision_model.generate_content([prompt, img])
                full_reply += f"📷 第 {idx+1} 張圖片判讀結果：\n{result.text}\n\n"
        else:
            prompt = f"""
你是台灣的專業醫療問診 AI 助理，請根據下列症狀描述，提供可能疾病、建議檢查與處置方式。
請用正體中文回覆，不使用簡體字或「僅供參考」。
症狀描述：{user_input}
"""
            result = text_model.generate_content(prompt)
            full_reply = result.text

    except Exception as e:
        full_reply = f"❌ 發生錯誤：{e}"

    # 顯示助理回覆
    with st.chat_message("assistant"):
        st.markdown(full_reply)

    # 儲存助理訊息
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_reply,
        "images": None
    })

    # 清空暫存圖片
    st.session_state.pending_images = []
