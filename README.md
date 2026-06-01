# 📱 iPhone Shop - Chatbot vs ReAct Agent Demo (Workshop Lab 3)

Chào mừng bạn đến với Lab 3 của khóa học **Agentic AI**! Dự án này là một ứng dụng demo chạy trên nền tảng **Streamlit**, cho phép bạn trải nghiệm và so sánh sự khác biệt giữa một Chatbot thông thường và một **ReAct Agent** (Reasoning + Acting) có khả năng tự động suy luận và gọi các công cụ (tools) cần thiết để trả lời khách hàng.

Dự án này sử dụng mô hình **Gemini API** (`gemini-3.1-flash-lite`) làm bộ não cốt lõi để thực thi vòng lặp ReAct (*Thought -> Action -> Observation*).

---

## 🛠️ Yêu Cầu Hệ Thống

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
- **Python 3.9** trở lên (Khuyên dùng Python 3.10 hoặc 3.11).
- Một **Gemini API Key** hoạt động tốt. Bạn có thể lấy khóa này miễn phí từ [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Các Bước Cài Đặt và Chạy Demo

Hãy thực hiện tuần tự các bước sau đây để thiết lập môi trường và khởi chạy ứng dụng:

### Bước 1: Mở Terminal tại Thư Mục Dự Án
Mở ứng dụng Terminal (đối với macOS/Linux) hoặc PowerShell / Command Prompt (đối với Windows) và di chuyển vào thư mục chứa mã nguồn của dự án này.

### Bước 2: Tạo Môi Trường Ảo (Virtual Environment)
Việc sử dụng môi trường ảo giúp cô lập các thư viện của dự án, tránh xung đột hệ thống.

* **Trên Windows (PowerShell / Command Prompt):**
  ```powershell
  python -m venv venv
  ```

* **Trên macOS / Linux:**
  ```bash
  python3 -m venv venv
  ```

### Bước 3: Kích Hoạt Môi Trường Ảo

* **Trên Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Nếu gặp lỗi phân quyền Script Execution Policy, hãy chạy lệnh `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` rồi thử lại).*

* **Trên Windows (Command Prompt - cmd):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```

* **Trên macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

Sau khi kích hoạt thành công, bạn sẽ thấy tiền tố `(venv)` hiển thị ở đầu dòng lệnh của Terminal.

### Bước 4: Cài Đặt Các Thư Viện Cần Thiết
Chạy lệnh sau để tải và cài đặt toàn bộ dependencies trong file `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Bước 5: Cấu Hình Biến Môi Trường (API Key)
Ứng dụng cần có Gemini API Key để giao tiếp với mô hình ngôn ngữ lớn.

1. Tạo file cấu hình `.env` bằng cách sao chép file ví dụ:
   * **Trên Windows (PowerShell):**
     ```powershell
     copy .env.example .env
     ```
   * **Trên macOS / Linux / Git Bash:**
     ```bash
     cp .env.example .env
     ```

2. Mở file `.env` vừa tạo và thay thế giá trị mẫu bằng API Key thực tế của bạn:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   ```

> [!TIP]
> Nếu bạn chưa điền API Key vào file `.env`, giao diện Streamlit khi chạy cũng sẽ hiển thị một ô nhập liệu an toàn để bạn dán trực tiếp API Key vào đó.

### Bước 6: Khởi Chạy Ứng Dụng Streamlit
Chạy lệnh sau để khởi động máy chủ cục bộ và giao diện Web:

```bash
streamlit run app.py
```

Sau khi khởi chạy thành công, trình duyệt mặc định của bạn sẽ tự động mở trang web ở địa chỉ:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 📂 Cấu Trúc Thư Mục Dự Án

Để tiện cho việc nghiên cứu và thực hành, dưới đây là các thư mục/file quan trọng:

*   `app.py`: Tệp giao diện chính (Streamlit UI) kết nối người dùng, Agent và các Tools.
*   `src/agent/agent.py`: Chứa class chính `ReActAgent` thực hiện vòng lặp suy luận *Thought-Action-Observation*.
*   `src/core/`: Chứa các provider gọi LLM (Gemini, OpenAI, Local Model qua llama-cpp).
*   `src/tools/`:
    *   `shop_tools.py`: Định nghĩa các công cụ bán hàng như kiểm kho (`check_stock`), chiết khấu (`get_discount`), tính ship (`calc_shipping`).
    *   `iphone_db.json`: Cơ sở dữ liệu mẫu của cửa hàng iPhone.
*   `logs/`: Nơi lưu trữ nhật ký hoạt động chi tiết (dạng JSON) của Agent để phân tích hiệu năng và debug.

---

## 🎯 Ví Dụ Thử Nghiệm

Khi giao diện Web của **📱 iPhone Shop** mở lên, hãy thử nhập một câu hỏi phức tạp yêu cầu nhiều bước suy luận và gọi nhiều công cụ, ví dụ:

> *"Tôi muốn mua 2 chiếc iPhone 15 và dùng mã giảm giá WINNER, giao hàng đến Hà Nội. Tính tổng chi phí cho tôi?"*

Hãy quan sát phần **"Xem quá trình suy luận (ReAct Steps)"** để thấy cách Agent:
1.  **Thought 1**: Nhận diện cần kiểm tra kho & giá của *iPhone 15*.
2.  **Action 1**: Gọi `check_stock(item_name="iPhone 15")`.
3.  **Observation 1**: Nhận kết quả tồn kho và giá tiền.
4.  **Thought 2**: Cần lấy giá trị giảm giá của coupon *WINNER*.
5.  **Action 2**: Gọi `get_discount(coupon_code="WINNER")`.
6.  **Observation 2**: Nhận mức giảm giá (ví dụ: 10%).
7.  **Thought 3**: Cần tính phí vận chuyển về *Hà Nội*.
8.  **Action 3**: Gọi `calc_shipping(weight=0.8, destination="Hanoi")`.
9.  **Observation 3**: Nhận chi phí ship.
10. **Final Answer**: Tổng hợp tất cả dữ liệu, tính toán toán học và đưa ra câu trả lời chi tiết cuối cùng cho khách hàng.

---

## ⚠️ Giải Quyết Sự Cố Thường Gặp (Troubleshooting)

*   **Lỗi `ModuleNotFoundError`**: Đảm bảo bạn đã kích hoạt môi trường ảo `(venv)` và chạy lệnh `pip install -r requirements.txt`.
*   **Lỗi API Key không hợp lệ**: Hãy kiểm tra lại xem file `.env` đã được lưu đúng vị trí thư mục gốc chưa, hoặc nhập trực tiếp khóa trên giao diện web của ứng dụng.
*   **Lỗi phân quyền chạy script trên Windows**: Nếu gặp lỗi khi chạy lệnh kích hoạt `Activate.ps1`, hãy mở PowerShell bằng quyền Administrator và chạy lệnh:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    ```

Chúc bạn có một buổi thực hành Lab thú vị và học hỏi được nhiều kiến thức bổ ích về Agentic AI! 🚀
