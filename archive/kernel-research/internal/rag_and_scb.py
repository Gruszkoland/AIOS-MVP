"""
TIER 0c — RAG + Session Continuity Bridge (SCB [4])
Lokalna implementacja retrieval-augmented generation dla Genesis Record.
Oparty na ChromaDB + SentenceTransformers (all-MiniLM-L6-v2).
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SearchResult:
    """SearchResult format dla RAG queries."""
    document_id: str
    source_file: str
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGLoaderBasic:
    """TIER 0c: Bazowa implementacja RAG dla Genesis Record (bez external deps)."""

    def __init__(self, genesis_path: Path = None):
        if genesis_path is None:
            genesis_path = Path(__file__).parent.parent / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU"
        self.genesis_path = genesis_path
        self.documents = []
        self.index = {}

    def load_all_reports(self) -> int:
        """Ładuje wszystkie raporty z Genesis Record."""
        if not self.genesis_path.exists():
            raise FileNotFoundError(f"Genesis Record path missing: {self.genesis_path}")

        count = 0
        for md_file in self.genesis_path.glob("**/*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.documents.append({
                    "id": md_file.stem,
                    "path": str(md_file),
                    "content": content,
                    "loaded_at": datetime.now().isoformat(),
                })
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load {md_file}: {e}")
        
        return count

    def search_keyword(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Bazowa keyword search (bez ML, dla TIER 0c MVP)."""
        query_lower = query.lower()
        results = []

        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Simple keyword matching
            if query_lower in content_lower:
                occurrences = content_lower.count(query_lower)
                score = min(1.0, occurrences / 10.0)  # Normalizuj do 0-1
                
                results.append(SearchResult(
                    document_id=doc["id"],
                    source_file=doc["path"],
                    content=doc["content"][:500],  # Preview
                    score=score,
                    metadata={"occurrences": occurrences}
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def search_by_guardian_law(self, law_id: str, top_k: int = 5) -> List[SearchResult]:
        """Szuka dokumentów wspominających konkretne Guardian Laws."""
        return self.search_keyword(f"G{law_id}", top_k)

    def export_session_state(self, output_file: Path) -> None:
        """Eksportuje stan sesji (SCB end-of-session export)."""
        export = {
            "timestamp": datetime.now().isoformat(),
            "documents_indexed": len(self.documents),
            "genesis_path": str(self.genesis_path),
            "documents": self.documents,
        }
        with open(output_file, "w") as f:
            json.dump(export, f, indent=2)


class SCBSessionContinuity:
    """Session Continuity Bridge (SCB [4]) — zarządzanie stanem między sesjami."""

    @staticmethod
    def save_session_context(
        session_id: str,
        active_todos: List[Dict],
        session_data: Dict[str, Any],
        output_dir: Path = None
    ) -> Path:
        """Zapisuje kontekst sesji dla przyszłych sesji."""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "memories" / "session"
        output_dir.mkdir(parents=True, exist_ok=True)

        export_file = output_dir / f"{session_id}_export.json"
        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "active_todos": active_todos,
            "session_data": session_data,
        }
        with open(export_file, "w") as f:
            json.dump(data, f, indent=2)
        
        return export_file

    @staticmethod
    def load_session_context(session_id: str, memory_dir: Path = None) -> Optional[Dict[str, Any]]:
        """Ładuje wcześniejszą sesję z memory."""
        if memory_dir is None:
            memory_dir = Path(__file__).parent.parent / "memories" / "session"
        
        export_file = memory_dir / f"{session_id}_export.json"
        if not export_file.exists():
            return None
        
        with open(export_file) as f:
            return json.load(f)


if __name__ == "__main__":
    # Test TIER 0c
    print("=== Testing TIER 0c RAG ===")
    rag = RAGLoaderBasic()
    count = rag.load_all_reports()
    print(f"Loaded {count} reports from Genesis Record")

    if count > 0:
        results = rag.search_keyword("Guardian", top_k=3)
        print(f"\nSearch results for 'Guardian':")
        for r in results:
            print(f"  - {r.document_id} (score: {r.score:.2f})")

    # Test SCB
    print("\n=== Testing SCB ===")
    session_data = {"test": "value"}
    export_file = SCBSessionContinuity.save_session_context(
        "TEST_SESSION_001",
        [],
        session_data
    )
    print(f"Session exported to: {export_file}")
