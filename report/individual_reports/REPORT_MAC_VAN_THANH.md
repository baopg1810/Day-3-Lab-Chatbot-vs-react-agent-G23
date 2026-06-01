# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và Tên**: Mạc Văn Thanh
- **Mã Sinh Viên**: 2A202600638
- **Ngày nộp**: 01/06/2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

Trong lab này, tôi đã hoàn thiện và kiểm tra các module sau:

- **Các module đã triển khai**:
  - `src/telemetry/logger.py`
  - `src/telemetry/metrics.py`
  - `src/core/gemini_provider.py`

---

### Mô tả chi tiết từng module

#### `logger.py` — Class `IndustryLogger`

Class `IndustryLogger` khởi tạo **hai logger Python riêng biệt**:

- `json_logger`: ghi từng sự kiện ra file `logs/YYYY-MM-DD.log` dưới dạng một dòng JSON (sử dụng `json.dumps(..., ensure_ascii=False)`).
- `readable_logger`: ghi ra file `logs/YYYY-MM-DD.readable.log` và console, định dạng dễ đọc bằng border `=` và `-`.

Phương thức `log_event(event_type, data)` xây dựng payload `{"timestamp", "event", "data"}`, rồi gọi cả hai logger. Phương thức `_format_readable()` xử lý riêng bốn loại sự kiện:

| Sự kiện | Nội dung ghi lại |
|---------|-----------------|
| `AGENT_START` | `input` (câu hỏi user) và `model` (tên model) |
| `LLM_RESPONSE` | `step` (số bước) và `raw_text` (toàn bộ phản hồi thô của LLM) |
| `LLM_METRIC` | `provider`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`, `cost_estimate` |
| `AGENT_END` | `steps` (tổng số bước), `status`, và dict `metrics` tích lũy |

Ngoài ra có `info(msg)` và `error(msg, exc_info=True)` để ghi log thông thường.

---

#### `metrics.py` — Class `PerformanceTracker`

Class `PerformanceTracker` lưu danh sách `session_metrics` (list các dict).

- **`track_request(provider, model, usage, latency_ms)`**: Tạo dict metric từ các tham số, gọi `_calculate_cost()`, lưu vào `session_metrics`, rồi gọi `logger.log_event("LLM_METRIC", metric)`.
- **`_calculate_cost(model, usage)`**: Tính chi phí theo công thức:
  - Input: `prompt_tokens / 1_000_000 × 0.25`
  - Output: `completion_tokens / 1_000_000 × 1.50`
  - Trả về tổng `input_cost + output_cost`.

Biến global `tracker = PerformanceTracker()` được dùng chung trong toàn dự án.

---

#### `gemini_provider.py` — Class `GeminiProvider`

`GeminiProvider` kế thừa `LLMProvider` (abstract base class có hai abstract method: `generate()` và `stream()`).

- **`__init__`**: Đọc `GEMINI_API_KEY` từ tham số hoặc biến môi trường, gọi `genai.configure(api_key=...)`, khởi tạo `genai.GenerativeModel(model_name)`. Mặc định dùng model `"gemini-3.1-flash-lite"`.

- **`generate(prompt, system_prompt)`**:
  1. Nếu có `system_prompt`, ghép thành `"System: {system_prompt}\n\nUser: {prompt}"`.
  2. Gọi `self.model.generate_content(full_prompt, generation_config={"stop_sequences": ["Observation:", "Observation"]})`.
  3. Đo `latency_ms = int((end_time - start_time) * 1000)`.
  4. Đọc `response.usage_metadata` để lấy `prompt_token_count`, `candidates_token_count`, `total_token_count`.
  5. Trả về dict: `{"content", "usage", "latency_ms", "provider": "google"}`.

- **`stream(prompt, system_prompt)`**: Gọi `generate_content(..., stream=True, ...)` với cùng `stop_sequences`, yield từng `chunk.text`.

---

### Tích hợp vào `agent.py`

Trong `ReActAgent.run()`, ba module trên được dùng như sau:

```python
# Ghi bắt đầu
logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

# Mỗi bước vòng lặp ReAct
response_dict = self.llm.generate(running_prompt, system_prompt=self.get_system_prompt())
logger.log_event("LLM_RESPONSE", {"raw_text": llm_text, "step": step_count + 1})
tracker.track_request(provider=..., model=..., usage=..., latency_ms=...)

# Khi kết thúc
logger.log_event("AGENT_END", {"steps": ..., "status": ..., "metrics": self.metrics})
```

---

## II. Phân Tích Bug & Cách Xử Lý (10 Điểm)

### Mô tả vấn đề

**Vấn đề**: Hàm `parse_llm_response()` trong `agent.py` không tách được `Action` khi LLM trả về phản hồi không đúng định dạng `Thought/Action/Final Answer`. Khi đó agent rơi vào nhánh `else` ở dòng 237–247:

```python
else:
    fallback_msg = f"Tôi không thể hiểu yêu cầu tiếp theo. Phản hồi thô của tôi: {llm_text}"
    logger.log_event("AGENT_END", {..., "status": "error_parsing", ...})
    return fallback_msg
```

**Nguồn log**: File `logs/YYYY-MM-DD.readable.log` — sự kiện `LLM_RESPONSE` hiển thị `raw_text` không chứa từ khóa `Thought:` hay `Action:`, tiếp theo là `AGENT_END` với `status: "error_parsing"`.

---

### Chẩn đoán nguyên nhân

Hàm `parse_llm_response()` dùng ba bước regex:

1. Tìm `Final Answer` — dùng pattern `r"Final\s+Answer\s*\d*:\s*(.*)"`.
2. Tìm `Thought` — dùng pattern `r"Thought\s*\d*:\s*(.*?)(?=Action\s*\d*:|Final\s+Answer\s*\d*:|$)"`.
3. Tìm `Action` — dùng pattern `r"Action\s*\d*:\s*(.*?)(?=Thought\s*\d*:|Final\s+Answer\s*\d*:|$)"`, rồi tách `tool_name` từ `([a-zA-Z0-9_]+)\(`.

Khi LLM trả về văn bản có thêm markdown (ví dụ dùng dấu `**`, thụt đầu dòng, hoặc không viết đúng `Thought 1:` mà viết `Thought:`), các regex này không khớp. Kết quả là `thought=None`, `action=None`, `final_answer=None`.

Thêm vào đó, nếu `llm_text` không rỗng thì fallback ở dòng 208–209 sẽ kích hoạt:

```python
if not thought and not action and not final_answer and llm_text:
    final_answer = llm_text
```

Tuy nhiên nếu `llm_text` **là chuỗi rỗng** (response bị cắt bởi `stop_sequences`), cả fallback lẫn nhánh `final_answer` đều không chạy, dẫn đến trả về `fallback_msg`.

---

### Giải pháp đã áp dụng trong code

**1. Bước 4 — Fallback tìm cú pháp gọi hàm** (đã có trong `parse_llm_response()`):

```python
# Dòng 84-92 trong agent.py
if not action and not final_match:
    call_match = re.search(r"([a-zA-Z0-9_]+)\((.*)\)", text_clean)
    if call_match:
        tool_name = call_match.group(1).strip()
        action = call_match.group(0).strip()
        if not thought:
            thought = text_clean.split(action)[0].replace("Thought:", "").strip()
```

Nếu regex chuẩn không khớp nhưng LLM vẫn sinh ra cú pháp `ten_cong_cu(tham_so)`, bước này vẫn tách được `tool_name` và `action`.

**2. Fallback `final_answer = llm_text`** (dòng 208–209 trong `agent.py`):

Khi không parse được gì nhưng LLM vẫn trả về văn bản có nội dung, agent gán toàn bộ text đó làm `final_answer` thay vì dừng với lỗi.

**3. System prompt có ví dụ minh họa** (trong `get_system_prompt()`):

`get_system_prompt()` cung cấp ví dụ cụ thể với `Thought 1:`, `Action 1:`, `Observation 1:` và cảnh báo `⚠️ NGUYÊN TẮC CỰC KỲ QUAN TRỌNG` để LLM tuân thủ định dạng, giảm tần suất xuất hiện lỗi parse.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct Agent (10 Điểm)

**1. Về khả năng suy luận từng bước (Reasoning)**: Block `Thought` trong ReAct buộc LLM phải viết rõ lý do trước khi gọi công cụ. Trong demo này, agent cần gọi lần lượt `check_stock()`, `get_discount()`, `calc_shipping()` theo thứ tự logic và dùng kết quả `Observation` từ bước trước để quyết định bước tiếp. Chatbot không có cơ chế này — chatbot trả lời trực tiếp từ kiến thức có sẵn mà không truy vấn dữ liệu thực tế.

**2. Về độ tin cậy (Reliability)**: Agent ReAct phụ thuộc vào `parse_llm_response()` để hoạt động đúng. Nếu LLM không tuân thủ định dạng, agent sẽ kích hoạt fallback hoặc trả về `fallback_msg`. Chatbot ít bị lỗi hơn với câu hỏi đơn giản vì không cần bước parse trung gian. Tuy nhiên với câu hỏi đa bước (ví dụ: tính tổng giá 2 máy có giảm giá và phí ship), chatbot có thể trả lời sai vì không có dữ liệu tồn kho thực tế.

**3. Về vai trò của Observation**: Sau mỗi lần gọi tool, `_execute_tool()` trả về chuỗi kết quả thực tế và được nối vào `running_prompt` dưới dạng `Observation {n}: ...`. Điều này giúp LLM ở bước tiếp theo nhìn thấy kết quả thực tế thay vì phải tự đoán. Ví dụ, sau khi nhận `Observation: Còn 15 chiếc, giá 21.000.000đ/chiếc`, agent mới tính giá tổng chính xác.

---

## IV. Đề Xuất Cải Tiến (5 Điểm)

Các đề xuất sau dựa trên các hạn chế quan sát được trực tiếp từ code hiện tại:

- **Scalability**: `GeminiProvider.generate()` hiện là synchronous. Có thể chuyển sang `async def` để phục vụ nhiều request song song, phù hợp khi triển khai thực tế với nhiều người dùng đồng thời trên Streamlit hoặc API server.

- **Safety**: `_execute_tool()` hiện bắt `Exception` chung và trả về chuỗi lỗi. Có thể thêm kiểm tra kiểu dữ liệu đầu vào (ví dụ: `weight` trong `calc_shipping` phải là số dương) trước khi gọi hàm tool, tránh để lỗi xảy ra trong `try/except`.

- **Performance**: `PerformanceTracker` hiện chỉ lưu `session_metrics` trong bộ nhớ. Có thể lưu sang file hoặc database để theo dõi chi phí tích lũy theo thời gian thay vì mất sau mỗi phiên chạy.

---

> [!NOTE]
> Báo cáo được viết hoàn toàn bằng tiếng Việt, dựa trực tiếp trên code trong repository.
> Nếu nộp chính thức, đổi tên file thành `REPORT_Mac_Van_Thanh.md`.
