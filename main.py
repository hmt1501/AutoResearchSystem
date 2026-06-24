"""AutoResearchSystem CLI entry point.

Usage:
    python main.py --topic "AI in healthcare" --docs ./data/documents/
    python main.py --topic "..." --questions 6        # custom question count
    python main.py --topic "..." --no-ingest          # reuse existing vector store
"""
import argparse
from pathlib import Path

from core import config, file_manager
from core.logging import get_logger
from core.task_manager import TaskManager
from rag import chunker, document_loader
from rag.vector_db import VectorDB

log = get_logger("main")


def ingest(docs_dir: Path, vdb: VectorDB) -> int:
    paths = file_manager.list_documents(docs_dir)
    if not paths:
        log.warning("No documents found in %s", docs_dir)
        return 0
    docs = document_loader.load_documents(paths)
    chunks = chunker.chunk_documents(docs)
    return vdb.add_chunks(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoResearchSystem")
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument("--docs", default=str(config.DOCUMENTS_DIR),
                        help="Directory of source documents")
    parser.add_argument("--questions", type=int, default=5,
                        help="Research depth: number of internal aspects to analyze "
                             "(not shown in the report; higher = more comprehensive)")
    parser.add_argument("--no-ingest", action="store_true",
                        help="Skip ingestion and reuse the existing vector store")
    args = parser.parse_args()

    vdb = VectorDB()
    if not args.no_ingest:
        n = ingest(Path(args.docs), vdb)
        log.info("Ingested %d chunk(s).", n)

    if vdb.count() == 0:
        log.error("Vector store is empty. Add documents to %s and run again.", args.docs)
        return

    def progress(i, total, question, status):
        print(f"  [{i}/{total}] {status.upper():8} {question[:70]}")

    tm = TaskManager(vector_db=vdb)
    result = tm.run(args.topic, n_questions=args.questions, progress=progress)
    tm.close()

    print("\n=== Done ===")
    print(f"Status: {result['status']}")
    for fmt, path in result["exports"].items():
        print(f"  {fmt:9}: {path}")


if __name__ == "__main__":
    main()
