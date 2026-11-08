$ErrorActionPreference = "Stop"
python -m marginpulse_engine.cli --files examples/distributor_demo.xlsx --client-id demo-uae-distributor --profile distributor --currency AED --country UAE --as-of-date 2026-10-31 --output-root .\storage
