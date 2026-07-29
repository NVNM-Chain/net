# NVNM Chain Networks

This repository contains network information for the various NVNM Chain networks.

NVNM Chain networks are **Layer 2 consumer chains** (Interchain Security) that derive
their validator set from a MANTRA Chain Layer 1 provider network:

| Network                          | Status             | Network version (binary version) | Provider (L1)              | Description                          |
| -------------------------------- | ------------------ | -------------------------------- | -------------------------- | ------------------------------------ |
| [mainnet](nvnm-1)                | :heavy_check_mark: | v1 (1.1.0)                       | [mantra-1](https://github.com/MANTRA-Chain/net/tree/main/mantra-1)               | NVNM Chain mainnet network.          |
| [testnet](nvnm-testnet-1)        | :heavy_check_mark: | v1 (1.1.0)                       | [mantra-dukong-1](https://github.com/MANTRA-Chain/net/tree/main/mantra-dukong-1) | NVNM Chain testnet network.          |

Each network has a corresponding directory (linked to above) containing network information.
Each directory includes, at a minimum:

| File                | Description                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------------- |
| `version.txt`       | The [nvnmchain](//github.com/NVNM-Chain/nvnmchain/releases) version used to participate in the network.  |
| `chain-id.txt`      | The "chain-id" of the network.                                                                           |
| `genesis.json`      | The genesis file for the network.                                                                        |
| `seed-nodes.txt`    | A list of seed node addresses for the network.                                                           |
| `rpc-nodes.txt`     | A list of COSMOS RPC node addresses for the network.                                                     |
| `evm-rpc-nodes.txt` | A list of EVM RPC node addresses for the network.                                                        |
| `evm-nodes.txt`     | A list of EVM node addresses (RPC + WebSocket) for the network.                                          |
| `api-nodes.txt`     | A list of API (LCD) node addresses for the network.                                                      |
| `explorer-url.txt`  | The URL(s) of explorer UIs for the network.                                                              |
| `meta.json`         | Chain-registry-style metadata (endpoints, binaries, fees, peers, snapshots).                             |

> **Note:** NVNM Chain L2 nodes require a synced MANTRA Chain L1 provider node
> (`mantra-1` for mainnet, `mantra-dukong-1` for testnet). See the
> [MANTRA-Chain/net](https://github.com/MANTRA-Chain/net) repo for provider network information.

## Usage

The information in this repo may be used to automate tasks when deploying or configuring
[nvnmchain](//github.com/NVNM-Chain/nvnmchain) software.

The format is standardized across the networks so that you can use the same method
to fetch the information for all of them - just change the base URL

```sh
NVNMCHAIN_NET_BASE=https://raw.githubusercontent.com/NVNM-Chain/net/main

##
#  Use _one_ of the following:
##

# nvnm-1
NVNMCHAIN_NET="$NVNMCHAIN_NET_BASE/nvnm-1"

# nvnm-testnet-1
NVNMCHAIN_NET="$NVNMCHAIN_NET_BASE/nvnm-testnet-1"
```

## Fetching Information

### Version

```sh
NVNMCHAIN_VERSION="$(curl -s "$NVNMCHAIN_NET/version.txt")"
```

### Chain ID

```sh
NVNMCHAIN_CHAIN_ID="$(curl -s "$NVNMCHAIN_NET/chain-id.txt")"
```

### Genesis

```sh
curl -s "$NVNMCHAIN_NET/genesis.json" > genesis.json
```

### Seed Nodes

```sh
curl -s "$NVNMCHAIN_NET/seed-nodes.txt" | paste -d, -s
```

### RPC Node

Print a random RPC endpoint

```sh
curl -s "$NVNMCHAIN_NET/rpc-nodes.txt" | shuf -n 1
```

### EVM RPC Node

Print a random RPC endpoint

```sh
curl -s "$NVNMCHAIN_NET/evm-rpc-nodes.txt" | shuf -n 1
```

### API Node

Print a random API endpoint

```sh
curl -s "$NVNMCHAIN_NET/api-nodes.txt" | shuf -n 1
```
