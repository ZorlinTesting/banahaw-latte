Django Application for match-betting administration:

Prerequisites:
1. Fill out 'team_info.csv' containing the [name,acronym,base_pr,origin,seed] of each team within the tournament
2. Under scrape_matches.py, correct the 'selector' and 'url' variables for the target scrape
3. create_sublist() might need to be adjusted based on the data structure
4. Use a fresh db before running, archive the previous 'db.sqlite3' file

Commands:
manage.py makemigrations
manage.py migrate
manage.py create_teams
manage.py scrape_matches

Notes:
1. After running scrape_matches command, the 'match count' defaults to BO1,
use admin action 'Update Match Count attribute' to correct the attributes for multiple objects.