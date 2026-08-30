from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator

from .canonical import sha256_file, sha256_json, sha256_text, stable_json, write_jsonl

JSON_DATA_PREFIX = "var jsonData = "
ASSETS_DATA_PREFIX = "var assetsJson = "


def load_chat_html(path: Path) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """Extract the embedded conversation and asset JSON from ChatGPT chat.html."""
    source = path.read_text(encoding="utf-8")
    start = source.index(JSON_DATA_PREFIX) + len(JSON_DATA_PREFIX)
    json_end = source.index("\n      " + ASSETS_DATA_PREFIX, start)
    conversations = json.loads(source[start:json_end].strip())

    assets_start = json_end + len("\n      " + ASSETS_DATA_PREFIX)
    # assetsJson is followed by JS code. JSONDecoder lets us stop exactly at the JSON boundary.
    assets, _ = json.JSONDecoder().raw_decode(source[assets_start:].lstrip())
    return conversations, assets


def load_json_shards(paths: list[Path]) -> list[dict[str, Any]]:
    conversations: list[dict[str, Any]] = []
    for path in sorted(paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a list in {path}")
        conversations.extend(payload)
    return conversations


def extract_text(content: dict[str, Any] | None) -> str:
    """Extract searchable text without discarding the original content JSON.

    Exact source content is always retained separately in content_json/message_json.
    This field exists only for retrieval/search.
    """
    if not content:
        return ""
    ctype = content.get("content_type")
    pieces: list[str] = []
    if ctype in {"text", "multimodal_text"}:
        for part in content.get("parts") or []:
            if isinstance(part, str):
                pieces.append(part)
            elif isinstance(part, dict):
                # Preserve textual/transcript parts; binary assets are represented separately.
                for key in ("text", "transcript"):
                    value = part.get(key)
                    if isinstance(value, str) and value:
                        pieces.append(value)
    elif ctype == "reasoning_recap":
        value = content.get("content")
        if isinstance(value, str):
            pieces.append(value)
    elif ctype == "thoughts":
        for thought in content.get("thoughts") or []:
            if isinstance(thought, str):
                pieces.append(thought)
            elif isinstance(thought, dict):
                for key in ("content", "text", "summary"):
                    value = thought.get(key)
                    if isinstance(value, str) and value:
                        pieces.append(value)
    else:
        # Unknown future content types: pull direct textual values conservatively.
        for key in ("text", "content", "transcript"):
            value = content.get(key)
            if isinstance(value, str) and value:
                pieces.append(value)
    return "\n".join(pieces)


def discover_attachment_refs(message: dict[str, Any], asset_names: list[str] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, ref: str, metadata: dict[str, Any] | None = None) -> None:
        key = (kind, ref)
        if ref and key not in seen:
            seen.add(key)
            refs.append({"kind": kind, "ref": ref, "metadata": metadata})

    for name in asset_names or []:
        add("export_asset", name)

    content = message.get("content") or {}
    for part in content.get("parts") or []:
        if isinstance(part, dict):
            pointer = part.get("asset_pointer")
            if isinstance(pointer, str):
                add("asset_pointer", pointer, {k: v for k, v in part.items() if k != "metadata"})

    metadata = message.get("metadata") or {}
    for attachment in metadata.get("attachments") or []:
        if isinstance(attachment, dict):
            ref = attachment.get("id") or attachment.get("file_id") or attachment.get("name") or attachment.get("asset_pointer")
            if isinstance(ref, str):
                add("metadata_attachment", ref, attachment)

    return refs


def iter_canonical(conversations: list[dict[str, Any]], assets: dict[str, list[str]] | None, source_name: str):
    assets = assets or {}
    stats = Counter()
    conv_rows: list[dict[str, Any]] = []
    node_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    message_rows: list[dict[str, Any]] = []
    attachment_rows: list[dict[str, Any]] = []

    for conv in conversations:
        conversation_id = conv.get("conversation_id") or conv.get("id")
        mapping = conv.get("mapping") or {}
        child_map: dict[str, list[str]] = defaultdict(list)
        for node_id, node in mapping.items():
            parent_id = node.get("parent")
            if parent_id:
                child_map[parent_id].append(node_id)

        conv_meta = {k: v for k, v in conv.items() if k != "mapping"}
        conv_rows.append({
            "conversation_id": conversation_id,
            "title": conv.get("title"),
            "create_time": conv.get("create_time"),
            "update_time": conv.get("update_time"),
            "current_node_id": conv.get("current_node"),
            "source": source_name,
            "source_conversation_sha256": sha256_json(conv),
            "metadata_json": stable_json(conv_meta),
        })
        stats["conversations"] += 1

        for node_id, node in mapping.items():
            message = node.get("message")
            parent_id = node.get("parent")
            children = sorted(child_map.get(node_id, []))
            node_rows.append({
                "node_id": node_id,
                "conversation_id": conversation_id,
                "parent_node_id": parent_id,
                "has_message": message is not None,
                "children": children,
                "children_count": len(children),
                "is_branch_point": len(children) > 1,
                "is_current_node": node_id == conv.get("current_node"),
                "source": source_name,
                "source_node_sha256": sha256_json(node),
            })
            stats["nodes"] += 1
            if len(children) > 1:
                stats["branch_points"] += 1
            if parent_id:
                edge_rows.append({
                    "conversation_id": conversation_id,
                    "parent_node_id": parent_id,
                    "child_node_id": node_id,
                    "edge_type": "PARENT_OF",
                    "source": source_name,
                })
                stats["edges"] += 1

            if message is None:
                stats["null_message_nodes"] += 1
                continue

            msg_id = message.get("id") or node_id
            author = message.get("author") or {}
            content = message.get("content") or {}
            metadata = message.get("metadata") or {}
            text = extract_text(content)
            row = {
                "message_id": msg_id,
                "node_id": node_id,
                "conversation_id": conversation_id,
                "parent_node_id": parent_id,
                "role": author.get("role"),
                "author_name": author.get("name"),
                "create_time": message.get("create_time"),
                "update_time": message.get("update_time"),
                "status": message.get("status"),
                "recipient": message.get("recipient"),
                "weight": message.get("weight"),
                "end_turn": message.get("end_turn"),
                "content_type": content.get("content_type"),
                "text": text,
                "text_sha256": sha256_text(text),
                "content_json": stable_json(content),
                "metadata_json": stable_json(metadata),
                "message_json": stable_json(message),
                "source": source_name,
                "source_message_sha256": sha256_json(message),
            }
            message_rows.append(row)
            stats["messages"] += 1
            stats[f"role:{author.get('role')}"] += 1
            stats[f"content_type:{content.get('content_type')}"] += 1
            stats["text_characters"] += len(text)

            for ref in discover_attachment_refs(message, assets.get(msg_id)):
                attachment_rows.append({
                    "conversation_id": conversation_id,
                    "message_id": msg_id,
                    "node_id": node_id,
                    "kind": ref["kind"],
                    "ref": ref["ref"],
                    "metadata_json": stable_json(ref.get("metadata")) if ref.get("metadata") is not None else None,
                    "source": source_name,
                })
                stats["attachment_refs"] += 1

    return conv_rows, node_rows, edge_rows, message_rows, attachment_rows, stats


def import_chatgpt(source: Path, output_dir: Path) -> dict[str, Any]:
    started = time.time()
    if source.is_file() and source.name.lower() == "chat.html":
        conversations, assets = load_chat_html(source)
        source_kind = "chatgpt_chat_html"
        source_files = [source]
    elif source.is_dir():
        shards = sorted(source.glob("conversations-*.json"))
        if not shards:
            raise FileNotFoundError("No conversations-*.json shards found")
        conversations = load_json_shards(shards)
        assets = {}
        source_kind = "chatgpt_json_shards"
        source_files = shards
    else:
        raise ValueError("Source must be chat.html or a directory containing conversations-*.json")

    source_name = source.name
    convs, nodes, edges, messages, attachments, stats = iter_canonical(conversations, assets, source_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {}
    for name, rows in [
        ("conversations.jsonl", convs),
        ("nodes.jsonl", nodes),
        ("edges.jsonl", edges),
        ("messages.jsonl", messages),
        ("attachments.jsonl", attachments),
    ]:
        count, digest = write_jsonl(output_dir / name, rows)
        files[name] = {"rows": count, "sha256": digest, "bytes": (output_dir / name).stat().st_size}

    manifest = {
        "format": "portable-memory-os-canonical-v1",
        "source_kind": source_kind,
        "source_files": [
            {"name": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in source_files
        ],
        "counts": dict(sorted(stats.items())),
        "outputs": files,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a ChatGPT data export into lossless canonical JSONL")
    parser.add_argument("source", type=Path, help="chat.html or folder containing conversations-*.json")
    parser.add_argument("output", type=Path, help="output directory")
    args = parser.parse_args()
    manifest = import_chatgpt(args.source, args.output)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
