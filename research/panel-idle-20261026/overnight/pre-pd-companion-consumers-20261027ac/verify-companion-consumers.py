#!/usr/bin/env python3
"""Verify the two fixed companion-table consumers and bounded math models."""

from pathlib import Path
import hashlib
import json
import math
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PACKAGE = BASE / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
Y = BASE / "ap-table-source-20261027y"
AB = BASE / "pre-pd-stored-values-20261027ab"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, "SHA-256 " + str(path))
    return raw


def u16(raw, offset):
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw, offset):
    return struct.unpack_from("<I", raw, offset)[0]


def bl_target(image, address):
    first, second = struct.unpack_from("<HH", image, address)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding {address:#x}")
    s = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    value = ((s << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def cstring(package, va):
    start = va + 0x200
    end = package.index(b"\0", start, start + 80)
    return package[start:end].decode("ascii")


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def spc_lane(counts, threshold, cap, levels):
    """Model image-0 0x10334 for one lane, including u32 prefix wrap."""
    need(len(counts) == len(levels) == 16, "SPC model extents")
    running = 0
    crossing = None
    for index, value in enumerate(counts):
        running = (running + value) & 0xFFFFFFFF
        if running >= threshold:
            crossing = index
            break
    if crossing is None:
        return {"crossing": None, "output": levels[15] & 0xFFFF}
    ceiling = 1023 if crossing == 0 else (levels[crossing - 1] - 1) & 0xFFFFFFFF
    return {"crossing": crossing, "output": min(cap, ceiling) & 0xFFFF}


def npc_lane(counts, levels, index_limit, value_limit, cap, factor):
    """Model the lane-local source/companion math in image-0 0x19064."""
    need(len(counts) == len(levels) == 16, "NPC model extents")
    limit = min(index_limit, 16)
    filtered = [value if index <= limit and value <= value_limit else 0
                for index, value in enumerate(counts)]
    boundaries = [1024] + list(levels)
    maximum, maximum_index = 0, None
    for index, value in enumerate(filtered):
        if index == 15 and boundaries[16] == 0:
            break
        if maximum < value:  # strict: the first equal maximum is retained
            maximum, maximum_index = value, index
    if maximum == 0:
        return {"filtered": filtered, "maximum": 0, "maximum_index": None,
                "selected_scalar": 0, "output": 0}
    upper, lower = boundaries[maximum_index], boundaries[maximum_index + 1]
    if lower <= cap < upper:
        selected = cap
    else:
        selected = (upper - 1) & 0xFFFFFFFF
    # The selected body converts to f32, multiplies by its common returned
    # factor, adds f32 0.5, converts to u32, then stores the low halfword.
    product = f32(f32(float(selected)) * f32(factor))
    scaled = f32(f32(0.5) + product)
    # This host fixture model covers ordinary in-range conversions only. It
    # is not an emulator for ARM exceptional conversions or live FPSCR modes.
    need(math.isfinite(scaled) and 0 <= scaled < 2**32,
         "NPC fixture conversion outside finite nonnegative u32 domain")
    converted = int(scaled)
    return {"filtered": filtered, "maximum": maximum,
            "maximum_index": maximum_index, "selected_scalar": selected,
            "output": converted & 0xFFFF}


def npc_final(lanes, selection_flag):
    """Apply 0x19064's final +0x150 selection to three lane results."""
    need(len(lanes) == 3, "NPC final lanes")
    best_index, best_maximum = 0, 0
    for index, lane in enumerate(lanes):
        if best_maximum <= lane["maximum"]:  # equal peaks select the later lane
            best_index, best_maximum = index, lane["maximum"]
    if selection_flag == 1:
        return {"selected_lane": best_index, "output": lanes[best_index]["output"]}
    return {"selected_lane": None, "output": max(lane["output"] for lane in lanes)}


def main():
    package = load(PACKAGE,
                   "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "package extent")
    load(Y / "trace-table-source.py",
         "2ea74933a733b1065dafb1dc230c569122b1e18be2f69b3ac99895bf83b516b6")
    load(Y / "table-source-trace.md",
         "52774f5a67d1f927a05c71dd7788da2b4601091472ac9e3230b53692c89aacdb")
    load(AB / "verify-stored-values.py",
         "8d484ee5478f36008deefcf345ee73723a4ab9c0584acf1c1f1d7ee04cf99755")
    load(AB / "stored-values.md",
         "31312fd987633bba78f4d9edc87c149d766181a50a5c99c01ba6be1632c7ac3f")
    image = package[0x200:0x40200]

    pre_pd = package[0x80600:0x80800]
    need(sha(pre_pd) == "11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f",
         "Pre-PD record")
    need(pre_pd[:32] == b"Pre-PD" + bytes(26) and
         [u32(pre_pd, offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0x6C, 0xAC)] ==
         [7, 0x58410000, 1, 0x8000, 0, 0xAB0], "Pre-PD first group")
    companion = package[0x88178:0x881B8]
    need(sha(companion) == "87665b6d2c1cd41ead5bc1d2ff4eb693e9b8350d77c053249151a0eed53b0542",
         "stored companion")
    levels = list(struct.unpack("<16I", companion))
    need(levels == [960, 768, 640, 512, 448, 384, 320, 256,
                    192, 160, 128, 96, 64, 36, 1, 0], "stored levels")
    need(all(first > second for first, second in zip(levels, levels[1:])),
         "strictly descending levels")

    need(sha(image[0x10334:0x10424]) ==
         "12d4d300b3402aab6bb23d31744b4bc9a1babb12698075c45fdd399c872c0dc2",
         "complete 0x10334 consumer")
    need(sha(image[0x19064:0x19330]) ==
         "d6e9d5f5d129583ba1b248b790c947558e6759bd49371ec3ebe7f9832bff842a",
         "complete 0x19064 consumer")
    need(u32(image, 0x10428) == u32(image, 0x19334) == 0x58410178,
         "companion literals")
    need(image[0x10340:0x10344].hex() == "384f394e" and
         image[0x190AE:0x190B6].hex() == "dff88092a0480490",
         "source and companion loads")

    # Both external per-lane cap helpers are byte-identical max(A[k],B[k])
    # selectors over the same two exact fixed arrays.
    need(sha(image[0x19338:0x19364]) == sha(image[0x23510:0x2353C]) ==
         "1c1ef2774d5f516ebade2b709a8e341545a49b87306f9b3afbd92b2dabe1abd1",
         "byte-identical cap selectors")
    need((u32(image, 0x1935C), u32(image, 0x19360),
          u32(image, 0x23534), u32(image, 0x23538)) ==
         (0x584301F0, 0x584311F0, 0x584301F0, 0x584311F0),
         "cap arrays")
    need(bl_target(image, 0x10366) == 0x23510 and
         bl_target(image, 0x19174) == 0x19338 and
         bl_target(image, 0x19150) == 0x1AE9C, "consumer helper calls")
    need(sha(image[0x1AE9C:0x1AF52]) ==
         "8761bfa3a6e42095a66d789dfa95d0541708ae85203136409b96d65f6f0223b4",
         "three-float transform")

    # Positive named RAM-record context, without promoting root 0x47010000
    # to AP_RTP or naming either fixed table.
    registry = package[0x3CCBC:0x3CF08]
    rows = [struct.unpack_from("<7I", registry, index * 28) for index in range(21)]
    need(rows[5][:3] == (0x3DE3C, 0x2000F7C2, 0x124) and
         cstring(package, 0x3DE3C) == "AP_SPC", "AP_SPC registry")
    need(rows[2][:3] == (0x3DE84, 0x2000D71C, 0x540) and
         cstring(package, 0x3DE84) == "NPC_AP", "NPC_AP registry")
    need(image[0xF4F0:0xF4F4].hex() == "00487047" and
         u32(image, 0xF4F4) == 0x2000F7C2, "AP_SPC getter")
    need(image[0xEF9C:0xEFA0].hex() == "00487047" and
         u32(image, 0xEFA0) == 0x2000D71C, "NPC_AP getter")
    need(image[0xEF94:0xEF98].hex() == "00487047" and
         u32(image, 0xEF98) == 0x47010000, "unnamed context-root getter")

    # Semantic boundary fixtures for 0x10334.
    zero = [0] * 16
    first = zero.copy(); first[0] = 1
    second = zero.copy(); second[1] = 1
    last = zero.copy(); last[15] = 1
    need(spc_lane(first, 1, 2000, levels) == {"crossing": 0, "output": 1023},
         "SPC first-bin special ceiling")
    need(spc_lane(first, 1, 500, levels) == {"crossing": 0, "output": 500},
         "SPC cap below special ceiling")
    need(spc_lane(second, 1, 2000, levels) == {"crossing": 1, "output": 959},
         "SPC companion previous boundary")
    need(spc_lane(last, 1, 2000, levels) == {"crossing": 15, "output": 0} and
         spc_lane(zero, 1, 2000, levels) == {"crossing": None, "output": 0},
         "SPC last/no crossing boundary")
    wrapped = zero.copy(); wrapped[0], wrapped[1] = 0xFFFFFFFE, 5
    need(spc_lane(wrapped, 0xFFFFFFFF, 2000, levels) ==
         {"crossing": None, "output": 0}, "SPC u32 prefix wrap")
    underflow_levels = levels.copy(); underflow_levels[0] = 0
    need(spc_lane(second, 1, 2000, underflow_levels) ==
         {"crossing": 1, "output": 2000}, "SPC boundary subtraction wraps before unsigned min")

    # Semantic boundary fixtures for 0x19064.
    lane = zero.copy(); lane[2] = 100
    interpolated = npc_lane(lane, levels, 16, 1000, 700, 1.0)
    upper_fallback = npc_lane(lane, levels, 16, 1000, 800, 1.0)
    need((interpolated["maximum_index"], interpolated["selected_scalar"],
          interpolated["output"]) == (2, 700, 700), "NPC in-bin interpolation")
    need((upper_fallback["maximum_index"], upper_fallback["selected_scalar"],
          upper_fallback["output"]) == (2, 767, 767), "NPC boundary fallback")
    underflow_peak = npc_lane(second, underflow_levels, 16, 1000, 2000, 0.25)
    need(underflow_peak["selected_scalar"] == 0xFFFFFFFF,
         "NPC boundary subtraction wraps before unsigned-to-float conversion")
    need(npc_lane(lane, levels, 16, 1000, 765, 0.5)["output"] == 383 and
         npc_lane(lane, levels, 16, 1000, 700, 0.25)["output"] == 175,
         "NPC fractional factor plus-half then truncation, not generic round")
    large_levels = [20000000] + [0] * 15
    need(npc_lane(second, large_levels, 16, 1000, 16777217, 0.5)["output"] == 0,
         "NPC host binary32 rounding before low-halfword store")
    fifteenth = zero.copy(); fifteenth[15] = 100
    need(npc_lane(fifteenth, levels, 16, 1000, 1, 1.0)["maximum"] == 0,
         "NPC stored zero terminal boundary skips bin15")
    tie = zero.copy(); tie[2] = tie[3] = 100
    need(npc_lane(tie, levels, 16, 1000, 700, 1.0)["maximum_index"] == 2,
         "NPC strict earliest maximum")
    need(npc_lane(lane, levels, 1, 1000, 700, 1.0)["maximum"] == 0 and
         npc_lane(lane, levels, 16, 99, 700, 1.0)["maximum"] == 0,
         "NPC index/value filters")
    lanes = [npc_lane([10] + zero[1:], levels, 16, 1000, 980, 1.0),
             npc_lane([20] + zero[1:], levels, 16, 1000, 970, 1.0),
             npc_lane([5] + zero[1:], levels, 16, 1000, 990, 1.0)]
    need(npc_final(lanes, 1) == {"selected_lane": 1, "output": 970},
         "NPC flag1 maximum-source lane")
    need(npc_final(lanes, 0) == {"selected_lane": None, "output": 990},
         "NPC other flag maximum output")
    equal_lanes = [npc_lane([20] + zero[1:], levels, 16, 1000, cap, 1.0)
                   for cap in (980, 970, 990)]
    need(npc_final(equal_lanes, 1) == {"selected_lane": 2, "output": 990},
         "NPC equal peaks select last lane")

    ceilings = [1023] + [value - 1 for value in levels[:-1]]
    output = {
        "schema": "pre-pd-companion-consumers-v1", "target_operations": 0,
        "companion_address": "0x58410178", "stored_companion_words": levels,
        "stored_values_live_at_observation_proved": False,
        "consumer_10334": {"named_record": "AP_SPC", "lanes": 3,
                           "prefix_addition_bits": 32,
                           "crossing_output_ceilings": ceilings,
                           "output_offsets": ["+0x5a", "+0x5c", "+0x5e"]},
        "consumer_19064": {"named_record": "NPC_AP", "source_lanes_used_in_math": 3,
                           "fourth_lane_role": "copied to unnamed context only",
                           "per_lane_output_offsets": ["+0x56", "+0x58", "+0x5a"],
                           "final_output_offset": "+0x150",
                           "terminal_zero_skips_bin15_for_stored_companion": True,
                           "per_lane_first_equal_bin_retained": True,
                           "cross_lane_last_equal_peak_selected": True},
        "individual_field_units_identified": False,
        "runtime_source_or_companion_values_captured": False,
        "runtime_producer_identified": False, "physical_causality_proved": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
