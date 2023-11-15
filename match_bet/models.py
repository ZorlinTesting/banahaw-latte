from django.db import models
from django.utils import timezone


class Team(models.Model):
    ORIGIN_CHOICES = [
        ('lck', 'LCK'),
        ('lcs', 'LCS'),
        ('lec', 'LEC'),
        ('lpl', 'LPL'),
        ('vcs', 'VCS'),
    ]
    SEEDING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
    ]

    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=10)
    base_pr = models.FloatField()
    current_pr = models.FloatField()
    pr_history = models.JSONField(default=list, null=True, blank=True)
    seed = models.IntegerField(choices=SEEDING_CHOICES)
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES)

    def __str__(self):
        return self.name


class Match(models.Model):
    list_display = ('display_info', 'stage', 'teams' 'formatted_datetime')

    STAGE_CHOICES = [
        ('swiss', 'Swiss Stage'),
        ('knockout', 'Knockout Stage'),
        ('final', 'Final'),
    ]
    BO_CHOICES = [(1, 'BO1'),
                  (3, 'BO3'),
                  (5, 'BO5'),
                  ]
    RESULT_CHOICES = [('1-0', '1-0'),
                      ('2-0', '2-0'),
                      ('2-1', '2-1'),
                      ('3-0', '3-0'),
                      ('3-1', '3-1'),
                      ('3-2', '3-2'),
                      ]

    datetime = models.DateTimeField(unique=True)
    stage = models.CharField(
        max_length=255, choices=STAGE_CHOICES, default='swiss')
    teams = models.ManyToManyField(
        Team, through='MatchTeamRelation', related_name='matches')
    best_of = models.IntegerField(choices=BO_CHOICES, default=5)
    result = models.CharField(max_length=10, null=True, blank=True)
    winner = models.ForeignKey(Team, null=True, blank=True,
                               related_name='match_winners', on_delete=models.SET_NULL)
    is_concluded = models.BooleanField(default=False)

    # Add a field for current odds
    current_odds = models.JSONField(default=tuple, null=True, blank=True)

    # Add a field for odds history
    odds_history = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        formatted_date = self.datetime.strftime(
            '%m/%d - %I%p').replace(' 0', ' ')
        teams = ", ".join([team.name for team in self.teams.all()])
        return f"{formatted_date} | {teams}"

    class Meta:
        verbose_name_plural = 'matches'

    def update_current_odds(self, new_odds):  # Currently inactive
        # Update current odds
        self.current_odds = new_odds
        self.save()

    def archive_current_odds(self):  # Currently inactive
        # Move current odds to bet history
        if self.current_odds is not None:
            self.bet_history.append({
                'timestamp': timezone.now().isoformat(),
                'odds': self.current_odds
            })
            self.current_odds = None
            self.save()

    def calculate_new_odds(self):  # Currently inactive
        # Your logic for calculating new odds based on certain conditions (time, number of bets)

        # For example, let's say new odds are calculated based on some conditions
        new_odds = 2.5

        # Update current odds and archive previous odds
        self.archive_current_odds()
        self.update_current_odds(new_odds)


class MatchTeamRelation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    is_team1 = models.BooleanField()
    is_winner = models.BooleanField(blank=True, null=True)
    match_score = models.CharField(max_length=10, blank=True, null=True)
    pr_delta = models.FloatField(blank=True, null=True)

    class Meta:
        # Ensure uniqueness for each team in a match
        unique_together = ('team', 'match')


class User(models.Model):
    name = models.CharField(max_length=255)
    balance = models.FloatField()

    def __str__(self):
        return self.name


class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    odds = models.FloatField()
    stake = models.FloatField()

    def __str__(self):
        return f"{self.user} bet {self.stake} on {self.team} in match {self.match}"
