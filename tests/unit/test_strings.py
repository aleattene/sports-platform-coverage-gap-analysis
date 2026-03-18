"""Tests for src.utils.strings — slugify function."""

import pytest
from src.utils.strings import slugify


class TestSlugify:

    def test_simple_string(self) -> None:
        assert slugify("Hello World") == "Hello_World"

    def test_leading_trailing_whitespace(self) -> None:
        assert slugify("  spaced  ") == "spaced"

    def test_single_quotes_removed(self) -> None:
        assert slugify("Valle d'Aosta") == "Valle_dAosta"

    def test_forward_slash_replaced_with_hyphen(self) -> None:
        assert slugify("Trentino-Alto Adige/Südtirol") == "Trentino-Alto_Adige-Südtirol"

    def test_multiple_whitespace_collapsed(self) -> None:
        assert slugify("too   many   spaces") == "too_many_spaces"

    def test_accented_characters_preserved(self) -> None:
        assert slugify("Émilia-Romagna") == "Émilia-Romagna"

    def test_special_characters_removed(self) -> None:
        assert slugify("test@#$%value") == "testvalue"

    def test_empty_string(self) -> None:
        assert slugify("") == ""

    def test_only_whitespace(self) -> None:
        assert slugify("   ") == ""

    def test_numbers_preserved(self) -> None:
        assert slugify("region 01") == "region_01"

    def test_combined_real_world(self) -> None:
        """Test with a value similar to real region/province names."""
        assert slugify("Valle d'Aosta/Vallée d'Aoste") == "Valle_dAosta-Vallée_dAoste"
