"""Settings parsing tests."""

from app.config import Settings


def test_cors_origins_accept_comma_separated_values() -> None:
    settings = Settings(cors_origins="http://localhost:5173, http://localhost:8080")
    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://localhost:8080",
    ]


def test_cors_origins_accept_json_array() -> None:
    settings = Settings(cors_origins='["http://localhost:5173", "http://localhost:8080"]')
    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://localhost:8080",
    ]
