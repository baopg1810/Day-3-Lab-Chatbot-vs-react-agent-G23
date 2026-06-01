import os
import re
import ast
import inspect
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

def parse_arguments(args_str: str) -> Dict[str, Any]:
    """
    Sử dụng AST để phân tích cú pháp chuỗi tham số một cách an toàn.
    Ví dụ:
      - 'item_name="iPhone"' -> {'item_name': 'iPhone'}
      - 'weight=0.8, destination="Hanoi"' -> {'weight': 0.8, 'destination': 'Hanoi'}
    """
    args_str = args_str.strip()
    if not args_str:
        return {"args": [], "kwargs": {}}
        
    try:
        # Bọc chuỗi tham số thành lời gọi hàm giả lập để parse bằng AST
        tree = ast.parse(f"dummy({args_str})")
        call_node = tree.body[0].value
        kwargs = {}
        args = []
        
        for kw in call_node.keywords:
            # Lấy giá trị của keyword argument (hỗ trợ các phiên bản Python khác nhau)
            val = getattr(kw.value, 'value', getattr(kw.value, 'n', getattr(kw.value, 's', None)))
            kwargs[kw.arg] = val
            
        for arg in call_node.args:
            val = getattr(arg, 'value', getattr(arg, 'n', getattr(arg, 's', None)))
            args.append(val)
            
        return {"args": args, "kwargs": kwargs}
    except Exception:
        # Fallback thủ công nếu AST thất bại (ví dụ chuỗi không đúng định dạng python)
        kwargs = {}
        parts = args_str.split(",")
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                kwargs[k] = v
            else:
                val = part.strip().strip("'\"")
                if val:
                    kwargs["arg"] = val
        return {"args": [], "kwargs": kwargs}

def parse_llm_response(text: str) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Phân tích phản hồi của LLM để tách Thought, Action, Tool và Final Answer.
    Hỗ trợ cả trường hợp có số thứ tự bước (Thought 1:, Action 1:) hoặc không.
    """
    text_clean = text.strip()
    
    # 1. Tìm Final Answer trước
    final_match = re.search(r"Final\s+Answer\s*\d*:\s*(.*)", text_clean, re.IGNORECASE | re.DOTALL)
    if final_match:
        return None, None, None, final_match.group(1).strip()
        
    thought = None
    action = None
    tool_name = None
    
    # 2. Tìm Thought
    thought_match = re.search(r"Thought\s*\d*:\s*(.*?)(?=Action\s*\d*:|Final\s+Answer\s*\d*:|$)", text_clean, re.IGNORECASE | re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()
        
    # 3. Tìm Action
    action_match = re.search(r"Action\s*\d*:\s*(.*?)(?=Thought\s*\d*:|Final\s+Answer\s*\d*:|$)", text_clean, re.IGNORECASE | re.DOTALL)
    if action_match:
        action = action_match.group(1).strip()
        # Trích xuất tên tool từ hành động, ví dụ: check_stock(item_name="iPhone") -> check_stock
        tool_name_match = re.match(r"([a-zA-Z0-9_]+)\(", action)
        if tool_name_match:
            tool_name = tool_name_match.group(1).strip()
            
    # 4. Fallback: Nếu không khớp từ khóa nhưng có cú pháp gọi hàm
    if not action and not final_match:
        call_match = re.search(r"([a-zA-Z0-9_]+)\((.*)\)", text_clean)
        if call_match:
            tool_name = call_match.group(1).strip()
            action = call_match.group(0).strip()
            if not thought:
                thought = text_clean.split(action)[0].replace("Thought:", "").strip()
                
    return thought, action, tool_name, None

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Optimized for selling iPhones using local LLMs.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.steps = []  # Lưu trữ các bước chạy chi tiết để hiển thị lên UI

    def get_system_prompt(self) -> str:
        """
        Tạo system prompt hướng dẫn agent tuân thủ cấu trúc ReAct.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""Bạn là một trợ lý bán hàng thông minh tại cửa hàng điện thoại iPhone.
Bạn có quyền truy cập vào các công cụ sau:
{tool_descriptions}

Quy trình làm việc bắt buộc phải tuân theo cấu trúc sau:
Thought 1: Lý do tại sao bạn cần gọi công cụ này.
Action 1: ten_cong_cu(tham_so="gia_tri")
Observation 1: Kết quả nhận được từ công cụ.
Thought 2: Lý do tại sao cần gọi công cụ tiếp theo dựa trên kết quả vừa nhận được.
Action 2: ten_cong_cu_khac(tham_so="gia_tri")
Observation 2: Kết quả nhận được từ công cụ tiếp theo.
... (lặp lại Thought/Action/Observation nếu cần thiết)
Final Answer: Câu trả lời cuối cùng đầy đủ và chi tiết cho khách hàng.

Ví dụ minh họa:
Thought 1: Cần kiểm tra còn hàng không trước khi tính giá.
Action 1: check_stock(item_name="iPhone 15")
Observation 1: Còn 15 chiếc, giá 21.000.000đ/chiếc.
Thought 2: Có hàng. Giờ check mã giảm giá WINNER.
Action 2: get_discount(coupon_code="WINNER")
Observation 2: Giảm 10%.
Thought 3: 2 x 21M = 42M. Giảm 10% = 37.8M. Cần tính phí ship.
Action 3: calc_shipping(weight=0.8, destination="Hanoi")
Observation 3: 50.000đ.
Final Answer: Tổng: 37.850.000đ (2 iPhone 15 42M - 10% = 37.8M + ship 50K). Giao về Hà Nội.

⚠️ NGUYÊN TẮC CỰC KỲ QUAN TRỌNG:
1. Bạn chỉ được gọi các công cụ có trong danh sách trên. Viết đúng tên công cụ và cú pháp truyền tham số.
2. TUYỆT ĐỐI KHÔNG TỰ Ý GIẢ ĐỊNH THÔNG TIN THIẾU: Không bao giờ tự đoán địa chỉ nhận hàng của khách (ví dụ: TP.HCM, Hà Nội,...) hoặc tự đoán mã giảm giá nếu khách hàng chưa hề cung cấp trong cuộc hội thoại.
3. HỎI LẠI KHÁCH HÀNG KHI THIẾU THÔNG TIN:
   - Nếu khách hàng hỏi về phí vận chuyển hoặc tổng giá đã bao gồm phí ship, nhưng bạn chưa biết địa chỉ giao hàng của họ, hãy KHÔNG gọi công cụ `calc_shipping` bằng địa chỉ giả định. Thay vào đó, dừng vòng lặp suy luận ngay lập tức và đưa ra Final Answer để hỏi khách hàng địa chỉ giao hàng của họ.
   - Nếu khách hàng không nhắc đến mã giảm giá, bạn không cần gọi công cụ `get_discount` và không cần đoán mã giảm giá. Hãy tính tổng tiền dựa trên giá sản phẩm và phí ship (nếu có địa chỉ), sau đó thông báo cho khách rằng họ có thể cung cấp thêm mã giảm giá (nếu có).
"""

    def run(self, user_input: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Chạy vòng lặp ReAct: Thought -> Action -> Observation -> ... -> Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        self.steps = []
        self.metrics = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_latency_ms": 0,
            "total_cost": 0.0
        }
        
        # Xây dựng prompt chứa ngữ cảnh lịch sử chat nếu có
        running_prompt = ""
        if chat_history:
            for msg in chat_history:
                role_label = "Khách hàng" if msg["role"] == "user" else "Trợ lý"
                running_prompt += f"{role_label}: {msg['content']}\n"
                
        running_prompt += f"Khách hàng: {user_input}"
        step_count = 0
        
        while step_count < self.max_steps:
            # Gọi LLM sinh bước tiếp theo
            # Đảm bảo truyền system prompt cho mô hình local định dạng chính xác
            response_dict = self.llm.generate(running_prompt, system_prompt=self.get_system_prompt())
            llm_text = response_dict.get("content", "").strip()
            
            # Ghi nhận log thô từ mô hình
            logger.log_event("LLM_RESPONSE", {"raw_text": llm_text, "step": step_count + 1})
            
            # Ghi nhận chỉ số cuộc gọi LLM và tính toán chi phí (cost)
            tracker.track_request(
                provider=response_dict.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=response_dict.get("usage", {}),
                latency_ms=response_dict.get("latency_ms", 0)
            )
            
            # Tích lũy các chỉ số cho lượt request hiện tại
            usage = response_dict.get("usage", {})
            p_tokens = usage.get("prompt_tokens", 0)
            c_tokens = usage.get("completion_tokens", 0)
            t_tokens = usage.get("total_tokens", 0)
            lat = response_dict.get("latency_ms", 0)
            
            self.metrics["total_prompt_tokens"] += p_tokens
            self.metrics["total_completion_tokens"] += c_tokens
            self.metrics["total_tokens"] += t_tokens
            self.metrics["total_latency_ms"] += lat
            
            # Tính cost của cuộc gọi này và cộng vào tổng cost
            step_cost = (p_tokens / 1000000.0) * 0.25 + (c_tokens / 1000000.0) * 1.50
            self.metrics["total_cost"] += step_cost
            
            # Phân tích cú pháp phản hồi
            thought, action, tool_name, final_answer = parse_llm_response(llm_text)
            
            # Fallback nếu LLM không trả về đúng định dạng nhưng có sinh văn bản
            if not thought and not action and not final_answer and llm_text:
                final_answer = llm_text
                
            if final_answer:
                # Ghi nhận bước hoàn thành cuối cùng
                self.steps.append({
                    "step": step_count + 1,
                    "thought": thought or "Đã có đủ thông tin để trả lời.",
                    "action": "Final Answer",
                    "observation": final_answer
                })
                logger.log_event("AGENT_END", {"steps": step_count + 1, "status": "success", "metrics": self.metrics})
                return final_answer
                
            if action and tool_name:
                # Thực thi công cụ
                observation = self._execute_tool(tool_name, action.split("(", 1)[1][:-1])
                
                # Lưu bước này vào history của Agent
                self.steps.append({
                    "step": step_count + 1,
                    "thought": thought or f"Gọi công cụ {tool_name}",
                    "action": action,
                    "observation": observation
                })
                
                # Cập nhật prompt chạy cho bước tiếp theo
                # Tạo định dạng rõ ràng để LLM đọc hiểu lịch sử hội thoại
                running_prompt += f"\nThought {step_count + 1}: {thought or ''}\nAction {step_count + 1}: {action}\nObservation {step_count + 1}: {observation}"
            else:
                # Nếu không thể parse được action hoặc final answer, dừng vòng lặp tránh lặp vô hạn
                fallback_msg = f"Tôi không thể hiểu yêu cầu tiếp theo. Phản hồi thô của tôi: {llm_text}"
                self.steps.append({
                    "step": step_count + 1,
                    "thought": "Lỗi phân tích cú pháp phản hồi.",
                    "action": "None",
                    "observation": fallback_msg
                })
                logger.log_event("AGENT_END", {"steps": step_count + 1, "status": "error_parsing", "metrics": self.metrics})
                return fallback_msg
                
            step_count += 1
            
        logger.log_event("AGENT_END", {"steps": step_count, "status": "max_steps_reached", "metrics": self.metrics})
        return "Tôi chưa thể hoàn thành câu trả lời sau số bước tối đa cho phép."

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Phương thức hỗ trợ thực thi công cụ theo tên và tham số dạng chuỗi.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                func = tool.get('func')
                if not func:
                    return f"Lỗi: Công cụ {tool_name} chưa được gán hàm xử lý."
                
                # Parse arguments
                parsed = parse_arguments(args_str)
                args = parsed.get("args", [])
                kwargs = parsed.get("kwargs", {})
                
                try:
                    # Kiểm tra chữ ký hàm để khớp tham số mờ (Fuzzy matching)
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    
                    adjusted_kwargs = {}
                    for k, v in kwargs.items():
                        matched = False
                        for p in params:
                            # Khớp không phân biệt chữ hoa thường hoặc khớp một phần tên tham số
                            if k.lower() in p.lower() or p.lower() in k.lower():
                                adjusted_kwargs[p] = v
                                matched = True
                                break
                        if not matched:
                            adjusted_kwargs[k] = v
                            
                    # Nếu hàm chỉ nhận 1 tham số mà kwargs có key tên chung chung dạng 'arg'
                    for p in params:
                        if p not in adjusted_kwargs and len(adjusted_kwargs) == 1 and "arg" in adjusted_kwargs:
                            adjusted_kwargs[p] = adjusted_kwargs.pop("arg")
                            
                    # Thực thi hàm
                    if adjusted_kwargs:
                        return func(**adjusted_kwargs)
                    elif args:
                        return func(*args)
                    else:
                        return func()
                except Exception as e:
                    return f"Lỗi khi thực thi công cụ {tool_name}: {e}"
                    
        return f"Không tìm thấy công cụ {tool_name}."
