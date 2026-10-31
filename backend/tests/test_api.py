"""End-to-end API tests against a real Postgres (set TEST_DATABASE_URL, else skipped)."""
import importlib.util, os, sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set")
ROOT = Path(__file__).resolve().parents[2]
V = "/api/v1"


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


@pytest_asyncio.fixture(scope="session")
async def client():
    import main
    from db.database import Base, engine
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    await _load_script("import_hsk").main(prune=True)
    await _load_script("import_content").main(prune=True)
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
        yield ac
    await engine.dispose()


async def _user(client, name):
    body = {"email": f"{name}@x.com", "username": name, "password": "password123"}
    r = await client.post(f"{V}/auth/register", json=body)
    assert r.status_code == 201, r.text
    r = await client.post(f"{V}/auth/login", json={"email": body["email"], "password": body["password"]})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()


async def test_auth_flow(client):
    h, tokens = await _user(client, "alice")
    me = (await client.get(f"{V}/auth/me", headers=h)).json()
    assert me["username"] == "alice" and me["xp"] == 0 and me["hsk_level"] == "HSK1"
    assert (await client.post(f"{V}/auth/register", json={"email": "alice@x.com", "username": "alice2", "password": "password123"})).status_code in (400, 409)
    assert (await client.post(f"{V}/auth/login", json={"email": "alice@x.com", "password": "wrongpass1"})).status_code == 401
    assert (await client.get(f"{V}/auth/me")).status_code in (401, 403)
    r = await client.post(f"{V}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200 and r.json()["access_token"]
    # a refresh token must not work as an access token
    bad = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert (await client.get(f"{V}/auth/me", headers=bad)).status_code == 401


async def test_vocabulary(client):
    h, _ = await _user(client, "bob")
    r = (await client.get(f"{V}/vocabulary/words?hsk_level=HSK1&limit=200", headers=h)).json()
    assert r["total"] == 300 and r["words"][0]["definitions"] and r["words"][0]["hsk_level"] == "HSK1"
    thanks = (await client.get(f"{V}/vocabulary/words?search=谢谢", headers=h)).json()["words"]
    w = next(x for x in thanks if x["simplified"] == "谢谢")
    assert w["pinyin"] == "xiè xie" and w["pinyin_numeric"] == "xie4 xie5" and "thank" in " ".join(w["definitions"])
    assert (await client.get(f"{V}/vocabulary/words/{w['id']}", headers=h)).json()["simplified"] == "谢谢"
    assert (await client.get(f"{V}/vocabulary/words/999999", headers=h)).status_code == 404
    s = (await client.get(f"{V}/vocabulary/words?search=thank", headers=h)).json()
    assert any(x["simplified"] == "谢谢" for x in s["words"])
    # heteronyms are separate cards with their own level + meaning
    xing = {x["pinyin"]: x for x in (await client.get(f"{V}/vocabulary/words?search=行", headers=h)).json()["words"] if x["simplified"] == "行"}
    assert xing["xíng"]["hsk_level"] == "HSK3" and xing["háng"]["hsk_level"] == "HSK5"
    assert xing["xíng"]["definitions"] != xing["háng"]["definitions"]
    # un-filtered ordering: lowest level first, never HSK3+ before HSK1 (NULL-rank regression)
    first = (await client.get(f"{V}/vocabulary/words?limit=5", headers=h)).json()["words"]
    assert all(x["hsk_level"] == "HSK1" for x in first)
    totals = {lv: (await client.get(f"{V}/vocabulary/words?hsk_level={lv}&limit=1", headers=h)).json()["total"]
              for lv in ("HSK1", "HSK6")}
    assert totals == {"HSK1": 300, "HSK6": 1792}


async def test_srs_review_cycle(client):
    h, _ = await _user(client, "carol")
    queue = (await client.get(f"{V}/vocabulary/review?hsk_level=HSK1&limit=5", headers=h)).json()
    assert len(queue) == 5
    wid = queue[0]["id"]
    r1 = (await client.post(f"{V}/vocabulary/review", json={"word_id": wid, "quality": 5}, headers=h)).json()
    assert r1["interval_days"] == 1 and r1["xp_gained"] == 5
    r2 = (await client.post(f"{V}/vocabulary/review", json={"word_id": wid, "quality": 5}, headers=h)).json()
    assert r2["interval_days"] == 6
    r3 = (await client.post(f"{V}/vocabulary/review", json={"word_id": wid, "quality": 1}, headers=h)).json()
    assert r3["interval_days"] == 1 and r3["xp_gained"] == 1
    # reviewed word is scheduled in the future -> no longer in the due queue
    q2 = (await client.get(f"{V}/vocabulary/review?hsk_level=HSK1&limit=100", headers=h)).json()
    assert wid not in [w["id"] for w in q2] and len(q2) == 100
    assert (await client.get(f"{V}/vocabulary/review?limit=101", headers=h)).status_code == 422
    assert (await client.post(f"{V}/vocabulary/review", json={"word_id": wid, "quality": 6}, headers=h)).status_code == 422
    assert (await client.post(f"{V}/vocabulary/review", json={"word_id": 999999, "quality": 3}, headers=h)).status_code == 404
    prog = (await client.get(f"{V}/vocabulary/progress", headers=h)).json()
    assert prog["user_xp"] == 11 and prog["levels"]["HSK1"]["total"] == 300
    assert (await client.get(f"{V}/auth/me", headers=h)).json()["xp"] == 11


async def test_reading_and_grammar(client):
    h, _ = await _user(client, "dave")
    texts = (await client.get(f"{V}/reading/texts?hsk_level=HSK1", headers=h)).json()
    assert len(texts) == 5 and not any(t["completed"] for t in texts)
    tid = texts[0]["id"]
    detail = (await client.get(f"{V}/reading/texts/{tid}", headers=h)).json()
    assert detail["content"] and detail["content_pinyin"] and detail["translation"]
    a = (await client.post(f"{V}/reading/texts/{tid}/complete", json={"comprehension_score": 80}, headers=h)).json()
    b = (await client.post(f"{V}/reading/texts/{tid}/complete", json={}, headers=h)).json()
    assert (a["xp_gained"], b["xp_gained"], b["total_xp"]) == (10, 0, 10)
    assert (await client.get(f"{V}/reading/texts/{tid}", headers=h)).json()["completed"] is True
    assert (await client.post(f"{V}/reading/texts/{tid}/complete", json={"comprehension_score": 150}, headers=h)).status_code == 422
    assert (await client.get(f"{V}/reading/texts/9999", headers=h)).status_code == 404

    lessons = (await client.get(f"{V}/grammar/lessons?hsk_level=HSK1", headers=h)).json()
    assert len(lessons) == 8 and [l["order_index"] for l in lessons] == sorted(l["order_index"] for l in lessons)
    d = (await client.get(f"{V}/grammar/lessons/{lessons[0]['id']}", headers=h)).json()
    assert d["examples"][0]["zh"] and d["explanation"]
    c1 = (await client.post(f"{V}/grammar/lessons/{lessons[0]['id']}/complete", headers=h)).json()
    c2 = (await client.post(f"{V}/grammar/lessons/{lessons[0]['id']}/complete", headers=h)).json()
    assert (c1["xp_gained"], c2["xp_gained"]) == (10, 0)


async def test_mock_test_flow(client):
    h, _ = await _user(client, "erin")
    h2, _ = await _user(client, "frank")
    start = (await client.post(f"{V}/tests/start?hsk_level=HSK1&num_questions=10", headers=h)).json()
    assert start["total_questions"] == 10 and len(start["questions"]) == 10
    assert "correct_option" not in start["questions"][0]  # never leak answers pre-submit
    aid = start["attempt_id"]
    for lv in ("HSK2", "HSK6"):  # every level now has a question bank
        r6 = await client.post(f"{V}/tests/start?hsk_level={lv}&num_questions=5", headers=h)
        assert r6.status_code == 200 and r6.json()["total_questions"] == 5
    assert (await client.post(f"{V}/tests/{aid}/submit", json={"answers": {}}, headers=h2)).status_code == 404  # not frank's
    assert (await client.post(f"{V}/tests/{aid}/submit", json={"answers": {"1": "Z"}}, headers=h)).status_code == 422

    # Look up truth directly in the DB to submit a perfect run
    from sqlalchemy import select
    from db.database import AsyncSessionLocal
    from models.hsk_test import HskTestQuestion
    async with AsyncSessionLocal() as db:
        truth = {q.id: q.correct_option for q in (await db.execute(select(HskTestQuestion))).scalars()}
    answers = {q["id"]: truth[q["id"]] for q in start["questions"]}
    res = (await client.post(f"{V}/tests/{aid}/submit", json={"answers": answers}, headers=h)).json()
    assert res["correct_answers"] == 10 and res["score_percent"] == 100.0 and res["passed"] is True
    assert res["xp_gained"] == 10 * 2 + 20 and all(r["explanation"] for r in res["results"])
    assert (await client.post(f"{V}/tests/{aid}/submit", json={"answers": answers}, headers=h)).status_code == 409

    # all-wrong -> fail, partial credit logic
    s2 = (await client.post(f"{V}/tests/start?hsk_level=HSK1&num_questions=5", headers=h)).json()
    wrong = {q["id"]: next(o for o in "ABCD" if o != truth[q["id"]]) for q in s2["questions"]}
    r2 = (await client.post(f"{V}/tests/{s2['attempt_id']}/submit", json={"answers": wrong}, headers=h)).json()
    assert r2["correct_answers"] == 0 and r2["passed"] is False and r2["xp_gained"] == 0
    hist = (await client.get(f"{V}/tests/history", headers=h)).json()
    assert len(hist) == 2
    assert (await client.get(f"{V}/auth/me", headers=h)).json()["xp"] == 40


async def test_audio_route(client):
    h, _ = await _user(client, "gina")
    f = Path(os.environ["AUDIO_DIR"]) / "hsk1"
    f.mkdir(parents=True, exist_ok=True)
    mp3 = f / "zz_fixture.mp3"
    mp3.write_bytes(b"ID3fake")
    try:
        r = await client.get(f"{V}/audio/hsk1/zz_fixture.mp3")
        assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg"
    finally:
        mp3.unlink()
    # word payloads expose a local file as audio_path once it exists, null otherwise
    w = (await client.get(f"{V}/vocabulary/words?search=谢谢", headers=h)).json()["words"][0]
    assert w["audio_path"] is None
    mp3.write_bytes(b"ID3fake")
    try:
        (f / "谢谢.mp3").write_bytes(b"ID3fake")
        w = (await client.get(f"{V}/vocabulary/words?search=谢谢", headers=h)).json()["words"][0]
        assert w["audio_path"] == "/api/v1/audio/hsk1/谢谢.mp3"
        assert (await client.get(f"{V}{w['audio_path'][len('/api/v1'):]}")).status_code == 200
        # a reading-specific recording takes precedence over the plain one
        (f / "谢谢_xie4xie5.mp3").write_bytes(b"ID3fake")
        w = (await client.get(f"{V}/vocabulary/words?search=谢谢", headers=h)).json()["words"][0]
        assert w["audio_path"] == "/api/v1/audio/hsk1/谢谢_xie4xie5.mp3"
    finally:
        mp3.unlink(missing_ok=True); (f / "谢谢.mp3").unlink(missing_ok=True); (f / "谢谢_xie4xie5.mp3").unlink(missing_ok=True)
    assert (await client.get(f"{V}/audio/hsk1/nope.mp3")).status_code == 404
    assert (await client.get(f"{V}/audio/hsk1/..%2F..%2Fmain.py")).status_code == 404
    assert (await client.get(f"{V}/audio/hsk1/x.txt")).status_code == 404


async def test_content_prune_removes_questions_no_longer_in_the_data_files(client):
    from sqlalchemy import func, select
    from db.database import AsyncSessionLocal
    from models.hsk_test import HskTestQuestion, QuestionType
    from models.user import HskLevel
    async with AsyncSessionLocal() as db:
        before = (await db.execute(select(func.count()).select_from(HskTestQuestion))).scalar_one()
        db.add(HskTestQuestion(hsk_level=HskLevel.HSK1, question_type=QuestionType.VOCABULARY, question_text="STALE question about an old word list",
                               option_a="a", option_b="b", option_c="c", option_d="d", correct_option="A", explanation="x"))
        await db.commit()
    out = await _load_script("import_content").main(prune=True)
    async with AsyncSessionLocal() as db:
        after = (await db.execute(select(func.count()).select_from(HskTestQuestion))).scalar_one()
        stale = (await db.execute(select(func.count()).select_from(HskTestQuestion).where(HskTestQuestion.question_text.like("STALE%")))).scalar_one()
    assert after == before and stale == 0
