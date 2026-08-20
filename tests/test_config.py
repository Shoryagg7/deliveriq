"""Config guards — the ones whose failure mode is a security hole, not a crash.

G04: JWT_SECRET used to default to a value published in this repository, so
anyone with the source could mint an ops token and every `require_ops` guard in
the project was decorative. These tests assert the app now refuses to build a
Settings object rather than falling back to something forgeable.

Settings is instantiated at import time, so these construct it directly with
explicit kwargs instead of re-importing the module — same validators, no import
cache to fight.
"""

import pytest
from pydantic import ValidationError

from app.core.config import BANNED_JWT_SECRETS, MIN_JWT_SECRET_BYTES, Settings

_DB = "postgresql://u:p@localhost:5432/d"
_GOOD = "a" * MIN_JWT_SECRET_BYTES


def _settings(**overrides):
    # _env_file=None so a developer's real .env cannot satisfy a field the test
    # is deliberately leaving unset — otherwise this passes on their machine and
    # fails in CI, or worse, the reverse.
    return Settings(database_url=_DB, _env_file=None, **overrides)


def test_missing_jwt_secret_is_rejected(monkeypatch):
    """No default means no silent fallback to a forgeable key.

    `_env_file=None` suppresses the dotenv file but NOT os.environ, and conftest
    exports JWT_SECRET for the rest of the suite — so the variable has to be
    removed for this test to be testing anything at all.
    """
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError) as err:
        _settings()
    assert "jwt_secret" in str(err.value).lower()


@pytest.mark.parametrize("banned", sorted(BANNED_JWT_SECRETS))
def test_placeholder_secrets_are_rejected(banned):
    """Including 'dev-only-change-me', the value that actually shipped."""
    with pytest.raises(ValidationError):
        _settings(jwt_secret=banned)


def test_placeholder_check_ignores_case_and_whitespace():
    """`JWT_SECRET=" Dev-Only-Change-Me "` is the same non-secret."""
    with pytest.raises(ValidationError):
        _settings(jwt_secret="  Dev-Only-Change-Me  ")


def test_short_secret_is_rejected():
    """A key shorter than the hash it feeds is weaker than HS256 itself."""
    with pytest.raises(ValidationError) as err:
        _settings(jwt_secret="a" * (MIN_JWT_SECRET_BYTES - 1))
    assert str(MIN_JWT_SECRET_BYTES) in str(err.value)


def test_secret_length_is_measured_in_bytes_not_characters():
    """31 multi-byte characters are well over 32 bytes; 31 ASCII ones are not.

    The same distinction bcrypt's 72-byte limit turns on — worth being
    consistent about which unit a length check uses.
    """
    _settings(jwt_secret="é" * 16)  # 32 bytes, 16 chars — accepted
    with pytest.raises(ValidationError):
        _settings(jwt_secret="é" * 15)  # 30 bytes — rejected


def test_a_real_secret_is_accepted():
    assert _settings(jwt_secret=_GOOD).jwt_secret == _GOOD
