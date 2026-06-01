import json
import os
import unicodedata

DB_PATH = os.path.join(os.path.dirname(__file__), "iphone_db.json")

def load_db():
    if not os.path.exists(DB_PATH):
        return {
            "products": {
                "iphone": {"name": "iPhone", "stock": 15, "price": 25000000, "description": "Điện thoại Apple iPhone tiêu chuẩn"}
            },
            "coupons": {"WINNER": 0.10},
            "shipping": {"hanoi": 50000, "ha noi": 50000}
        }
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def strip_accents(text: str) -> str:
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    return text.decode("utf-8").lower()

def check_stock(item_name: str) -> str:
    """Kiểm tra tồn kho và đơn giá của một mặt hàng điện thoại."""
    db = load_db()
    name_clean = item_name.strip().lower()
    name_clean_ascii = strip_accents(name_clean)
    
    # Nếu chỉ gõ chung chung "iphone" hoặc "điện thoại iphone"
    if name_clean in ["iphone", "dien thoai iphone", "dien thoai"] or name_clean_ascii in ["iphone", "dien thoai iphone", "dien thoai"]:
        return "Vui lòng chỉ rõ mã dòng iPhone cụ thể bạn muốn mua (ví dụ: iPhone 14, iPhone 15, iPhone 16...)."
        
    # 1. Thử khớp chính xác trước
    if name_clean in db["products"]:
        prod = db["products"][name_clean]
        return f"Còn {prod['stock']} chiếc, giá {prod['price']:,}đ/chiếc."
    
    # 2. Thử khớp mờ và tìm đối tượng khớp tốt nhất (có độ dài lệch ít nhất)
    best_match_key = None
    best_match_len_diff = float('inf')
    
    for key, prod in db["products"].items():
        key_ascii = strip_accents(key)
        if key in name_clean or name_clean in key or key_ascii in name_clean_ascii or name_clean_ascii in key_ascii:
            len_diff = abs(len(key) - len(name_clean))
            if len_diff < best_match_len_diff:
                best_match_len_diff = len_diff
                best_match_key = key
                
    if best_match_key:
        prod = db["products"][best_match_key]
        return f"Còn {prod['stock']} chiếc, giá {prod['price']:,}đ/chiếc."
            
    return f"Không tìm thấy sản phẩm '{item_name}'."

def get_discount(coupon_code: str) -> str:
    """Lấy phần trăm giảm giá của mã giảm giá."""
    db = load_db()
    code_clean = coupon_code.strip().upper()
    if code_clean in db["coupons"]:
        discount = db["coupons"][code_clean]
        return f"Giảm {int(discount * 100)}%."
    return "Mã giảm giá không hợp lệ."

def calc_shipping(weight, destination: str) -> str:
    """Tính toán chi phí vận chuyển dựa trên trọng lượng sản phẩm (kg) và điểm đến."""
    db = load_db()
    dest_clean = destination.strip().lower()
    dest_ascii = strip_accents(dest_clean)
    
    # Ép kiểu weight nếu bị truyền dạng string
    try:
        if isinstance(weight, str):
            weight = float(weight.replace(",", ".").strip())
    except Exception:
        weight = 0.5
        
    fee = 0
    found = False
    
    # Duyệt kiểm tra điểm đến
    for city, cost in db["shipping"].items():
        city_ascii = strip_accents(city)
        if city in dest_clean or dest_clean in city or city_ascii in dest_ascii or dest_ascii in city_ascii:
            fee = cost
            found = True
            break
            
    if not found:
        # Mặc định phí ship nếu không tìm thấy là 80.000đ
        fee = 80000
        
    return f"{fee:,}đ."
