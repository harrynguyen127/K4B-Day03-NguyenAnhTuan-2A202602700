"""
📚 [REFERENCE ONLY / CODE MẪU THAM KHẢO]
🧠 CẤP ĐỘ 3: NATIVE MCP AGENT (Native Tool Calling + MCP Server Integration)
⚠️ Lưu ý: File này chỉ dùng để đọc tham khảo kiến trúc. Không chỉnh sửa hay debug file này.
"""

import json

def get_weather(city: str) -> str:
    return f"Thời tiết {city}: 28°C, Nắng nhẹ."

def run_level3_demo():
    print("=== DEMO CẤP ĐỘ 3: NATIVE MCP AGENT ===")
    user_goal = "Tra cứu số ngày phép năm còn lại của NV2026001"
    print(f"🎯 Goal: {user_goal}")
    print("🧠 [Thought]: Phát sinh Native Tool Call 'manage_employee_leave'...")
    print("🛠️ [Native Tool Call]: manage_employee_leave({'action': 'leave_balance_query', 'employee_id': 'NV2026001'})")
    print("👁️ [MCP Server Observation]: {'employee_id': 'NV2026001', 'annual_leave_remaining': 12}")
    print("🏁 [Final Answer]: Nhân viên NV2026001 còn 12 ngày phép năm.")

if __name__ == "__main__":
    run_level3_demo()
