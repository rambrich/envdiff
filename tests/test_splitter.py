"""Tests for envdiff.splitter."""
import pytest
from envdiff.splitter import SplitGroup, SplitResult, split_env_by_prefix


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_KEY": "abc",
        "AWS_SECRET": "xyz",
        "APP_NAME": "myapp",
        "UNTAGGED": "value",
    }


def test_split_returns_split_result(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    assert isinstance(result, SplitResult)


def test_split_env_name_stored(sample_env):
    result = split_env_by_prefix(sample_env, ["DB"], env_name="production")
    assert result.env_name == "production"


def test_split_group_names(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    assert result.group_names == ["DB", "AWS"]


def test_split_db_group_contains_correct_keys(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    db = result.get_group("DB")
    assert db is not None
    assert set(db.env.keys()) == {"DB_HOST", "DB_PORT"}


def test_split_aws_group_contains_correct_keys(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    aws = result.get_group("AWS")
    assert aws is not None
    assert set(aws.env.keys()) == {"AWS_KEY", "AWS_SECRET"}


def test_split_remainder_contains_unclaimed_keys(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    assert "APP_NAME" in result.remainder
    assert "UNTAGGED" in result.remainder


def test_split_remainder_excludes_claimed_keys(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    assert "DB_HOST" not in result.remainder
    assert "AWS_KEY" not in result.remainder


def test_split_total_grouped_keys(sample_env):
    result = split_env_by_prefix(sample_env, ["DB", "AWS"])
    assert result.total_grouped_keys == 4


def test_split_strip_prefix_removes_prefix(sample_env):
    result = split_env_by_prefix(sample_env, ["DB"], strip_prefix=True)
    db = result.get_group("DB")
    assert "HOST" in db.env
    assert "PORT" in db.env
    assert "DB_HOST" not in db.env


def test_split_strip_prefix_values_preserved(sample_env):
    result = split_env_by_prefix(sample_env, ["DB"], strip_prefix=True)
    db = result.get_group("DB")
    assert db.env["HOST"] == "localhost"


def test_split_get_group_returns_none_for_unknown(sample_env):
    result = split_env_by_prefix(sample_env, ["DB"])
    assert result.get_group("NONEXISTENT") is None


def test_split_empty_env_produces_empty_groups():
    result = split_env_by_prefix({}, ["DB", "AWS"])
    for g in result.groups:
        assert g.key_count == 0
    assert result.remainder == {}


def test_split_no_prefixes_everything_in_remainder(sample_env):
    result = split_env_by_prefix(sample_env, [])
    assert result.groups == []
    assert result.remainder == sample_env


def test_split_group_key_count(sample_env):
    result = split_env_by_prefix(sample_env, ["AWS"])
    aws = result.get_group("AWS")
    assert aws.key_count == 2
