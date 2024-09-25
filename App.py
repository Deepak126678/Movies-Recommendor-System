import pickle
import streamlit as st
import requests
import pandas as pd
from collections import defaultdict
from pathlib import Path
import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path to the local image
image_path = Path(__file__).parent / "static" / "MOVIE.jpeg"

if not image_path.is_file():
    st.error(f"Image not found at {image_path}")
else:
    image_base64 = get_base64_of_bin_file(image_path)

    # Inject CSS with the background image
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{image_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: -1;
        }}
        .title {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 0.5em;
            color: #f28e2b;
            font-weight: bold;
            text-shadow: 2px 2px 4px #000000;
        }}
        .subheader {{
            text-align: center;
            font-size: 1.5em;
            color: #4e79a7;
            font-weight: bold;
            text-shadow: 1px 1px 2px #000000;
        }}
        .section-title {{
            font-size: 1.75em;
            color: #e15759;
            font-weight: bold;
            margin-top: 1em;
            text-shadow: 1px 1px 2px #000000;
        }}
        .movie-card {{
            text-align: center;
            margin: 1em 0;
            color: white;
        }}
        .movie-title {{
            font-weight: bold;
            font-size: 1.1em;
            color: #f28e2b;
            text-shadow: 1px 1px 2px #000000;
        }}
        .movie-poster:hover {{
            transform: scale(1.05);
            transition: transform 0.2s;
        }}
        .movie-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to fetch movie details including poster, rating, overview, and trailer
def fetch_movie_details(movie_id):
    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=eeaa04316d6da99c068c8a375da80ab4&language=en-US')
    data = response.json()
    poster_path = "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    rating = data['vote_average']
    overview = data['overview']
    trailer_url = fetch_trailer(movie_id)
    cast = fetch_cast(movie_id)
    return poster_path, rating, overview, trailer_url, cast

# Function to fetch movie trailer
def fetch_trailer(movie_id):
    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=eeaa04316d6da99c068c8a375da80ab4&language=en-US')
    data = response.json()
    if data['results']:
        trailer_key = data['results'][0]['key']
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}"
        return trailer_url
    return None

# Function to fetch movie cast
def fetch_cast(movie_id):
    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key=eeaa04316d6da99c068c8a375da80ab4&language=en-US')
    data = response.json()
    cast_list = [cast['name'] for cast in data['cast'][:5]]  # Get top 5 cast members
    return ", ".join(cast_list)

# Function to recommend movies
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_details = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        details = fetch_movie_details(movie_id)
        recommended_movies_details.append(details)
    return recommended_movies, recommended_movies_details

# Function to fetch trending movies
def fetch_trending_movies():
    response = requests.get('https://api.themoviedb.org/3/trending/movie/week?api_key=eeaa04316d6da99c068c8a375da80ab4')
    data = response.json()
    trending_movies = data['results'][:5]  # Get top 5 trending movies
    trending_movie_details = []
    for movie in trending_movies:
        title = movie['title']
        details = fetch_movie_details(movie['id'])
        trending_movie_details.append((title, details))
    return trending_movie_details

# Function to fetch movies by genre
def fetch_movies_by_genre(genre_id):
    response = requests.get(
        f'https://api.themoviedb.org/3/discover/movie?api_key=eeaa04316d6da99c068c8a375da80ab4&with_genres={genre_id}')
    data = response.json()
    genre_movies = data['results'][:5]  # Get top 5 movies by genre
    genre_movie_details = []
    for movie in genre_movies:
        title = movie['title']
        details = fetch_movie_details(movie['id'])
        genre_movie_details.append((title, details))
    return genre_movie_details

# Load movies data and similarity matrix
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Initialize or load watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Initialize reviews and ratings storage
if 'reviews' not in st.session_state:
    st.session_state.reviews = defaultdict(list)
if 'ratings' not in st.session_state:
    st.session_state.ratings = defaultdict(list)

# Initialize favorite actors and directors
if 'favorite_actors' not in st.session_state:
    st.session_state.favorite_actors = []
if 'favorite_directors' not in st.session_state:
    st.session_state.favorite_directors = []

# Add to watchlist
def add_to_watchlist(movie_name):
    if movie_name not in st.session_state.watchlist:
        st.session_state.watchlist.append(movie_name)
        st.success(f"Added {movie_name} to your watchlist!")
    else:
        st.info(f"{movie_name} is already in your watchlist!")

# Add review and rating
def add_review(movie_name, review, rating):
    st.session_state.reviews[movie_name].append(review)
    st.session_state.ratings[movie_name].append(rating)
    st.success(f"Added your review for {movie_name}!")

# Calculate average rating
def calculate_average_rating(movie_name):
    if st.session_state.ratings[movie_name]:
        return sum(st.session_state.ratings[movie_name]) / len(st.session_state.ratings[movie_name])
    return None

# Fetch movies by favorite actors or directors
def fetch_movies_by_favorites(favorites, type='actor'):
    fav_movies = []
    for favorite in favorites:
        response = requests.get(
            f'https://api.themoviedb.org/3/search/person?api_key=eeaa04316d6da99c068c8a375da80ab4&query={favorite}')
        data = response.json()
        if data['results']:
            person_id = data['results'][0]['id']
            credits_response = requests.get(
                f'https://api.themoviedb.org/3/person/{person_id}/movie_credits?api_key=eeaa04316d6da99c068c8a375da80ab4')
            credits_data = credits_response.json()
            if type == 'actor':
                fav_movies.extend(credits_data['cast'][:5])  # Get top 5 movies
            elif type == 'director':
                fav_movies.extend(credits_data['crew'][:5])  # Get top 5 movies
    return fav_movies

# Streamlit interface
st.markdown('<div class="overlay"></div>', unsafe_allow_html=True)
st.markdown('<h1 class="title">🎬 Movie Recommender System</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="subheader">Find your next favorite movie!</h2>', unsafe_allow_html=True)

# Sidebar for watchlist
st.sidebar.markdown('### Watchlist')
if st.session_state.watchlist:
    for movie in st.session_state.watchlist:
        st.sidebar.write(f"- {movie}")
else:
    st.sidebar.write("Your watchlist is empty.")

# Sidebar for favorite actors and directors
st.sidebar.markdown('### Add Favorite Actors/Directors')
favorite_actor = st.sidebar.text_input('Favorite Actor')
if st.sidebar.button('Add Actor'):
    st.session_state.favorite_actors.append(favorite_actor)
    st.sidebar.write('Favorite Actors:', st.session_state.favorite_actors)

favorite_director = st.sidebar.text_input('Favorite Director')
if st.sidebar.button('Add Director'):
    st.session_state.favorite_directors.append(favorite_director)
    st.sidebar.write('Favorite Directors:', st.session_state.favorite_directors)

if st.sidebar.button('Get Recommendations by Favorites'):
    with st.spinner('Fetching recommendations...'):
        favorite_movies = fetch_movies_by_favorites(st.session_state.favorite_actors, type='actor')
        favorite_movies.extend(fetch_movies_by_favorites(st.session_state.favorite_directors, type='director'))
        for movie in favorite_movies:
            title = movie['title']
            details = fetch_movie_details(movie['id'])
            st.sidebar.write(f"{title} - {details}")

# Search bar to find a movie by title
st.sidebar.markdown('### Search for a Movie')
search_query = st.sidebar.text_input('Enter movie title')
if st.sidebar.button('Search'):
    response = requests.get(
        f'https://api.themoviedb.org/3/search/movie?api_key=eeaa04316d6da99c068c8a375da80ab4&query={search_query}')
    data = response.json()
    if data['results']:
        movie = data['results'][0]
        title = movie['title']
        details = fetch_movie_details(movie['id'])
        poster, rating, overview, trailer_url, cast = details
        st.sidebar.image(poster, width=100)
        st.sidebar.write(f"*{title}*")
        st.sidebar.write(f"Rating: {rating}")
        st.sidebar.write(f"Overview: {overview[:100]}...")
        st.sidebar.write(f"Cast: {cast}")
        if trailer_url:
            st.sidebar.write(f"[Watch Trailer]({trailer_url})")
        if st.sidebar.button(f"Add {title} to Watchlist"):
            add_to_watchlist(title)

# Tabs for Trending, Recommendations, and Genre-based Recommendations
tab1, tab2, tab3, tab4 = st.tabs(["Trending Movies", "Recommendations", "Genre-Based Recommendations", "Reviews"])

with tab1:
    st.markdown('<div class="section-title">Trending Movies:</div>', unsafe_allow_html=True)
    trending_movies = fetch_trending_movies()
    cols = st.columns(5)

    for col, (name, details) in zip(cols, trending_movies):
        poster, rating, overview, trailer_url, cast = details
        with col:
            st.markdown(f"""
                <div class="movie-container">
                    <img src="{poster}" class="movie-poster" style="width:100%; height:auto; border-radius:10px;">
                    <p class="movie-title">{name}</p>
                    <p>⭐ {rating}</p>
                    <p>{overview[:100]}...</p>
                    <p><b>Cast:</b> {cast}</p>
                    {"<a href='" + trailer_url + "' target='_blank'>Watch Trailer</a>" if trailer_url else ""}
                </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-title">Select a movie you like:</div>', unsafe_allow_html=True)
    selected_movie_name = st.selectbox('', movies['title'].values)

    if st.button('Recommend'):
        with st.spinner('Fetching recommendations...'):
            names, details_list = recommend(selected_movie_name)

        st.markdown('<div class="section-title">Recommended Movies:</div>', unsafe_allow_html=True)
        cols = st.columns(5)

        for col, (name, details) in zip(cols, zip(names, details_list)):
            poster, rating, overview, trailer_url, cast = details
            with col:
                st.markdown(f"""
                    <div class="movie-container">
                        <img src="{poster}" class="movie-poster" style="width:100%; height:auto; border-radius:10px;">
                        <p class="movie-title">{name}</p>
                        <p>⭐ {rating}</p>
                        <p>{overview[:100]}...</p>
                        <p><b>Cast:</b> {cast}</p>
                        {"<a href='" + trailer_url + "' target='_blank'>Watch Trailer</a>" if trailer_url else ""}
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Add {name} to Watchlist", key=name):
                    add_to_watchlist(name)

with tab3:
    st.markdown('<div class="section-title">Get recommendations by genre:</div>', unsafe_allow_html=True)
    genres = {
        "Action": 28,
        "Comedy": 35,
        "Drama": 18,
        "Fantasy": 14,
        "Horror": 27,
        "Romance": 10749,
        "Science Fiction": 878,
        "Thriller": 53
    }
    selected_genre = st.selectbox('Select a genre:', list(genres.keys()))

    if st.button('Show Genre Recommendations'):
        with st.spinner('Fetching genre recommendations...'):
            genre_movies = fetch_movies_by_genre(genres[selected_genre])
        st.markdown(f'<div class="section-title">{selected_genre} Movies:</div>', unsafe_allow_html=True)
        cols = st.columns(5)
        for col, (name, details) in zip(cols, genre_movies):
            poster, rating, overview, trailer_url, cast = details
            with col:
                st.markdown(f"""
                    <div class="movie-container">
                        <img src="{poster}" class="movie-poster" style="width:100%; height:auto; border-radius:10px;">
                        <p class="movie-title">{name}</p>
                        <p>⭐ {rating}</p>
                        <p>{overview[:100]}...</p>
                        <p><b>Cast:</b> {cast}</p>
                        {"<a href='" + trailer_url + "' target='_blank'>Watch Trailer</a>" if trailer_url else ""}
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Add {name} to Watchlist", key=name):
                    add_to_watchlist(name)

with tab4:
    st.markdown('<div class="section-title">Add a review for a movie:</div>', unsafe_allow_html=True)
    review_movie_name = st.selectbox('Select a movie:', movies['title'].values, key='review_movie_select')
    review_text = st.text_area('Enter your review:')
    review_rating = st.slider('Rate the movie:', 0, 10, 5)
    if st.button('Submit Review'):
        add_review(review_movie_name, review_text, review_rating)
    st.markdown('<div class="section-title">Reviews:</div>', unsafe_allow_html=True)
    for movie, reviews in st.session_state.reviews.items():
        st.markdown(f"*{movie}*")
        avg_rating = calculate_average_rating(movie)
        if avg_rating:
            st.write(f"Average Rating: {avg_rating:.2f}")
        for review in reviews:
            st.write(f"- {review}")
