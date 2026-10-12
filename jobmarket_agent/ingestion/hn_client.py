from dataclasses import dataclass

import requests

ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
ALGOLIA_ITEM_URL = "https://hn.algolia.com/api/v1/items"


@dataclass(frozen=True)
class HNComment:
    id: str
    text: str
    created_at: str


@dataclass(frozen=True)
class HNThread:
    story_id: str
    title: str
    created_at: str
    comments: list[HNComment]


def find_latest_hiring_thread() -> tuple[str, str]:
    params: dict[str, str | int] = {
        "query": "who is hiring",
        "tags": "story,author_whoishiring",
        "hitsPerPage": 10,
    }
    resp = requests.get(ALGOLIA_SEARCH_URL, params=params, timeout=10)
    resp.raise_for_status()

    hits = resp.json()["hits"]
    for hit in hits:
        if "who is hiring" in hit["title"].lower():
            return hit["objectID"], hit["title"]

    raise RuntimeError(f"No 'Who is hiring' thread found in {len(hits)} newest whoishiring posts")


def fetch_thread(story_id: str) -> HNThread:
    resp = requests.get(f"{ALGOLIA_ITEM_URL}/{story_id}", timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    comments: list[HNComment] = []
    for child in payload["children"]:
        # Deleted comments carry a null `text`; blank ones are not postings either.
        text = (child.get("text") or "").strip()
        created_at = child.get("created_at") or ""
        if not text:
            continue
        comments.append(HNComment(id=str(child["id"]), text=text, created_at=created_at))

    return HNThread(
        story_id=story_id,
        title=payload["title"],
        created_at=payload["created_at"],
        comments=comments,
    )


if __name__ == "__main__":
    story_id, _ = find_latest_hiring_thread()
    thread = fetch_thread(story_id)
    print(f"thread:   {thread.title}")
    print(f"story_id: {thread.story_id}")
    print(f"posted:   {thread.created_at}")
    print(f"comments: {len(thread.comments)}")
    print(f"verify:   https://news.ycombinator.com/item?id={thread.story_id}")
