"""Tests for utility functions."""

from pathlib import Path

import pytest

from youtube_to_kimi.utils import ensure_dir, format_size, sanitize_filename


class TestSanitizeFilename:
    def test_removes_invalid_chars(self) -> None:
        assert sanitize_filename('a/b:c*d?e"f<g>h|i') == "a_b_c_d_e_f_g_h_i"

    def test_replaces_whitespace(self) -> None:
        assert sanitize_filename("hello world\ttest") == "hello_world_test"

    def test_strips_leading_trailing_dots_and_underscores(self) -> None:
        assert sanitize_filename("...hello...") == "hello"
        assert sanitize_filename("___hello___") == "hello"

    def test_empty_string(self) -> None:
        assert sanitize_filename("") == ""

    def test_already_safe(self) -> None:
        assert sanitize_filename("hello_world") == "hello_world"


class TestEnsureDir:
    def test_creates_missing_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "dir"
        result = ensure_dir(target)
        assert result == target
        assert target.exists()
        assert target.is_dir()

    def test_returns_existing_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "existing"
        target.mkdir()
        result = ensure_dir(target)
        assert result == target
        assert target.exists()


class TestFormatSize:
    @pytest.mark.parametrize(
        ("size", "expected"),
        [
            (0, "0.0 B"),
            (512, "512.0 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1024 * 1024 * 1024 * 1024, "1.0 TB"),
        ],
    )
    def test_conversions(self, size: int, expected: str) -> None:
        assert format_size(size) == expected

    def test_negative_size(self) -> None:
        assert format_size(-1024) == "-1.0 KB"
