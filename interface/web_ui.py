"""Gradio web UI with two modes:

  - Research tab: topic -> auto-generated questions -> reviewed answers -> report.
  - Chat tab: ask single questions and get answers grounded in your documents.

Both modes share the same persistent document store, so documents you upload in
either tab are available to both and persist across sessions.
"""
import shutil
from pathlib import Path

from core import config, file_manager
from core.chat import RagChat
from core.logging import get_logger
from core.task_manager import TaskManager
from rag import chunker, document_loader
from rag.vector_db import VectorDB

log = get_logger("web_ui")


def _ingest_uploaded(files) -> int:
    """Copy uploaded files into data/documents and add them to the vector store."""
    if not files:
        return 0
    saved = []
    for f in files:
        src = Path(f.name if hasattr(f, "name") else f)
        dest = config.DOCUMENTS_DIR / src.name
        if src.resolve() != dest.resolve():
            shutil.copy(src, dest)
        saved.append(dest)
    docs = document_loader.load_documents(saved)
    chunks = chunker.chunk_documents(docs)
    return VectorDB().add_chunks(chunks)


# --- Research tab ------------------------------------------------------------
def run_research(files, topic, n_questions):
    if not topic or not topic.strip():
        return "Please enter a topic.", None, None, None

    n_ingested = _ingest_uploaded(files)
    vdb = VectorDB()
    if vdb.count() == 0:
        return ("No documents in the vector store. Upload at least one document.",
                None, None, None)

    log_lines = [f"Ingested {n_ingested} new chunk(s). Store has {vdb.count()} chunks.", ""]

    def progress(i, total, question, status):
        log_lines.append(f"[{i}/{total}] {status.upper()}: {question}")

    tm = TaskManager(vector_db=vdb)
    result = tm.run(topic.strip(), n_questions=int(n_questions), progress=progress)
    tm.close()

    log_lines.append("")
    log_lines.append(f"Status: {result['status']}")
    exports = result["exports"]
    return ("\n".join(log_lines), exports["markdown"], exports["docx"], exports["pdf"])


# --- Chat tab ----------------------------------------------------------------
def chat_ingest(files):
    n = _ingest_uploaded(files)
    return f"Ingested {n} new chunk(s). Store now has {VectorDB().count()} chunks."


def chat_respond(message, history):
    """history is a list of {'role','content'} dicts (Gradio 'messages' format)."""
    history = history or []
    # Rebuild (user, assistant) pairs for the chat orchestrator's memory.
    pairs = []
    pending_user = None
    for turn in history:
        if turn["role"] == "user":
            pending_user = turn["content"]
        elif turn["role"] == "assistant" and pending_user is not None:
            pairs.append((pending_user, turn["content"]))
            pending_user = None

    result = RagChat().ask(message, history=pairs)
    answer = result["answer"]
    if result["sources"]:
        preview = "\n".join(f"- {s[:160]}{'...' if len(s) > 160 else ''}"
                            for s in result["sources"])
        answer += f"\n\n<details><summary>Sources ({len(result['sources'])})</summary>\n\n{preview}\n</details>"

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return history, ""


def build_ui():
    import gradio as gr

    with gr.Blocks(title="AutoResearchSystem") as demo:
        gr.Markdown("# AutoResearchSystem")

        with gr.Tabs():
            # ----- Research -----
            with gr.Tab("📄 Research"):
                gr.Markdown("Upload documents, enter a topic, and generate a full report.")
                with gr.Row():
                    with gr.Column():
                        r_files = gr.File(label="Documents (PDF/DOCX/TXT/MD)",
                                          file_count="multiple")
                        r_topic = gr.Textbox(label="Topic",
                                             placeholder="e.g. AI in healthcare")
                        r_nq = gr.Slider(
                            1, 10, value=5, step=1,
                            label="Độ sâu nghiên cứu (số khía cạnh phân tích)",
                            info="Số góc độ hệ thống tự phân tích để viết báo cáo. "
                                 "Cao hơn = bao quát hơn nhưng chậm và tốn token hơn. "
                                 "Các câu hỏi này dùng nội bộ, không hiện trong báo cáo.",
                        )
                        r_btn = gr.Button("Run Research", variant="primary")
                    with gr.Column():
                        r_status = gr.Textbox(label="Progress", lines=16)
                        r_md = gr.File(label="Markdown (.md)")
                        r_docx = gr.File(label="Word (.docx)")
                        r_pdf = gr.File(label="PDF (.pdf)")
                r_btn.click(run_research, [r_files, r_topic, r_nq],
                            [r_status, r_md, r_docx, r_pdf])

            # ----- Chat -----
            with gr.Tab("💬 Chat"):
                gr.Markdown(
                    "Ask questions directly. Answers are grounded in your documents "
                    "(shared with the Research tab and saved long-term)."
                )
                with gr.Row():
                    c_files = gr.File(label="Add documents (optional)",
                                      file_count="multiple", scale=3)
                    c_ingest_btn = gr.Button("Ingest", scale=1)
                c_ingest_status = gr.Markdown()
                c_chatbot = gr.Chatbot(height=420, label="Chat")
                c_msg = gr.Textbox(label="Your question",
                                   placeholder="Ask something about your documents...")
                with gr.Row():
                    c_send = gr.Button("Send", variant="primary")
                    c_clear = gr.Button("Clear")

                c_ingest_btn.click(chat_ingest, [c_files], [c_ingest_status])
                c_send.click(chat_respond, [c_msg, c_chatbot], [c_chatbot, c_msg])
                c_msg.submit(chat_respond, [c_msg, c_chatbot], [c_chatbot, c_msg])
                c_clear.click(lambda: ([], ""), None, [c_chatbot, c_msg])

    return demo


def main():
    file_manager.ensure_output_dirs()
    build_ui().launch()


if __name__ == "__main__":
    main()
