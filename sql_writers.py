import sqlite3

TRUE_BLUE_RESULT_MAP = {
    "victory": 1,
    "draw": 0,
    "defeat": -1
}

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

def write_match_to_database(DB_PATH, match_tags, match, players_info, player_tag):
    """Writes all data from a given match to the sql databaswe
    DB_PATH - file path to the db file
    match_tags - player tags in match in order (first 3 are true blue)
    match - information about the match
    players_info[tag] - information about specific players
    player_tag - tag of the players from whose battlelog this match was scraped
    """

    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        battle = match.get("battle", {})
        event = match.get("event", {})
        battle_time = match["battleTime"]

        # Generage Match ID
        match_id = f"{battle_time}_{''.join(sorted(match_tags))}"

        # Determine game result
        raw_result = battle.get("result")
        match_result = 0
        if raw_result in TRUE_BLUE_RESULT_MAP:
            if player_tag in match_tags[:3]:
                match_result = TRUE_BLUE_RESULT_MAP[raw_result]
            else:
                match_result = -TRUE_BLUE_RESULT_MAP[raw_result]

        # Insert into `matches` table
        cursor.execute("""
            INSERT OR IGNORE INTO matches (
                match_id, battle_time, event_id, event_mode, event_map,
                battle_type, battle_result, battle_duration, battle_star_player_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            battle_time,
            event["id"],
            event["mode"],
            event["map"],
            battle["type"],
            match_result,  # Stores 1 (Blue Win), -1 (Red Win), 0 (Draw)
            battle["duration"],
            battle["starPlayer"]["tag"]
        ))

        # Insert data for each player into `match_players` table
        teams = battle.get("teams", [])
        for i, tag in enumerate(match_tags):
            in_blue_team = tag in match_tags[:3]
            team_index = 0 if in_blue_team else 1
            player_index = i if in_blue_team else i - 3

            player_data = {}
            if team_index < len(teams) and player_index < len(teams[team_index]):
                player_data = teams[team_index][player_index]

            brawler = player_data.get("brawler", {})
            player_profile = players_info.get(tag, {}) if players_info else {}

            cursor.execute("""
                INSERT INTO match_players (
                    match_id, player_tag, player_name, team_index,
                    brawler_id, brawler_name, brawler_power, brawler_trophies,
                    player_trophies, player_highest_trophies, player_3vs3_victories,
                    player_solo_victories, player_duo_victories, player_exp_level,
                    player_total_prestige_level, player_ranked_elo, player_highest_ranked_elo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                tag,
                player_data["name"],
                team_index,
                brawler["id"],
                brawler["name"],
                brawler["power"],
                brawler["trophies"],
                player_profile["trophies"],
                player_profile["highestTrophies"],
                player_profile["3vs3Victories"],
                player_profile["soloVictories"],
                player_profile["duoVictories"],
                player_profile["expLevel"],
                player_profile["totalPrestigeLevel"],
                player_profile["rankedElo"],
                player_profile["highestAllTimeRankedElo"],
            ))

        con.commit()

    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()
