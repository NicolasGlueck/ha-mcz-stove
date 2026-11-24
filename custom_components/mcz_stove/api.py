"""Local client for the HottoH Wi-Fi module of MCZ pellet stoves, TCP port 5001, plain text, no authentication.

Frame: '#' + seq(5) + client(4) + length(4 hex) + command(4) + data + CRC-16/CCITT-FALSE(4 hex) + '\\n',
the CRC covers everything after '#'. One command per connection; a lock makes sure that
requests never run in parallel (the module does not cope well with concurrent connections).
"""
from __future__ import annotations

import asyncio
from contextlib import suppress
import random

from .const import F_LEVEL_MAX, F_LEVEL_MIN, P_FAN_BASE, P_LEVEL, P_POWER, fan_fields

TIMEOUT = 5.0
RETRIES = 3


class HottohError(Exception):
    """Stove unreachable or response unusable."""


class HottohRejected(HottohError):
    """The stove rejected a write command or the value is out of range."""


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def build_frame(cmd: str, data: str) -> bytes:
    body = f"{random.randint(1, 99999):05d}IOS-{len(data):04X}{cmd}{data}"
    return f"#{body}{crc16(body.encode()):04X}\n".encode()


def parse_frame(raw: bytes) -> str:
    """Check the CRC and return the response starting at the command word (e.g. 'DATR0;65;...')."""
    line = raw.decode(errors="replace").strip()
    if not line.startswith("#") or len(line) < 22:
        raise HottohError(f"malformed response: {line!r}")
    body, crc = line[1:-4], line[-4:]
    if f"{crc16(body.encode()):04X}" != crc.upper():
        raise HottohError(f"CRC mismatch: {line!r}")
    return body[13:]


class HottohClient:
    """Async client, one TCP connection per command."""

    def __init__(self, host: str, port: int = 5001) -> None:
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()

    async def _once(self, cmd: str, data: str) -> str:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        try:
            writer.write(build_frame(cmd, data))
            await writer.drain()
            raw = await reader.readuntil(b"\n")
        finally:
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()
        return parse_frame(raw)

    async def request(self, cmd: str, data: str) -> str:
        async with self._lock:
            last: Exception | None = None
            for attempt in range(RETRIES):
                try:
                    return await asyncio.wait_for(self._once(cmd, data), TIMEOUT)
                except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError, HottohError) as err:
                    last = err
                    await asyncio.sleep(0.5 + attempt)
            raise HottohError(f"{self.host}:{self.port} not reachable: {last}")

    async def read_fields(self) -> list[int]:
        """DATR0 -> list of numeric fields."""
        resp = await self.request("DATR", "0;")
        if not resp.startswith("DATR"):
            raise HottohError(f"unexpected response: {resp!r}")
        try:
            return [int(x) for x in resp[4:].rstrip(";").split(";")]
        except ValueError as err:
            raise HottohError(f"cannot parse fields: {resp!r}") from err

    async def read_info(self) -> tuple[str | None, int | None]:
        """INFR -> (firmware, Wi-Fi signal in dBm). The signal can be 'nosig'."""
        parts = (await self.request("INFR", ""))[4:].rstrip(";").split(";")
        firmware = parts[1] if len(parts) > 1 else None
        rssi = int(parts[2]) if len(parts) > 2 and parts[2].lstrip("-").isdigit() else None
        return firmware, rssi

    async def write(self, param: int, value: int) -> None:
        resp = await self.request("DATW", f"{param};{value};")
        if not resp.startswith("DATWOK"):
            raise HottohRejected(f"stove rejected {param}={value}: {resp!r}")

    async def set_power(self, on: bool) -> None:
        await self.write(P_POWER, 1 if on else 0)

    async def set_level(self, level: int, fields: list[int]) -> None:
        lo, hi = fields[F_LEVEL_MIN], fields[F_LEVEL_MAX]
        if not lo <= level <= hi:
            raise HottohRejected(f"power level {level} outside {lo}..{hi}")
        await self.write(P_LEVEL, level)

    async def set_fan(self, nr: int, value: int, fields: list[int]) -> None:
        hi = fields[fan_fields(nr)[2]]
        if not 0 <= value <= hi:
            raise HottohRejected(f"fan {nr}: {value} outside 0..{hi}")
        await self.write(P_FAN_BASE + nr, value)
