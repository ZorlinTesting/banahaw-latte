from django.contrib import admin
from .models import Match, Team, Bet, User, MatchTeamRelation
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render

# Register your models here.
admin.site.register(Bet)
admin.site.register(User)

class MatchTeamRelationInline(admin.TabularInline):
    model = MatchTeamRelation
    extra = 0

class MatchAdmin(admin.ModelAdmin):
    inlines = [MatchTeamRelationInline]
    list_display = ('formatted_datetime', 'stage', 'best_of_display', 'display_info', 'display_current_odds','winner', 'result')

    def display_current_odds(self, obj):
        # Format the current_odds data
        if obj.current_odds:
            formatted_odds = f"{obj.current_odds[0]:.2f} vs {obj.current_odds[1]:.2f}"
            return formatted_odds
        return ''
    
    display_current_odds.short_description = 'Current Odds'


    def display_info(self, obj):
        teams = " vs ".join([team.name for team in obj.teams.all()])
        return f"{teams}"
    
    
    display_info.short_description = 'Matchup'
    
    def best_of_display(self, obj):
        return dict(Match.BO_CHOICES).get(obj.best_of, obj.best_of)

    best_of_display.short_description = 'Match Count'

    def formatted_datetime(self, obj):
        return obj.datetime.strftime('%m/%d - %I%p').replace(' 0', ' ')
    
    formatted_datetime.short_description = 'Date & Time'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'winner':
            # Limit choices to teams involved in the match
            match_id = request.resolver_match.kwargs.get('object_id')
            if match_id:
                match_teams = Team.objects.filter(matchteamrelation__match_id=match_id)
                kwargs['queryset'] = match_teams
            else:
                kwargs['queryset'] = Team.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    #--admin actions--#
    
    actions = ['update_attributes']

    @admin.action(description="Update Match Count attribute")
    def update_attributes(self, request, queryset): 
        # Store the selected queryset in session data for confirmation
        request.session['selected_matches'] = [obj.id for obj in queryset]

        # Redirect to the confirmation screen
        return HttpResponseRedirect(reverse('admin:confirm_edit_attributes'))
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('confirm-edit-attributes/', self.confirm_edit_attributes,
                name='confirm_edit_attributes'),
            path('execute-edit-attributes/', self.execute_edit_attributes,
                name='execute_edit_attributes'),
        ]
        return custom_urls + urls
    
    def confirm_edit_attributes(self, request):
        # Retrieve the selected products from session data
        selected_match_ids = request.session.get('selected_matches', [])

        # Retrieve the products based on the IDs
        selected_matches = Match.objects.filter(
            id__in=selected_match_ids)

        context = {
            'selected_matches': selected_matches,
        }

        return render(request, 'admin/confirm_edit_attributes.html', context)
    
    def execute_edit_attributes(self, request):
        # Retrieve the selected products from session data
        selected_product_ids = request.session.get('selected_matches', [])

        # Retrieve the products based on the IDs
        selected_matches = Match.objects.filter(id__in=selected_product_ids)

        success_updates = []
        error_updates = []

        # # Retrieve the new attribute values from the form input
        new_match_count = int(request.POST.get('new_match_count'))

        # Loop through the selected matches
        for match in selected_matches:
            # Update the match attribute
            match.best_of = new_match_count
            match.save()

            # Append the updated match to the success list
            success_updates.append(match)

        # Generate a message to inform the user about the results
        success_message = f"Updated {len(success_updates)} products successfully."
        error_message = f"Failed to update {len(error_updates)} products."

        # Clear the session data
        del request.session['selected_matches']

        context = {
            'success_message': success_message,
            'error_message': error_message,
            'success_updates': success_updates,
            'error_updates': error_updates
        }

        return render(request, 'admin/summary_screen.html', context)


class TeamAdmin(admin.ModelAdmin):
    inlines = [MatchTeamRelationInline]

    list_display = ('name', 'acronym', 'base_pr', 'current_pr', 'origin', 'seed')

    def display_matches(self, obj):
        return ", ".join([str(match) for match in obj.matches.all()])

    display_matches.short_description = 'Matches'

    def display_winner(self, obj):
        return str(obj.winner) if obj.winner else 'No Winner'

    display_winner.short_description = 'Winner'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'winner':
            team_id = request.resolver_match.kwargs.get('object_id')
            if team_id:
                team = Team.objects.get(pk=team_id)
                kwargs['queryset'] = team.matches.all()
            else:
                kwargs['queryset'] = Team.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Team, TeamAdmin)
admin.site.register(MatchTeamRelation)
admin.site.register(Match, MatchAdmin)
