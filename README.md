# AutoResearchSystem

**Trợ lý research tự động dựa trên tài liệu (RAG).** Bạn đưa một chủ đề → hệ thống
tự phân tích tài liệu của bạn từ nhiều góc → tổng hợp thành **báo cáo research hoàn
chỉnh** (Markdown / Word / PDF). Ngoài ra có **chế độ Chat** để hỏi đáp trực tiếp với
tài liệu.

> Quy trình bên trong: chủ đề → sinh câu hỏi nội bộ → truy hồi đoạn tài liệu liên quan
> (RAG) → trả lời → tự chấm điểm → tự sửa nếu chưa đạt → **tổng hợp thành bài research**.
> Người đọc chỉ thấy bài research cuối cùng, không thấy các câu hỏi nội bộ.

---

## 1. Công dụng

- **Viết báo cáo research** từ tài liệu bạn cung cấp (PDF, DOCX, TXT, MD).
- **Hybrid**: nếu chủ đề không có trong tài liệu, hệ thống vẫn trả lời bằng kiến thức
  chung của AI, có **gắn nhãn rõ ràng** `[From documents]` / `[General knowledge]`.
- **Hỗ trợ tiếng Việt** tốt (embedding đa ngôn ngữ chạy local).
- **Chat hỏi đáp** với tài liệu, có nhớ ngữ cảnh hội thoại và hiển thị nguồn trích dẫn.
- **Xuất 3 định dạng**: `.md`, `.docx`, `.pdf` cho mỗi lần research.
- **Embedding chạy local trên CPU** — không tốn token, không gửi tài liệu đi để mã hóa.

---

## 2. Yêu cầu

- **Python 3.10+** (đã test trên 3.14).
- **OpenRouter API key** (lấy tại https://openrouter.ai/keys) — dùng để gọi mô hình LLM.
- *(Tùy chọn)* **Microsoft Word** hoặc **LibreOffice** để xuất PDF. Nếu không có,
  hệ thống vẫn xuất `.md` + `.docx` và bỏ qua PDF (có cảnh báo).

---

## 3. Cài đặt sau khi clone về

```bash
# 1. Clone
git clone https://github.com/hmt1501/AutoResearchSystem.git
cd AutoResearchSystem

# 2. Tạo môi trường ảo + cài thư viện
python -m venv .venv
.venv\Scripts\activate              # Windows CMD
# PowerShell: .venv\Scripts\Activate.ps1
# (Linux/macOS): source .venv/bin/activate
pip install -r requirements.txt

# 3. Tạo file .env và điền API key
copy .env.example .env              # Windows  (Linux/macOS: cp .env.example .env)
# Mở .env, dán key vào dòng:  OPENROUTER_API_KEY=sk-or-...
```

> **Lần chạy đầu tiên** sẽ tự tải model embedding đa ngôn ngữ (~470MB) về máy — chỉ
> tải một lần, sau đó chạy hoàn toàn offline cho phần embedding.

> **Lưu ý quan trọng:** kho vector và tài liệu **không** được đưa lên GitHub (để bảo
> mật + nhẹ repo). Nên sau khi clone, bạn cần **nạp lại tài liệu** (xem Mục 4/5) —
> hệ thống sẽ tự embedding lại.

### Nếu lệnh `python` báo lỗi (Windows)
Máy có thể chưa cài Python chuẩn. Cách nhanh nhất là dùng [uv](https://docs.astral.sh/uv/):
```bash
uv venv --python 3.12 .venv
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
```
Sau đó chạy bằng `.\.venv\Scripts\python.exe <lệnh>` thay cho `python <lệnh>`.

---

## 4. Dùng bằng giao diện web (khuyên dùng)

```bash
python -m interface.web_ui
```
Mở trình duyệt vào địa chỉ hiện ra (mặc định http://127.0.0.1:7860).

Giao diện có **2 tab**:

### 📄 Tab Research — tạo báo cáo
```
┌─────────────────────────────┬──────────────────────────────┐
│ Documents  [Tải tài liệu]   │  Progress                    │
│ Topic      [____________]   │  [1/5] DONE: ...             │
│ Độ sâu     [====●====] 5     │  Synthesizing report...      │
│      [ Run Research ]       │  Markdown (.md)   [Tải về]   │
│                             │  Word (.docx)     [Tải về]   │
│                             │  PDF (.pdf)       [Tải về]   │
└─────────────────────────────┴──────────────────────────────┘
```
**Thao tác:**
1. **Tải tài liệu** lên (PDF/DOCX/TXT/MD) — có thể bỏ qua nếu chỉ research bằng kiến
   thức chung.
2. Nhập **Topic** (chủ đề), ví dụ: `Chiến lược định giá ứng dụng tại Việt Nam`.
3. Chỉnh **Độ sâu nghiên cứu** (1–10): càng cao càng bao quát nhưng chậm và tốn token
   hơn. (Đây là số khía cạnh phân tích nội bộ, **không** hiện trong báo cáo.)
4. Bấm **Run Research** → theo dõi tiến trình bên phải → tải về `.md`/`.docx`/`.pdf`.

### 💬 Tab Chat — hỏi đáp
```
┌──────────────────────────────────────────────┐
│ [Tài liệu (tùy chọn)]   [ Ingest ]           │
│ ┌──────────────────────────────────────────┐ │
│ │  Bạn: PPP của Việt Nam là bao nhiêu?      │ │
│ │  AI : [From documents] PPP = 0.46 ...     │ │
│ │       ▸ Sources (5)                       │ │
│ └──────────────────────────────────────────┘ │
│ [Nhập câu hỏi...]          [ Send ] [ Clear ] │
└──────────────────────────────────────────────┘
```
**Thao tác:** gõ câu hỏi → **Send**. Trả lời sẽ bám tài liệu (kèm nguồn trích dẫn ở
mục *Sources*) hoặc dùng kiến thức chung nếu tài liệu không có. Chat **nhớ ngữ cảnh**
trong phiên, nên hỏi nối ("rủi ro của nó là gì?") vẫn hiểu.

> Tài liệu của 2 tab **dùng chung một kho**, nên nạp ở tab nào thì tab kia cũng dùng được.

---

## 5. Dùng bằng dòng lệnh (CLI)

```bash
# Đặt tài liệu vào data/documents/ rồi chạy:
python main.py --topic "AI trong y tế" --docs ./data/documents/

# Các tùy chọn:
python main.py --topic "..." --questions 8       # tăng độ sâu nghiên cứu
python main.py --topic "..." --no-ingest         # dùng lại kho vector cũ, không nạp lại
```
Kết quả ghi vào `data/outputs/report_<thời-gian>.{md,docx,pdf,meta.json}`.

---

## 6. Chạy định kỳ (Scheduler)

```bash
python -m interface.scheduler --topic "..." --interval 3600 --max-runs 0
# interval: giây giữa các lần chạy | max-runs 0 = chạy mãi
```

---

## 7. Kiểm thử (offline, không cần API key)

```bash
python -m tests.test_offline
```
Kiểm tra phần cắt chunk, embedding/truy hồi local, và logic quyết định retry — toàn bộ
chạy local, không tốn token.

---

## 8. Cấu hình (`.env`)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `OPENROUTER_API_KEY` | *(bắt buộc)* | Khóa API OpenRouter |
| `PRIMARY_MODEL` | `anthropic/claude-haiku-4.5` | Model chính (rẻ, nhanh). Đổi sang `anthropic/claude-sonnet-4.6` nếu muốn sâu hơn (đắt hơn). |
| `FALLBACK_MODEL` | `google/gemini-2.5-flash` | Model dự phòng ở lần retry cuối |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Model embedding (đa ngôn ngữ, chạy local) |
| `SIMILARITY_THRESHOLD` | `0.3` | Ngưỡng giữ chunk liên quan |

Các tham số khác (số retry, kích thước chunk, top-K...) ở [core/config.py](core/config.py).

---

## 9. Kiến trúc

| Tầng | Thư mục | Trách nhiệm |
|------|---------|-------------|
| Core | `core/` | config, logging, SQLite, file, điều phối (`task_manager`), chat |
| AI | `ai/` | client OpenRouter, prompt, sinh câu trả lời, reviewer |
| RAG | `rag/` | nạp tài liệu, cắt chunk, embedding local, ChromaDB, truy hồi |
| Research | `research/` | sinh câu hỏi, viết lại truy vấn, kiểm định, tự sửa, tổng hợp |
| Output | `output/` | xuất markdown, word, pdf, metadata |
| Interface | `interface/` | CLI, web UI (Gradio), scheduler |

### Nguyên tắc thiết kế chính
- **Hybrid sourcing** — ưu tiên tài liệu; thiếu thì dùng kiến thức chung, gắn nhãn nguồn.
- **Báo cáo là bài research tổng hợp** (Tóm tắt → Giới thiệu → Phân tích → Kết luận) qua
  [research/synthesizer.py](research/synthesizer.py); Q&A nội bộ không hiển thị (vẫn lưu
  trong SQLite + `.meta.json` để audit).
- **`reviewer.py` chỉ chấm điểm**, không quyết định retry — việc đó do
  [research/verification.py](research/verification.py) đảm nhiệm duy nhất.
- **`auto_fix.py` cải thiện câu trả lời cũ** dựa trên góp ý của reviewer (không viết lại từ đầu).
- **Embedding chạy local trên CPU** — không tốn token, hỗ trợ tiếng Việt.
- **Ép UTF-8 console** để CLI in được tiếng Việt trên Windows.

---

## 10. Quyền riêng tư (tóm tắt)

- **Chạy local, không ra mạng:** tài liệu gốc, embedding, kho vector (ChromaDB),
  database, và toàn bộ file báo cáo.
- **Gửi lên OpenRouter (để LLM trả lời):** câu hỏi + các đoạn tài liệu liên quan đã
  truy hồi. Đây là điều bắt buộc khi dùng LLM đám mây.
- **Chat không được lưu** xuống đĩa và **không** dùng để huấn luyện gì cả — chỉ tồn tại
  trong bộ nhớ phiên hiện tại.
- Muốn **tuyệt đối không gửi gì ra ngoài**: thay LLM đám mây bằng LLM chạy local (vd Ollama).

---

## 11. Ghi chú kỹ thuật

- Tên thư mục dùng định danh Python hợp lệ (`core`, `ai`, …) thay vì tên có số ở đầu
  (`01_core`) như spec gốc, vì Python không cho tên bắt đầu bằng số.
- Xuất PDF dùng docx→PDF (docx2pdf / LibreOffice) thay cho weasyprint, để tránh phụ
  thuộc thư viện GTK/Pango khó cài trên Windows.
- Đổi model embedding sẽ làm kho vector cũ không tương thích → cần reset và nạp lại
  tài liệu.
