import csv
import os
import httpx
import asyncio
from dotenv import load_dotenv
from collections import deque
from csv_data_writters import write_match_data_1, write_match_data_2

load_dotenv()

API_KEY = os.getenv("API_KEY")
CSV_FILE = "data.csv"
STARTING_TAG = os.getenv("TAG")

MATCHES_TO_FETCH = 10000
PLAYERS_TO_SEARCH_CONCURRENTLY = 8 # Amount of players the script will request the battlelogs from at a time

# How many request we send at once
CONCURRENCY_LIMIT = 20
semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

# Wrapper function to apply the concurrency limit to your API calls
async def fetch_player_safely(client, tag, headers):
    formatted_tag = tag.replace("#", "%23")
    url = f"https://api.brawlstars.com/v1/players/{formatted_tag}"
    async with semaphore:
        return await get_API_info(client, url, headers)

def main():
    asyncio.run(scrape_data(STARTING_TAG, API_KEY, matches_to_fetch=MATCHES_TO_FETCH, game_mode="brawlBall", map_name="Grass Knot")) # 

async def scrape_data(starting_tag, key, matches_to_fetch, game_mode=None, map_name=None):
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
    
    player_queue = [starting_tag]
    player_battlelogs = {}

    matches_scraped = 0
    
    print(f"Starting scrape. Target: {matches_to_fetch} matches.")
    async with httpx.AsyncClient() as client:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            while player_queue and matches_scraped < matches_to_fetch:
                # Get the next player in the queue
                current_tag = player_queue.pop(0)

                if current_tag in player_battlelogs:
                    battle_log = player_battlelogs.pop(current_tag)
                else:   
                    # Return current tag to the start of the queue
                    player_queue.insert(0, starting_tag)
                    # Select tags to fetch
                    tags_to_fetch = player_queue[:PLAYERS_TO_SEARCH_CONCURRENTLY]

                    api_calls = []
                    for tag in tags_to_fetch:
                        # Format the tag
                        formatted_tag = tag.replace("#", "%23")
                        url = f"https://api.brawlstars.com/v1/players/{formatted_tag}/battlelog"
                        api_calls.append(get_API_info(client, url, headers))

                    responses = await asyncio.gather(*api_calls)
                    for tag, response in zip(tags_to_fetch, responses):
                        if response is not None:
                            player_battlelogs[tag] = response["items"]
                    # Restart loop after fetching new data
                    continue

                # Mark player as checked
                checked_players.add(current_tag)
                print(f"[{matches_scraped}/{matches_to_fetch}] Scraped player log: {current_tag}")

                battlelog = []
                for match in battle_log:
                    event = match["event"]
                    battle = match["battle"]

                    match_mode = event["mode"]
                    match_map = event["map"]
                    battle_time = match["battleTime"]

                    # Filter by game mode and map (if provided)
                    if game_mode and match_mode != game_mode:
                        continue
                    if map_name and match_map != map_name:
                        continue

                    # Ignore friendly matches
                    if match["battle"]["type"] == "friendly":
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
                        battlelog.append(match)
                        checked_matches.add(unique_match_id)

                # Get all player information we will need
                battlelog_players = await get_battlelog_info(client, battlelog, headers)

                # Add new tags to the queue
                for tag in battlelog_players.keys():
                    if tag not in checked_players and tag not in player_queue:
                            player_queue.append(tag)

                matches_scraped += len(battlelog)
                write_battlelog_info(writer, battlelog, battlelog_players, current_tag)
            
    if not player_queue:
        print("\nNo players left to search")
    else:
        print("\nEnough matches found")

    print("Scrape complete!")
    print(f"Total unique matches written: {matches_scraped}")

async def get_battlelog_info(client, battlelog, headers):
    """Takes in an async client, battlelog and headers.
    Returns a dictionary, whose keys are tags, that contains all matches and player information from the battlelog.
    Also removes matches with broken tags from battlelog
    """
    unique_tags = set()
    players_info = {}

    tags_to_fetch = set()
    match_requirements = []
    
    for match in battlelog:
        match_tags = set()
        battle = match["battle"]
    
        # Differ between 3v3 and Showdown matches
        if "teams" in battle:
            for team in battle["teams"]:
                for player in team:
                    if player["tag"] not in unique_tags:
                        match_tags.add(player["tag"])
        elif "players" in battle:
            for player in battle["players"]:
                if player["tag"] not in unique_tags:
                    match_tags.add(player["tag"])
    
        # Track tags needed for this specific run
        tags_to_fetch.update(match_tags)
        match_requirements.append((match, match_tags))

    unfiltered_fetched_info = {}
    if tags_to_fetch:
        async with asyncio.TaskGroup() as tg:
            # Create tasks mapped by tag
            tasks = {
                tag: tg.create_task(fetch_player_safely(client, tag, headers)) 
                for tag in tags_to_fetch
            }

        # Extract results once the TaskGroup finishes
        for tag, task in tasks.items():
            result = task.result()
            if result is not None:
                unfiltered_fetched_info[tag] = result

    # Filter out broken matches
    broken_matches = []
    for match, match_tags in match_requirements:
        fail = False
        match_player_info = {}

        for tag in match_tags:
            # If tag is not broken
            if tag in unfiltered_fetched_info:
                match_player_info[tag] = unfiltered_fetched_info[tag]
            else:
                fail = True

        if fail:
            if match not in broken_matches:
                broken_matches.append(match)
                battlelog.remove(match)
        else:
            players_info.update(match_player_info)
    return players_info

def write_battlelog_info(writer, battlelog, players_info, player_tag):
    """Write the wanted information from the battlelog into the data csv file"""
    for match in battlelog:
        # ignore draws for now
        if match["battle"]["result"] == "draw":
            continue

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
        # There might be a broken tag in a match still, so um ignore it (TODO: fix this this is a bandaid solution)
        # #JGG9CG009 broken player
        write_match_data_1(writer, tags, match, players_info, player_tag)
        # try:
        #     write_match_data_1(CSV_FILE, tags, match, players_info, player_tag)
        # except KeyError:
        #     continue

async def get_API_info(client, url, headers):
    """Takes in an async client, url, and headers.
    Returns the JSON data dictionary from the Supercell API with specific url.
    """
    tag = url.split("%23")[1].split("/")[0]
    while True:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                return response.json()
                
            elif response.status_code == 429:
                print(f"Rate limited for {tag}. Waiting 1 seconds to retry...")
                await asyncio.sleep(1)
                continue
                
            else:
                #print(f"Data for {tag} unavailable - API Error (Status: {response.status_code})")
                return None
                
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # Catches network drops/timeouts and retries
            print(f"Network error fetching {tag}: {e}. Retrying in 1 seconds...")
            await asyncio.sleep(1)

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