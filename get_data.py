import requests
from typing import Literal, List
import csv
import os
from dotenv import load_dotenv
from collections import deque

load_dotenv()

API_KEY = os.getenv("API_KEY")
CSV_FILE = "data.csv"
STARTING_TAG = "GRYYRYCLL"

PLAYER_DATA_COUNT = 10

def main():
    scrape_data(STARTING_TAG, API_KEY, players_to_check=1, game_mode="brawlBall", map_name="Goalies")

def write_match_data(match, file_name, gamemode):
    """
    Writes match data to a CSV file. 
    Built to be easily expandable for pulling trophies, wins, etc.
    """
    players = []
    
    # Brawl Stars API structure splits players into 'teams' (3v3, Duo Showdown) 
    # or 'players' (Solo Showdown, etc.)
    if "teams" in match["battle"]:
        for team in match["battle"]["teams"]:
            for player in team:
                players.append(player)
    elif "players" in match["battle"]:
        for player in match["battle"]["players"]:
            players.append(player)
            
    # Open the CSV file in append mode
    with open(file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Pull player name
        row_data = [player['name'] for player in players]
        
        # Insert the gamemode at the very beginning of the row
        row_data.insert(0, gamemode)
        
        # Write to the CSV
        writer.writerow(row_data)

def scrape_data(starting_tag, key, players_to_check, game_mode=None, map_name=None):
    """
    Scrapes battle logs from the Brawl Stars API, iterating through players
    they played with to gather a dataset of unique matches.
    """

    headers = {
        "Authorization": f"Bearer {key}"
    }
    
    checked_players = set()
    checked_matches = set()
    
    # A queue to hold players we need to check (FIFO)
    player_queue = deque([starting_tag])
    file_name = "brawl_stars_matches.csv"
    players_scraped = 0
    
    print(f"Starting scrape. Target: {players_to_check} players.")
    
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
            
            # 1. Filter by game mode and map (if provided)
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
            match_player_tags.sort()
            unique_match_id = f"{battle_time}_{''.join(match_player_tags)}"
            
            if unique_match_id not in checked_matches:
                # New match found! Mark it and write it.
                checked_matches.add(unique_match_id)
                write_match_data(match, file_name, match_mode)
                
            # Add newly discovered players to our queue
            for tag in match_player_tags:
                if tag not in checked_players and tag not in player_queue:
                    player_queue.append(tag)
                    
    print("\nScrape complete!")
    print(f"Total unique matches written: {len(checked_matches)}")


if __name__ == "__main__":
    main()