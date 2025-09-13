from depths.layers.l3_ai import L3AI

def test_l3_get_history_returns_list_when_empty():
    ai = L3AI()
    assert ai.get_history("unknown") == []
