# Mainnet Upgrade Guide: From Version v1.1 to v1.2 (`nvnm-1`)

> **Upgrade type:** state-migration upgrade that bulk-loads the NVNM cite dataset
> into the `anchoring` module. Every **node** must stage ~460 MB of export data
> on local disk **before** the upgrade height. Read this whole document first —
> Steps 1–2 must be completed before the chain reaches the upgrade height; there
> is no way to supply the data after the fact.

## Overview

- **On-chain upgrade name**: `v1.2.0`
- **v1.2 Upgrade Block Height**: `2046500`
- **v1.2 Upgrade Countdown**: [Block Countdown](https://evm.explorer.nvnmchain.io/block/countdown/2046500)
- **v1.2 Release**: [Release Page](https://github.com/NVNM-Chain/nvnmchain/releases/tag/v1.2.0)
- **v1.2 Bulk data (public)**: `https://nvnmchain-ops-data.nvnmchain.tech/mainnet-bulk-data`
- **v1.2 Bulk data archive (public)**: `https://nvnmchain-ops-data.nvnmchain.tech/mainnet-bulk-data/nvnm-cite-mainnet-full-export.zip`
  (checksum: `.../nvnm-cite-mainnet-full-export-checksum.txt`)

> **Reminder:** NVNM Chain is a Layer 2 consumer chain of MANTRA Chain (`mantra-1`).
> Ensure your MANTRA Chain L1 provider node is healthy and running a compatible
> version before upgrading the L2 `nvnmchaind` binary.

> **No on-chain governance:** `nvnm-1` is an Interchain Security consumer chain and
> does **not** run an `x/gov` module — there is no upgrade proposal to vote on. The
> `v1.2.0` `SoftwareUpgrade` (and its block height) is scheduled by the chain
> authority and announced by the NVNM Chain team. Operators act on the announced
> upgrade height; there is nothing to vote on or submit.

---

## What this upgrade does

The mainnet case-law export (**2,114 registries, 11,944,960 records**; ~3.6 GB
uncompressed / ~460 MB gzipped, across 4 tranches — federal appellate, federal
complete, state pilot, state remainder) is loaded entirely by the v1.2.0 upgrade
handler in a single `SeedAnchoringData` call. These records are written by **state
migration**, not by `addRecord` transactions, so log-scanning indexers will not
see them — use keyed/offset-paged `records()` reads instead.

### Baked into the binary (nothing to configure)

- The `registries.json` / `manifest.json` (all 4 tranches) are compiled into
  `nvnmchaind` from `app/upgrades/v1_2/data/`. They are identical for every
  validator that builds from the same release.
- The registry admin/creator address (`nvnm14a3em3mr9mvta9ccgk80wn0dxgzt5lkt2r8trx`)
  is hardcoded in the binary. It is set once per registry and can never be changed
  by any message handler — nothing to configure.

### What you must supply

The bulk tranche data (the `*.jsonl.gz` files) is **not** in the binary. Each node
must stage it on local disk before the upgrade height. The handler verifies every
file byte-for-byte against `manifest.json` before writing anything to state, and is
**fail-closed**: any missing file, sha256 mismatch, or record/registry count
mismatch aborts the upgrade before the block commits (no partial state).

---

## Pre-upgrade requirements

> **Recommended upgrade-time spec (both VM and Kubernetes): 128 GB RAM and 16 vCPU.**
> Provision this for **every** node role that applies the upgrade (validator,
> full/archive, and any sentries that run the binary) for the duration of the
> upgrade. You can scale back to normal sizing afterwards (see Step 5 / Path B).

| Resource | Guidance |
| --- | --- |
| **RAM** | **Recommended: 128 GB.** Every write inside an upgrade handler is buffered in an **in-memory cache** until the block commits. All 11.94M records land in a single block's write cache, so peak RAM scales with the **full** record count. 128 GB leaves comfortable headroom above the working set; do not run this upgrade on a memory-tight node. |
| **CPU** | **Recommended: 16 vCPU.** The seed is largely sequential state writes, but the surrounding IAVL commit, indexing, and normal consensus work benefit from headroom — 16 vCPU keeps the node responsive through the load and the post-handler commit phase. |
| **Disk** | Writing into the IAVL store grows `data/` by **more than** the raw uncompressed size (tree-node overhead, historical versions, indexing). Keep generous free space beyond the ~3.6 GB raw record size. Not yet precisely benchmarked — err generous. |
| **Staging disk** | ~460 MB for the gzipped export at the staging path (below). |
| **Go (build-from-source only)** | Go 1.24.x. |

---

## Step 1 — Obtain and stage the export

The export is published (public, read-only) as a single archive, plus its checksum:

```
https://nvnmchain-ops-data.nvnmchain.tech/mainnet-bulk-data/nvnm-cite-mainnet-full-export.zip
https://nvnmchain-ops-data.nvnmchain.tech/mainnet-bulk-data/nvnm-cite-mainnet-full-export-checksum.txt
```

> These two object names are specific to the **v1.2.0** export. Do not assume the
> same filenames for future upgrades — always use the archive/checksum path
> announced for that release's bulk data (see Overview above).

Unzipped, the archive produces this exact tree — do not modify it:

```
mainnet-full-export/
├── manifest.json
├── registries.json
├── tranche-1-federal-appellate/*.jsonl.gz
├── tranche-2-federal-complete/*.jsonl.gz
├── tranche-3-state-pilot/*.jsonl.gz
└── tranche-4-state-remainder/*.jsonl.gz
```

Stage the **entire directory** at this exact path under your node's home directory:

```
<node-home>/upgrades/v1_2/mainnet-full-export/
```

> To stage elsewhere (different disk, shared mount), set
> `NVNMCHAIN_V1_2_EXPORT_DIR=/abs/path/to/mainnet-full-export` on the node process
> instead — it overrides the default path entirely.

### Download, verify checksum, and unzip (no credentials needed)

Run this on the node (VM) or inside the staging container (K8s). It fails closed on
a checksum mismatch, so a truncated or corrupted download is caught here rather than
at the upgrade height:

```bash
set -euo pipefail
BASE="https://nvnmchain-ops-data.nvnmchain.tech/mainnet-bulk-data"
DEST="${NVNMCHAIN_V1_2_EXPORT_DIR:-$HOME/.nvnmchain/upgrades/v1_2/mainnet-full-export}"
TMP="$(mktemp -d)"

wget -q -O "$TMP/export.zip"    "$BASE/nvnm-cite-mainnet-full-export.zip"
wget -q -O "$TMP/export.sha256" "$BASE/nvnm-cite-mainnet-full-export-checksum.txt"

EXPECTED_SHA=$(cut -d: -f2 "$TMP/export.sha256" | tr -d '[:space:]')
ACTUAL_SHA=$(sha256sum "$TMP/export.zip" | awk '{print $1}')
if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
  echo "Checksum mismatch: expected $EXPECTED_SHA, got $ACTUAL_SHA" >&2
  rm -rf "$TMP"
  exit 1
fi
echo "Checksum verified."

rm -rf "$DEST"
unzip -q -o "$TMP/export.zip" -d "$(dirname "$DEST")"
rm -rf "$TMP"
echo "Export staged at $DEST"
```

> On Kubernetes, run the same script as an **init container / one-shot Job** that
> mounts the node's data PVC, writing into `.../upgrades/v1_2/mainnet-full-export/`.
> Because the bucket is public and read-only, no object-storage credentials or
> secrets are required — no AWS/R2 access keys, no `aws s3` calls, just `wget` +
> `sha256sum` + `unzip`. All three are included in stock `busybox`/Alpine images,
> so nothing needs to be installed at runtime — useful if your container runs as a
> non-root user, since package managers (e.g. `apk add`) require root. Do this for
> **every** node that will apply the upgrade (validator, full/archive, and any
> sentries that also run the binary).

---

## Step 2 — Verify the staged data (before the upgrade height)

The handler will verify at the upgrade height and refuse to proceed on any mismatch —
but discovering that then means the chain is already stalled waiting on you. Verify
locally first. From inside the staged `mainnet-full-export/` directory:

```bash
cd "${NVNMCHAIN_V1_2_EXPORT_DIR:-$HOME/.nvnmchain/upgrades/v1_2/mainnet-full-export}"
python3 - <<'EOF'
import json, hashlib, pathlib, sys

base = pathlib.Path(".")
manifest = json.loads((base / "manifest.json").read_text())

bad = []
for f in manifest["files"]:
    path = base / f["file"]
    if not path.exists():
        bad.append((f["file"], "missing"))
        continue
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != f["sha256_gz"]:
        bad.append((f["file"], f"sha256 mismatch: want {f['sha256_gz']}, got {got}"))

print(f"checked {len(manifest['files'])} files, {len(bad)} problems")
for name, reason in bad:
    print(f"  {name}: {reason}")
sys.exit(1 if bad else 0)
EOF
```

**Do not proceed until this reports `0 problems`.** Expected output:

```
checked 2114 files, 0 problems
```

Optionally confirm the manifest totals match this release
(`2,114 registries / 11,944,960 records` across all 4 tranches).

---

## Step 3 — Prepare the `v1.2.0` binary

Choose the deployment path that matches your setup. Both stage the same data
(Steps 1–2) and reach the same on-chain result.

### Path A — VM / bare-metal with Cosmovisor (recommended for standalone nodes)

> **Scale the VM up first.** Before the upgrade height, resize the node to the
> **recommended 128 GB RAM / 16 vCPU** (e.g. resize the instance / attach a larger
> machine type, or move to a temporary high-memory host). Peak RAM scales with the
> full 11.94M record count held in the block's write cache — do not run this on a
> memory-tight VM. You can resize back to normal sizing after the upgrade completes
> and the post-handler IAVL commit has finished (Step 5).

If Cosmovisor is not yet configured, set it up once:

```bash
go install github.com/cosmos/cosmos-sdk/cosmovisor/cmd/cosmovisor@v1.6.0
mkdir -p ~/.nvnmchain/cosmovisor/genesis/bin
mkdir -p ~/.nvnmchain/cosmovisor/upgrades
cp "$(command -v nvnmchaind)" ~/.nvnmchain/cosmovisor/genesis/bin

# Environment (add to ~/.profile)
export DAEMON_NAME=nvnmchaind
export DAEMON_HOME=$HOME/.nvnmchain
export DAEMON_ALLOW_DOWNLOAD_BINARIES=false
export DAEMON_RESTART_AFTER_UPGRADE=true
export DAEMON_LOG_BUFFER_SIZE=512
export UNSAFE_SKIP_BACKUP=true
```

Stage the `v1.2.0` binary under the Cosmovisor upgrade path. The on-chain upgrade
name is `v1.2.0`, so the directory must be `.../cosmovisor/upgrades/v1.2.0/bin`:

```bash
UPGRADE_NAME="v1.2.0"      # must match the on-chain SoftwareUpgrade name
UPGRADE_VERSION="1.2.0"    # release tag without the leading v
mkdir -p ~/.nvnmchain/cosmovisor/upgrades/$UPGRADE_NAME/bin
if [[ $(uname -m) == 'arm64' || $(uname -m) == 'aarch64' ]]; then ARCH=arm64; else ARCH=amd64; fi
if [[ $(uname) == 'Darwin' ]]; then OS=darwin; else OS=linux; fi
wget https://github.com/NVNM-Chain/nvnmchain/releases/download/v$UPGRADE_VERSION/nvnmchaind-$UPGRADE_VERSION-$OS-$ARCH.tar.gz
tar -xvf nvnmchaind-$UPGRADE_VERSION-$OS-$ARCH.tar.gz -C ~/.nvnmchain/cosmovisor/upgrades/$UPGRADE_NAME/bin
rm nvnmchaind-$UPGRADE_VERSION-$OS-$ARCH.tar.gz
```

> Or auto-provision from `cosmovisor.json` in this directory once it has real
> checksums (regenerate it with the `create-binaries-json` workflow after the
> release is cut). At the upgrade height Cosmovisor swaps to `v1.2.0` automatically.

**Build from source** (alternative):

```bash
cd $HOME/nvnmchain && git fetch --tags && git checkout v1.2.0 && make build
cp build/nvnmchaind ~/.nvnmchain/cosmovisor/upgrades/v1.2.0/bin
```

### Path B — Kubernetes

The K8s flow mirrors Path A but is expressed as cluster operations. It is
provider-neutral — use whatever operator/manifests your platform provides:

1. **Snapshot first (Step 4).** Take a volume snapshot of each node's data volume
   as a rollback point before doing anything else.
2. **Scale up resources.** Reschedule the NVNM node pods onto a node class sized to
   the **recommended 128 GB RAM / 16 vCPU** for the duration of the upgrade (peak RAM
   scales with the full 11.94M record count — see requirements), and set pod
   requests/limits to match. Apply to **all** node roles that run the binary
   (validator, full/archive, sentries).
3. **Stage the data onto the node's data volume.** Run the Step 1 download/verify/
   unzip as an **init container or one-shot Job** that mounts the same PVC as the
   node and writes to `.../upgrades/v1_2/mainnet-full-export/` (or set
   `NVNMCHAIN_V1_2_EXPORT_DIR`). No storage credentials needed — the bucket is
   public and the archive's checksum is verified before unzipping. Then run the
   Step 2 verification (expect `checked 2114 files, 0 problems`).
4. **Roll out the `v1.2.0` image** so the pod restarts on the new binary at the
   upgrade height (either via your operator's version/upgrade field, or by having
   Cosmovisor inside the container swap binaries as in Path A).
5. **After the upgrade completes**, remove the staging init container/Job and scale
   the pods' CPU/memory back to normal.

> Whatever operator you use, the invariants are the same: (a) a pre-upgrade
> snapshot exists, (b) the verified export is present on the node's data volume at
> the staging path before the upgrade height, and (c) the pod has enough RAM to
> hold the full write cache.

---

## Step 4 — Back up / snapshot before the upgrade

Always capture a rollback point immediately before the upgrade height:

- **VM:** stop the node cleanly and copy/snapshot `~/.nvnmchain/data` (or take a
  disk/volume snapshot). Also back up `~/.nvnmchain/config` (keys,
  `priv_validator_key.json`, `node_key.json`).
- **Kubernetes:** take a volume snapshot of each node's data PVC (quiescing writes
  during the snapshot gives the cleanest result).

---

## Step 5 — Run the upgrade and watch the logs

Let the node reach the upgrade height with the `v1.2.0` binary staged (Cosmovisor
swaps automatically; manual operators halt at the panic and start `v1.2.0`). Watch for:

```
Starting v1.2.0 upgrade...
Running module migrations...
Seeding 2114 anchoring registries...
Seeded 2114 anchoring registries
Loading tranche 1 records...
Loading tranche 2 records...
Loading tranche 3 records...
Loading tranche 4 records...
Seeded 11944960 anchoring records
Upgrade v1.2.0 complete
```

**Expect an extended pause in block production while this runs** — it is millions of
sequential state writes executed synchronously inside a single upgrade block. After
the handler finishes, a separate, silent IAVL-tree write + disk-commit phase runs
(no extra log lines); watch `<node-home>/data/application.db` size to see it begin.

Do **not** restart or kill the node just because it looks stalled. Check for forward
progress first — new `Loading tranche N...` lines, climbing RSS in `ps`, or eventual
growth in `application.db` — before concluding anything is wrong.

---

## If it fails

The handler is **fail-closed**: any sha256 mismatch, missing file, or count mismatch
aborts the upgrade with a clear error naming the offending file and
expected-vs-actual value. Because this happens **before** the block commits, **no
partial state is persisted** — an OOM kill has the same effect. Fix the environment
and restart the node; the upgrade retries cleanly from the same height.

Common causes:

- **Wrong path** — confirm `.../upgrades/v1_2/mainnet-full-export/` (or your
  `NVNMCHAIN_V1_2_EXPORT_DIR`) contains the tranche directories directly, not a
  nested `mainnet-full-export/mainnet-full-export/`.
- **Incomplete transfer** — re-run the Step 2 verification.
- **Wrong export version** — the `manifest.json` totals must read **2,114 registries /
  11,944,960 records** across all 4 tranches for this binary.
- **Insufficient memory** — scale up RAM / free memory and retry (see requirements).

---

## Post-upgrade verification

```bash
# Total registries after load
nvnmchaind query anchoring registries --output json | jq '.registries | length'
# expect: (pre-existing registries) + 2114

# Spot-check a known registry's creator/name/description/metadata
nvnmchaind q anchoring registries --page-reverse --page-limit 1
# creator should be nvnm14a3em3mr9mvta9ccgk80wn0dxgzt5lkt2r8trx for seeded registries
```

Cross-check per-registry record counts against the manifest's `files[].records` for
any registry you want to independently confirm. Reconciliation does **not** depend on
transaction logs or events (these were written by state migration, not `addRecord`),
so use keyed/offset-paged `records()` reads.

---

## Additional resources

- Docs: <https://docs.nvnmchain.io>
- Binary releases: <https://github.com/NVNM-Chain/nvnmchain/releases>
- Upstream operator runbook: [`app/upgrades/v1_2/UPGRADE_RUNBOOK.md`](https://github.com/NVNM-Chain/nvnmchain/blob/main/app/upgrades/v1_2/UPGRADE_RUNBOOK.md)
