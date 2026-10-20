"""What RomM tells the store switcher about its own copies of a game.

A server can hold several entries under one title, such as a Linux port
beside the Windows original, or two builds of the same game. The switcher
labels those entries from ``disambiguators`` and orders them by
``default_rank``, both read from a game's metadata (see
``src/lib/variant-labels.ts`` and ``src/lib/game-grouping.ts``). This module
says what they are for RomM.
"""

from __future__ import annotations

import re
from typing import Any

# RomM reads ``(<provider>-<digits>)`` filename segments to force a metadata
# match and leaves them in ``tags``. They name no build, so they are dropped.
# The providers are those with a tag parser in RomM's metadata handlers.
_PROVIDER_ID_TAG = re.compile(
    r"(?:igdb|ss|ssfr|moby|hltb|ra|steam|launchbox|pouet|demozoo|csdb)-\d+",
    re.IGNORECASE,
)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _build_tags(item: dict[str, Any], platform: str) -> list[str]:
    tags = item.get("tags")
    if not isinstance(tags, list):
        return []
    kept = []
    for tag in map(_text, tags):
        if (
            tag
            and not _PROVIDER_ID_TAG.fullmatch(tag)
            and tag.casefold() != platform.casefold()
        ):
            kept.append(tag)
    return kept


def _is_main_sibling(item: dict[str, Any]) -> bool:
    user = item.get("rom_user")
    return isinstance(user, dict) and user.get("is_main_sibling") is True


def variant_metadata(item: dict[str, Any]) -> dict[str, Any]:
    """``default_rank`` always, plus ``disambiguators`` when there are any.

    Entries run from most to least telling: the platform's display name, then
    the filename tags as one entry. A ``platform_display_name`` is the
    server's own wording; an empty one adds no entry instead of falling back
    to the slug.

    The rank puts a Linux copy first because it runs natively, then the copy
    the user marked as the main sibling on the server. The main flag is only
    meaningful within one platform, so the platform decides first.
    """
    platform = _text(item.get("platform_display_name"))
    entries = [platform] if platform else []
    tags = _build_tags(item, platform)
    if tags:
        entries.append(", ".join(tags))

    tier = 0 if item.get("platform_slug") == "linux" else 1
    meta: dict[str, Any] = {
        "default_rank": tier * 2 + (0 if _is_main_sibling(item) else 1),
    }
    if entries:
        meta["disambiguators"] = entries
    return meta
