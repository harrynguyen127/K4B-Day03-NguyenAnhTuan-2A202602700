# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Anh Tuấn  
> **Mã Sinh Viên / Mã Học viên:** 2A202602700
> **Chủ đề Lựa chọn:** *Trợ lý Nhân sự VinFast (HR Assistant):* Tra cứu ngày phép còn lại, chính sách bảo hiểm và tạo đơn xin nghỉ phép.

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | Đề tài mở rộng không dừng ở trả lời rời rạc mà yêu cầu Agent xâu chuỗi nhiều bước: (1) xác định loại nghỉ nhân viên đang hỏi (ốm đau / thai sản / phép năm...), (2) tra cứu chính sách bảo hiểm ứng với loại nghỉ đó (`insurance_policy_query`), (3) tra cứu song song số ngày phép năm có lương còn lại (`leave_balance_query`), (4) tổng hợp 2 nguồn dữ liệu để tư vấn ngược lại cho nhân viên (ví dụ: nghỉ ốm có bảo hiểm chi trả % lương ra sao, nghỉ thai sản được hưởng bao lâu, có nên trừ vào phép năm hay không), rồi (5) mới tạo đơn xin nghỉ phép. Chuỗi 4-5 bước nối tiếp và có tổng hợp chéo dữ liệu này đạt mức tối đa. |
| **2. Tool Interaction** | 5 / 5 | Bắt buộc phải kết nối MCP Server / CSDL nhân sự bên ngoài với ít nhất 3 Tool: `leave_balance_query` (số ngày phép có lương còn lại theo mã nhân viên), `insurance_policy_query` (chính sách/quyền lợi bảo hiểm theo `leave_type` — ốm đau, thai sản, phép năm...) và `create_leave_request` (hành động tạo đơn). Đây đều là dữ liệu cá nhân hoá/chính sách nội bộ thật, LLM không thể tự bịa mà bắt buộc phải gọi Tool để tránh tư vấn sai chế độ. |
| **3. Dynamic Decision** | 5 / 5 | Nội dung tư vấn và quyết định tạo đơn phụ thuộc trực tiếp vào việc kết hợp Observation từ 2 Tool tra cứu khác nhau: cùng một câu hỏi "tôi muốn nghỉ 5 ngày" nhưng nếu là nghỉ ốm thì Agent phải dẫn chính sách bảo hiểm y tế (không trừ phép năm), còn nếu là nghỉ phép năm thông thường thì phải đối chiếu số ngày còn lại trước khi tạo đơn — tức bước tiếp theo (tư vấn gì, có tạo đơn hay không) rẽ nhánh động theo loại nghỉ và kết quả tra cứu, không thể áp dụng một luồng cố định. |
| **4. Long Horizon Goal** | 3 / 5 | Mục tiêu "tư vấn đúng chế độ + tạo đúng đơn nghỉ phép" cần giữ xuyên suốt qua vài lượt hội thoại (xác định loại nghỉ → tra chính sách bảo hiểm → tra phép còn lại → tư vấn → xác nhận → tạo đơn), nhưng vẫn là tác vụ tư vấn/giao dịch kết thúc trong một phiên ngắn, không đòi hỏi Agent duy trì trạng thái/kế hoạch qua nhiều ngày/nhiều phiên như các bài toán lập kế hoạch dài hạn thực sự. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Tổng 18/20 > ngưỡng 12/20 → Đề tài "Trợ lý Nhân sự VinFast (HR Assistant)" (bản mở rộng có liên kết chính sách bảo hiểm để tư vấn ngược theo loại nghỉ) rất phù hợp triển khai dưới dạng ReAct Agent: cần tra cứu dữ liệu từ ≥2 nguồn khác nhau (phép còn lại + chính sách bảo hiểm theo loại nghỉ), tổng hợp suy luận rồi mới hành động tạo đơn — vượt xa mức tối thiểu 2 Tool của đề bài.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85
      }
    },
    "latency_ms": 120.5
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** ___ / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
