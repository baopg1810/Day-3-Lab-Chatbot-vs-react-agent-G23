# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Phạm Văn Mạnh]
- **Student ID**: [2A202600837]
- **Date**: [01/06/2026]

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: [e.g., `src/tools/search_tool.py`]
- **Code Highlights**: [Copy snippets or link file lines]
- **Documentation**: [Brief explanation of how your code interacts with the ReAct loop]


Trong project này, tôi phụ trách phát triển giao diện chatbot bằng Streamlit và tích hợp cơ chế suy luận ReAct Agent với Gemini API.

Các thành phần tôi trực tiếp thực hiện gồm:

Xây dựng giao diện chatbot theo phong cách Gemini UI.
Tích hợp Gemini 3.1 Flash Lite API.
Hiển thị quá trình suy luận ReAct:
Thought
Action
Observation
Quản lý lịch sử hội thoại bằng st.session_state.
Tích hợp hệ thống tool calling cho shop tools.
Thiết kế UI hiển thị reasoning steps theo thời gian thực.
Modules Implemented
app.py
src/tools/shop_tools.py
Code Highlights
1. Khởi tạo ReAct Agent
agent = ReActAgent(
    llm=llm,
    tools=tools_list,
    max_steps=max_steps
)

Đoạn code trên dùng để:

kết nối Gemini LLM,
truyền danh sách tools,
thiết lập giới hạn reasoning steps cho ReAct Agent.
2. Hiển thị Thought / Action / Observation
for s in steps:
    thought = s["thought"]
    action = s["action"]
    observation = s["observation"]

Tôi triển khai phần render reasoning process để người dùng có thể theo dõi toàn bộ quá trình suy luận của Agent thay vì chỉ nhận Final Answer.

3. Tool Registration
tools_list = [
    {
        "name": "check_stock",
        "description": "Kiểm tra tồn kho sản phẩm",
        "func": check_stock
    },
    {
        "name": "get_discount",
        "description": "Lấy phần trăm giảm giá",
        "func": get_discount
    }
]

Agent có thể tự lựa chọn tool phù hợp dựa trên yêu cầu của người dùng.

Documentation

Luồng hoạt động của hệ thống:

User Query
   ↓
ReAct Agent
   ↓
Thought
   ↓
Action (Tool Call)
   ↓
Observation
   ↓
Final Answer

ReAct loop giúp Agent suy luận từng bước trước khi đưa ra câu trả lời cuối cùng.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]


Problem Description

Trong quá trình phát triển, Agent đôi khi bị lặp reasoning loop và liên tục gọi lại cùng một tool nhiều lần.

Ví dụ:

Action: check_stock(iPhone 15)
Observation: Stock available
Action: check_stock(iPhone 15)
Observation: Stock available

Điều này gây:

tăng số lượng token,
phản hồi chậm,
reasoning loop không cần thiết.
Diagnosis

Nguyên nhân chính:

Prompt chưa hướng dẫn rõ khi nào Agent cần dừng reasoning.
Observation chưa đủ rõ để model hiểu rằng đã có đủ thông tin.

Ngoài ra:

Gemini đôi khi tiếp tục gọi tool dù đã có kết quả phù hợp.
Solution

Tôi đã:

thêm giới hạn max_steps,
cải thiện format observation,
tối ưu prompt examples trong system prompt.

Ví dụ:

max_steps = 5

Sau khi sửa:

Agent dừng đúng lúc,
giảm số lần gọi tool dư thừa,
cải thiện tốc độ phản hồi.
---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
3.  **Observation**: How did the environment feedback (observations) influence the next steps?

1. Reasoning

Thought block giúp Agent:

suy luận từng bước,
xác định tool phù hợp,
phân tích logic rõ ràng hơn chatbot truyền thống.

Ví dụ:

Chatbot thường trả lời trực tiếp bằng kiến thức có sẵn.
ReAct Agent có thể thật sự gọi tool để kiểm tra tồn kho sản phẩm.
2. Reliability

Trong một số trường hợp, ReAct Agent hoạt động kém hơn chatbot:

Ví dụ:
câu hỏi đơn giản nhưng Agent vẫn gọi tool,
reasoning loop quá dài,
tool output không đúng format.

Điều này làm:

tăng latency,
tăng token cost,
phản hồi phức tạp hơn mức cần thiết.
3. Observation

Observation là thành phần rất quan trọng trong ReAct loop.

Observation giúp Agent:

hiểu kết quả từ tool,
quyết định bước tiếp theo,
giảm hallucination.

Ví dụ:

Observation:
Stock = 0

Sau observation này, Agent có thể:

đề xuất sản phẩm khác,
hoặc thông báo hết hàng cho người dùng.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: [e.g., Use an asynchronous queue for tool calls]
- **Safety**: [e.g., Implement a 'Supervisor' LLM to audit the agent's actions]
- **Performance**: [e.g., Vector DB for tool retrieval in a many-tool system]

Scalability
Tách frontend và backend bằng FastAPI.
Sử dụng asynchronous queue cho tool calling.
Tích hợp Redis để quản lý tasks.
Safety
Thêm supervisor model để kiểm tra output.
Validate tool arguments trước khi thực thi.
Giới hạn số lần tool calling để tránh infinite loops.
Performance
Cache kết quả tool calls.
Tối ưu prompt để giảm token usage.
Sử dụng vector database khi số lượng tools lớn hơn.
Conclusion

Thông qua lab này, tôi hiểu rõ sự khác biệt giữa:

chatbot truyền thống,
và ReAct Agent có reasoning + tool use.

ReAct Agent mạnh hơn trong các bài toán:

cần reasoning nhiều bước,
cần truy cập dữ liệu ngoài,
cần thực hiện hành động thông qua tools.

Tuy nhiên, hệ thống cũng phức tạp hơn và cần:

prompt engineering,
loop control,
tool validation,
monitoring logs.

Lab giúp tôi hiểu sâu hơn về cách xây dựng AI Agent thực tế cho production systems.

---

