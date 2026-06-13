import requests
import csv
import os
import httpx
import asyncio
from dotenv import load_dotenv
from collections import deque

load_dotenv()

API_KEY = os.getenv("API_KEY")
CSV_FILE = "data.csv"
STARTING_TAG = os.getenv("TAG")

headers_list = ["Game Mode", "P1_Wins", "P2_Wins", "P3_Wins", "P4_Wins", "P5_Wins", "P6_Wins"]

PLAYER_DATA_COUNT = 10

TRUE_BLUE_RESULT_MAP = {
    "victory": 1,
    "draw": 0,
    "defeat": -1
}

def main():
    asyncio.run(scrape_data(STARTING_TAG, API_KEY, players_to_check=1, game_mode="brawlBall")) # map_name="Goalies"

def write_match_data(match, file_name, gamemode, player_tag, players_info):
    """
    Writes match data to a CSV file. 
    Built to be easily expandable for pulling trophies, wins, etc.
    """
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
    # Open the CSV file in append mode
    with open(file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Pull player name
        row_data = []
        for player_info in players_info:
            row_data.append(player_info['name'])
        
        # Insert game result
        if "teams" in match["battle"]:
            if player_tag in tags[:3]:
                row_data.append(TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
            else:
                row_data.append(-TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
        
        # Insert the gamemode at the very beginning of the row
        row_data.insert(0, gamemode)
        
        # Write to the CSV
        writer.writerow(row_data)

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

    # csv file details
    file_name = CSV_FILE
    with open(file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers_list)

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

            for match in battle_log:
                event = match.get("event", {})
                battle = match.get("battle", {})

                match_mode = event.get("mode")
                match_map = event.get("map")
                battle_time = match.get("battleTime")

                matches_to_fetch = []

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

            battlelog_players = get_battlelog_info(client, matches_to_fetch, headers)
                    
    print("\nScrape complete!")
    print(f"Total unique matches written: {len(checked_matches)}")

async def get_battlelog_info(client, battlelog, headers):
    """Takes in an async client, battlelog and headers.
    Returns a dictionary, that contains all matches and player information from the battlelog.
    """
    unique_tags = set()

    # Get all tags from the battle log
    for match in battlelog:
        battle = match['battle']

        # Differ between 3v3 and Showdown matches
        if "teams" in battle:
            for team in battle["teams"]:
                for player in team:
                    unique_tags.add(player["tag"])
        elif "players" in battle:
            for player in battle["players"]:
                unique_tags.add(player["tag"])

        # Make a list of dicts containing all info about the 6-10 players in a match
        players_info = []
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for tag in unique_tags:
                task = tg.create_task(get_player_info(client, tag, headers))
                tasks.append(task)

        broken_tags = 0
        for task in tasks:
            result = task.result()
            if result is None:
                broken_tags += 1
            players_info.append(result)
        
        if broken_tags:
            print(f"Warning! {broken_tags} broken tag(s) in battlelog!")


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

if __name__ == "__main__":
    main()