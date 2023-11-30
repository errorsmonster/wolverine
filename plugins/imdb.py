from pyrogram import Client, filters
from imdb import Cinemagoer

ia = Cinemagoer()

@Client.on_message(filters.command("suggest"))
def suggest_movie(_, message):
    try:
        _, *args = message.text.split(" ", 2)
        if len(args) < 1:
            raise ValueError("Please provide at least a genre. Example: /suggest action")
        
        genre = args[0]
        language = args[1] if len(args) > 1 else None

        if genre.lower() == "top250":
            movies = get_top250_movies()
        else:
            movies = get_movies(genre, language)
        
        if movies:
            suggestion = format_movie_suggestion(movies)
            message.reply_text(suggestion)
        else:
            message.reply_text("No movies found for the given query.")
    
    except ValueError as e:
        message.reply_text(str(e))

def get_movies(genre, language):
    try:
        movies = ia.search_movie(genre)
        if language:
            movies = [movie for movie in movies if language.lower() in movie.get('languages', [])]
        return movies[:10]  # Return top 10 movies for simplicity
    
    except Exception as e:
        return None

def get_top250_movies():
    try:
        top = ia.get_top250_movies()
        return top
    
    except Exception as e:
        return None

def format_movie_suggestion(movies):
    suggestion = "**Movie suggestions:**\n"
    for movie in movies:
        title = movie.get("title", "N/A")
        year = movie.get("year", "N/A")
        suggestion += f"- {title} ({year})\n"
    return suggestion