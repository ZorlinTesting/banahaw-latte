import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
from ...models import Match, Team, MatchTeamRelation
from django.shortcuts import get_object_or_404

from django.db import IntegrityError
from django.core.management.base import BaseCommand

# constants
ELO = 1500
K = 16

# Specify the file path
json_file_path = 'scrape_data.json'

selector = 'tr.ml-row:nth-of-type(n+8) td'
# selector = '.ml-w8.ml-row td'  # alternate selector just for Grand Finals


url = 'https://lol.fandom.com/wiki/2023_Season_World_Championship/Main_Event'


def extract_data_from_url(url):
    # Function to extract data from a given URL

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract data using the provided selector
        selected_data = soup.select(selector)

        # Return the extracted data
        return [data.text for data in selected_data]
    else:
        # Print an error message if the request was not successful
        print(
            f"Failed to fetch content from {url}. Status code: {response.status_code}")
        return None


def convert_to_datetime(input_str):
    # Extract relevant portion of the string
    greater_str = input_str.split(',')[0]
    date_list = greater_str.split(' ')

    # Convert month name to month number
    months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
              'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
    month = months[date_list[1]]

    # Convert the year to an integer
    year = int(date_list[2])

    # Create a datetime object
    date_time_obj = datetime(year, month, int(date_list[0]), int(date_list[3][:2]), int(
        date_list[3][3:5]), int(date_list[3][6:8]), tzinfo=timezone.utc)

    # Adjust for the UTC offset
    utc_offset = int(date_list[4][:3])
    date_time_obj = date_time_obj - timedelta(hours=utc_offset)

    # Convert the datetime object to Philippine Time (UTC+8)
    date_time_obj = date_time_obj + timedelta(hours=8)

    return date_time_obj


def scrape_and_write():
    extracted_data = extract_data_from_url(url)
    data_to_write = {"data": extracted_data}

    # Open the file in write mode ('w')
    with open(json_file_path, 'w') as json_file:
        # Write the data to the JSON file
        json.dump(data_to_write, json_file, indent=4)


def create_sublists(input_list):
    result = []
    current_sublist = []

    for element in input_list:
        starts_with_separator = element.startswith('\u2060\u2060')

        if not starts_with_separator:
            current_sublist.append(element)
        else:
            current_sublist.append(element)
            result.append(current_sublist)
            current_sublist = []

    return result


def pr_to_odds(team1, team2):
    processed_pr1 = 1-(round((float(team1.current_pr)/18), 4))
    processed_pr2 = 1-(round((float(team2.current_pr)/18), 4))
    win_prob_1 = processed_pr1 / (processed_pr1 + processed_pr2)
    odds_1 = round((1 / win_prob_1), 2)
    win_prob_2 = processed_pr2 / (processed_pr1 + processed_pr2)
    odds_2 = round((1 / win_prob_2), 2)
    return odds_1, odds_2


def check_winner(score1, score2):
    if score1 > score2:
        return True, False
    elif score1 < score2:
        return False, True


def pr_to_elo(pr):
    return (1-(round((float(pr)/18), 4))) * ELO


def elo_to_pr(elo):
    return round((1 - (elo / ELO)) * 18, 4)


def adjust_team_pr(team1, team2, team1_is_win):

    elo1 = pr_to_elo(team1.current_pr)
    elo2 = pr_to_elo(team2.current_pr)

    expected_score1 = 1 / (1 + (10 ** ((elo2 - elo1) / 400)))
    expected_score2 = 1 / (1 + (10 ** ((elo1 - elo2) / 400)))

    if team1_is_win:
        actual_score1 = 1
        actual_score2 = 0
    elif not team1_is_win:
        actual_score1 = 0
        actual_score2 = 1

    elo1 += K * (actual_score1 - expected_score1)
    elo2 += K * (actual_score2 - expected_score2)

    new_pr1 = elo_to_pr(elo1)
    new_pr2 = elo_to_pr(elo2)

    team1.pr_history.append(team1.current_pr)
    old_pr1 = team1.current_pr
    team1.current_pr = new_pr1
    team1.save()

    team2.pr_history.append(team2.current_pr)
    old_pr2 = team2.current_pr
    team2.current_pr = new_pr2
    team2.save()

    return old_pr1, old_pr2, new_pr1, new_pr2


class Command(BaseCommand):
    help = 'My custom Django command'

    def handle(self, *args, **options):
        # Scrape from selected URL using css selector to return Match objects
        # Also used to update the scores and match results
        # Includes functionality to update power ranking based on ELO constants

        scrape_and_write()  # Writes scraped data, can be disabled for debugging

        # Open the file in read mode ('r')
        with open(json_file_path, 'r') as json_file:
            # Load the JSON content
            json_data = json.load(json_file)

        # Extract the list from the JSON data
        extracted_list = json_data.get("data", [])

        # create_sublists() should be adjusted based on the data structure of scraped site
        grouped_list = create_sublists(extracted_list)

        new_count = 0
        update_count = 0
        unchanged_count = 0

        for sublist in grouped_list:
            # Iterate through scraped sets

            # Remove '\u2060\u2060' from elements 0 and 2, should be adjusted based on data structure
            team1_str = sublist[0].replace('\u2060\u2060', '')
            team2_str = sublist[-1].replace('\u2060\u2060', '')
            team1_is_win = None
            team2_is_win = None
            score1_str = None
            score2_str = None
            matches_played = 0

            if 'TBD' not in team1_str or 'TBD' not in team2_str:  # Eliminate matches with TBD contenders

                if len(sublist) == 3:  # Upcoming match
                    date_str = sublist[1]
                    score1 = None
                    score2 = None

                elif len(sublist) == 5:  # Concluded match with score
                    date_str = sublist[3]
                    score1 = int(sublist[1])
                    score2 = int(sublist[2])
                    matches_played = score1 + score2

                    score1_str = f"{sublist[1]} - {sublist[2]}"
                    score2_str = f"{sublist[2]} - {sublist[1]}"

                # -- To ensure reusability, don't use sublist elements beyond this line --#

                # Search for existing Team model objects
                team1 = get_object_or_404(Team, acronym=team1_str)
                team2 = get_object_or_404(Team, acronym=team2_str)

                formatted_date = convert_to_datetime(date_str)

                # Save the match
                new_match, created = Match.objects.get_or_create(
                    datetime=formatted_date)

                # Check if match and its effects have been previously resolved:
                if not new_match.is_concluded:
                    print(team1, team2, formatted_date)

                    # Update Match fields based on winner and score
                    if score1 is not None and score2 is not None and score1 > score2:
                        # new_match.winner = team1
                        new_match.result = score1_str
                    elif score1 is not None and score2 is not None and score1 < score2:
                        # new_match.winner = team2
                        new_match.result = score2_str

                    new_match.save()

                    # On Match object creation, generate match odds based on teams' power rank at the time
                    if created:
                        odds1, odds2 = pr_to_odds(team1, team2)
                        new_match.current_odds = (odds1, odds2)
                        new_count += 1
                    else:
                        update_count += 1

                    # Create or update MatchTeamRelation instances
                    mtr1, created1 = MatchTeamRelation.objects.get_or_create(
                        team=team1, match=new_match, defaults={
                            'is_team1': True, 'is_winner': team1_is_win, 'match_score': score1_str}
                    )
                    mtr2, created2 = MatchTeamRelation.objects.get_or_create(
                        team=team2, match=new_match, defaults={
                            'is_team1': False, 'is_winner': team2_is_win, 'match_score': score2_str}
                    )

                    if len(sublist) == 5:
                        # For concluded matches, adjust team power rankings and match-team relations

                        # Only update pr if total of score equals match count and update only once
                        if (score1 * 2 >= new_match.best_of) or (score2 * 2 >= new_match.best_of) or (matches_played == new_match.best_of):
                            new_match.is_concluded = True

                            team1_is_win, team2_is_win = check_winner(
                                score1, score2)

                            old_pr1, old_pr2, new_pr1, new_pr2 = adjust_team_pr(
                                team1, team2, team1_is_win)

                            mtr1.pr_delta = round((new_pr1 - old_pr1), 4)
                            mtr2.pr_delta = round((new_pr2 - old_pr2), 4)
                            mtr1.is_winner = team1_is_win
                            mtr2.is_winner = team2_is_win

                        mtr1.is_team1 = True
                        mtr1.match_score = score1_str
                        mtr1.save()

                        mtr2.is_team1 = False
                        mtr2.match_score = score2_str
                        mtr2.save()

                    # Update Match fields based on winner and score
                    if team1_is_win:
                        new_match.winner = team1
                        # new_match.result = score1
                    elif team2_is_win:
                        new_match.winner = team2
                        # new_match.result = score2

                    new_match.save()
                else:
                    unchanged_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'New match objects created: {new_count}'))
        self.stdout.write(self.style.SUCCESS(
            f'Match objects updated: {update_count}'))
        self.stdout.write(self.style.SUCCESS(
            f'Match objects unchanged: {unchanged_count}'))
