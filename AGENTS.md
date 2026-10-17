# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
This is **Specter Patch**, a content mod for **Command & Conquer: Generals — Zero Hour**.
The bulk of the repo is game data shipped as binary artifacts (`.big` archives, multi-part
split zips like `Data.z01`, `Data/INI` game-config text files, `payload.rar`) plus a set of
developer **Python tools** under `patch/tools/`. The playable engine is a Windows binary, so
**there is no GUI application that can run in this Linux VM** — the only runnable/testable
component here is the Python tooling, exercised from the terminal.

### Environment / dependencies
- Tools are **pure Python 3 standard library** — there is nothing to `pip install` and no
  `requirements.txt`/`pyproject.toml`/lockfile. The VM's system `python3` (3.12) is sufficient.
- The update script therefore only sanity-checks the interpreter; adding a package install step
  would be misleading. There is no build step, no Node, no Docker.

### Running / testing the tools (all from repo root `/workspace`)
- Docs live in `patch/tools/economy/README.txt` and `patch/tools/big/README.txt`; the multiplayer
  gate is `patch/SYNC_CHECKLIST.md`. Reference those rather than duplicating commands.
- Economy tools support flags such as `--dry-run`, `--report <csv>`, `--side <Country>`, and
  `preview_price.py` never writes. Prefer `--dry-run` when you only want to verify behavior:
  - `python3 patch/tools/economy/preview_price.py --side America --base-cost 2000 --origin Imported --tech Gen5Fighter --category Aircraft`
  - `python3 patch/tools/economy/apply_country_balance.py --dry-run --report /tmp/out.csv`
  - `python3 patch/tools/economy/apply_build_limits.py --dry-run`
- **Gatekeeper:** `python3 patch/tools/economy/sync_audit.py` runs the deterministic multiplayer
  audit (duplicate IDs, Side ownership, LinkKeys, a temp-dir bake-idempotency re-run, and a
  `SYNC_MANIFEST.sha256` check). It exits non-zero and prints `FAIL` when the tracked content has
  outstanding issues. As of this setup the checked-in content already reports errors/warnings
  (e.g. a stale `SYNC_MANIFEST.sha256` and duplicate Objects) — a `FAIL` here is a verdict about
  repo content, **not** a broken environment. Regenerate the manifest with
  `patch/tools/economy/generate_sync_manifest.py` when intentionally changing content.

### Important gotchas
- **`patch/tools/ini_integrity_repair.py` and `patch/tools/boot_cleanup.py` have NO `--dry-run`
  or `--help`.** They ignore all args and immediately rewrite tracked `Data/INI` files, overwrite
  their `*_REPORT.md`/`Repair_Report.txt`, and can create `patch/Data/INI/CommandSet_BootFix_Stubs.ini`.
  Do not run them just to "inspect" — run only when you intend to commit their output, and
  `git checkout -- .` (plus delete the stub) to revert if you ran them by accident.
- The economy `apply_*` scripts without `--dry-run` also mutate `Data/INI` in place (they bake
  `; PatchBaseCost` markers). Use `--dry-run` for verification.
- Vendor archives at the repo root (`Data.zip`, `Specter_Data*`, `_SPEC_*`, `payload.rar`, `*.big`)
  are intentionally byte-frozen (see `.gitignore` note); `sync_audit.py` flags them if they ever
  show as modified in git. Never let them appear dirty.
- Most `patch/tools/big/build_specter_*_big.py` scripts are one-off historical build steps that
  hardcode paths and import each other; treat them as artifacts, not reusable CLIs. The reusable
  BIG utilities are `extract_spec_big_to_loose.py`, `merge_patch_into_spec_big.py`, and the
  `pack_specter_patch_final_*` packers (all argparse-driven).
