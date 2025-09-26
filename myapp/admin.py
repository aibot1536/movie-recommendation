from django.contrib import admin
from .models import Movie, Rating, Subscription, Genre, WatchList

# Register your models here.
admin.site.register(Movie)
admin.site.register(Rating)
admin.site.register(Subscription)
admin.site.register(Genre)
admin.site.register(WatchList)