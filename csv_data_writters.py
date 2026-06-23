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
    "highestAllTimeRankedElo"
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

def write_match_data_2(file_name, match_tags, match, players_info, player_tag):
    """Writes player tag"""
    with open(file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        row_data = []

        for tag in match_tags:
            row_data.append(tag)

        # Write to the CSV
        writer.writerow(row_data)
