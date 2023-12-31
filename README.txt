Django Application for match-betting administration:

Functionality:
- Allows bulk creating Teams with power ranking (PR) from CSV file
- Creates Match listings by scraping match info from a schedule site
- Calculates odds based on the teams' pr rating, and also update matches with score outcomes/results
- Automatically recalculates PR rating, ensuring relevant adjustments for subsequent matches

Prerequisites:
1. Fill out 'team_info.csv' containing the [name,acronym,base_pr,origin,seed] of each team within the tournament
2. Under scrape_matches.py, correct the 'selector' and 'url' variables for the target scrape, and
3. create_sublist() might need to be adjusted based on the data structure
4. Check models.py as some attribute choices might need to be adjusted (Team origins & seed, Match count & stages, etc.) 
5. Use a fresh db before running, archive the previous 'db.sqlite3' file

Limitations/Areas for expansion:
- Limited to Match, Team, MatchRelation objects, no User and Bet objects.
- Base/Current Odds only, no functionality for adjusting based on some chosen factors.
- Limited to one tournament only.
- 'Eliminated' or other tags can be added for Team objects

Notes:
- After running scrape_matches command, the 'match count' defaults to BO1,
use admin action 'Update Match Count attribute' to correct the attributes for multiple objects.

Quick-run commands (paste to terminal):
manage.py makemigrations
manage.py migrate
manage.py create_teams
manage.py scrape_matches