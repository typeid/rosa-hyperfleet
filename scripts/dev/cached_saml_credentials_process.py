#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import subprocess


def get_cache_key(account_id, role_name, region):
    key_string = f"{account_id}-{role_name}-{region}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def get_cache_path(cache_key):
    cache_dir = Path.home() / ".aws" / "cli" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"saml-{cache_key}.json"


def is_cache_valid(cache_file):
    if not cache_file.exists():
        return False

    try:
        with open(cache_file) as f:
            cached = json.load(f)

        expiration = datetime.fromisoformat(cached["Expiration"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        time_remaining = (expiration - now).total_seconds()
        return time_remaining > 300
    except (json.JSONDecodeError, KeyError, ValueError):
        return False


def fetch_credentials(account_id, role_name, region, duration_seconds):
    script_path = Path(__file__).parent / "saml_credential_handling.py"
    cmd = [str(script_path), account_id, role_name, region, str(duration_seconds)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_msg = result.stderr.strip()
        try:
            error_data = json.loads(error_msg)
            error_msg = error_data.get("error", error_msg)
        except (json.JSONDecodeError, TypeError):
            pass
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def main():
    if len(sys.argv) < 3:
        print("Usage: cached-saml-credential-process.py <account_id> <role_name> [region] [duration_seconds]", file=sys.stderr)
        sys.exit(1)

    account_id = sys.argv[1]
    role_name = sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"
    duration_seconds = int(sys.argv[4]) if len(sys.argv) > 4 else 3600

    cache_key = get_cache_key(account_id, role_name, region)
    cache_file = get_cache_path(cache_key)

    if is_cache_valid(cache_file):
        with open(cache_file) as f:
            credentials = json.load(f)
        print(json.dumps(credentials))
    else:
        credentials = fetch_credentials(account_id, role_name, region, duration_seconds)

        with open(cache_file, 'w') as f:
            json.dump(credentials, f)

        print(json.dumps(credentials))


if __name__ == "__main__":
    main()
