"""
# This script is modified and based on the script in https://github.com/osmosis-labs/osmosis/blob/main/scripts/release/create_binaries_json/create_binaries_json.py
Usage:
This script generates a JSON object containing binary download URLs and their corresponding checksums
for a given release tag of NVNM-Chain/nvnmchain or from a provided checksum URL.
The binary JSON is compatible with cosmovisor and with the chain registry.

You can run this script with the following commands:

❯ python create_binaries_json.py --chain_id nvnm-1 --checksums_url https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/sha256sum.txt

Output:
{
  "binaries": {
    "linux/amd64": "https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/nvnmchaind-1.1.0-linux-amd64.tar.gz?checksum=<checksum>",
    "linux/arm64": "https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/nvnmchaind-1.1.0-linux-arm64.tar.gz?checksum=<checksum>",
    "darwin/amd64": "https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/nvnmchaind-1.1.0-darwin-amd64.tar.gz?checksum=<checksum>",
    "darwin/arm64": "https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/nvnmchaind-1.1.0-darwin-arm64.tar.gz?checksum=<checksum>"
  }
}

Expects a checksum in the form:

<CHECKSUM>  nvnmchaind-<VERSION>-<OS>-<ARCH>[.tar.gz]
<CHECKSUM>  nvnmchaind-<VERSION>-<OS>-<ARCH>[.tar.gz]
...

Example:

6c310a2bec0ce599d2f0605c77e40869987bc92f5768999ea6896fd5ae57c547  nvnmchaind-1.1.0-linux-amd64
f34150fce9fa48812fcef24b303e22c858b47fead4b1db71bf72bee8b53e8a03  nvnmchaind-1.1.0-linux-amd64.tar.gz

(From: https://github.com/NVNM-Chain/nvnmchain/releases/download/v1.1.0/sha256sum.txt)

❯ python create_binaries_json.py --chain_id nvnm-1 --tag v1.1.0

Expect a checksum to be present at:
https://github.com/NVNM-Chain/nvnmchain/releases/download/<TAG>/sha256sum.txt
"""

import requests
import json
import argparse
import re
import os
import sys

def validate_chain_id(chain_id):
    return chain_id in ['nvnm-1', 'nvnm-testnet-1']

def validate_tag(tag):
    pattern = '^v[0-9]+.[0-9]+.[0-9]+(-rc[0-9]+)?$'
    return bool(re.match(pattern, tag))

def major_tag(tag, upgrade_version):
    if upgrade_version:
        return upgrade_version
    return tag.split('.')[0]

def download_checksums(checksums_url):

    response = requests.get(checksums_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch sha256sum.txt. Status code: {response.status_code}")
    return response.text

def checksums_to_binaries_json(checksums):

    binaries = {}

    # Parse the content and create the binaries dictionary
    for line in checksums.splitlines():
        checksum, filename = line.split('  ')

        # include only tar.gz files for nvnmchaind
        if filename.endswith('.tar.gz') and filename.startswith('nvnmchaind'):
            parts = filename.replace('.tar.gz', '').split('-')

            # Handle both regular versions and rc versions
            # nvnmchaind-X.Y.Z-platform-architecture.tar.gz
            # nvnmchaind-X.Y.Z-rcN-platform-architecture.tar.gz
            if len(parts) == 4:
                # Regular version
                _, tag, platform, arch = parts
            elif len(parts) == 5:
                # RC version (e.g., 1.0.0-rc0)
                _, version, rc, platform, arch = parts
                tag = f"{version}-{rc}"
            else:
                print(f"Error: Expected binary name in the form: nvnmchaind-X.Y.Z-platform-architecture.tar.gz or nvnmchaind-X.Y.Z-rcN-platform-architecture.tar.gz, but got {filename}")
                sys.exit(1)

            # exclude universal binaries and windows binaries
            if arch == 'all' or platform == 'windows':
                continue
            binaries[f"{platform}/{arch}"] = f"https://github.com/NVNM-Chain/nvnmchain/releases/download/v{tag}/{filename}?checksum=sha256:{checksum}"

    if not binaries:
        print("Error: No binaries found in the checksum file")
        sys.exit(1)

    # sort the binaries with linux first
    binaries = dict(sorted(binaries.items(), key=lambda item: item[0].split('/')[0] != 'linux'))

    binaries_json = {
        "binaries": binaries
    }

    return json.dumps(binaries_json, indent=2)

def main():

    parser = argparse.ArgumentParser(description="Create binaries json")
    parser.add_argument('--chain_id', metavar='chain_id', type=str, required=True, help='The Chain ID for which the binaries JSON is being generated (e.g., nvnm-1|nvnm-testnet-1)')
    parser.add_argument('--tag', metavar='tag', type=str, help='the tag to use (e.g v1.1.0)')
    parser.add_argument('--checksums_url', metavar='checksums_url', type=str, help='URL to the checksum')
    parser.add_argument('--upgrade_version', metavar='upgrade_version', type=str, help='Upgrade version for output directory (optional)')

    args = parser.parse_args()

    # Treat empty strings as None
    tag = args.tag if args.tag else None
    checksums_url = args.checksums_url if args.checksums_url else None
    upgrade_version = args.upgrade_version if args.upgrade_version else None

    # Validate the tag format
    if tag and not validate_tag(tag):
        print("Error: The provided tag does not follow the 'vX.Y.Z' format.")
        sys.exit(1)

    if not validate_chain_id(args.chain_id):
        print("Error: The provided chain_id is invalid.")
        sys.exit(1)

    # Require at least one of --tag or --checksums_url
    if not tag and not checksums_url:
        parser.error("Provide at least one of --tag or --checksums_url")
        sys.exit(1)

    # Also require either --tag or --upgrade_version to determine the output directory
    if not (tag or upgrade_version):
        parser.error("Either --tag or --upgrade_version must be provided to determine the output directory.")
        sys.exit(1)

    checksums_url = checksums_url if checksums_url else f"https://github.com/NVNM-Chain/nvnmchain/releases/download/{tag}/sha256sum.txt"
    checksums = download_checksums(checksums_url)
    binaries_json = checksums_to_binaries_json(checksums)
    print(binaries_json)

    # Write the filled template to a file
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', args.chain_id, 'upgrades', major_tag(tag, upgrade_version))

    os.makedirs(output_directory, exist_ok=True)

    output_file_path = os.path.join(output_directory, f'cosmovisor.json')

    with open(output_file_path, 'w') as output_file:
        output_file.write(binaries_json)

    print(f"Binaries JSON generated at: {output_file_path}")

if __name__ == "__main__":
    main()
