import csv

TRUE_BLUE_RESULT_MAP = {
    "victory": 1,
    "draw": 0,
    "defeat": -1
}

FEATURES = [
    "brawler",
    "3vs3Victories",
    "totalPrestigeLevel",
    "highestAllTimeRankedElo",

    "eloDiffAvg",        # Difference in average team rank
    "eloDiffMax",        # Compares the highest-ranked carrying player on each team
    "eloDiffMin",        # Compares the weakest link player on each team
    "winsDiffTotal",     # Overall 3v3 experience difference between teams
    "winsDiffMax",       # Difference between the most veteran players
    "prestigeDiffTotal"  # Account overall status/investment tier gaps
]

def write_match_data_1(writer, match_tags, match, players_info, player_tag):
    """Writes player 3v3 wins, Prestige amounts, brawler picks"""
    row_data = []

    for i, tag in enumerate(match_tags):
        in_blue_team = tag in match_tags[:3]
        team_index = 0 if in_blue_team else 1
        player_index = i if in_blue_team else i - 3

        # BRAWLER IS ALWAYS FIRST! IMPORTANT!!
        if "brawler" in FEATURES:
            row_data.append(match['battle']['teams'][team_index][player_index]['brawler']['name'])

        if "3vs3Victories" in FEATURES:
            row_data.append(players_info[tag]['3vs3Victories'])
        if "totalPrestigeLevel" in FEATURES:
            row_data.append(players_info[tag]['totalPrestigeLevel'])
        if "rankedElo" in FEATURES:
            row_data.append(players_info[tag]["rankedElo"])
        if "highestAllTimeRankedElo" in FEATURES:
            row_data.append(players_info[tag]["highestAllTimeRankedElo"])

    # Insert game result
    if "teams" in match["battle"]:
        if player_tag in match_tags[:3]:
            row_data.append(TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
        else:
            row_data.append(-TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
    
    # Write to the CSV
    writer.writerow(row_data)


def write_match_data_2(writer, match_tags, match, players_info, player_tag):
    """Writes player tag"""
    row_data = []

    blueWins = []
    bluePrestige = []
    blueElo = []

    redWins = []
    redPrestige = []
    redElo = []

    for tag in match_tags:
        in_blue_team = tag in match_tags[:3]
        
        wins = players_info[tag]['3vs3Victories']
        prestige = players_info[tag]['totalPrestigeLevel']
        elo = players_info[tag]['highestAllTimeRankedElo']
        
        if in_blue_team:
            blueWins.append(wins)
            bluePrestige.append(prestige)
            blueElo.append(elo)
        else:
            redWins.append(wins)
            redPrestige.append(prestige)
            redElo.append(elo)
    if "eloDiffAvg" in FEATURES:
        eloDiffAvg = (sum(blueElo) / 3) - (sum(redElo) / 3)
        row_data.append(eloDiffAvg)

    if "eloDiffMax" in FEATURES:
        eloDiffMax = max(blueElo) - max(redElo)
        row_data.append(eloDiffMax)

    if "eloDiffMin" in FEATURES:
        eloDiffMin = min(blueElo) - min(redElo)
        row_data.append(eloDiffMin)

    if "winsDiffTotal" in FEATURES:
        winsDiffTotal = sum(blueWins) - sum(redWins)
        row_data.append(winsDiffTotal)

    if "winsDiffMax" in FEATURES:
        winsDiffMax = max(blueWins) - max(redWins)
        row_data.append(winsDiffMax)

    if "prestigeDiffTotal" in FEATURES:
        prestigeDiffTotal = sum(bluePrestige) - sum(redPrestige)
        row_data.append(prestigeDiffTotal)

    # Insert game result
    if "teams" in match["battle"]:
        if player_tag in match_tags[:3]:
            row_data.append(TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
        else:
            row_data.append(-TRUE_BLUE_RESULT_MAP[match["battle"]["result"]])
    
    # Write to the CSV
    writer.writerow(row_data)
