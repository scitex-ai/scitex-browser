"""Read-only protected-main/tag identity checks for Browser release jobs.

Requires Python 3.11+. This verifies remote source facts, not actor, runtime
admission or PyPI publisher trust. It never requests an OIDC token or uploads.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.request

REPOSITORY = "scitex-ai/scitex-browser"
TAG = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA = re.compile(r"[0-9a-f]{40}")

def api(path, status=200, *, open_url=urllib.request.urlopen):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com/" + path, headers=headers)
    with open_url(request, timeout=10) as response:
        if response.status != status:
            raise ValueError("GitHub identity response did not match")
        if status == 204:
            return {"status": 204}
        body = response.read(1048577)
        if len(body) > 1048576:
            raise ValueError("GitHub identity response too large")
        return json.loads(body)

def resolve(tag, query=api):
    if not TAG.fullmatch(tag):
        raise ValueError("release requires an existing vX.Y.Z tag")
    prefix = "repos/" + REPOSITORY
    before = query(prefix + "/branches/main")
    if (
        before.get("name") != "main"
        or before.get("protected") is not True
        or not SHA.fullmatch(before.get("commit", {}).get("sha", ""))
    ):
        raise ValueError("release main is not protected and qualified")
    main_commit = before["commit"]["sha"]
    ref = query(prefix + "/git/ref/tags/" + tag)
    if ref.get("ref") != "refs/tags/" + tag:
        raise ValueError("returned tag ref differs")
    item = ref["object"]
    tag_object = (item.get("type"), item.get("sha"))
    seen = set()
    for _ in range(5):
        digest = item.get("sha", "")
        if not SHA.fullmatch(digest) or digest in seen:
            raise ValueError("invalid or cyclic tag object")
        seen.add(digest)
        if item.get("type") == "commit":
            break
        if item.get("type") != "tag":
            raise ValueError("tag does not resolve to a commit")
        item = query(prefix + "/git/tags/" + digest)["object"]
    else:
        raise ValueError("tag annotation depth exceeded")
    commit = item["sha"]
    comparison = query(prefix + "/compare/" + commit + "..." + main_commit)
    if comparison.get("base_commit", {}).get("sha") != commit or comparison.get(
        "status"
    ) not in {"ahead", "identical"}:
        raise ValueError("release source has not been promoted to main")
    content = query(prefix + "/contents/pyproject.toml?ref=" + commit)
    if content.get("encoding") != "base64":
        raise ValueError("unsupported metadata encoding")
    raw = base64.b64decode(content["content"].replace("\n", ""), validate=True)
    if len(raw) > 131072 or hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest() != content.get("sha"):
        raise ValueError("release metadata Git identity differs")
    project = tomllib.loads(raw.decode())["project"]
    if (
        project["name"].replace("_", "-").lower() != "scitex-browser"
        or project["version"] != tag[1:]
    ):
        raise ValueError("tag and project metadata differ")
    after = query(prefix + "/branches/main")
    if (
        after.get("name") != "main"
        or after.get("protected") is not True
        or after.get("commit", {}).get("sha") != main_commit
    ):
        raise ValueError("release main changed during source qualification")
    final_ref = query(prefix + "/git/ref/tags/" + tag)
    if (
        final_ref.get("ref") != "refs/tags/" + tag
        or (
            final_ref.get("object", {}).get("type"),
            final_ref.get("object", {}).get("sha"),
        ) != tag_object
    ):
        raise ValueError("Release tag changed during source qualification")
    return {"tag": tag, "commit": commit, "version": tag[1:]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    if not SHA.fullmatch(args.commit):
        raise ValueError("Expected release source must be an immutable commit")
    identity = resolve(args.tag)
    if identity["commit"] != args.commit:
        raise ValueError("Remote tag and expected build source differ")
    json.dump(identity, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
