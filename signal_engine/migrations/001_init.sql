CREATE TABLE IF NOT EXISTS subreddits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    group_name TEXT NOT NULL DEFAULT 'core',
    active INTEGER NOT NULL DEFAULT 1,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fetch_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('post_feed','comment_feed')),
    http_status INTEGER,
    bytes INTEGER,
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS posts(
    id TEXT PRIMARY KEY,
    subreddit TEXT NOT NULL REFERENCES subreddits(name),
    title TEXT NOT NULL,
    author TEXT,
    selftext TEXT NOT NULL DEFAULT '',
    permalink TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    etag TEXT,
    comments_done_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_sub_created ON posts(subreddit, created_utc);

CREATE TABLE IF NOT EXISTS comments(
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL REFERENCES posts(id),
    subreddit TEXT NOT NULL,
    author TEXT,
    body TEXT NOT NULL,
    permalink TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_sub_created ON comments(subreddit, created_utc);

CREATE TABLE IF NOT EXISTS phrase_stats(
    subreddit TEXT NOT NULL,
    phrase TEXT NOT NULL,
    day TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(subreddit, phrase, day)
);

CREATE TABLE IF NOT EXISTS pain_clusters(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    first_seen TEXT,
    last_seen TEXT,
    mention_count INTEGER NOT NULL DEFAULT 0,
    desperation_score REAL NOT NULL DEFAULT 0,
    caution_flag INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cluster_members(
    cluster_id INTEGER NOT NULL REFERENCES pain_clusters(id),
    ref_type TEXT NOT NULL CHECK(ref_type IN ('post','comment')),
    ref_id TEXT NOT NULL,
    quote TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    PRIMARY KEY(cluster_id, ref_type, ref_id)
);

CREATE TABLE IF NOT EXISTS intent_scores(
    ref_type TEXT NOT NULL CHECK(ref_type IN ('post','comment')),
    ref_id TEXT NOT NULL,
    heuristic_score INTEGER,
    llm_score INTEGER,
    scored_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY(ref_type, ref_id)
);

CREATE TABLE IF NOT EXISTS profiles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subreddit TEXT NOT NULL,
    snapshot_md TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS eval_marks(
    ref_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK(verdict IN ('real_problem','noise')),
    marked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY(ref_type, ref_id)
);

CREATE TABLE IF NOT EXISTS digests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    md TEXT NOT NULL,
    json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
