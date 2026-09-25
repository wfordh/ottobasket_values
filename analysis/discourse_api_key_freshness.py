import logging
import os

from fluent_discourse import Discourse  # type: ignore

logging.basicConfig(level=logging.INFO)


def main():
    logging.info("Creating the Discourse client object.")
    client = Discourse(
        base_url="https://community.ottoneu.com",
        username="higginsford",
        api_key=os.environ.get("DISCOURSE_API_KEY", None),
    )

    assert client.api_key

    topic_id = 15812
    content = "This is a test post to keep the Discourse API key from rotating. You can ignore it."

    data = {"topic_id": topic_id, "raw": content}
    logging.info("Posting to Discourse")
    client.posts.json.post(data)


if __name__ == "__main__":
    main()
