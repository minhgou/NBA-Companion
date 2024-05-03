"""
Main module for the NBA Companion API
"""
import json
import pandas as pd
from flask import Flask, request, jsonify
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players


app = Flask(__name__)


@app.route('/career_stats', methods=['GET'])
def get_player_stats():
    """
    Gets career averages of specified NBA player.

    Args:
        - player_name (str): Name of current or former NBA player.

    Returns:
        - dict: A JSON object of the player's average stats over their career.
    """
    player_name = request.args.get("player_name")
    player_id = get_player_id_from_name(player_name)

    if player_name is None:
        response = {
            "error": "Player name is missing.",
            "status_code": 400
            }
        return jsonify(response), response['status_code']

    player_id = get_player_id_from_name(player_name)

    if player_id is None:
        response = {
            "error": "Player name not found.",
            "status_code": 404
            }
        return jsonify(response), response['status_code']

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_data = career.get_data_frames()[0]

    stats_cols = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA',
                'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                'OREB', 'DREB', 'PF']

    per_game_cols = ['MPG', 'PPG', 'RPG', 'APG', 'SPG', 'BPG', 'TPG', 'FGM', 'FGA',
                    'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                    'ORPG', 'DRPG', 'PF']

    career_data_processed = pd.DataFrame(columns=['FULL_NAME', 'GP'] + per_game_cols)

    career_data_processed['GP'] = career_data['GP']
    career_data_processed['FULL_NAME'] = player_name
    for stat, per_game_stat in zip(stats_cols, per_game_cols):
        career_data_processed[per_game_stat] = round(career_data[stat] / career_data['GP'], 1)

    per_game_averages = {'FULL_NAME': player_name, 'GP': int(career_data_processed['GP'].sum())}
    per_game_averages.update(round(career_data_processed[per_game_cols].mean(), 1).to_dict())

    return json.dumps(per_game_averages, default=custom_json_encoder)


def get_player_id_from_name(player_name):
    """
    Gets an NBA player's ID from their full name

    Args:
        - player_name (str): Name of current or former NBA player.

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

if __name__ == '__main__':
    app.run(debug=True)
