# $NETWORK Upgrade Guide: From Version $CURRENT_VERSION to $UPGRADE_VERSION

## Overview

- **$UPGRADE_VERSION Proposal**: [Proposal Page](https://explorer.mantrachain.io/$EXPLORER_NETWORK/proposals/$PROPOSAL_ID)
- **$UPGRADE_VERSION Upgrade Block Height**: $UPGRADE_BLOCK
- **$UPGRADE_VERSION Upgrade Countdown**: [Block Countdown](https://explorer.mantrachain.io/$EXPLORER_NETWORK/blocks/$UPGRADE_BLOCK)
- **$UPGRADE_VERSION Release**: [Release Page](https://github.com/NVNM-Chain/nvnmchain/releases/tag/v$UPGRADE_TAG_NUM)
- **$UPGRADE_VERSION Docker Image**: [ghcr.io/nvnm-chain/nvnmchain:v$UPGRADE_TAG_NUM](https://github.com/nvnm-chain/nvnmchain/pkgs/container/nvnmchain)

> **Reminder:** NVNM Chain is a Layer 2 consumer chain. Before upgrading the L2
> `nvnmchaind` binary, ensure your MANTRA Chain L1 provider node is healthy and
> running a compatible version.

## Hardware Requirements

### Memory Specifications

Although this upgrade is not expected to be resource-intensive, a minimum of 32GB of RAM is advised. If you cannot meet this requirement, setting up a swap space is recommended.

#### Configuring Swap Space

_Execute these commands to set up a 32GB swap space_:

```sh
sudo swapoff -a
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

_To ensure the swap space persists after reboot_:

```sh
sudo cp /etc/fstab /etc/fstab.bak
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

For an in-depth guide on swap configuration, please refer to [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04).

---

## Cosmovisor Configuration

### Initial Setup (For First-Time Users)

If you have not previously configured Cosmovisor, follow this section; otherwise, proceed to the next section.

Cosmovisor is strongly recommended for validators to minimize downtime during upgrades. It automates the binary replacement process according to on-chain `SoftwareUpgrade` proposals.

Documentation for Cosmovisor can be found [here](https://docs.cosmos.network/main/tooling/cosmovisor).

#### Installation Steps

_Run these commands to install and configure Cosmovisor_:


```sh
go install github.com/cosmos/cosmos-sdk/cosmovisor/cmd/cosmovisor@v1.6.0
mkdir -p ~/.nvnmchain
mkdir -p ~/.nvnmchain/cosmovisor
mkdir -p ~/.nvnmchain/cosmovisor/genesis
mkdir -p ~/.nvnmchain/cosmovisor/genesis/bin
mkdir -p ~/.nvnmchain/cosmovisor/upgrades
cp $GOPATH/bin/nvnmchaind ~/.nvnmchain/cosmovisor/genesis/bin
```

_Add these lines to your profile to set up environment variables_:

```sh
echo "# Setup Cosmovisor" >> ~/.profile
echo "export DAEMON_NAME=nvnmchaind" >> ~/.profile
echo "export DAEMON_HOME=$HOME/.nvnmchain" >> ~/.profile
echo "export DAEMON_ALLOW_DOWNLOAD_BINARIES=false" >> ~/.profile
echo "export DAEMON_LOG_BUFFER_SIZE=512" >> ~/.profile
echo "export DAEMON_RESTART_AFTER_UPGRADE=true" >> ~/.profile
echo "export UNSAFE_SKIP_BACKUP=true" >> ~/.profile
source ~/.profile
```

### Upgrading to $UPGRADE_VERSION

_To prepare for the upgrade, execute these commands_:

#### Approach 1: Download Pre-built Release

```sh
upgrade_version="$UPGRADE_TAG_NUM"
upgrade_name="$UPGRADE_VERSION"
mkdir -p ~/.nvnmchain/cosmovisor/upgrades/$upgrade_name/bin
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/NVNM-Chain/nvnmchain/releases/download/v$upgrade_version/nvnmchaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf nvnmchaind-$upgrade_version-$OS-$ARCH.tar.gz -C ~/.nvnmchain/cosmovisor/upgrades/$upgrade_name/bin
rm nvnmchaind-$upgrade_version-$OS-$ARCH.tar.gz
```

#### Approach 2: Build from Source

```sh
upgrade_version="$UPGRADE_TAG_NUM"
upgrade_name="$UPGRADE_VERSION"
mkdir -p ~/.nvnmchain/cosmovisor/upgrades/$upgrade_name/bin
cd $HOME/nvnmchain
git fetch --tags
git checkout v$upgrade_version
make build
cp build/nvnmchaind ~/.nvnmchain/cosmovisor/upgrades/$upgrade_name/bin
```

At the designated block height, Cosmovisor will automatically upgrade to version $UPGRADE_VERSION.

---

## Manual Upgrade Procedure

Follow these steps if you opt for a manual upgrade:

1. Monitor nvnmchaind until it reaches the specified upgrade block height: $UPGRADE_BLOCK.
2. Observe for a panic message followed by continuous peer logs, then halt the daemon.
3. Perform these steps:

### Approach 1: Download Pre-built Release

```sh
upgrade_version="$UPGRADE_TAG_NUM"
upgrade_name="$UPGRADE_VERSION"
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/NVNM-Chain/nvnmchain/releases/download/v$upgrade_version/nvnmchaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf nvnmchaind-$upgrade_version-$OS-$ARCH.tar.gz -C $GOPATH/bin
```

### Approach 2: Build from Source

```sh
upgrade_version="$UPGRADE_TAG_NUM"
cd $HOME/nvnmchain
git fetch --tags
git checkout v$upgrade_version
make install
```

4. Restart the nvnmchaind daemon and observe the upgrade.

---

## Additional Resources

If you need more help, please:

- go to <https://docs.nvnmchain.io>
- reach out to the NVNM Chain team.
