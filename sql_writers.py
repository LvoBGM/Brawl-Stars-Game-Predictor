import sqlite3

def setup_matches_database(db_path="matches.db"):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()

    # Table for storing player performance per match
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            battle_time TEXT,
            event_id INTEGER,
            event_mode TEXT,
            event_map TEXT,
            battle_type TEXT,
            battle_result TEXT,
            battle_duration INTEGER,
            battle_star_player_tag TEXT
                );
            """)

    con.commit()
    return con