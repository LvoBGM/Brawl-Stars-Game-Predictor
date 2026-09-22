import sqlite3

def setup_database(DB_PATH):
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()

    # Enable key restraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table for match data
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

    # Table for player performace in a match data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            player_tag TEXT,
            player_name TEXT,
            team_index INTEGER,
            brawler_id INTEGER,
            brawler_name TEXT,
            brawler_power INTEGER,
            brawler_trophies INTEGER,
            player_trophies INTEGER,
            player_highest_trophies INTEGER,
            player_3vs3_victories INTEGER,
            player_solo_victories INTEGER,
            player_duo_victories INTEGER,
            player_exp_level INTEGER,
            player_total_prestige_level INTEGER,
            player_ranked_elo INTEGER,
            player_highest_ranked_elo INTEGER,
            FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
        );
    """)

    con.commit()
    con.close()

