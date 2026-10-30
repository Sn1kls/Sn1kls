"""Rewrite the "Recently shipped" section of README.md from my merged pull requests."""

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "Sn1kls"
LIMIT = 6
README = Path(__file__).parent / "README.md"
SECTION = re.compile(r"(<!-- recent_start -->\n).*?(<!-- recent_end -->)", re.DOTALL)


def fetch_merged_pull_requests() -> list[dict]:
    query = f"is:pr is:merged is:public author:{USER} user:{USER} -repo:{USER}/{USER}"
    params = urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": 30})
    request = urllib.request.Request(f"https://api.github.com/search/issues?{params}")
    request.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        items = json.load(response)["items"]
    items.sort(key=lambda item: item["pull_request"]["merged_at"], reverse=True)
    return items[:LIMIT]


def render(pull_requests: list[dict]) -> str:
    lines = []
    for pull_request in pull_requests:
        repository = pull_request["repository_url"].rsplit("/", 1)[-1]
        merged = datetime.fromisoformat(pull_request["pull_request"]["merged_at"].replace("Z", "+00:00"))
        lines.append(
            f"- [{repository}](https://github.com/{USER}/{repository}): "
            f"[{pull_request['title']}]({pull_request['html_url']}), {merged:%d %b %Y}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    pull_requests = fetch_merged_pull_requests()
    if not pull_requests:
        return
    readme = README.read_text()
    README.write_text(SECTION.sub(lambda match: match[1] + render(pull_requests) + match[2], readme))


if __name__ == "__main__":
    main()
