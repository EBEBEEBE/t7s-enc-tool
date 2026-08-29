from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core import AssetCryptError, Keys, build_output_path, collect_inputs, process_one
from core.detection import choose_mode
from core.processing import format_mode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="t7s_assetcrypt", description="Decrypt/encrypt t7s-style .enc asset files. Folder input is processed recursively.")
    parser.add_argument("command", nargs="?", choices=("decrypt", "d", "decode", "encrypt", "e", "encode"), help="decrypt/d/decode or encrypt/e/encode")
    parser.add_argument("input", nargs="?", help="Input file or folder. Folder input is recursive.")
    parser.add_argument("-o", "--output", help="Output filename/folder. For multiple inputs, a non-directory value is used as a filename prefix.")
    parser.add_argument("-k", "--key", default="key.txt", help="Plain-text key file (default: key.txt).")
    parser.add_argument("-t", "--type", choices=("v1", "v2", "v2z"), help="Force format: v1, v2, or v2z. Without this option, automatic per-file inference is used.")
    parser.add_argument("--auto", action="store_true", help="Automatic recursive mode. decrypt: only .enc files; encrypt: skip .enc files.")
    parser.add_argument("--auto-decode", "-ad", action="store_true", help="Shortcut for automatic decrypt from the current directory when no input is supplied.")
    parser.add_argument("--auto-encode-transaction-data", "-aetd", action="store_true", help="Shortcut for automatic encrypt from the current directory when no input is supplied.")
    return parser


def normalize_command(raw: str | None) -> str | None:
    if raw in {"decrypt", "d", "decode"}: return "decrypt"
    if raw in {"encrypt", "e", "encode"}: return "encrypt"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = normalize_command(args.command)
    if args.auto_decode and args.auto_encode_transaction_data:
        parser.error("--auto-decode and --auto-encode-transaction-data are mutually exclusive.")
    if args.auto_decode:
        if command == "encrypt": parser.error("--auto-decode conflicts with the encrypt command.")
        command, args.auto = "decrypt", True
    if args.auto_encode_transaction_data:
        if command == "decrypt": parser.error("--auto-encode-transaction-data conflicts with the decrypt command.")
        command, args.auto = "encrypt", True
    if command is None:
        parser.print_help(sys.stderr); return 2
    if args.input: input_path = Path(args.input)
    elif args.auto or args.auto_decode or args.auto_encode_transaction_data: input_path = Path.cwd()
    else:
        parser.print_help(sys.stderr); return 2
    try:
        keys = Keys.from_file(Path(args.key))
        files, root = collect_inputs(input_path, command, args.auto)
        if not files:
            print("No matching input files found.", file=sys.stderr); return 1
        output = Path(args.output) if args.output else None
        multiple, successes, failures = len(files) > 1, 0, 0
        for source in files:
            if command == "decrypt" and source.suffix.lower() != ".enc" and input_path.is_dir(): continue
            version, use_lz4 = choose_mode(source, command, args.type)
            destination = build_output_path(source, root, output, multiple, command, version, keys)
            try:
                process_one(source, destination, command, version, use_lz4, keys)
                print(f"[OK] {source} -> {destination} ({format_mode(version, use_lz4)})"); successes += 1
            except Exception as exc:
                print(f"[ERROR] {source}: {exc}", file=sys.stderr); failures += 1
        print(f"Done: {successes} succeeded, {failures} failed.", file=sys.stderr if failures else sys.stdout)
        return 1 if failures else 0
    except AssetCryptError as exc:
        print(f"Error: {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
