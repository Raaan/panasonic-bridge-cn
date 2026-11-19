"""Generate a SmartIR codebook from the recorded Panasonic IR states."""

import argparse
import base64
import json
from pathlib import Path

from pyhvac.ir.codec import Frame, decode, encode
from pyhvac.ir.formats import from_broadlink, to_broadlink
from pyhvac.protocols.panasonic import PANASONIC_AC, PANASONIC_AC_SECOND


FANS = {
    "auto": "自动", "quiet": "超静", "1": "1档", "2": "2档",
    "3": "3档", "4": "4档", "5": "5档", "super": "超强",
}
SWINGS = {"auto": "自动", "1": "最上", "2": "上", "3": "中", "4": "下", "5": "最下"}


def decode_code(code):
    frames = decode(PANASONIC_AC, from_broadlink(base64.b64decode(code, validate=True)))
    if [len(frame.data) for frame in frames] != [8, 19]:
        raise ValueError("Unexpected Panasonic AC frame lengths")
    payload = frames[1].data
    if sum(payload[:-1]) % 256 != payload[-1]:
        raise ValueError("Invalid Panasonic AC checksum")
    return frames


def build(first, baseline, mode, temperature, fan, swing):
    data = bytearray(baseline)
    for field, value in (
        ("mode", mode),
        ("temperature", temperature),
        ("fan", "1" if fan == "quiet" else "5" if fan == "super" else fan),
        ("swing_v", swing),
    ):
        definition = PANASONIC_AC_SECOND.fields[field]
        PANASONIC_AC_SECOND.write_raw(data, field, definition.to_int(field, value))
    data[13] = (data[13] & ~0x20) | (0x20 if fan == "quiet" else 0)
    data[14] = (data[14] & ~0x04) | (0x04 if fan == "super" else 0)
    PANASONIC_AC_SECOND.checksum.apply(data)
    packet = to_broadlink(encode(PANASONIC_AC, [
        Frame("first", first), Frame("second", bytes(data)),
    ]))
    encoded = base64.b64encode(packet).decode("ascii")
    if decode_code(encoded)[1].data != data:
        raise ValueError("BroadLink round-trip mismatch")
    return encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for the generated SmartIR JSON")
    args = parser.parse_args()
    samples = json.loads(Path(__file__).with_name("samples.json").read_text(encoding="utf-8"))
    captured = {name: decode_code(code) for name, code in samples.items()}
    checks = [
        ("cool_auto_25", "cool", 25, "auto", "auto"),
        ("heat_auto_24", "heat", 24, "auto", "auto"),
        ("cool_quiet_26", "cool", 26, "quiet", "auto"),
        ("cool_fan1_26", "cool", 26, "1", "auto"),
        ("cool_fan1_top_26", "cool", 26, "1", "1"),
        ("cool_fan5_top_27", "cool", 27, "5", "1"),
        ("cool_super_top_27", "cool", 27, "super", "1"),
        ("cool_super_bottom_26", "cool", 26, "super", "5"),
    ]
    baselines = {"cool": captured["cool_auto_25"], "heat": captured["heat_auto_24"]}
    for name, mode, temperature, fan, swing in checks:
        frames = baselines[mode]
        result = build(frames[0].data, frames[1].data, mode, temperature, fan, swing)
        if decode_code(result)[1].data != captured[name][1].data:
            raise ValueError(f"Generated state differs from sample: {name}")

    commands = {"off": samples["off_tested"]}
    for mode in ("cool", "heat", "dry"):
        frames = baselines["heat" if mode == "heat" else "cool"]
        commands[mode] = {}
        for fan, fan_label in FANS.items():
            commands[mode][fan_label] = {}
            for swing, swing_label in SWINGS.items():
                commands[mode][fan_label][swing_label] = {
                    str(temp): build(frames[0].data, frames[1].data, mode, temp, fan, swing)
                    for temp in range(16, 31)
                }
    result = {
        "manufacturer": "Panasonic",
        "supportedModels": ["CS-SFD13KQ10"],
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "minTemperature": 16,
        "maxTemperature": 30,
        "precision": 1,
        "operationModes": ["cool", "heat", "dry"],
        "fanModes": list(FANS.values()),
        "swingModes": list(SWINGS.values()),
        "commands": commands,
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {args.output} (2,160 states plus OFF)")


if __name__ == "__main__":
    main()

