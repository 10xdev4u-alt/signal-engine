CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    ref_type UNINDEXED,
    ref_id UNINDEXED,
    subreddit UNINDEXED,
    title,
    body,
    permalink UNINDEXED,
    created_utc UNINDEXED
);

CREATE TRIGGER IF NOT EXISTS posts_ai_fts AFTER INSERT ON posts BEGIN
    INSERT INTO search_index(ref_type, ref_id, subreddit, title, body, permalink, created_utc)
    VALUES('post', new.id, new.subreddit, new.title, new.selftext, new.permalink, new.created_utc);
END;

CREATE TRIGGER IF NOT EXISTS comments_ai_fts AFTER INSERT ON comments BEGIN
    INSERT INTO search_index(ref_type, ref_id, subreddit, title, body, permalink, created_utc)
    VALUES('comment', new.id, new.subreddit, '', new.body, new.permalink, new.created_utc);
END;
