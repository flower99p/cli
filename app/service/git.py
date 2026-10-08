import os
import re
import subprocess
import requests
import xml.etree.ElementTree as ET

DEFAULT_OWNER = "flower99p"
DEFAULT_REPO = "cli"
DEFAULT_BRANCH = "main"


def get_repo_context():
    """Return GitHub owner/repo/branch from git remote when available."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        remote_url = ""

    if remote_url:
        match = re.search(r"github\.com[:/](.+?)/([^/.]+?)(?:\.git)?$", remote_url)
        if match:
            owner, repo = match.groups()
            try:
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip() or DEFAULT_BRANCH
            except Exception:
                branch = DEFAULT_BRANCH
            return owner, repo, branch

    owner = os.getenv("GITHUB_OWNER", DEFAULT_OWNER)
    repo = os.getenv("GITHUB_REPO", DEFAULT_REPO)
    branch = os.getenv("GITHUB_BRANCH", DEFAULT_BRANCH)
    return owner, repo, branch


def get_local_commit():
    """Return current local commit hash, or None if not in a git repo."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def get_latest_commit_atom():
    """Return the latest commit SHA from GitHub via the Atom feed (no auth)."""
    owner, repo, branch = get_repo_context()
    url = f"https://github.com/{owner}/{repo}/commits/{branch}.atom"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        return None
    entry_id = entry.find("a:id", ns)
    if entry_id is None or not entry_id.text:
        return None
    return entry_id.text.rsplit("/", 1)[-1]


def check_for_updates():
    local = get_local_commit()
    try:
        remote = get_latest_commit_atom()
    except Exception:
        remote = None

    if not remote:
        return False

    if not local:
        return False

    if local != remote:
        print(f"⚠️  A newer version is available (remote {remote[:7]} vs local {local[:7]}).")
        print("   Run: git pull --rebase to update.")
        return True
    return False
