from ingestion.schema import build_article, stable_id


def test_stable_id_is_deterministic():
    a = stable_id("https://example.com/a", "Hello")
    b = stable_id("https://example.com/a", "Hello")
    assert a == b
    assert len(a) == 24


def test_stable_id_changes_on_url_or_title():
    base = stable_id("https://example.com/a", "Hello")
    assert base != stable_id("https://example.com/b", "Hello")
    assert base != stable_id("https://example.com/a", "World")


def test_build_article_drops_when_missing_url_or_title():
    assert build_article(source="x", title=None, content="c", url="u", published_at=None) is None
    assert build_article(source="x", title="t", content="c", url=None, published_at=None) is None


def test_build_article_normalizes_published_at():
    art = build_article(
        source="newsapi:Foo",
        title="A title",
        content="body",
        url="https://example.com/x",
        published_at="2024-01-01T12:34:56Z",
    )
    assert art is not None
    assert art.published_at.startswith("2024-01-01T12:34:56")
    assert art.id and art.fetched_at
