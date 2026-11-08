from __future__ import annotations
import argparse, json
from pathlib import Path
from .engine import analyze_paths


def main():
    parser = argparse.ArgumentParser(description="Run the MarginPulse configurable BI engine on CSV/XLSX datasets.")
    parser.add_argument("--files", nargs="+", required=True, help="Input CSV/XLSX file paths")
    parser.add_argument("--client-id", default="demo_client")
    parser.add_argument("--profile", choices=["auto", "distributor", "retailer", "service"], default="auto")
    parser.add_argument("--currency", default="INR")
    parser.add_argument("--country", default="India")
    parser.add_argument("--as-of-date", default=None)
    parser.add_argument("--config", default=None, help="Optional JSON config file for dataset_map, mappings and thresholds")
    parser.add_argument("--output-root", default="./storage")
    args = parser.parse_args()
    config = {"client_id": args.client_id, "profile": args.profile, "currency": args.currency, "country": args.country}
    if args.as_of_date:
        config["as_of_date"] = args.as_of_date
    if args.config:
        user_cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        config.update(user_cfg)
    result = analyze_paths(args.files, config, args.output_root)
    print(json.dumps(result["summary"], indent=2, default=str))
    print(f"\nOutput package: {result['output_zip']}")

if __name__ == "__main__":
    main()
