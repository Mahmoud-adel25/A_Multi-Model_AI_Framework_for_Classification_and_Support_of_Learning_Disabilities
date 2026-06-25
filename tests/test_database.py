"""Tests for database/db_handler.py — CRUD, export, duplicate names."""

import uuid


def test_create_and_get_user(db):
    uid = "test-user-001"
    created = db.create_or_get_user(uid, name="Sara", age=8)
    assert created["user_id"] == uid
    assert created["name"] == "Sara"

    fetched = db.get_user(uid)
    assert fetched is not None
    assert fetched["name"] == "Sara"
    assert fetched["age"] == 8


def test_get_user_by_name_finds_existing(db):
    uid = str(uuid.uuid4())[:12]
    db.create_or_get_user(uid, name="Ali", age=7)
    found = db.get_user_by_name("Ali")
    assert found is not None
    assert found["user_id"] == uid


def test_get_user_by_name_case_insensitive(db):
    uid = str(uuid.uuid4())[:12]
    db.create_or_get_user(uid, name="Maya", age=9)
    found = db.get_user_by_name("  MAYA  ")
    assert found is not None
    assert found["user_id"] == uid


def test_get_user_by_name_empty_returns_none(db):
    assert db.get_user_by_name("") is None
    assert db.get_user_by_name("   ") is None


def test_duplicate_name_lookup_returns_first_match(db):
    db.create_or_get_user("user-a", name="SameName", age=8)
    db.create_or_get_user("user-b", name="SameName", age=9)
    found = db.get_user_by_name("SameName")
    assert found is not None
    assert found["user_id"] in ("user-a", "user-b")


def test_record_and_retrieve_attention_result(db):
    uid = str(uuid.uuid4())[:12]
    db.create_or_get_user(uid, name="Child", age=8)
    rid = db.record_attention_result(
        user_id=uid,
        target_letter="A",
        total_targets=10,
        correct_clicks=8,
        incorrect_clicks=2,
        accuracy=0.8,
        time_spent_seconds=60.0,
        focus_duration_target=5,
        completed_duration=55,
        age_at_test=8,
    )
    assert rid > 0
    history = db.get_attention_history(uid, limit=5)
    assert len(history) == 1
    assert history[0]["accuracy"] == 0.8


def test_export_user_data_empty_user(db):
    uid = "nonexistent-user-id"
    data = db.export_user_data(uid)
    assert data["user_info"] is None
    assert data["classification_history"] == []
    assert data["attention_history"] == []
    assert data["total_stars"] == 0


def test_export_user_data_with_attention_history(db):
    uid = str(uuid.uuid4())[:12]
    db.create_or_get_user(uid, name="Exporter", age=10)
    db.record_attention_result(
        user_id=uid,
        target_letter="B",
        total_targets=5,
        correct_clicks=4,
        incorrect_clicks=1,
        accuracy=0.8,
        time_spent_seconds=30.0,
        focus_duration_target=3,
        completed_duration=28,
        age_at_test=10,
    )
    data = db.export_user_data(uid)
    assert data["user_info"]["name"] == "Exporter"
    assert len(data["attention_history"]) == 1
    assert data["progress_summary"] is not None


def test_award_stars_and_total(db):
    uid = str(uuid.uuid4())[:12]
    db.create_or_get_user(uid, name="StarKid", age=8)
    db.award_stars(uid, "attention", 2, reason="test")
    assert db.get_total_stars(uid) == 2
