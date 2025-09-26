from django.urls import path
from .views import home, logout_user, register_user, recommend_movies_view, movie_details_view, manage_subscriptions, rated_movies_view, search_movie, watch_list, get_genres

urlpatterns = [
    path('', home , name="home"),
    path('logout', logout_user, name="logout"),
    path('register', register_user, name="register"),
    path('recommend/', recommend_movies_view, name="recommend_movies"),
    path('movie/<str:movie_title>/', movie_details_view, name="movie_details"),
    path('subscription/', manage_subscriptions, name="manage_subscription"),
    path("rated/", rated_movies_view, name="rated_movies"),
    path('search/', search_movie, name='search'),
    path('watchlist/', watch_list, name='watch_list'),
    path('personality-quiz/', get_genres, name='personality-quiz'),
]