"""Tests for ``stores.romm.variants``: the facts that tell same-title RomM
entries apart and the rank that prefers a native or server-chosen main copy."""
from __future__ import annotations

import pytest

from unifideck.stores.romm.variants import variant_metadata


def row(slug="linux", platform="Linux", tags=(), main=False, **extra):
    item = {
        "platform_slug": slug,
        "platform_display_name": platform,
        "platform_custom_name": "",
        "tags": list(tags),
        "rom_user": {"is_main_sibling": main},
    }
    item.update(extra)
    return item


def test_linux_row_with_tag():
    assert variant_metadata(row(tags=["Ghostship"])) == {
        "disambiguators": ["Linux", "Ghostship"],
        "default_rank": 1,
    }


@pytest.mark.parametrize(
    ("slug", "platform", "main", "rank"),
    [
        ("linux", "Linux", True, 0),
        ("linux", "Linux", False, 1),
        ("win", "Windows", True, 2),
        ("win", "Windows", False, 3),
    ],
)
def test_rank_puts_platform_before_main_sibling(slug, platform, main, rank):
    assert variant_metadata(row(slug, platform, main=main))["default_rank"] == rank


def test_several_tags_become_one_entry():
    assert variant_metadata(row(tags=["A", "B"]))["disambiguators"] == ["Linux", "A, B"]


@pytest.mark.parametrize(
    "provider",
    ["igdb", "ss", "ssfr", "moby", "hltb", "ra", "steam", "launchbox", "pouet", "demozoo", "csdb"],
)
def test_provider_id_tags_are_dropped(provider):
    meta = variant_metadata(row(tags=[f"{provider.upper()}-123", "Ghostship"]))
    assert meta["disambiguators"] == ["Linux", "Ghostship"]


def test_only_provider_id_tags_leave_no_tag_entry():
    assert variant_metadata(row(tags=["igdb-79247"]))["disambiguators"] == ["Linux"]


def test_other_hyphenated_tags_are_kept():
    assert variant_metadata(row(tags=["Remix-2", "igdb-1x"]))["disambiguators"] == [
        "Linux",
        "Remix-2, igdb-1x",
    ]


def test_tag_equal_to_the_platform_is_skipped():
    meta = variant_metadata(row("win", "Windows", tags=["windows", "Ghostship"]))
    assert meta["disambiguators"] == ["Windows", "Ghostship"]
    assert variant_metadata(row("win", "Windows", tags=["Windows"]))["disambiguators"] == ["Windows"]


def test_tags_are_trimmed_and_blanks_dropped():
    assert variant_metadata(row(tags=[" A ", "", "  "]))["disambiguators"] == ["Linux", "A"]


def test_platform_entry_uses_the_display_name_without_a_slug_fallback():
    assert "disambiguators" not in variant_metadata(row(platform="", tags=[]))
    assert variant_metadata(row(platform=" ", tags=["X"]))["disambiguators"] == ["X"]


@pytest.mark.parametrize("tags", [None, "Ghostship", 5, [None, 3, {}]])
def test_malformed_tags_do_not_crash(tags):
    item = row()
    item["tags"] = tags
    assert variant_metadata(item)["disambiguators"] == ["Linux"]


def test_missing_fields_still_rank():
    assert variant_metadata({}) == {"default_rank": 3}


@pytest.mark.parametrize("user", [None, "x", {}, {"is_main_sibling": None}, {"is_main_sibling": 1}])
def test_only_a_true_main_flag_counts(user):
    item = row()
    item["rom_user"] = user
    assert variant_metadata(item)["default_rank"] == 1
