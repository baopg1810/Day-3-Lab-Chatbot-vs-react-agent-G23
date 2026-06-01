import os
import sys
import time
import json
import streamlit as st
from typing import List, Dict, Any, Optional, Generator
from dotenv import load_dotenv

# Thêm thư mục gốc của dự án vào sys.path để đảm bảo import chéo hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import các module của dự án
from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider
from src.tools.shop_tools import check_stock, get_discount, calc_shipping

# Load biến môi trường
load_dotenv()

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="iPhone Shop",
    page_icon="📱",
    layout="wide",
)

# Custom CSS để tạo giao diện Chat giống Gemini (Clean, Modern, Sleek)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Giao diện Header kiểu Gemini */
    .gemini-header {
        font-weight: 800;
        font-size: 2.2rem;
        background: linear-gradient(74deg, #4285F4 0%, #9B51E0 50%, #E040FB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .gemini-subtitle {
        color: #757575;
        font-size: 1.05rem;
        margin-bottom: 30px;
    }

    /* Thẻ ReAct Steps (Màu hồng đào cho Thought/Action giống mẫu trước) */
    .react-card {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        font-size: 0.95rem;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    .thought-action-box {
        background-color: #FFF0F2;
        border-left: 5px solid #FF4A6B;
        border-top: 1px solid #FFD0D8;
        border-right: 1px solid #FFD0D8;
        border-bottom: 1px solid #FFD0D8;
    }
    .thought-title {
        color: #C21838;
        font-weight: 700;
        margin-bottom: 4px;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .action-text {
        font-family: 'Fira Code', monospace;
        color: #4A1521;
        background-color: #FFE0E6;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 3px;
        border: 1px solid #FFB8C6;
    }
    
    /* Observation Box (Xanh biển) */
    .observation-box {
        background-color: #F0F6FF;
        border-left: 5px solid #1E88E5;
        border-top: 1px solid #D0E3FF;
        border-right: 1px solid #D0E3FF;
        border-bottom: 1px solid #D0E3FF;
        margin-left: 20px;
        margin-bottom: 15px;
    }
    .observation-title {
        color: #0D47A1;
        font-weight: 700;
        margin-bottom: 4px;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .observation-content {
        color: #1565C0;
        font-weight: 500;
    }
    
    /* Final Answer Box (Xanh lá) */
    .final-answer-box {
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        border-top: 1px solid #C8E6C9;
        border-right: 1px solid #C8E6C9;
        border-bottom: 1px solid #C8E6C9;
        font-size: 1rem;
    }
    .final-title {
        color: #2E7D32;
        font-weight: 800;
        margin-bottom: 6px;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo các cấu hình
max_steps = 5
gemini_key = os.getenv("GEMINI_API_KEY")

# --- MAIN HEADER ---
st.markdown("<div class='gemini-header'>📱iPhone Shop</div>", unsafe_allow_html=True)
st.markdown("<div class='gemini-subtitle'>Trò chuyện thời gian thực với trợ lý bán hàng ReAct chạy bằng Gemini 3.1 Flash Lite</div>", unsafe_allow_html=True)
# Nút kết thúc hội thoại hiện tại
if st.button("❌ Kết thúc hội thoại (Bắt đầu hội thoại mới)", type="secondary"):
    st.session_state.messages = []
    st.success("Đã kết thúc hội thoại. Hãy bắt đầu cuộc trò chuyện mới!")
    time.sleep(1.0)
    st.rerun()

# Yêu cầu nhập API Key nếu chưa cấu hình
if not gemini_key:
    gemini_key = st.text_input("Nhập Gemini API Key của bạn:", type="password")
    if not gemini_key:
        st.warning("⚠️ Vui lòng cấu hình GEMINI_API_KEY trong file `.env` hoặc nhập trực tiếp ở ô trên để bắt đầu chat.")
        st.stop()

# Khởi tạo mô hình LLM & Agent
try:
    llm = GeminiProvider(model_name="gemini-3.1-flash-lite", api_key=gemini_key)
except Exception as e:
    st.error(f"Lỗi khi kết nối Gemini API: {e}")
    st.stop()

tools_list = [
    {
        "name": "check_stock",
        "description": "Kiểm tra tồn kho và đơn giá của sản phẩm. Tham số: item_name (chuỗi).",
        "func": check_stock
    },
    {
        "name": "get_discount",
        "description": "Lấy phần trăm giảm giá của mã giảm giá. Tham số: coupon_code (chuỗi).",
        "func": get_discount
    },
    {
        "name": "calc_shipping",
        "description": "Tính toán chi phí vận chuyển dựa trên trọng lượng và điểm đến. Tham số: weight (số thực), destination (chuỗi).",
        "func": calc_shipping
    }
]

agent = ReActAgent(llm=llm, tools=tools_list, max_steps=max_steps)

# Khởi tạo lịch sử chat trong Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HIỂN THỊ LỊCH SỬ CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            # Đối với Assistant, nếu có ReAct steps, gom vào expander
            if "steps" in msg and msg["steps"]:
                with st.expander("🧠 Xem quá trình suy luận (ReAct Steps)"):
                    for s in msg["steps"]:
                        step_num = s["step"]
                        thought = s["thought"]
                        action = s["action"]
                        observation = s["observation"]
                        
                        if action != "Final Answer":
                            st.markdown(f"""
                            <div class="react-card thought-action-box">
                                <div class="thought-title">🧠 Thought {step_num}:</div>
                                <div>{thought}</div>
                                <div class="thought-title" style="margin-top: 8px;">🛠️ Action {step_num}:</div>
                                <div class="action-text">{action}</div>
                            </div>
                            <div class="react-card observation-box">
                                <div class="observation-title">📦 Observation {step_num}:</div>
                                <div class="observation-content">{observation}</div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Hiển thị câu trả lời cuối cùng
            st.markdown(msg["content"])

# --- NHẬN TIN NHẮN MỚI ---
user_query = st.chat_input("Hỏi gì đó về sản phẩm iPhone...")

if user_query:
    # 1. Hiển thị tin nhắn của user ngay lập tức
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Lưu vào lịch sử chat
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # 2. Xử lý phản hồi từ Agent
    with st.chat_message("assistant"):
        # Chứa container để hiển thị quá trình suy nghĩ trực tiếp
        think_expander = st.expander("🧠 Đang suy luận và gọi công cụ...", expanded=True)
        final_answer_placeholder = st.empty()
        
        # Lấy lịch sử hội thoại trước câu hỏi hiện tại làm ngữ cảnh
        chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        
        # Chạy agent và đo lường
        with st.spinner("Agent đang hoạt động..."):
            final_response = agent.run(user_query, chat_history=chat_history)
            steps = agent.steps
        
        # Render các bước ReAct vào expander sau khi chạy xong
        with think_expander:
            for s in steps:
                step_num = s["step"]
                thought = s["thought"]
                action = s["action"]
                observation = s["observation"]
                
                if action != "Final Answer":
                    st.markdown(f"""
                    <div class="react-card thought-action-box">
                        <div class="thought-title">🧠 Thought {step_num}:</div>
                        <div>{thought}</div>
                        <div class="thought-title" style="margin-top: 8px;">🛠️ Action {step_num}:</div>
                        <div class="action-text">{action}</div>
                    </div>
                    <div class="react-card observation-box">
                        <div class="observation-title">📦 Observation {step_num}:</div>
                        <div class="observation-content">{observation}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Thay đổi nhãn expander thành trạng thái đã hoàn thành
        think_expander.title = "🧠 Đã hoàn thành quá trình suy luận (ReAct Steps)"
        
        # Hiển thị câu trả lời cuối cùng
        final_answer_placeholder.markdown(final_response)
        
        # Lưu vào lịch sử chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_response,
            "steps": steps
        })
        
        # Trigger reload để cập nhật giao diện
        st.rerun()

