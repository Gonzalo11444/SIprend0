-- Tabla para Twitch
CREATE TABLE IF NOT EXISTS twitch_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    followers INT,
    viewers INT,
    stream_online BOOLEAN,
    total_views INT,
    title TEXT
);


-- Tabla para YouTube
CREATE TABLE youtube_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    subscribers INTEGER,
    views_total INTEGER,
    latest_video_title TEXT
);
