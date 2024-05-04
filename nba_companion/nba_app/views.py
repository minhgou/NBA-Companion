"""
Module containing views for the NBA Companion application.

Includes views for the home page and for retrieving NBA regular season career stats of players.

Functions:
    - home: Renders the home page of the NBA Companion.
    - regular_season: Retrieves and renders the NBA regular season career stats of a
      specified player
"""

import json
import logging
from django.shortcuts import render
from nba_app.utils import *


# Configure logging
logging.basicConfig(
    filename='nba_companion/nba_companion.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def home(request):
    """
    NBA Companion Home Page.
    """

    return render(request, 'home.html')


def player_profile(request):
    """
    View that gets a specfied NBA player's NBA general profile.
    """

    try:
        player_name = request.GET.get('player_name')

        if player_name:
            player_info, avg_per_game = get_player_profile(player_name)
            player_image_url = get_player_image(player_name)

            logging.info("Successfully loaded player profile.")

            return render(request, 'player_profile.html',
                            {
                                "player_info": player_info,
                                "reg_season_avg": json.loads(avg_per_game),
                                "player_image_url": player_image_url
                            }
                            )
        return render(request, 'player_profile_search.html')

    except json.JSONDecodeError as error:
        logging.error("Unable to find player: %s", error)
        error_message = "Unable to find player. Please try again."

        return render(
            request,
            'player_profile_search.html',
            {'error_message': error_message}
        )


def regular_season(request):
    """
    View that gets a specfied player's NBA regular season career stats.
    """

    try:
        player_name = request.GET.get('player_name')
        stats_type = request.GET.get('type')
        if player_name:
            if not stats_type:
                stats_type = 'averages'

            totals, totals_per_season, avg_per_game, avg_per_season = get_regular_season_stats(
                player_name)
            player_image_url = get_player_image(player_name)

            logging.info("Successfully loaded regular season career.")

            return render(request, 'regular_season_career.html',
                          {
                              "type" : stats_type,
                              "reg_season_totals": json.loads(totals),
                              "reg_season_totals_per_season": json.loads(totals_per_season),
                              "reg_season_avg": json.loads(avg_per_game),
                              "reg_season_avg_per_season": json.loads(avg_per_season),
                              "player_image_url": player_image_url
                          }
                          )
        return render(request, 'regular_season_career_search.html')

    except json.JSONDecodeError as error:
        logging.error("Unable to find player: %s", error)
        error_message = "Unable to find player. Please try again."

        return render(
            request,
            'regular_season_career_search.html',
            {'error_message': error_message}
        )
