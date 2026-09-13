"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND

Khai báo Tool Schema và execution layer mô phỏng cho Trợ lý Nhân sự
VinFast. Toàn bộ dữ liệu trong tệp này chỉ dùng cho bài thực hành.
"""

import json
from datetime import date, timedelta
from typing import Any, Dict, Optional


# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMA CHUẨN NATIVE JSON SCHEMA
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "manage_employee_leave",
        "description": (
            "Tra cứu phép năm, chính sách bảo hiểm hoặc tạo đơn "
            "nghỉ phép cho nhân viên VinFast."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "leave_balance_query",
                        "insurance_policy_query",
                        "create_leave_request",
                    ],
                    "description": "Nghiệp vụ nhân sự cần thực hiện.",
                },
                "employee_id": {
                    "type": "string",
                    "description": "Mã nhân viên, ví dụ: NV2026001.",
                },
                "leave_type": {
                    "type": "string",
                    "enum": ["phép năm", "ốm đau", "thai sản"],
                    "description": (
                        "Loại nghỉ. Bắt buộc với insurance_policy_query "
                        "và create_leave_request."
                    ),
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Ngày bắt đầu YYYY-MM-DD; bắt buộc khi tạo đơn.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Ngày kết thúc YYYY-MM-DD; bắt buộc khi tạo đơn.",
                },
                "reason": {
                    "type": "string",
                    "description": "Lý do nghỉ; bắt buộc khi tạo đơn.",
                },
            },
            "required": ["action", "employee_id"],
            "additionalProperties": False,
        },
    }
]


# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_EMPLOYEE_DATABASE = {
    "NV2026001": {
        "full_name": "Nguyễn Văn An",
        "department": "Sản xuất",
        "annual_leave_remaining": 12,
    },
    "NV2026002": {
        "full_name": "Trần Thị Bình",
        "department": "Kỹ thuật",
        "annual_leave_remaining": 8,
    },
}

MOCK_INSURANCE_POLICIES = {
    "phép năm": {
        "benefit": "Hưởng 100% lương theo chính sách mock.",
        "deducted_from_annual_leave": True,
        "note": "Số ngày nghỉ được trừ vào phép năm còn lại.",
    },
    "ốm đau": {
        "benefit": "Hưởng 75% mức lương theo chính sách mock khi đủ điều kiện.",
        "deducted_from_annual_leave": False,
        "note": "Nghỉ ốm không trừ phép năm trong mô phỏng này.",
    },
    "thai sản": {
        "benefit": "Thời gian hưởng chế độ là 6 tháng theo chính sách mock.",
        "deducted_from_annual_leave": False,
        "note": "Nghỉ thai sản không trừ phép năm trong mô phỏng này.",
    },
}


def _json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _validation_error(message: str) -> str:
    return _json_response({"status": "VALIDATION_ERROR", "message": message})


def _normalize_employee_id(employee_id: Any) -> str:
    return str(employee_id or "").strip().upper()


def _normalize_leave_type(leave_type: Any) -> str:
    return str(leave_type or "").strip().lower()


def _parse_iso_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Thiếu trường bắt buộc '{field_name}'.")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(
            f"Trường '{field_name}' phải có định dạng YYYY-MM-DD."
        ) from exc


def _count_working_days(start_date: date, end_date: date) -> int:
    current_date = start_date
    working_days = 0
    while current_date <= end_date:
        if current_date.weekday() < 5:
            working_days += 1
        current_date += timedelta(days=1)
    return working_days


def execute_manage_employee_leave(
    action: str,
    employee_id: str,
    leave_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reason: Optional[str] = None,
) -> str:
    """Thực thi các nghiệp vụ nghỉ phép trên dữ liệu mock."""
    normalized_action = str(action or "").strip()
    normalized_employee_id = _normalize_employee_id(employee_id)

    if normalized_action not in {
        "leave_balance_query",
        "insurance_policy_query",
        "create_leave_request",
    }:
        return _json_response({
            "status": "UNKNOWN_ACTION",
            "message": f"Action '{normalized_action}' không được hỗ trợ.",
        })

    if not normalized_employee_id:
        return _validation_error("Thiếu trường bắt buộc 'employee_id'.")

    employee = MOCK_EMPLOYEE_DATABASE.get(normalized_employee_id)
    if employee is None:
        return _json_response({
            "status": "NOT_FOUND",
            "employee_id": normalized_employee_id,
            "message": f"Không tìm thấy dữ liệu nhân viên có mã '{normalized_employee_id}'.",
        })

    if normalized_action == "leave_balance_query":
        return _json_response({
            "status": "SUCCESS",
            "action": normalized_action,
            "employee_id": normalized_employee_id,
            "employee": employee,
            "annual_leave_remaining": employee["annual_leave_remaining"],
            "message": (
                f"Nhân viên {normalized_employee_id} còn "
                f"{employee['annual_leave_remaining']} ngày phép năm."
            ),
        })

    normalized_leave_type = _normalize_leave_type(leave_type)
    if not normalized_leave_type:
        return _validation_error(
            f"Action '{normalized_action}' yêu cầu trường 'leave_type'."
        )

    policy = MOCK_INSURANCE_POLICIES.get(normalized_leave_type)
    if policy is None:
        supported_types = ", ".join(MOCK_INSURANCE_POLICIES)
        return _validation_error(
            f"Loại nghỉ '{normalized_leave_type}' không hợp lệ. "
            f"Các loại được hỗ trợ: {supported_types}."
        )

    if normalized_action == "insurance_policy_query":
        return _json_response({
            "status": "SUCCESS",
            "action": normalized_action,
            "employee_id": normalized_employee_id,
            "leave_type": normalized_leave_type,
            "policy": policy,
            "message": (
                f"Chính sách mock cho nghỉ {normalized_leave_type}: "
                f"{policy['benefit']} {policy['note']}"
            ),
        })

    if not isinstance(reason, str) or not reason.strip():
        return _validation_error(
            "Action 'create_leave_request' yêu cầu trường 'reason'."
        )

    try:
        parsed_start_date = _parse_iso_date(start_date, "start_date")
        parsed_end_date = _parse_iso_date(end_date, "end_date")
    except ValueError as exc:
        return _validation_error(str(exc))

    if parsed_start_date > parsed_end_date:
        return _validation_error("'end_date' không được trước 'start_date'.")

    working_days = _count_working_days(parsed_start_date, parsed_end_date)
    if working_days == 0:
        return _validation_error("Khoảng nghỉ không có ngày làm việc.")

    current_balance = employee["annual_leave_remaining"]
    deducted_from_annual_leave = policy["deducted_from_annual_leave"]
    if deducted_from_annual_leave and working_days > current_balance:
        return _validation_error(
            f"Đơn yêu cầu {working_days} ngày làm việc nhưng nhân viên chỉ "
            f"còn {current_balance} ngày phép năm."
        )

    projected_balance = (
        current_balance - working_days
        if deducted_from_annual_leave
        else current_balance
    )
    request_id = (
        f"LR-{normalized_employee_id}-"
        f"{parsed_start_date:%Y%m%d}-{parsed_end_date:%Y%m%d}"
    )
    return _json_response({
        "status": "SUCCESS",
        "action": normalized_action,
        "request_id": request_id,
        "employee_id": normalized_employee_id,
        "employee_name": employee["full_name"],
        "leave_type": normalized_leave_type,
        "start_date": parsed_start_date.isoformat(),
        "end_date": parsed_end_date.isoformat(),
        "working_days": working_days,
        "reason": reason.strip(),
        "deducted_from_annual_leave": deducted_from_annual_leave,
        "annual_leave_remaining": current_balance,
        "projected_annual_leave_remaining": projected_balance,
        "message": (
            f"Đã tạo đơn {request_id} cho {normalized_employee_id}: "
            f"nghỉ {normalized_leave_type} {working_days} ngày làm việc."
        ),
    })


TOOL_ROUTER = {"manage_employee_leave": execute_manage_employee_leave}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Trung chuyển tool call và luôn trả kết quả dưới dạng JSON string."""
    tool = TOOL_ROUTER.get(tool_name)
    if tool is None:
        return _json_response({
            "status": "UNKNOWN_TOOL",
            "error": f"Tool '{tool_name}' không tồn tại.",
        })
    if not isinstance(arguments, dict):
        return _validation_error("Tool arguments phải là một JSON object.")
    try:
        return tool(**arguments)
    except TypeError as exc:
        return _validation_error(f"Tham số tool không hợp lệ: {exc}")
    except Exception as exc:
        return _json_response({"status": "EXECUTION_ERROR", "error": str(exc)})


def run_tools_check() -> None:
    """In Pass Signal cho Task 2.1 khi chạy trực tiếp tệp này."""
    expected_tool_name = "manage_employee_leave"
    registered_tools = [tool.get("name") for tool in TOOLS_SCHEMA]

    if expected_tool_name not in registered_tools:
        print(f"❌ [TOOLS CHECK]: Chưa đăng ký tool '{expected_tool_name}'.")
        raise SystemExit(1)

    print(
        f"✅ [TOOLS CHECK]: Đã đăng ký thành công "
        f"{len(registered_tools)} Native Tool HR trong TOOLS_SCHEMA!"
    )

    result = json.loads(dispatch_tool_call(expected_tool_name, {
        "action": "leave_balance_query",
        "employee_id": "NV2026001",
    }))
    if result.get("status") != "SUCCESS":
        print(
            f"❌ Kết quả gọi thử {expected_tool_name}: "
            f"Status {result.get('status', 'UNKNOWN')}"
        )
        raise SystemExit(1)

    employee_name = result.get("employee", {}).get("full_name", "NV2026001")
    leave_remaining = result.get("annual_leave_remaining")
    print(
        f"🧪 Kết quả gọi thử {expected_tool_name}: Status SUCCESS "
        f"(Nhân viên {employee_name} còn {leave_remaining} ngày phép năm)"
    )


if __name__ == "__main__":
    run_tools_check()
