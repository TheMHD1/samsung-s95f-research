"""Pure host model of image1 bd58; no device, network, or write interface."""
import struct

LANES = 1920
PACKED_BYTES = 2880
SNAPSHOT_BYTES = 0xB60
FIRST_LANE = 568
CANDIDATE_X = (570, 571, 622, 623, 624, 625, 632, 633)
BASES = {"top": 0x20015000, "bottom": 0x20015F10}


def unpack_group(raw):
    """Exactly be4a..be88/bed4..bf90: 32-bit load plus halfword at +4."""
    if len(raw) != 6:
        raise ValueError("group must be exactly six bytes")
    word, tail = struct.unpack("<IH", raw)
    return (word & 0xFFF, (word >> 12) & 0xFFF,
            (word >> 24) | ((tail & 15) << 8), tail >> 4)


def lane_from_x(x, xbase):
    if not (0 <= x <= 0xFFFF and 0 <= xbase <= 0xFFFF):
        raise ValueError("halfword coordinate")
    lane = (x - xbase) & 0xFFFF
    if lane >= LANES:
        raise ValueError("coordinate outside unpacked lane span")
    return lane


def window(kind, length=104):
    """Only the two statically qualified low-SRAM windows; not a reader."""
    if kind not in BASES or length not in (104, 120):
        raise ValueError("unknown fixed window")
    offset = (FIRST_LANE // 4) * 6
    cpu = BASES[kind] + offset
    if offset + length > SNAPSHOT_BYTES or not (0x20000000 <= cpu < cpu + length <= 0x20020000):
        raise ValueError("SRAM bounds")
    bus = cpu + 0x27000000
    groups = 17 if length == 104 else 20
    return {"kind": kind, "cpu": cpu, "bus": bus, "bytes": length,
            "first_lane": FIRST_LANE, "complete_lanes": groups * 4,
            "decode_bytes": groups * 6, "ignored_tail_bytes": length - groups * 6,
            "header_hex": struct.pack("<III", 0x101, bus, length).hex()}


def decode_window(raw, *, kind, length=104, xbase=0):
    plan = window(kind, length)
    if len(raw) != length:
        raise ValueError("exact advertised byte count required")
    # These fixed addresses are selected for the captured xbase=0 only.
    if xbase != 0:
        raise ValueError("captured xbase drift: requalification required")
    values = []
    for offset in range(0, plan["decode_bytes"], 6):
        values.extend(unpack_group(raw[offset:offset + 6]))
    result = {}
    for x in CANDIDATE_X:
        lane = lane_from_x(x, xbase)
        index = lane - plan["first_lane"]
        if not 0 <= index < len(values):
            raise ValueError("candidate outside fixed window")
        result[x] = values[index]
    return result


def amplitude_candidates(b, difference):
    """Unsigned 12-bit inputs plus absolute difference; does not assign epoch/type."""
    if not (0 <= b <= 4095 and 0 <= difference <= 4095):
        raise ValueError("12-bit amplitude/difference")
    return sorted({a for a in (b - difference, b + difference) if 0 <= a <= 4095})
