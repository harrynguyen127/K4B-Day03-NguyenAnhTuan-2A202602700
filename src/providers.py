"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


def _prompt_with_tool_history(
    prompt: str,
    tool_history: Optional[List[Dict[str, Any]]],
) -> str:
    """Bổ sung các Observation cũ vào prompt cho provider stateless."""
    if not tool_history:
        return prompt
    history_json = json.dumps(tool_history, ensure_ascii=False)
    return (
        f"Yêu cầu ban đầu: {prompt}\n\n"
        f"Lịch sử Tool Call và Observation: {history_json}\n\n"
        "Hãy không lặp lại action đã thành công. Nếu đã đủ dữ liệu, "
        "hãy trả lời cuối cùng bằng văn bản."
    )


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        history = tool_history or []
        completed_actions = {
            item.get("arguments", {}).get("action")
            for item in history
            if item.get("observation", {}).get("status") == "SUCCESS"
        }
        if history and history[-1].get("observation", {}).get("status") != "SUCCESS":
            observation = history[-1]["observation"]
            return {
                "type": "text",
                "content": observation.get("message") or observation.get("error") or "Không thể hoàn tất yêu cầu.",
                "thought": "Tool báo lỗi; tôi phản hồi theo Observation và không bịa dữ liệu.",
            }

        employee_match = re.search(r"nv\d{7}", prompt_lower)
        employee_id = employee_match.group(0).upper() if employee_match else ""
        is_multi_step = (
            "chính sách" in prompt_lower
            and "phép" in prompt_lower
            and ("tạo" in prompt_lower or "đơn" in prompt_lower)
        )
        wants_creation = "tạo" in prompt_lower or "xin nghỉ" in prompt_lower
        wants_policy = "chính sách" in prompt_lower or "bảo hiểm" in prompt_lower
        wants_balance = "còn lại" in prompt_lower or "số ngày phép" in prompt_lower

        if "quy trình" in prompt_lower and not employee_id and not history:
            return {
                "type": "text",
                "content": (
                    "[Mock Agent Response]: Quy trình chung gồm chọn loại nghỉ, "
                    "nhập thời gian và lý do, sau đó gửi đơn cho quản lý phê duyệt."
                ),
                "thought": "Câu hỏi chung về quy trình HR, không cần gọi Tool.",
            }

        leave_type = "ốm đau" if "ốm" in prompt_lower else "phép năm"
        date_matches = re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", prompt)
        iso_dates = [f"{year}-{month.zfill(2)}-{day.zfill(2)}" for day, month, year in date_matches]

        def tool_call(action: str, extra_arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            arguments = {"action": action, "employee_id": employee_id}
            arguments.update(extra_arguments or {})
            return {
                "type": "tool_call",
                "tool_name": "manage_employee_leave",
                "arguments": arguments,
                "thought": f"Cần thực hiện nghiệp vụ HR '{action}'.",
            }

        if is_multi_step:
            if "insurance_policy_query" not in completed_actions:
                return tool_call("insurance_policy_query", {"leave_type": leave_type})
            if "leave_balance_query" not in completed_actions:
                return tool_call("leave_balance_query")
            if "create_leave_request" not in completed_actions:
                if len(iso_dates) < 2:
                    return {
                        "type": "text",
                        "content": "Vui lòng cung cấp đủ ngày bắt đầu và ngày kết thúc.",
                        "thought": "Thiếu khoảng ngày để tạo đơn.",
                    }
                return tool_call("create_leave_request", {
                    "leave_type": leave_type,
                    "start_date": iso_dates[0],
                    "end_date": iso_dates[1],
                    "reason": "Nghỉ ốm theo yêu cầu của nhân viên.",
                })
        elif wants_creation and "create_leave_request" not in completed_actions:
            if not employee_id or len(iso_dates) < 2:
                return {
                    "type": "text",
                    "content": "Vui lòng cung cấp mã nhân viên và khoảng ngày nghỉ.",
                    "thought": "Thiếu dữ liệu bắt buộc để tạo đơn.",
                }
            return tool_call("create_leave_request", {
                "leave_type": leave_type,
                "start_date": iso_dates[0],
                "end_date": iso_dates[1],
                "reason": "Về quê giải quyết việc gia đình." if "gia đình" in prompt_lower else "Nghỉ theo yêu cầu của nhân viên.",
            })
        elif wants_policy and "insurance_policy_query" not in completed_actions:
            return tool_call("insurance_policy_query", {"leave_type": leave_type})
        elif wants_balance and "leave_balance_query" not in completed_actions:
            return tool_call("leave_balance_query")

        if history:
            messages = [
                item.get("observation", {}).get("message", "")
                for item in history
                if item.get("observation", {}).get("message")
            ]
            return {
                "type": "text",
                "content": " ".join(messages),
                "thought": "Đã có đủ Observation để tổng hợp câu trả lời.",
            }

        return {
            "type": "text",
            "content": (
                "[Mock Agent Response]: Quy trình chung gồm chọn loại nghỉ, "
                "nhập thời gian và lý do, sau đó gửi đơn cho quản lý phê duyệt."
            ),
            "thought": "Câu hỏi chung về quy trình HR, không cần gọi Tool.",
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=_prompt_with_tool_history(prompt, tool_history),
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": _prompt_with_tool_history(prompt, tool_history)})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
