"""第5回 宿題（実装）: 検索結果に前後ページを付ける処理のテスト。埋め込みAPIは呼ばない。"""

from app import retrieval


def _page(document_id: str, n: int) -> dict:
    return {"page_id": f"{document_id}-p{n:03d}", "document_id": document_id, "lecture": 1,
            "document_title": "t", "section": "s", "title": f"p{n}", "page": n, "content": f"本文{n}"}


PAGES = [_page("lec01-main", n) for n in (1, 2, 3, 4, 5)] + [_page("lec02-main", n) for n in (1, 2)]


def _patch(monkeypatch, hit_ids):
    hits = [{**next(p for p in PAGES if p["page_id"] == i), "distance": 0.1 * k}
            for k, i in enumerate(hit_ids)]
    monkeypatch.setattr(retrieval, "search", lambda query: hits)
    monkeypatch.setattr(retrieval, "load_pages", lambda source=None: PAGES)


def test_window_zero_returns_hits_only(monkeypatch):
    _patch(monkeypatch, ["lec01-main-p003"])
    results = retrieval.search_with_neighbors("q", window=0)
    assert [r["page_id"] for r in results] == ["lec01-main-p003"]
    assert results[0]["role"] == "hit"


def test_adds_previous_and_next_page_in_reading_order(monkeypatch):
    _patch(monkeypatch, ["lec01-main-p003"])
    results = retrieval.search_with_neighbors("q", window=1)
    assert [r["page_id"] for r in results] == ["lec01-main-p002", "lec01-main-p003", "lec01-main-p004"]
    assert [r["role"] for r in results] == ["neighbor", "hit", "neighbor"]
    assert results[0]["neighbor_of"] == "lec01-main-p003"
    assert "distance" not in results[0] and "distance" in results[1]


def test_does_not_cross_documents(monkeypatch):
    _patch(monkeypatch, ["lec01-main-p005"])
    results = retrieval.search_with_neighbors("q", window=1)
    assert [r["page_id"] for r in results] == ["lec01-main-p004", "lec01-main-p005"]


def test_no_duplicates_and_hits_keep_hit_role(monkeypatch):
    _patch(monkeypatch, ["lec01-main-p002", "lec01-main-p003"])
    results = retrieval.search_with_neighbors("q", window=1)
    ids = [r["page_id"] for r in results]
    assert len(ids) == len(set(ids))
    assert ids == ["lec01-main-p001", "lec01-main-p002", "lec01-main-p003", "lec01-main-p004"]
    roles = {r["page_id"]: r["role"] for r in results}
    assert roles["lec01-main-p002"] == roles["lec01-main-p003"] == "hit"
