# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thành Chiến
- **Student ID**: 2A202600861
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

### Specific Contribution

Trong dự án ReAct Agent cho cửa hàng bán iPhone, tôi chịu trách nhiệm xây dựng bộ công cụ (tool layer) và dữ liệu mô phỏng để Agent có thể truy vấn thông tin sản phẩm thay vì trả lời bằng kiến thức nội bộ của mô hình.

### Modules Implemented

- `iphone_tools.py`
- `iphone_db.json`

### Features Implemented

#### 1. Product Inventory Lookup

Xây dựng hàm `check_stock()` để:

- Kiểm tra số lượng tồn kho.
- Trả về giá bán của sản phẩm.
- Hỗ trợ tìm kiếm gần đúng (fuzzy matching).
- Hỗ trợ nhập liệu có hoặc không dấu tiếng Việt.

Ví dụ:

```python
def check_stock(item_name: str) -> str:
    ...
```

Người dùng có thể nhập:

```text
iphone 15 pro
Iphone15 Pro
điện thoại iphone 15 pro
```

và hệ thống vẫn nhận diện đúng sản phẩm.

#### 2. Coupon Validation Tool

Xây dựng hàm:

```python
def get_discount(coupon_code: str) -> str:
```

Cho phép Agent:

- Kiểm tra tính hợp lệ của mã giảm giá.
- Trả về phần trăm giảm giá tương ứng.

Ví dụ:

```text
WINNER → Giảm 10%
SALE20 → Giảm 20%
```

#### 3. Shipping Cost Calculator

Xây dựng hàm:

```python
def calc_shipping(weight, destination: str) -> str:
```

Chức năng:

- Tính phí vận chuyển dựa trên khu vực.
- Hỗ trợ nhiều cách viết địa danh.

Ví dụ:

```text
Hà Nội
Ha Noi
hanoi
```

đều được xử lý thành cùng một kết quả.

#### 4. Demo Product Database

Thiết kế file:

```json
iphone_db.json
```

bao gồm:

- 11 mẫu iPhone.
- Thông tin giá bán.
- Tồn kho.
- Mã giảm giá.
- Phí vận chuyển.

Ví dụ:

```json
"iphone 16 pro": {
    "stock": 10,
    "price": 28000000
}
```

### Documentation

Các tool được đăng ký vào ReAct Agent dưới dạng các Action.

Ví dụ luồng hoạt động:

```text
Thought: Người dùng hỏi giá iPhone 16 Pro.
Action: check_stock("iphone 16 pro")
Observation: Còn 10 chiếc, giá 28,000,000đ.
Final Answer: iPhone 16 Pro hiện còn 10 chiếc với giá 28 triệu đồng.
```

Nhờ đó Agent có thể lấy dữ liệu từ cơ sở dữ liệu thay vì tự suy đoán thông tin như chatbot thông thường.

---

## II. Debugging Case Study (10 Points)

### Problem Description

Trong quá trình kiểm thử, Agent thường không tìm được sản phẩm khi người dùng nhập tên sản phẩm không đúng định dạng.

Ví dụ:

```text
User: còn iphone15promax không?
```

Agent gọi:

```text
Action: check_stock("iphone15promax")
```

và nhận được:

```text
Không tìm thấy sản phẩm.
```

### Log Source

Ví dụ log:

```text
Thought: Need inventory information.
Action: check_stock("iphone15promax")

Observation:
Không tìm thấy sản phẩm 'iphone15promax'
```

### Diagnosis

Nguyên nhân là do:

- Người dùng không nhập dấu cách giữa các từ.
- Dữ liệu được lưu dưới dạng:

```text
iphone 15 pro max
```

trong khi Agent truyền:

```text
iphone15promax
```

Tool ban đầu chỉ hỗ trợ so khớp chính xác nên không thể tìm thấy sản phẩm.

Đây là lỗi ở tầng thiết kế Tool thay vì lỗi của mô hình LLM.

### Solution

Tôi đã bổ sung:

#### Chuẩn hóa chuỗi đầu vào

```python
def strip_accents(text: str):
```

để loại bỏ dấu tiếng Việt và chuẩn hóa dữ liệu.

#### Fuzzy Matching

```python
if key in name_clean or name_clean in key:
```

để hỗ trợ tìm kiếm gần đúng.

Sau khi cập nhật:

```text
iphone15promax
iphone 15 pro max
IPhone 15 Pro Max
```

đều được ánh xạ tới cùng một sản phẩm.

Kết quả là Agent trả lời chính xác hơn và giảm đáng kể số lần gọi tool thất bại.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

Chatbot truyền thống chỉ dựa vào kiến thức đã được huấn luyện.

Ví dụ với câu hỏi:

```text
Còn bao nhiêu chiếc iPhone 16 Pro?
```

Chatbot không thể biết chính xác số lượng tồn kho thực tế.

Trong khi đó, ReAct Agent thực hiện quy trình:

```text
Thought
→ Action
→ Observation
→ Final Answer
```

Agent sẽ chủ động truy vấn dữ liệu thông qua tool trước khi trả lời, giúp kết quả chính xác và đáng tin cậy hơn.

### 2. Reliability

Trong một số trường hợp Agent hoạt động kém hơn Chatbot:

- Chọn sai tool.
- Truyền tham số không đúng định dạng.
- Gọi tool nhiều lần không cần thiết.
- Tool trả về lỗi hoặc dữ liệu không đầy đủ.

Ví dụ:

```text
Action: check_stock("iphone")
```

Tool yêu cầu người dùng cung cấp model cụ thể, khiến Agent phải thực hiện thêm bước hỏi lại.

Trong khi Chatbot có thể đưa ra câu trả lời chung chung ngay lập tức.

### 3. Observation

Observation là yếu tố quan trọng nhất trong vòng lặp ReAct.

Ví dụ:

```text
Action: get_discount("WINNER")

Observation:
Giảm 10%.
```

Agent sẽ sử dụng kết quả này để tạo câu trả lời cuối cùng:

```text
Mã giảm giá WINNER hiện áp dụng mức giảm 10%.
```

Điều này cho thấy Agent phản hồi dựa trên dữ liệu thực tế từ môi trường thay vì chỉ dựa trên xác suất sinh văn bản.

---

## IV. Future Improvements (5 Points)

### Scalability

- Chuyển dữ liệu từ JSON sang MySQL hoặc PostgreSQL.
- Xây dựng Inventory Service riêng thay vì đọc trực tiếp file JSON.
- Hỗ trợ số lượng sản phẩm lớn hơn và nhiều danh mục sản phẩm khác ngoài iPhone.

### Safety

- Kiểm tra và xác thực dữ liệu đầu vào.
- Giới hạn các Action được phép thực hiện.
- Bổ sung cơ chế chống Prompt Injection trước khi gọi tool.

### Performance

- Sử dụng cache cho các truy vấn thường xuyên.
- Tích hợp Vector Database để tìm kiếm sản phẩm theo ngữ nghĩa.
- Tối ưu quá trình lựa chọn tool nhằm giảm số lần gọi không cần thiết.

---
