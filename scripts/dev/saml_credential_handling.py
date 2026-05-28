#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "boto3",
#     "botocore",
#     "requests",
#     "pyquery",
#     "requests-kerberos",
# ]
# ///
import json
import sys
import boto3
import botocore
import requests
from pyquery import PyQuery as pq
from requests_kerberos import OPTIONAL, HTTPKerberosAuth

SAML_URL = "https://auth.redhat.com/auth/realms/EmployeeIDP/protocol/saml/clients/itaws"


def get_saml_token(saml_url):
    try:
        with requests.Session() as session:
            session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
            r = session.get(saml_url)
            r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise RuntimeError(
                "Kerberos authentication failed. Do you have a valid Kerberos ticket?"
            ) from e
        raise
    p = pq(r.text).xhtml_to_html()
    form = p("form")
    saml_token = form("input:hidden").attr("value")
    return saml_token


def main():
    if len(sys.argv) < 3:
        print("Usage: saml-credential-process.py <account_id> <role_name> [region] [duration_seconds]", file=sys.stderr)
        sys.exit(1)

    account_id = sys.argv[1]
    role_name = sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"
    duration_seconds = int(sys.argv[4]) if len(sys.argv) > 4 else 3600

    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    principal_arn = f"arn:aws:iam::{account_id}:saml-provider/RedHatInternal"

    try:
        saml_token = get_saml_token(SAML_URL)

        sts = boto3.client(
            "sts",
            config=botocore.config.Config(signature_version=botocore.UNSIGNED),
            region_name=region,
        )
        response = sts.assume_role_with_saml(
            RoleArn=role_arn,
            PrincipalArn=principal_arn,
            SAMLAssertion=saml_token,
            DurationSeconds=duration_seconds,
        )

        creds = response["Credentials"]
        output = {
            "Version": 1,
            "AccessKeyId": creds["AccessKeyId"],
            "SecretAccessKey": creds["SecretAccessKey"],
            "SessionToken": creds["SessionToken"],
            "Expiration": creds["Expiration"].isoformat(),
        }
        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
