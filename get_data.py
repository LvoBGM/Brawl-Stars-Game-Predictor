import requests
import os
import httpx
import asyncio
from dotenv import load_dotenv
from collections import deque
from csv_data_writters import write_match_data_1

load_dotenv()

API_KEY = os.getenv("API_KEY")
CSV_FILE = "data.csv"
STARTING_TAG = os.getenv("TAG")

PLAYER_DATA_COUNT = 10

def main():
    asyncio.run(scrape_data(STARTING_TAG, API_KEY, players_to_check=1, game_mode="brawlBall")) # map_name="Goalies"

async def scrape_data(starting_tag, key, players_to_check, game_mode=None, map_name=None):
    """
    Scrapes battle logs from the Brawl Stars API, iterating through players
    they played with to gather a dataset of unique matches.
    """
    
    if starting_tag[0] != "#":
        print(f"Starting tag should be in format #S0MELETTER5. Your input: {starting_tag}")
        return

    headers = {
        "Authorization": f"Bearer {key}"
    }
    
    checked_players = set()
    checked_matches = set()
    
    # A queue to hold players we need to check (FIFO)
    player_queue = deque([starting_tag])

    players_scraped = 0
    
    print(f"Starting scrape. Target: {players_to_check} players.")
    async with httpx.AsyncClient() as client:
        while player_queue and players_scraped < players_to_check:
            # Get the next player in the queue
            current_tag = player_queue.popleft()

            # Format the tag
            formatted_tag = current_tag.replace("#", "%23")

            url = f"https://api.brawlstars.com/v1/players/{formatted_tag}/battlelog"

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Skipping {current_tag} - API Error (Status: {response.status_code})")
                continue

            battle_log = response.json().get("items", [])

            # Mark player as checked and increment our counter
            checked_players.add(current_tag)
            players_scraped += 1
            print(f"[{players_scraped}/{players_to_check}] Scraped player log: {current_tag}")

            matches_to_fetch = []
            for match in battle_log:
                event = match.get("event", {})
                battle = match.get("battle", {})

                match_mode = event.get("mode")
                match_map = event.get("map")
                battle_time = match.get("battleTime")

                # Filter by game mode and map (if provided)
                if game_mode and match_mode != game_mode:
                    continue
                if map_name and match_map != map_name:
                    continue

                # Extract player tags from the match
                match_player_tags = []
                if "teams" in battle:
                    for team in battle["teams"]:
                        for p in team:
                            match_player_tags.append(p["tag"])
                elif "players" in battle:
                    for p in battle["players"]:
                        match_player_tags.append(p["tag"])

                # Check for duplicate matches
                unique_match_id = f"{battle_time}_{''.join(sorted(match_player_tags))}"

                if unique_match_id not in checked_matches:
                    # New match found! Mark it and write it.
                    matches_to_fetch.append(match)
                    checked_matches.add(unique_match_id)

                # Add newly discovered players to our queue
                for tag in match_player_tags:
                    if tag not in checked_players and tag not in player_queue:
                        player_queue.append(tag)

            # Get all player information we will need
            battlelog_players = await get_battlelog_info(client, matches_to_fetch, headers)

            write_battlelog_info(matches_to_fetch, battlelog_players, current_tag)
            
                    
    print("\nScrape complete!")
    print(f"Total unique matches written: {len(checked_matches)}")

async def get_battlelog_info(client, battlelog, headers):
    """Takes in an async client, battlelog and headers.
    Returns a dictionary, whose keys are tags, that contains all matches and player information from the battlelog.
    Also removes matches with broken tags from battlelog
    """
    unique_tags = set()
    players_info = {}

    # Get all tags from the battle log
    broken_matches = []
    for match in battlelog:
        match_tags = set()
        battle = match['battle']

        # Differ between 3v3 and Showdown matches
        if "teams" in battle:
            for team in battle["teams"]:
                for player in team:
                    if player["tag"] not in unique_tags:
                        match_tags.add(player["tag"])
                        unique_tags.add(player["tag"])
        elif "players" in battle:
            for player in battle["players"]:
                if player["tag"] not in unique_tags:
                    match_tags.add(player["tag"])
                    unique_tags.add(player["tag"])

        # Make a list of dicts containing all info about the 6-10 players in a match
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for tag in match_tags:
                task = tg.create_task(get_player_info(client, tag, headers))
                tasks.append(task)

        match_player_info = {}
        fail = False
        for task in tasks:
            result = task.result()
            if result is None:
                print(f"Match has broken tag! Skipping match...")
                if match not in broken_matches:
                    broken_matches.append(match)
                fail = True
                continue
            match_player_info[result["tag"]] = result
        if not fail:
            players_info.update(match_player_info)

    for match in broken_matches:
        battlelog.remove(match)
    
    return players_info

def write_battlelog_info(battlelog, players_info, player_tag):
    """Write the wanted information from the battlelog into the data csv file"""
    for match in battlelog:
        players = []
        tags = []

        # Brawl Stars API structure splits players into 'teams' (3v3, Duo Showdown) 
        # or 'players' (Solo Showdown, etc.)
        if "teams" in match["battle"]:
            for team in match["battle"]["teams"]:
                for player in team:
                    players.append(player)
                    tags.append(player["tag"])
        elif "players" in match["battle"]:
            for player in match["battle"]["players"]:
                players.append(player)
                tags.append(player["tag"])

        # TODO: Refactor so that the writter to the csv only eneds the players list and not the tags as well
        write_match_data_1(CSV_FILE, tags, match, players_info, player_tag)


async def get_player_info(client, tag, headers):
    """Takes in an async client, tag, and headers.
    Returns the JSON data dictionary from the Supercell API about player info.
    """
    formatted_tag = tag.replace("#", "%23")
    url = f"https://api.brawlstars.com/v1/players/{formatted_tag}"
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            print(f"Data for {tag} unavailable - API Error (Status: {response.status_code})")
            return None
        return response.json()
        
    except Exception as e:
        print(f"Network error fetching {tag}: {e}")
        return None

def print_battle_data(battle_log_item):
    # Extract the battle time and event details
    battle_time = battle_log_item.get("battleTime", "Unknown Time")
    event = battle_log_item.get("event", {})
    mode = event.get("mode", "Unknown Mode")
    map_name = event.get("map", "Unknown Map")
    
    # Extract the specific details of the battle
    battle_details = battle_log_item.get("battle", {})
    result = battle_details.get("result", "N/A")  # victory, defeat, or draw
    duration = battle_details.get("duration", 0)   # in seconds
    trophy_change = battle_details.get("trophyChange", 0)
    
    print(f"=== Battle Log Entry ===")
    print(f"Time: {battle_time}")
    print(f"Mode: {mode.title()} | Map: {map_name}")
    print(f"Result: {result.upper()} | Duration: {duration}s | Trophies: {trophy_change:+d}")
    print("-" * 24)

    # Handle 3v3 modes (organized by 'teams')
    if "teams" in battle_details:
        print("Teams Overview:")
        for i, team in enumerate(battle_details["teams"], 1):
            print(f"  Team {i}:")
            for player in team:
                brawler = player.get("brawler", {})
                print(f"    - {player.get('name')} | Brawler: {brawler.get('name')} (Tag {player["tag"]})")
                
    # Handle Showdown / Solo modes (organized by 'players')
    elif "players" in battle_details:
        print("Players Standings:")
        # Sort by rank if available, otherwise just list them
        sorted_players = sorted(battle_details["players"], key=lambda x: x.get("rank", 99))
        for player in sorted_players:
            brawler = player.get("brawler", {})
            rank = player.get("rank", "?")
            print(f"  Rank {rank}: {player.get('name')} | Brawler: {brawler.get('name')} (Power {brawler.get('power')})")
            
    print("=" * 24 + "\n")

if __name__ == "__main__":
    main()