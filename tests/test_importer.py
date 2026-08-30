from memory_os.chatgpt_importer import extract_text, iter_canonical


def test_multimodal_text_and_branch_preserved():
    conversations = [{
        "conversation_id": "c1",
        "id": "c1",
        "title": "Branch test",
        "current_node": "a2",
        "create_time": 1.0,
        "update_time": 2.0,
        "mapping": {
            "root": {"id": "root", "message": None, "parent": None},
            "u1": {"id": "u1", "parent": "root", "message": {
                "id": "u1", "author": {"role": "user", "name": None}, "create_time": 1.1,
                "content": {"content_type": "multimodal_text", "parts": [{"asset_pointer": "file://x"}, "hello"]},
                "metadata": {}
            }},
            "a1": {"id": "a1", "parent": "u1", "message": {
                "id": "a1", "author": {"role": "assistant", "name": None}, "create_time": 1.2,
                "content": {"content_type": "text", "parts": ["first"]}, "metadata": {}
            }},
            "a2": {"id": "a2", "parent": "u1", "message": {
                "id": "a2", "author": {"role": "assistant", "name": None}, "create_time": 1.3,
                "content": {"content_type": "text", "parts": ["second"]}, "metadata": {}
            }},
        }
    }]
    convs, nodes, edges, messages, attachments, stats = iter_canonical(conversations, {}, "fixture")
    assert stats["branch_points"] == 1
    assert stats["messages"] == 3
    assert len(nodes) == 4
    assert len(edges) == 3
    assert next(m for m in messages if m["message_id"] == "u1")["text"] == "hello"
    assert any(a["ref"] == "file://x" for a in attachments)


def test_extract_reasoning_recap():
    assert extract_text({"content_type": "reasoning_recap", "content": "Thought for 4 seconds"}) == "Thought for 4 seconds"
