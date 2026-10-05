import argparse
import base64
import json
import os

import requests

from util import extract_public_key, verify_artifact_signature
from merkle_proof import DefaultHasher, verify_consistency, verify_inclusion, compute_leaf_hash

# Public Rekor instance used by cosign / sigstore.
REKOR_API_BASE = "https://rekor.sigstore.dev/api/v1"
REQUEST_TIMEOUT = 30


def get_log_entry(log_index, debug=False):
    # verify that log index value is sane
    if log_index is None or int(log_index) < 0:
        raise ValueError("log index must be a non-negative integer")

    url = f"{REKOR_API_BASE}/log/entries"
    response = requests.get(url, params={"logIndex": int(log_index)},
                            timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    # The response is a JSON object keyed by the entry UUID. For a single
    # logIndex query there is exactly one entry, so return its value.
    data = response.json()
    uuid, entry = next(iter(data.items()))
    if debug:
        print("fetched log entry")
        print("  uuid:", uuid)
        print("  logIndex:", entry.get("logIndex"))
    return entry


def get_verification_proof(log_index, debug=False):
    # verify that log index value is sane
    if log_index is None or int(log_index) < 0:
        raise ValueError("log index must be a non-negative integer")

    entry = get_log_entry(log_index, debug)

    # Leaf hash is computed from the canonical (base64) entry body per RFC 6962.
    leaf_hash = compute_leaf_hash(entry["body"])

    inclusion_proof = entry["verification"]["inclusionProof"]
    proof = {
        "index": inclusion_proof["logIndex"],
        "tree_size": inclusion_proof["treeSize"],
        "leaf_hash": leaf_hash,
        "hashes": inclusion_proof["hashes"],
        "root_hash": inclusion_proof["rootHash"],
    }
    if debug:
        print("verification proof:")
        print("  leaf index in tree:", proof["index"])
        print("  tree size:", proof["tree_size"])
        print("  leaf hash:", proof["leaf_hash"])
        print("  root hash:", proof["root_hash"])
    return proof


def inclusion(log_index, artifact_filepath, debug=False):
    # verify that log index and artifact filepath values are sane
    if log_index is None or int(log_index) < 0:
        raise ValueError("log index must be a non-negative integer")
    if not artifact_filepath or not os.path.isfile(artifact_filepath):
        raise ValueError(f"artifact filepath is not a valid file: {artifact_filepath!r}")

    entry = get_log_entry(log_index, debug)

    # The body is base64-encoded JSON describing a hashedrekord entry. From it
    # we pull the detached signature and the signing certificate (both base64).
    body = json.loads(base64.b64decode(entry["body"]))
    signature_b64 = body["spec"]["signature"]["content"]
    certificate_b64 = body["spec"]["signature"]["publicKey"]["content"]

    signature = base64.b64decode(signature_b64)
    certificate = base64.b64decode(certificate_b64)

    # Extract the public key from the certificate, then verify the artifact
    # signature against it.
    public_key = extract_public_key(certificate)
    if debug:
        print("extracted public key from certificate")
    verify_artifact_signature(signature, public_key, artifact_filepath)
    print("Signature is valid.")

    # Verify the inclusion proof: recompute the Merkle root from the leaf hash
    # and the audit path, and compare it to the published root hash.
    proof = get_verification_proof(log_index, debug)
    verify_inclusion(
        DefaultHasher,
        proof["index"],
        proof["tree_size"],
        proof["leaf_hash"],
        proof["hashes"],
        proof["root_hash"],
        debug,
    )
    print("Offline root hash calculation for inclusion verified.")


def get_latest_checkpoint(debug=False):
    # Fetch the latest checkpoint (signed tree head) from rekor.
    url = f"{REKOR_API_BASE}/log"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    checkpoint = response.json()

    if debug:
        print("latest checkpoint:")
        print("  treeID:", checkpoint.get("treeID"))
        print("  treeSize:", checkpoint.get("treeSize"))
        print("  rootHash:", checkpoint.get("rootHash"))
        with open("checkpoint.json", "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=4)
        print("  saved to checkpoint.json")
    return checkpoint


def consistency(prev_checkpoint, debug=False):
    # verify that prev checkpoint is not empty
    if not prev_checkpoint:
        raise ValueError("previous checkpoint must not be empty")
    for key in ("treeID", "treeSize", "rootHash"):
        if not prev_checkpoint.get(key):
            raise ValueError(f"previous checkpoint is missing {key}")

    latest = get_latest_checkpoint(debug)

    size1 = int(prev_checkpoint["treeSize"])
    size2 = int(latest["treeSize"])
    tree_id = prev_checkpoint["treeID"]

    # Obtain the consistency proof between the two tree sizes from Rekor.
    url = f"{REKOR_API_BASE}/log/proof"
    response = requests.get(
        url,
        params={"firstSize": size1, "lastSize": size2, "treeID": tree_id},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    proof = response.json()["hashes"]

    root1 = prev_checkpoint["rootHash"]
    root2 = latest["rootHash"]

    if debug:
        print("consistency proof:")
        print("  size1:", size1, "size2:", size2)
        print("  proof hashes:", len(proof))

    # Raises on mismatch; returns None on success.
    verify_consistency(DefaultHasher, size1, size2, proof, root1, root2)
    print("Consistency verification successful.")


def main():
    debug = False
    parser = argparse.ArgumentParser(description="Rekor Verifier")
    parser.add_argument('-d', '--debug', help='Debug mode',
                        required=False, action='store_true') # Default false
    parser.add_argument('-c', '--checkpoint', help='Obtain latest checkpoint\
                        from Rekor Server public instance',
                        required=False, action='store_true')
    parser.add_argument('--inclusion', help='Verify inclusion of an\
                        entry in the Rekor Transparency Log using log index\
                        and artifact filename.\
                        Usage: --inclusion 126574567',
                        required=False, type=int)
    parser.add_argument('--artifact', help='Artifact filepath for verifying\
                        signature',
                        required=False)
    parser.add_argument('--consistency', help='Verify consistency of a given\
                        checkpoint with the latest checkpoint.',
                        action='store_true')
    parser.add_argument('--tree-id', help='Tree ID for consistency proof',
                        required=False)
    parser.add_argument('--tree-size', help='Tree size for consistency proof',
                        required=False, type=int)
    parser.add_argument('--root-hash', help='Root hash for consistency proof',
                        required=False)
    args = parser.parse_args()
    if args.debug:
        debug = True
        print("enabled debug mode")
    if args.checkpoint:
        # get and print latest checkpoint from server
        # if debug is enabled, store it in a file checkpoint.json
        checkpoint = get_latest_checkpoint(debug)
        print(json.dumps(checkpoint, indent=4))
    if args.inclusion is not None:
        inclusion(args.inclusion, args.artifact, debug)
    if args.consistency:
        if not args.tree_id:
            print("please specify tree id for prev checkpoint")
            return
        if not args.tree_size:
            print("please specify tree size for prev checkpoint")
            return
        if not args.root_hash:
            print("please specify root hash for prev checkpoint")
            return

        prev_checkpoint = {}
        prev_checkpoint["treeID"] = args.tree_id
        prev_checkpoint["treeSize"] = args.tree_size
        prev_checkpoint["rootHash"] = args.root_hash

        consistency(prev_checkpoint, debug)

if __name__ == "__main__":
    main()
