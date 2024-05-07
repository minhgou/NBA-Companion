"""
A Python script for retrieving NBA player data

Functions:
    - get_regular_season_stats(player_name): Retrieves career regular-season averages
      and stats for a specified NBA player.
    - get_player_id_from_name(player_name): Gets the NBA player ID from their full name.
    - custom_json_encoder(obj): Custom JSON encoder for pandas DataFrame and Series objects.
    - get_player_image(player_name): Retrieves the NBA player headshot using the player's name.

"""
import json
import requests
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from bs4 import BeautifulSoup


def get_player_profile(player_name):
    """
    Gets general profile of NBA player.

    Args:
    - player_name (str): Full name of current or former NBA player.

    Returns:
        - dict: A dictionary containing bio stats about the player.
        - str: A JSON formatted string of the player's regular season averages.
    """

    player_id = get_player_id_from_name(player_name)
    player_bio_info = get_player_info(player_id)
    _, _, career_averages, _ = get_regular_season_stats(player_name)

    return player_bio_info, career_averages


def get_player_info(player_id):
    """
    Retrieve player information from the NBA website based on the provided player ID.

    Args:
        player_id (str): The unique identifier for the player.

    Returns:
        dict: A dictionary containing player information such as age, birth date, height, weight,
              country, draft information, last attended, and experience. If any information is not
              available, the corresponding value will be 'Unknown'.
    """

    url = f"https://www.nba.com/player/{player_id}"
    response = requests.get(url, timeout=5)
    player_info = {}
    label_value_map = {
        "AGE": "age",
        "BIRTHDATE": "birthdate",
        "HEIGHT": "height",
        "WEIGHT": "weight",
        "COUNTRY": "country",
        "DRAFT": "draft",
        "LAST ATTENDED": "last_attended",
        "EXPERIENCE": "experience"
        }

    # Scrape data from NBA page
    if response.url != 'https://www.nba.com/players' and response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        labels = soup.find_all('p', class_='PlayerSummary_playerInfoLabel__hb5fs')
        values = soup.find_all('p', class_='PlayerSummary_playerInfoValue__JS8_v')

        for label, value in zip(labels, values):
            label_text = label.text.strip().upper()  # Ensure case insensitivity
            value_text = value.text.strip()
            key = label_value_map.get(label_text)
            if key:
                player_info[key] = value_text
        return player_info

    # If response status is not 200, return default values
    default_value = 'Unknown'
    player_info = {key: default_value for key in label_value_map.values()}
    return player_info


def get_regular_season_stats(player_name):
    """
    Gets career averages of specified NBA player.

    Args:
        - player_name (str): Full name of current or former NBA player.

    Returns:
        - str: A JSON formatted string of the player's average stats over their career.
        - str: A JSON formatted string containing regular-season stats data for each season.
    """

    player_id = get_player_id_from_name(player_name)

    # Retrieve player career statistics
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_stats = career.get_data_frames()[0]
    career_stats = career_stats.rename(columns={'TEAM_ABBREVIATION': 'TEAM', 'PLAYER_AGE': 'AGE'})

    # Define column lists
    totals_cols = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA',
                'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                'OREB', 'DREB', 'PF']
    per_game_cols = ['MPG', 'PPG', 'RPG', 'APG', 'SPG', 'BPG', 'TPG', 'FGM', 'FGA',
                    'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                    'ORPG', 'DRPG', 'PF']
    percentage_stats = ['FG_PCT', 'FG3_PCT', 'FT_PCT']

    # Career Totals
    career_totals_per_season = career_stats[['SEASON_ID', 'AGE', 'GP', 'TEAM'] + totals_cols].copy()
    career_totals_per_season['FULL_NAME'] = player_name

    # Sum career totals and convert to int
    career_totals = {'FULL_NAME': player_name, 'GP': int(career_totals_per_season['GP'].sum())}
    career_totals.update(career_totals_per_season[totals_cols].sum().astype(int).to_dict())

    # Convert non-integer columns to int except for 'FULL_NAME', 'SEASON_ID', and percentage columns
    for col in career_totals_per_season.columns:
        if col not in ['FULL_NAME', 'SEASON_ID', 'TEAM'] + percentage_stats:
            career_totals_per_season[col] = career_totals_per_season[col].astype(int)

    # Career Averages
    career_avg_per_season = pd.DataFrame(
        columns=['FULL_NAME', 'SEASON_ID', 'AGE', 'TEAM', 'GP'] + per_game_cols
        )

    # Calculate per game averages
    for stat, per_game_stat in zip(totals_cols, per_game_cols):
        career_avg_per_season[per_game_stat] = round(career_stats[stat] / career_stats['GP'], 1)

    career_avg_per_season['FULL_NAME'] = player_name
    career_avg_per_season['SEASON_ID'] = career_stats['SEASON_ID']
    career_avg_per_season['AGE'] = career_stats['AGE']
    career_avg_per_season['TEAM'] = career_stats['TEAM']
    career_avg_per_season['GP'] = career_stats['GP']
    career_avg_per_season['AGE'] = career_avg_per_season['AGE'].astype('int')

    # Calculate career averages
    career_averages = {'FULL_NAME': player_name, 'GP': int(career_avg_per_season['GP'].sum())}
    career_averages.update(round(career_avg_per_season[per_game_cols].mean(), 1).to_dict())

    # Convert percentage Stats
    for stat in percentage_stats:
        career_avg_per_season[stat] = round(career_stats[stat] * 100, 1)
        career_averages[stat] = round(career_avg_per_season[stat].mean(), 1)
        career_totals_per_season[stat] = round(career_totals_per_season[stat] * 100, 1)
        career_totals[stat] = round(career_avg_per_season[stat].mean(), 1)

    # Convert DataFrames to dictionaries
    career_totals_per_season_json = career_totals_per_season.to_dict(orient='records')
    career_avg_per_season_json = career_avg_per_season.to_dict(orient='records')

    # Results
    totals = json.dumps(career_totals)
    totals_per_season = json.dumps(career_totals_per_season_json)
    avg_per_game = json.dumps(career_averages)
    avg_per_season = json.dumps(career_avg_per_season_json)

    return totals, totals_per_season, avg_per_game, avg_per_season



def get_player_id_from_name(player_name):
    """
    Gets an NBA player's ID from their full name.

    Args:
        - player_name (str): Full name of current or former NBA player.

    Returns:
        - player_id (str): The corresponding player ID to the player name.
    """

    all_players = players.get_players()
    for player in all_players:
        if player['full_name'].lower() == player_name.lower():
            return player['id']
    return None


def custom_json_encoder(obj):
    """
    Custom JSON encoder.

    Args:
        obj (Any): The object to encode into JSON.

    Returns:
        Any: The JSON-serializable representation of the input object.
        If the object is a pandas DataFrame, it is converted to a dictionary with
        orientation 'records'. If the object is a pandas Series, it is converted to a dictionary. 
        Otherwise, the object is returned unchanged.
    """

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    else:
        return obj


def get_player_image(player_name):
    """
    Gets NBA player headshot using player ID.

    Args:
        - player_name (str): Full name of current or former NBA player.

    Returns:
        - url (str) URL link to the headshot of NBA player.
          Defaults to fallback image URL if headshot doesn't exist.
    """

    player_id = get_player_id_from_name(player_name=player_name)
    url = f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png'

    if url:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Image URL is valid, render the image
            return url
        else:
            # Image URL is invalid or inaccessible, render fallback image
            url = "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"
            return url

    url = "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"
    return url
