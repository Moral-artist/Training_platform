import pytest

from data_model.data_model import Account, ExamAttempts
from tools.db_setup import (
    CONFIRMATION_TEXT,
    expected_table_names,
    require_empty_database,
    require_safe_request,
)


def test_recovery_schema_keeps_current_business_contract():
    assert "membership_level" in Account.__table__.c
    assert Account.__table__.c.membership_level.nullable is False
    assert "plan_id" in ExamAttempts.__table__.c
    assert ExamAttempts.__table__.c.plan_id.nullable is False
    assert {"accounts", "customed_plan", "exam_attempts", "video_assets"} <= (
        expected_table_names()
    )


def test_recovery_refuses_a_non_empty_database():
    with pytest.raises(ValueError, match="not empty"):
        require_empty_database({"accounts"})


def test_apply_requires_exact_confirmation():
    with pytest.raises(ValueError, match="requires --confirm"):
        require_safe_request(
            apply=True,
            confirmation=None,
            environment="development",
            allow_production_recovery=False,
        )

    require_safe_request(
        apply=True,
        confirmation=CONFIRMATION_TEXT,
        environment="development",
        allow_production_recovery=False,
    )


def test_production_recovery_requires_an_extra_manual_override():
    with pytest.raises(ValueError, match="Production recovery is blocked"):
        require_safe_request(
            apply=True,
            confirmation=CONFIRMATION_TEXT,
            environment="production",
            allow_production_recovery=False,
        )

    require_safe_request(
        apply=True,
        confirmation=CONFIRMATION_TEXT,
        environment="production",
        allow_production_recovery=True,
    )
