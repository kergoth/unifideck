"""Opaque game IDs bind server-local ROM numbers to one configured URL."""
from __future__ import annotations

import hashlib

from .client import RomMAPIError, normalize_server_url


def _server_namespace(server_url: str) -> str:
    return hashlib.sha256(normalize_server_url(server_url).encode()).hexdigest()


def scoped_game_id(server_url: str, rom_id: int) -> str:
    if isinstance(rom_id, bool) or not isinstance(rom_id, int) or rom_id <= 0:
        raise RomMAPIError("Invalid RomM ROM ID", code="invalid_id")
    return f"{_server_namespace(server_url)}_{rom_id}"


def rom_id_for_server(server_url: str, game_id: str) -> int:
    prefix, separator, suffix = game_id.partition("_")
    if not separator or prefix != _server_namespace(server_url):
        raise RomMAPIError("This game belongs to a different RomM server", code="wrong_server")
    if not suffix.isascii() or not suffix.isdecimal() or int(suffix) <= 0 or str(int(suffix)) != suffix:
        raise RomMAPIError("Invalid RomM game ID", code="invalid_id")
    return int(suffix)
