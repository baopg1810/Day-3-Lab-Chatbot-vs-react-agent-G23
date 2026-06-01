# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phùng Gia Bảo
- **Student ID**: 2A202600579
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

Đóng góp kỹ thuật cốt lõi của tôi trong dự án này tập trung hoàn toàn vào việc triển khai và tối ưu hóa file [agent.py] - trái tim của hệ thống Agent.

- **Modules Implementated**: 
  - Hoàn thiện lớp [ReActAgent] chịu trách nhiệm kiểm soát toàn bộ vòng lặp suy luận ReAct.
  
  - Triển khai chức năng gọi công cụ mềm dẻo (Fuzzy Matching parameters) sử dụng `inspect.signature` tại phương thức [_execute_tool].
- **Documentation**:
  Lớp `ReActAgent` nhận một `LLMProvider` và danh sách các định nghĩa công cụ `tools`. Khi gọi hàm `run(user_input)`, Agent sẽ lặp lại chu kỳ:
  1. Gửi lịch sử chạy hiện tại kèm System Instruction hướng dẫn cấu trúc suy nghĩ cho LLM.
  2. Phân tích văn bản phản hồi của LLM bằng Regex/AST.
  3. Nếu cần hành động, thực hiện gọi hàm Python tương ứng qua `_execute_tool`, nhận kết quả thực thi (`Observation`).
  4. Nối thêm kết quả vào lịch sử hội thoại chạy để làm dữ liệu đầu vào cho bước tiếp theo.
  5. Lặp lại cho đến khi LLM đưa ra `Final Answer` hoặc chạm ngưỡng `max_steps`.

---
## II. Debugging Case Study (10 Points)

Trong quá trình phát triển hệ thống Agent, tôi đã phân tích lỗi liên quan đến việc Agent tự giả định thông tin thiếu của người dùng để gọi công cụ.

- **Problem Description**:
  Khi người dùng hỏi: *"Tính phí vận chuyển cho tôi"* mà không cung cấp địa chỉ, Agent vẫn tiếp tục suy luận và tự ý gọi công cụ `calc_shipping(weight=0.5, destination="Hanoi")` do giả định Hà Nội là vị trí mặc định. Điều này dẫn đến câu trả lời thiếu chính xác và không an toàn cho giao dịch thực tế.
  
- **Log Source**:
  *Trích xuất từ [2026-06-01.readable.log]*
  ```text
  EVENT: LLM_RESPONSE
  Step       : 1
  Thought 1: Khách hàng muốn tính phí vận chuyển nhưng chưa cung cấp địa điểm. Tôi sẽ mặc định địa điểm là Hà Nội để chạy thử công cụ.
  Action 1: calc_shipping(weight=0.5, destination="Hanoi")
  ```

- **Diagnosis**:
  LLM cố gắng thực hiện tất cả các công cụ có sẵn để cho ra câu trả lời trực tiếp mà thiếu đi ràng buộc mang tính phòng vệ (guardrails). Mô hình ngôn ngữ lớn mặc định luôn muốn giải quyết vấn đề thay vì dừng lại đặt câu hỏi phản hồi cho người dùng.

- **Solution**:
  Tôi đã cập nhật `get_system_prompt()` để bổ sung các quy tắc nghiêm ngặt về dữ liệu thiếu:
  ```text
  ⚠️ NGUYÊN TẮC CỰC KỲ QUAN TRỌNG:
  1. TUYỆT ĐỐI KHÔNG TỰ Ý GIẢ ĐỊNH THÔNG TIN THIẾU.
  2. HỎI LẠI KHÁCH HÀNG KHI THIẾU THÔNG TIN: Nếu khách hàng hỏi về phí vận chuyển nhưng bạn chưa biết địa chỉ giao hàng, hãy KHÔNG gọi công cụ calc_shipping bằng địa chỉ giả định. Hãy dừng vòng lặp suy luận ngay lập tức và đưa ra Final Answer để hỏi khách hàng địa chỉ giao hàng.
  ```
  Sau khi bổ sung chỉ thị này, Agent đã chủ động dừng vòng lặp ReAct ngay bước đầu tiên để hỏi địa chỉ khách hàng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**:
    Khối suy nghĩ `Thought` hoạt động giống như một "nháp lập luận" (Chain of Thought). So với Chatbot trả lời trực tiếp dễ bị sai lệch số học hoặc đưa ra thông tin không có căn cứ, `Thought` giúp Agent phân tích yêu cầu thành các bước nhỏ hơn, sắp xếp thứ tự ưu tiên (ví dụ: phải kiểm tra sản phẩm trước khi áp dụng chiết khấu) và kiểm chứng tính hợp lý của kết quả thu được.

2.  **Reliability**:
    ReAct Agent có thể hoạt động kém hiệu quả hơn Chatbot truyền thống đối với các câu hỏi thăm hỏi thông thường (chào hỏi, thời tiết, hoặc các câu hỏi không cần công cụ). Ở những tình huống này, Agent phải mang theo prompt hệ thống rất dài chứa đầy định nghĩa công cụ, dẫn đến độ trễ (latency) cao hơn, tiêu tốn token nhiều hơn và đôi khi cố phân tích cú pháp không cần thiết.

3.  **Observation**:
    Các phản hồi thực tế từ môi trường (`Observation`) đóng vai trò là "mỏ neo thực tế" giúp Agent thoát khỏi sự mơ hồ. Ví dụ, nếu kết quả `check_stock` báo sản phẩm đã hết hàng, Agent sẽ lập tức dừng các bước tiếp theo (không tính giảm giá, không tính ship) mà trực tiếp đưa ra thông báo từ chối khéo léo trong `Final Answer`, điều hướng khách hàng sang dòng sản phẩm khác.

---

## IV. Future Improvements (5 Points)

Để đưa hệ thống Agent này lên môi trường sản xuất thực tế với quy mô lớn, tôi đề xuất các giải pháp sau:

- **Scalability**: Chuyển đổi mô hình ReAct tuần tự sang đồ thị trạng thái bất đồng bộ (ví dụ: sử dụng **LangGraph**). Điều này cho phép thực thi song song các công cụ độc lập (như kiểm tra tồn kho và kiểm tra mã giảm giá cùng một lúc), tối ưu hóa thời gian xử lý tổng thể.
- **Safety**: Triển khai một lớp kiểm soát an toàn độc lập (như **Llama Guard** hoặc mô hình phân loại Intent) ở đầu vào để lọc các câu hỏi có tính chất phá hoại, Prompt Injection, trước khi đưa vào vòng lặp ReAct tốn kém tài nguyên.
- **Performance**: Áp dụng cơ chế **Semantic Cache** cho các yêu cầu gọi công cụ. Nếu khách hàng hỏi những câu giống nhau liên tiếp, kết quả từ các tool có thể được trả về từ cache thay vì gọi lại LLM và chạy lại code Python, giảm thiểu độ trễ xuống dưới 100ms.
