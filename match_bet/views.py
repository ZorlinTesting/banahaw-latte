from django.shortcuts import render, redirect
from match_bet.management.commands.scrape_matches import Command

# Create your views here.
def start_scraping_view(request):
    # Execute the management command
    command = Command()
    command.handle()

    return redirect('/admin/match_bet/match/')