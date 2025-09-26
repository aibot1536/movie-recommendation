import requests
from requests.exceptions import RequestException, JSONDecodeError
from myapp.recommend import recommend_movies, recommend_from_title
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Genre, Subscription, Rating, Movie, WatchList
from django.core.paginator import Paginator
from django.http import JsonResponse
from myapp.new_recommend import recommend_cast


OMDB_API_KEY = "c9eb1bb2"

def home(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Logged In..")
            return redirect('home')
        else:
            messages.success(request, "There Was An Error Logging In, Plese Try Again..")
            return redirect('home')
    else:
        movies = Movie.objects.all()
        paginator = Paginator(movies, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        movies_with_posters = []
        for movie in page_obj:
            title = movie.title
            poster = get_movie_poster(movie.title)
            movies_with_posters.append({
                "title": title,
                "poster": poster
            })

        return render(request, 'index.html', {
            'movies': movies_with_posters,
            'page_obj': page_obj,
        })
    

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out..")
    return redirect('home')

"""abc abc#xyz#"""
def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You Have Successfully Registered! Welcome!")
            return redirect('home')
        
    else:
        form = SignUpForm()
        return render(request, "register.html", {"form":form})
    
    return render(request, "register.html", {"form":form})


def get_movie_poster(title):
    try:
        movie = Movie.objects.get(title=title)
    except Movie.DoesNotExist:
        print(f"Movie '{title}' not found in DB.")
        return ""

    if movie.poster:
        return movie.poster

    # Fetch from OMDB
    print(title)
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
    try:
        response = requests.get(url, timeout=5)  # Add timeout
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("Response") == "True":
                    poster_url = data.get("Poster", "")
                    if poster_url:
                        movie.poster = poster_url
                        movie.save()
                    return poster_url
                else:
                    print(f"OMDB Error for '{title}':", data.get("Error"))
            except ValueError:
                print(f"❌ Failed to parse JSON for '{title}':", response.text)
        else:
            print(f"❌ OMDB returned status {response.status_code} for '{title}'")
    except requests.RequestException as e:
        print(f"❌ Request to OMDB failed for '{title}':", e)

    return ""


def recommend_movies_view(request):
    recommendations = []
    recommendations2 = []

    if not request.user.is_authenticated:
        return redirect('home')

    # 1. Fetch user ratings from DB
    user_ratings = {
        rating.movie.title: rating.rating
        for rating in Rating.objects.filter(user=request.user)
    }

    titles = [title for title, value in user_ratings.items()]
    recommended_cast = recommend_cast(titles)
    recommendations2 = [
        {"title": title, "poster": get_movie_poster(title)}
        for title in recommended_cast
    ]

    # 2. Fetch preferred genres from Subscription model
    preferred_genres = [
        subscription.genre.name  # Capitalize to match genre names from dataset
        for subscription in Subscription.objects.filter(user=request.user)
    ]

    # 3. Generate recommendations
    if user_ratings:
        recommended_titles = recommend_movies(
            user_ratings,
            preferred_genres=preferred_genres,
            top_n=12
        )
        recommendations = [
            {"title": title, "poster": get_movie_poster(title)}
            for title in recommended_titles
        ]

    return render(request, "recommend.html", {
        "recommendations": recommendations,
        "recommendations2": recommendations2
    })


def fetch_movie_data_from_omdb(movie_title):
    try:
        movie_obj = Movie.objects.get(title=movie_title)
    except Movie.DoesNotExist:
        print(f"❌ Movie '{movie_title}' not found in database.")
        return None

    api_url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie_title}"
    
    try:
        response = requests.get(api_url, timeout=10)  # timeout avoids hanging
        response.raise_for_status()  # raise error if status != 200

        try:
            movie_data = response.json()
        except JSONDecodeError:
            print("❌ Failed to parse JSON from OMDb. Raw response:")
            print(response.text)
            return None

        if movie_data.get("Response") == "True":
            movie_obj.poster = movie_data.get("Poster")
            movie_obj.save()
            return movie_data
        else:
            print(f"⚠️ OMDb error: {movie_data.get('Error')}")
            return None

    except RequestException as e:
        print(f"❌ Request to OMDb failed: {e}")
        return None



def movie_details_view(request, movie_title):
    if not request.user.is_authenticated:
        return redirect('home')

    movie_obj = Movie.objects.get(title=movie_title)
    recommend = recommend_from_title(movie_title)
    recommendations = [{"title": m, "poster": get_movie_poster(m)} for m in recommend]

    # Handle POST requests for rating and watchlist
    if request.method == "POST":
        if "rating" in request.POST:
            rating_value = request.POST.get("rating")
            if rating_value == "remove":
                Rating.objects.filter(user=request.user, movie=movie_obj).delete()
            else:
                Rating.objects.update_or_create(
                    user=request.user,
                    movie=movie_obj,
                    defaults={"rating": int(rating_value)}
                )
        elif "add_watchlist" in request.POST:
            WatchList.objects.get_or_create(user=request.user, movie=movie_obj)
        elif "remove_watchlist" in request.POST:
            WatchList.objects.filter(user=request.user, movie=movie_obj).delete()
        return redirect("movie_details", movie_title=movie_title)

    # Get OMDb data using helper
    movie_data = fetch_movie_data_from_omdb(movie_title)

    context = {
        "recommendations": recommendations,
        "in_watchlist": WatchList.objects.filter(user=request.user, movie=movie_obj).exists()
    }

    if movie_data.get("Response") == "True":
        rating = Rating.objects.filter(user=request.user, movie=movie_obj).first()
        user_rating = str(rating.rating) if rating else ""
        context.update({
            "title": movie_data.get("Title"),
            "poster": movie_data.get("Poster"),
            "plot": movie_data.get("Plot"),
            "genre": movie_data.get("Genre"),
            "director": movie_data.get("Director"),
            "actors": movie_data.get("Actors"),
            "imdb_rating": movie_data.get("imdbRating"),
            "released": movie_data.get("Released"),
            "runtime": movie_data.get("Runtime"),
            "user_rating": user_rating,
        })
    else:
        context["error"] = "Movie not found!"

    return render(request, "movie_details.html", context)


def manage_subscriptions(request):
    if not request.user.is_authenticated:
        return redirect('home')

    user = request.user
    genres = Genre.objects.all()
    user_subscriptions = Genre.objects.filter(subscription__user=user)

    if request.method == 'POST':
        selected_genres = request.POST.getlist('genres')
        
        # Remove unchecked
        Subscription.objects.filter(user=user).exclude(genre__id__in=selected_genres).delete()
        
        # Add checked
        for genre_id in selected_genres:
            Subscription.objects.get_or_create(user=user, genre_id=genre_id)

        return redirect('manage_subscription')

    return render(request, 'subscription.html', {
        'genres': genres,
        'user_subscriptions': user_subscriptions
    })


def rated_movies_view(request):
    if not request.user.is_authenticated:
        return redirect('home')
    rated_movies = Rating.objects.filter(user=request.user).select_related('movie')
    return render(request, "rated_movies.html", {"rated_movies": rated_movies})


def search_movie(request):
    return render(request, 'search.html')


def watch_list(request):
    if not request.user.is_authenticated:
        return redirect('home')
    watchlist = WatchList.objects.filter(user=request.user)
    return render(request, "watchlist.html", {"watch_list": watchlist})





QUESTION_GENRE_MAPPING = {
    "q1": ["Action", "Thriller"],
    "q2": ["Adventure", "Fantasy"],
    "q3": ["Animation", "Family"],
    "q4": ["Comedy"],
    "q5": ["Mystery", "Crime"],
    "q6": ["Drama", "Romance"],
    "q7": ["Science Fiction"],
    "q8": ["Horror", "Thriller"],
    "q9": ["Documentary", "History"],
    "q10": ["Music"]
}




def get_genres(request):
    if not request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        genre_scores = {}

        for key, genres in QUESTION_GENRE_MAPPING.items():
            try:
                rating = int(request.POST.get(key, 3))  # Default to neutral rating
                rating = max(1, min(rating, 5))  # Clamp rating to 1–5
            except ValueError:
                rating = 3  # fallback

            for genre in genres:
                genre_scores[genre] = genre_scores.get(genre, 0) + rating

        # Sort by score and select top 5
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        top_genres = [genre for genre, score in sorted_genres[:5]]

        # Optionally use the genres to generate recommendations
        recommended_movies = recommend_movies(user_ratings={}, preferred_genres=top_genres, top_n=10)
        print(recommended_movies)
        recommendations = [{"title":title, "poster":get_movie_poster(title)} for title in recommended_movies]

        return render(request, 'personality_quiz.html', {
            "recommendations": recommendations
        })

    return render(request, 'personality_quiz.html')
