"""match.py 单元测试 · 姓名匹配（中等严格度）"""
import pytest
from hh_research.extract.researcher_mapping.match import (
    normalize_name,
    match_name,
)


class TestNormalizeName:
    def test_strips_accents(self):
        assert normalize_name("Tri Đào") == "tri dao"

    def test_lowercase(self):
        assert normalize_name("Tri Dao") == "tri dao"

    def test_removes_punctuation_keeps_hyphen(self):
        assert normalize_name("T. Dao") == "t dao"
        assert normalize_name("Jean-Paul Sartre") == "jean-paul sartre"


class TestMatchName:
    def test_exact_match(self):
        assert match_name("Tri Dao", "Tri Dao") is True

    def test_case_insensitive(self):
        assert match_name("tri dao", "TRI DAO") is True

    def test_initial_abbreviation(self):
        assert match_name("Tri Dao", "T. Dao") is True
        assert match_name("Tri Dao", "T Dao") is True

    def test_middle_name_substring(self):
        assert match_name("Tri Hoang Dao", "Tri Dao") is True
        assert match_name("Tri Dao", "Tri Hoang Dao") is True

    def test_chinese_to_pinyin(self):
        assert match_name("陈天奇", "Tianqi Chen") is True
        assert match_name("Tianqi Chen", "陈天奇") is True

    def test_chinese_pinyin_with_space(self):
        assert match_name("陈天奇", "Tian Qi Chen") is True

    def test_negative_different_person(self):
        assert match_name("Tri Dao", "Tianqi Chen") is False

    def test_negative_partial_first_name(self):
        assert match_name("Tri Dao", "Tom Dao") is False


from hh_research.extract.researcher_mapping.match import (
    normalize_affiliation,
    match_affiliation,
    ABBREVIATIONS,
)


class TestNormalizeAffiliation:
    def test_strip_punct_lowercase(self):
        assert normalize_affiliation("Princeton Univ.") == "princeton univ"

    def test_remove_filler_words(self):
        assert normalize_affiliation("Department of CS, Princeton University") == "cs princeton"

    def test_collapse_whitespace(self):
        assert normalize_affiliation("MIT  CSAIL") == "mit csail"


class TestMatchAffiliation:
    def test_substring_short_in_long(self):
        assert match_affiliation("Princeton", ["Department of CS, Princeton University"]) is True

    def test_substring_long_in_short(self):
        assert match_affiliation("Stanford University AI Lab", ["Stanford"]) is True

    def test_abbreviation_mit(self):
        assert match_affiliation("MIT", ["Massachusetts Institute of Technology"]) is True

    def test_abbreviation_cmu(self):
        assert match_affiliation("CMU", ["Carnegie Mellon University"]) is True

    def test_chinese_abbreviation(self):
        assert match_affiliation("清华", ["Tsinghua University"]) is True

    def test_negative_mit_vs_mass_general_hospital(self):
        assert match_affiliation("MIT", ["Massachusetts General Hospital"]) is False

    def test_negative_unrelated(self):
        assert match_affiliation("Princeton", ["UC Berkeley"]) is False

    def test_no_match_in_empty_list(self):
        assert match_affiliation("Princeton", []) is False

    def test_abbreviations_dict_contains_expected_keys(self):
        assert "mit" in ABBREVIATIONS
        assert "cmu" in ABBREVIATIONS
        assert "清华" in ABBREVIATIONS
