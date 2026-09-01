import json
from pathlib import Path

from memory_os.service import MemoryService
from memory_os.sqlite_store import build_sqlite


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _message(conversation_id: str, node_id: str, message_id: str, text: str, role: str = "user") -> dict:
    return {
        "message_id": message_id,
        "node_id": node_id,
        "conversation_id": conversation_id,
        "parent_node_id": None,
        "role": role,
        "author_name": None,
        "create_time": 1.0,
        "update_time": None,
        "status": "finished_successfully",
        "recipient": "all",
        "weight": 1.0,
        "end_turn": True,
        "content_type": "text",
        "text": text,
        "text_sha256": f"text-{conversation_id}-{message_id}",
        "content_json": json.dumps({"content_type": "text", "parts": [text]}),
        "metadata_json": "{}",
        "message_json": json.dumps({"id": message_id}),
        "source": "fixture",
        "source_message_sha256": f"message-{conversation_id}-{message_id}",
    }


def _canonical_dir(tmp_path: Path, conversations, nodes, edges, messages) -> Path:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _write_jsonl(canonical / "conversations.jsonl", conversations)
    _write_jsonl(canonical / "nodes.jsonl", nodes)
    _write_jsonl(canonical / "edges.jsonl", edges)
    _write_jsonl(canonical / "messages.jsonl", messages)
    (canonical / "attachments.jsonl").write_text("", encoding="utf-8")
    return canonical


def test_duplicate_node_and_message_ids_are_scoped_by_conversation(tmp_path):
    conversations = [
        {"conversation_id": "c1", "title": "One", "create_time": 1.0, "update_time": 1.0, "current_node_id": "shared-node", "source": "fixture", "source_conversation_sha256": "c1", "metadata_json": "{}"},
        {"conversation_id": "c2", "title": "Two", "create_time": 1.0, "update_time": 1.0, "current_node_id": "shared-node", "source": "fixture", "source_conversation_sha256": "c2", "metadata_json": "{}"},
    ]
    nodes = [
        {"node_id": "shared-node", "conversation_id": "c1", "parent_node_id": None, "has_message": True, "children": [], "children_count": 0, "is_branch_point": False, "is_current_node": True, "source": "fixture", "source_node_sha256": "n1"},
        {"node_id": "shared-node", "conversation_id": "c2", "parent_node_id": None, "has_message": True, "children": [], "children_count": 0, "is_branch_point": False, "is_current_node": True, "source": "fixture", "source_node_sha256": "n2"},
    ]
    messages = [
        _message("c1", "shared-node", "shared-message", "alpha memory"),
        _message("c2", "shared-node", "shared-message", "beta memory"),
    ]
    canonical = _canonical_dir(tmp_path, conversations, nodes, [], messages)
    db = tmp_path / "memory.sqlite"
    build_sqlite(canonical, db)
    service = MemoryService(db)

    assert service.stats()["messages"] == 2
    assert service.get_message("c1", "shared-message")["text"] == "alpha memory"
    assert service.get_message("c2", "shared-message")["text"] == "beta memory"


def test_active_branch_reconstruction_excludes_abandoned_branch(tmp_path):
    conversations = [
        {"conversation_id": "branch", "title": "Branch", "create_time": 1.0, "update_time": 4.0, "current_node_id": "current", "source": "fixture", "source_conversation_sha256": "branch", "metadata_json": "{}"}
    ]
    nodes = [
        {"node_id": "root", "conversation_id": "branch", "parent_node_id": None, "has_message": False, "children": ["turn"], "children_count": 1, "is_branch_point": False, "is_current_node": False, "source": "fixture", "source_node_sha256": "root"},
        {"node_id": "turn", "conversation_id": "branch", "parent_node_id": "root", "has_message": True, "children": ["old", "current"], "children_count": 2, "is_branch_point": True, "is_current_node": False, "source": "fixture", "source_node_sha256": "turn"},
        {"node_id": "old", "conversation_id": "branch", "parent_node_id": "turn", "has_message": True, "children": [], "children_count": 0, "is_branch_point": False, "is_current_node": False, "source": "fixture", "source_node_sha256": "old"},
        {"node_id": "current", "conversation_id": "branch", "parent_node_id": "turn", "has_message": True, "children": [], "children_count": 0, "is_branch_point": False, "is_current_node": True, "source": "fixture", "source_node_sha256": "current"},
    ]
    edges = [
        {"conversation_id": "branch", "parent_node_id": "root", "child_node_id": "turn", "edge_type": "parent_child", "source": "fixture"},
        {"conversation_id": "branch", "parent_node_id": "turn", "child_node_id": "old", "edge_type": "parent_child", "source": "fixture"},
        {"conversation_id": "branch", "parent_node_id": "turn", "child_node_id": "current", "edge_type": "parent_child", "source": "fixture"},
    ]
    first = _message("branch", "turn", "m1", "question")
    first["parent_node_id"] = "root"
    old = _message("branch", "old", "m2", "abandoned answer", "assistant")
    old["parent_node_id"] = "turn"
    current = _message("branch", "current", "m3", "current answer", "assistant")
    current["parent_node_id"] = "turn"

    canonical = _canonical_dir(tmp_path, conversations, nodes, edges, [first, old, current])
    db = tmp_path / "memory.sqlite"
    build_sqlite(canonical, db)
    service = MemoryService(db)

    active = service.get_conversation("branch", active_branch_only=True)
    assert [m["text"] for m in active["messages"]] == ["question", "current answer"]

    all_messages = service.get_conversation("branch", active_branch_only=False)
    assert {m["text"] for m in all_messages["messages"]} == {"question", "abandoned answer", "current answer"}
