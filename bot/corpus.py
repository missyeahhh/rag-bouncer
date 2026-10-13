"""Ghost documentation, fetched at run time and never copied into this repo.

The docs are not openly licensed, so the bot reads them from GitHub pinned to one
commit of TryGhost/Docs. Pinning keeps the eval stable: a score only moves when
the bot changes, not when Ghost edits its docs.
"""
import re
import urllib.request
from pathlib import Path

DOCS_SHA = "f9467f79902f2d35b7a18210b3d875c471b660d5"
RAW = "https://raw.githubusercontent.com/TryGhost/Docs/{sha}/{path}"
SOURCE = "https://github.com/TryGhost/Docs/blob/{sha}/{path}"
CACHE = Path(__file__).resolve().parent.parent / ".cache" / "docs" / DOCS_SHA

PAGES = [
    "config.mdx", "ghost-cli.mdx", "hosting.mdx",
    "install/ubuntu.mdx", "install/local.mdx", "install/docker.mdx",
    "faq/api-versioning.mdx", "faq/clustering-sharding-multi-server.mdx",
    "faq/digitalocean-smtp-blocked.mdx", "faq/errors-running-ghost-start.mdx",
    "faq/image-upload-issues.mdx", "faq/mail-config-error-google-cloud.mdx",
    "faq/mailgun-newsletters.mdx", "faq/major-versions-lts.mdx",
    "faq/manual-backup.mdx", "faq/missing-ssl-protocol.mdx",
    "faq/node-versions.mdx", "faq/proxying-https-infinite-loops.mdx",
    "faq/root-user-fix.mdx", "faq/supported-databases.mdx",
    "faq/supported-hosting-providers.mdx", "faq/translation.mdx",
    "faq/troubleshooting-mysql-database.mdx",
    "faq/unable-to-open-sqlite3-database-file.mdx",
    "faq/using-cloudflare-with-ghost.mdx", "faq/using-nvm.mdx",
]

MAX_CHARS = 1500


def _fetch(path):
    cached = CACHE / path
    if cached.exists():
        return cached.read_text()
    with urllib.request.urlopen(RAW.format(sha=DOCS_SHA, path=path), timeout=30) as r:
        text = r.read().decode("utf-8")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(text)
    return text


def load_chunks():
    """One chunk per section of each page, with the URL it came from."""
    chunks = []
    for path in PAGES:
        raw = _fetch(path)
        title = re.search(r'^title:\s*"?(.*?)"?\s*$', raw, flags=re.M)
        title = title.group(1) if title else path
        summary = re.search(r'^description:\s*"?(.*?)"?\s*$', raw, flags=re.M)
        if summary:
            # Some pages state the answer only in their front matter description.
            title = f"{title}\n\n{summary.group(1)}"
        text = re.sub(r"\A---.*?---\s*", "", raw, flags=re.S)
        for section in re.split(r"\n(?=## )", text):
            section = section.strip()
            for i in range(0, len(section), MAX_CHARS):
                part = section[i:i + MAX_CHARS].strip()
                if len(part) > 40:
                    # The page title goes in every chunk: many sections never repeat the topic.
                    chunks.append({"text": f"# {title}\n\n{part}", "source": SOURCE.format(sha=DOCS_SHA, path=path)})
    return chunks
