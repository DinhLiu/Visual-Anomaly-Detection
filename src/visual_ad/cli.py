"""Phase-one command line. No training or inference claims are made here."""

import argparse
import json
import sys
from pathlib import Path

from .common import digest, environment, now, read_json, source_hash, write_json
from .config import load_config
from .data import inspect_dataset, make_split, prepare, resolve_root, verify_files
from .reporting import archive_phase1_results, write_data_report


def parser():
    root = argparse.ArgumentParser(prog="vad", description="Visual AD Lab — phase-one data preparation")
    commands = root.add_subparsers(dest="command", required=True)
    env = commands.add_parser("environment", help="Record Python and installed package versions")
    env.add_argument("--output", type=Path)
    data = commands.add_parser("data")
    actions = data.add_subparsers(dest="action", required=True)
    archive = actions.add_parser("archive", help="Package a completed phase-one result directory")
    archive.add_argument("--output", type=Path, required=True)
    archive.add_argument("--archive", type=Path)
    for name in ("validate", "split", "prepare"):
        action = actions.add_parser(name)
        action.add_argument("--config", type=Path)
        action.add_argument("--root", type=Path)
        action.add_argument("--output", type=Path)
        action.add_argument("--seed", type=int)
        action.add_argument(
            "--allow-partial",
            action="store_true",
            help="Only for local fixtures; never the 15-category benchmark",
        )
        if name == "split":
            action.add_argument("--inventory", type=Path, required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    output = None
    try:
        if args.command == "environment":
            info = {**environment(), "source_fingerprint": source_hash()}
            if args.output:
                write_json(args.output, info)
            print(json.dumps(info, ensure_ascii=False, indent=2))
            return 0
        if args.action == "archive":
            result = archive_phase1_results(args.output, args.archive)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        config = load_config(
            args.config,
            data_root=args.root,
            output_root=args.output,
            seed=args.seed,
            require_all_categories=False if args.allow_partial else None,
        )
        root = resolve_root(config.data_root)
        candidate_output = config.output_root.resolve()
        if candidate_output.is_relative_to(root):
            raise ValueError("Output must be outside dataset root")
        output = candidate_output
        output.mkdir(parents=True, exist_ok=True)
        resolved = config.model_dump(mode="json")
        resolved["resolved_data_root"] = str(root)
        config_path = output / "resolved-config.json"
        if config_path.exists() and read_json(config_path) != resolved:
            raise ValueError("Output directory belongs to a different config; choose a new output directory")
        write_json(config_path, resolved)
        if args.action == "validate":
            inventory = inspect_dataset(root, config.require_all_categories, config.dataset_version)
            inventory_path = output / "inventory.json"
            if inventory_path.exists() and read_json(inventory_path) != inventory:
                raise ValueError(
                    "Inventory changed; choose a new output directory to preserve previous evidence"
                )
            write_json(inventory_path, inventory)
            result = {
                "status": "validated",
                "count": len(inventory["samples"]),
                "categories": inventory["categories"],
                "dataset_fingerprint": inventory["dataset_fingerprint"],
            }
            write_json(output / "validation.json", result)
        else:
            target = output / "split-manifest.json"
            if args.action == "split":
                inventory = read_json(args.inventory)
                current = inspect_dataset(root, config.require_all_categories, config.dataset_version)
                if (
                    current["dataset_fingerprint"] != inventory["dataset_fingerprint"]
                    or current["dataset_version"] != inventory["dataset_version"]
                ):
                    raise ValueError("Inventory is stale or belongs to another dataset version")
                manifest = make_split(current, config.seed)
                if target.exists() and read_json(target) != manifest:
                    raise ValueError("Refusing to overwrite a different split manifest")
                write_json(target, manifest)
                write_json(output / "inventory.json", current)
            else:
                manifest = prepare(
                    root, target, config.require_all_categories, config.seed, config.dataset_version
                )
            verify_files(root, manifest["samples"])
            result = write_data_report(root, manifest, output, resolved)
        write_json(
            output / "last-status.json",
            {"status": "completed", "action": args.action, "at": now(), "config_hash": digest(resolved)},
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        detail = {"status": "failed", "error": str(error), "at": now()}
        if output is not None and output.is_dir():
            write_json(output / "last-status.json", detail)
            (output / "failure-report.md").write_text(
                "# Kiểm tra chưa hoàn thành\n\n"
                + str(error)
                + "\n\nChưa có bằng chứng nghiệm thu lần chạy này. Sửa nguyên nhân rồi chạy lại cùng lệnh.\n"
            )
        print(json.dumps(detail, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
