BEGIN;


CREATE TABLE IF NOT EXISTS games (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    white_player_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    black_player_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    winner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    moves_pgn TEXT,
    status VARCHAR(20) DEFAULT 'ongoing',
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    time_control VARCHAR(20) NOT NULL,
    result VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_games_white_player ON games(white_player_id);
CREATE INDEX IF NOT EXISTS idx_games_black_player ON games(black_player_id);

CREATE TABLE IF NOT EXISTS rating_history (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    date TIMESTAMPTZ DEFAULT now()
);

COMMIT;
