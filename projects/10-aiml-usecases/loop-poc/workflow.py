import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import List

import requests
import psycopg2
from psycopg2.extras import execute_values
import anthropic
from flytekit import task, workflow, Secret

logger = logging.getLogger(__name__)

TWITTER_USER_ID = "25073877"
MAX_LOOP_ITERATIONS = 5
CONFIDENCE_THRESHOLD = 0.85
CLAUDE_MODEL = "claude-sonnet-4-6"

DB_DSN = os.environ.get("DATABASE_URL", "postgresql://localhost/tweets_db")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def get_db_conn():
    return psycopg2.connect(DB_DSN)


def ensure_schema(conn):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


@task
def fetch_tweets() -> List[int]:
    """Poll X API v2 filtered stream for Trump (user 25073877) and persist to Postgres."""
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}

    # Set up filtered stream rule for the target user
    rules_url = "https://api.twitter.com/2/tweets/search/stream/rules"
    existing = requests.get(rules_url, headers=headers, timeout=10).json()
    existing_ids = [r["id"] for r in existing.get("data", [])]
    if existing_ids:
        requests.post(
            rules_url,
            headers=headers,
            json={"delete": {"ids": existing_ids}},
            timeout=10,
        )
    requests.post(
        rules_url,
        headers=headers,
        json={"add": [{"value": f"from:{TWITTER_USER_ID}", "tag": "trump"}]},
        timeout=10,
    )

    tweet_fields = (
        "id,author_id,text,lang,referenced_tweets,public_metrics,created_at"
    )
    expansions = "author_id,referenced_tweets.id"
    user_fields = "username"
    stream_url = (
        f"https://api.twitter.com/2/tweets/search/stream"
        f"?tweet.fields={tweet_fields}&expansions={expansions}&user.fields={user_fields}"
    )

    conn = get_db_conn()
    ensure_schema(conn)

    tweet_ids: List[int] = []
    rows = []

    try:
        with requests.get(stream_url, headers=headers, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            deadline = time.time() + 60  # collect for 60 seconds
            for raw_line in resp.iter_lines():
                if time.time() > deadline:
                    break
                if not raw_line:
                    continue
                payload = json.loads(raw_line)
                tweet = payload.get("data", {})
                if not tweet:
                    continue

                includes = payload.get("includes", {})
                users = {u["id"]: u["username"] for u in includes.get("users", [])}
                ref_tweets = {t["id"]: t for t in includes.get("tweets", [])}

                referenced = tweet.get("referenced_tweets", [])
                ref_types = {r["type"] for r in referenced}
                is_retweet = "retweeted" in ref_types
                is_reply = "replied_to" in ref_types
                is_quote = "quoted" in ref_types
                in_reply_to = next(
                    (int(r["id"]) for r in referenced if r["type"] == "replied_to"), None
                )
                quoted_id = next(
                    (int(r["id"]) for r in referenced if r["type"] == "quoted"), None
                )

                metrics = tweet.get("public_metrics", {})
                author_id = int(tweet["author_id"])
                username = users.get(tweet["author_id"])
                tweeted_at = datetime.fromisoformat(
                    tweet["created_at"].replace("Z", "+00:00")
                )

                rows.append((
                    int(tweet["id"]),
                    author_id,
                    username,
                    tweet["text"],
                    tweet.get("lang"),
                    is_retweet,
                    is_reply,
                    is_quote,
                    in_reply_to,
                    quoted_id,
                    metrics.get("like_count", 0),
                    metrics.get("retweet_count", 0),
                    metrics.get("reply_count", 0),
                    metrics.get("quote_count", 0),
                    metrics.get("impression_count", 0),
                    tweeted_at,
                    datetime.now(timezone.utc),
                    json.dumps(payload),
                ))
                tweet_ids.append(int(tweet["id"]))
    except requests.exceptions.Timeout:
        logger.info("Stream timeout — proceeding with %d tweets collected", len(rows))

    if rows:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO tweets (
                    id, author_id, username, text, lang,
                    is_retweet, is_reply, is_quote,
                    in_reply_to_tweet_id, quoted_tweet_id,
                    likes, retweets, replies, quotes, impressions,
                    tweeted_at, fetched_at, raw_json
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING
                """,
                rows,
            )
        conn.commit()

    conn.close()
    logger.info("Stored %d new tweets", len(tweet_ids))
    return tweet_ids


def _loop_analysis_for_tweet(client: anthropic.Anthropic, tweet_text: str) -> tuple[str, int, float]:
    """Run the /loop self-refinement pattern for a single tweet.

    Returns (analysis, iterations_used, final_confidence).
    """
    system_prompt = (
        "You are a political analyst AI. Analyze tweets for sentiment, key topics, "
        "and political stance. After your analysis, you MUST end your response with "
        "a self-evaluation block in this exact format:\n\n"
        "CONFIDENCE: <float between 0.0 and 1.0>\n"
        "REASONING: <one sentence explaining your confidence score>\n\n"
        "Score 0.85+ only when you have clear evidence for all three dimensions "
        "(sentiment, topics, stance). Score lower when the tweet is ambiguous, "
        "lacks context, or you are uncertain about any dimension."
    )

    messages = [
        {
            "role": "user",
            "content": f"Analyze this tweet:\n\n{tweet_text}",
        }
    ]

    analysis = ""
    confidence = 0.0
    iterations = 0

    for iteration in range(1, MAX_LOOP_ITERATIONS + 1):
        iterations = iteration
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            thinking={"type": "adaptive"},
        )

        response_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Parse confidence from response
        confidence = 0.0
        for line in response_text.splitlines():
            if line.strip().startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
                break

        analysis = response_text

        if confidence >= CONFIDENCE_THRESHOLD:
            break

        # Re-prompt with previous answer as context
        messages.append({"role": "assistant", "content": response_text})
        messages.append({
            "role": "user",
            "content": (
                f"Your confidence was {confidence:.2f}, below the threshold of {CONFIDENCE_THRESHOLD}. "
                "Please refine your analysis. Look for additional signals in the tweet text, "
                "reconsider any ambiguous dimensions, and provide a more thorough assessment. "
                "Remember to end with the CONFIDENCE and REASONING lines."
            ),
        })

    return analysis, iterations, confidence


@task
def run_loop_analysis(tweet_ids: List[int]) -> None:
    """Run the /loop self-refinement Claude analysis on each tweet and persist results."""
    if not tweet_ids:
        logger.info("No tweets to analyze")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    conn = get_db_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, text FROM tweets WHERE id = ANY(%s) AND loop_analysis IS NULL",
                (tweet_ids,),
            )
            pending = cur.fetchall()

        logger.info("Analyzing %d tweets", len(pending))

        for tweet_id, tweet_text in pending:
            try:
                analysis, iterations, confidence = _loop_analysis_for_tweet(
                    client, tweet_text
                )
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE tweets
                        SET loop_analysis = %s,
                            loop_iterations = %s,
                            loop_confidence = %s
                        WHERE id = %s
                        """,
                        (analysis, iterations, confidence, tweet_id),
                    )
                conn.commit()
                logger.info(
                    "Tweet %s analyzed — iterations=%d confidence=%.2f",
                    tweet_id,
                    iterations,
                    confidence,
                )
            except Exception as exc:
                logger.error("Failed to analyze tweet %s: %s", tweet_id, exc)
                conn.rollback()
    finally:
        conn.close()


@workflow
def loop_poc_workflow() -> None:
    """Fetch tweets from Trump's account and run Claude /loop analysis on each."""
    tweet_ids = fetch_tweets()
    run_loop_analysis(tweet_ids=tweet_ids)
