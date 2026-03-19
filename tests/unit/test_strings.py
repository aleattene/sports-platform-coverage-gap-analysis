"""Tests for src.utils.strings — slugify function."""

from src.utils.strings import slugify


class TestSlugify:

    def test_simple_string(self) -> None:
        assert slugify("Hello World") == "hello_world"

    def test_leading_trailing_whitespace(self) -> None:
        assert slugify("  spaced  ") == "spaced"

    def test_single_quotes_removed(self) -> None:
        assert slugify("Valle d'Aosta") == "valle_d_aosta"

    def test_slashes_replaced(self) -> None:
        assert slugify("Trentino-Alto Adige/Südtirol") == "trentino_alto_adige_sudtirol"

    def test_multiple_whitespace_collapsed(self) -> None:
        assert slugify("too   many   spaces") == "too_many_spaces"

    def test_accented_characters_normalized(self) -> None:
        assert slugify("Émilia-Romagna") == "emilia_romagna"

    def test_special_characters_removed(self) -> None:
        assert slugify("test@#$%value") == "test_value"

    def test_empty_string(self) -> None:
        assert slugify("") == ""

    def test_only_whitespace(self) -> None:
        assert slugify("   ") == ""

    def test_numbers_preserved(self) -> None:
        assert slugify("region 01") == "region_01"

    def test_hyphens_replaced(self) -> None:
        assert slugify("Emilia-Romagna") == "emilia_romagna"

    def test_combined_real_world(self) -> None:
        """Test with a value similar to real region/province names."""
        assert slugify("Valle d'Aosta/Vallée d'Aoste") == "valle_d_aosta_vallee_d_aoste"
