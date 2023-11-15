from django.urls import path
from . import views

app_name = 'match_bet'

urlpatterns = [
    path('scrape/', views.start_scraping_view, name='scrape_matches'),

]



