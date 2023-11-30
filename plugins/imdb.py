from pyrogram import Client, filters
import requests
from info import TMDB_API_KEY

TMDB_API_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_API_HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_API_KEY}"
}

@Client.on_message(filters.command("suggest"))
def suggest_movie(_, message):
    try:
        _, *args = message.text.split(" ", 3)
        if len(args) < 1:
            raise ValueError("Please provide at least a genre. Example: /suggest action")
        
        genre = args[0]
        language = args[1] if len(args) > 1 else None
        year = args[2] if len(args) > 2 else None

        movies = get_movies(genre, language, year)
        
        if movies:
            suggestion = format_movie_suggestion(movies)
            message.reply_text(suggestion)
        else:
            message.reply_text("No movies found for the given query.")
    
    except ValueError as e:
        message.reply_text(str(e))

def get_movies(genre, language, year):
    params = {
        "language": language or "en",
        "page": "1",
        "sort_by": "popularity.desc",
        "with_genres": genre or None,
        "year": year or None
    }

    try:
        response = requests.get(TMDB_API_URL, headers=TMDB_API_HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data['results'][:10]  # Return top 10 movies for simplicity
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def format_movie_suggestion(movies):
    suggestion = "<b>Movie suggestions:</b>\n\n"
    number = 1
    for movie in movies:
        title = movie.get("title", "N/A")
        year = movie.get("release_date", "N/A")[:4]  # Get only the year from the release date
        suggestion += f"{number}. <code>{title} {year}</code>\n"
        number += 1
    return suggestion