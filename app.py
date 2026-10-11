# ════════════════════════════════════════════════════════════════════════════
#  CineMatch AI — TMDb-Powered Movie Recommendation Platform
#  Run with:  streamlit run app.py
# ════════════════════════════════════════════════════════════════════════════

import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────
# 🔑 TMDb API CONFIGURATION
# Paste your TMDb API key (v3 auth) below. Get one free at:
# https://www.themoviedb.org/settings/api
# ──────────────────────────────────────────────────────────────────────────

TMDB_API_KEY = "bcc934fc2355c30d9c1d92c502b3c83c"    
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_BASE_SMALL = "https://image.tmdb.org/t/p/w200"
REQUEST_TIMEOUT = 10

GENRES = {
    "🔪 Thriller": 53,
    "❤️ Romance": 10749,
    "💥 Action": 28,
    "😂 Comedy": 35,
    "🚀 Sci-Fi": 878,
}

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch AI 🎬",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Netflix/Spotify inspired dark theme
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0b0b0d;
    color: #eaeaea;
}
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.03em; }
h1 { font-size: 3.2rem !important; color: #E50914; margin-bottom: 0 !important;}
h2 { color: #ffffff; font-size: 1.8rem !important; }
h3 { color: #ffffff; font-size: 1.3rem !important; }

.subtitle { color: #9a9a9a; font-size: 1.05rem; margin-top: -4px; }

hr { border-color: #262626 !important; }

.movie-card {
    background: #161616;
    border: 1px solid #262626;
    border-radius: 14px;
    padding: 10px;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    height: 100%;
}
.movie-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 14px 30px rgba(229, 9, 20, 0.25);
    border-color: #E50914;
}
.movie-poster {
    width: 100%;
    border-radius: 10px;
    height: 300px;
    object-fit: cover;
    display: block;
}
.movie-title {
    font-weight: 700;
    font-size: 0.95rem;
    margin-top: 8px;
    color: #f5f5f5;
    min-height: 2.6em;
    line-height: 1.3em;
}
.movie-meta { font-size: 0.78rem; color: #8a8a8a; margin-top: 2px; }
.badge-rating {
    display: inline-block;
    background: #E50914;
    color: #fff;
    font-weight: 700;
    font-size: 0.75rem;
    border-radius: 20px;
    padding: 2px 10px;
    margin-top: 6px;
}
.section-header {
    border-left: 5px solid #E50914;
    padding-left: 14px;
    margin: 34px 0 16px 0;
}
.hero-box {
    background: linear-gradient(135deg, #161616 0%, #0b0b0d 100%);
    border: 1px solid #262626;
    border-radius: 18px;
    padding: 24px;
}
.stButton > button {
    background: #E50914;
    color: white;
    font-weight: 700;
    border: none;
    border-radius: 8px;
}
.stButton > button:hover { background: #b80710; color: white; }
.stTextInput > div > div > input {
    background: #161616;
    color: #eaeaea;
    border: 1px solid #333;
    border-radius: 10px;
}
div[data-testid="stExpander"] {
    background: #131313;
    border: 1px solid #262626;
    border-radius: 10px;
}
.placeholder-poster {
    width: 100%;
    height: 300px;
    background: linear-gradient(135deg, #1c1c1c, #262626);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.2rem;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# TMDb API HELPER FUNCTIONS  (with caching + error handling)
# ──────────────────────────────────────────────────────────────────────────

def _api_get(endpoint: str, params: dict | None = None) -> dict | None:
    """Generic safe GET wrapper for the TMDb API."""
    if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
        return None
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.error("❌ Invalid TMDb API key. Please check the TMDB_API_KEY variable.")
        else:
            st.error(f"⚠️ TMDb API error ({resp.status_code}) while calling `{endpoint}`.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ TMDb API request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🔌 Network error while contacting TMDb: {e}")
        return None


@st.cache_data(show_spinner=False, ttl=3600)
def search_movies(query: str) -> list[dict]:
    data = _api_get("/search/movie", {"query": query, "include_adult": "false"})
    if not data:
        return []
    return data.get("results", [])


@st.cache_data(show_spinner=False, ttl=3600)
def get_movie_details(movie_id: int) -> dict | None:
    return _api_get(f"/movie/{movie_id}")


@st.cache_data(show_spinner=False, ttl=3600)
def get_recommendations(movie_id: int) -> list[dict]:
    data = _api_get(f"/movie/{movie_id}/recommendations")
    if data and data.get("results"):
        return data["results"]
    # Fallback: TMDb "similar" endpoint if no recommendations exist
    data = _api_get(f"/movie/{movie_id}/similar")
    if not data:
        return []
    return data.get("results", [])


@st.cache_data(show_spinner=False, ttl=3600)
def get_movies_by_genre(genre_id: int, page: int = 1) -> list[dict]:
    data = _api_get("/discover/movie", {
        "with_genres": genre_id,
        "sort_by": "popularity.desc",
        "page": page,
    })
    if not data:
        return []
    return data.get("results", [])


def poster_url(path: str | None, size_base: str = IMG_BASE) -> str | None:
    if path:
        return f"{size_base}{path}"
    return None


def year_from_date(date_str: str | None) -> str:
    if date_str and len(date_str) >= 4:
        return date_str[:4]
    return "N/A"


# ──────────────────────────────────────────────────────────────────────────
# INTERACTIVE STAR RATING WIDGET
# ──────────────────────────────────────────────────────────────────────────

if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}


def render_star_rating(movie_id: int, key_prefix: str):
    """Renders an interactive 1-5 star rating control for a given movie."""
    widget_key = f"star_{key_prefix}_{movie_id}"

    if hasattr(st, "feedback"):
        # Native Streamlit star widget (Streamlit >= 1.36)
        result = st.feedback("stars", key=widget_key)
        if result is not None:
            stars = result + 1
            st.session_state.user_ratings[movie_id] = stars
            st.success(f"You rated this {stars} ⭐!")
    else:
        # Fallback for older Streamlit versions
        cols = st.columns([3, 2])
        with cols[0]:
            stars = st.select_slider(
                "Your rating",
                options=[1, 2, 3, 4, 5],
                value=st.session_state.user_ratings.get(movie_id, 3),
                key=widget_key,
                label_visibility="collapsed",
            )
        with cols[1]:
            if st.button("Rate", key=f"{widget_key}_btn"):
                st.session_state.user_ratings[movie_id] = stars
                st.success(f"You rated this {stars} ⭐!")

    existing = st.session_state.user_ratings.get(movie_id)
    if existing:
        st.caption(f"⭐ Your rating: {existing}/5")


# ──────────────────────────────────────────────────────────────────────────
# MOVIE CARD / GRID RENDERING
# ──────────────────────────────────────────────────────────────────────────

def render_movie_card(movie: dict, key_prefix: str):
    title = movie.get("title") or movie.get("name") or "Untitled"
    overview = movie.get("overview") or "No description available."
    release_date = movie.get("release_date", "")
    rating = movie.get("vote_average", 0)
    poster = poster_url(movie.get("poster_path"))
    movie_id = movie.get("id")

    with st.container(border=False):
        st.markdown('<div class="movie-card">', unsafe_allow_html=True)

        if poster:
            st.markdown(f'<img class="movie-poster" src="{poster}" alt="{title}">', unsafe_allow_html=True)
        else:
            st.markdown('<div class="placeholder-poster">🎬</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="movie-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="movie-meta">{year_from_date(release_date)}</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge-rating">⭐ {rating:.1f}</span>', unsafe_allow_html=True)

        with st.expander("📖 Overview & Rate"):
            st.write(overview)
            render_star_rating(movie_id, key_prefix)

        st.markdown('</div>', unsafe_allow_html=True)


def render_movie_grid(movies: list[dict], cols: int = 4, key_prefix: str = "grid"):
    if not movies:
        st.info("No movies to display.")
        return
    for i in range(0, len(movies), cols):
        row_movies = movies[i:i + cols]
        columns = st.columns(cols)
        for col, movie in zip(columns, row_movies):
            with col:
                render_movie_card(movie, f"{key_prefix}_{i}")


# ──────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────

st.markdown("<h1>CINEMATCH AI</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your personal AI-driven movie discovery engine, powered by TMDb.</p>',
            unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# API KEY GUARD
# ──────────────────────────────────────────────────────────────────────────
if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
    st.warning(
        "🔑 **No TMDb API key detected.** Please open `app.py` and paste your key into the "
        "`TMDB_API_KEY` variable near the top of the file, then rerun the app.\n\n"
        "Get a free key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)."
    )
    st.stop()


# ──────────────────────────────────────────────────────────────────────────
# SEARCH BAR
# ──────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header"><h2>🔍 Search Any Movie</h2></div>', unsafe_allow_html=True)

search_col, btn_col = st.columns([5, 1])
with search_col:
    query = st.text_input(
        "Search",
        placeholder="e.g. Inception, The Dark Knight, Interstellar…",
        label_visibility="collapsed",
    )
with btn_col:
    search_clicked = st.button("Search 🎬", use_container_width=True)

if query.strip() and (search_clicked or query):
    with st.spinner("Searching TMDb…"):
        results = search_movies(query.strip())

    if not results:
        st.warning(f"No results found for **'{query}'**. Try a different title.")
    else:
        # If multiple matches, let the user pick the right one
        if len(results) > 1:
            options = {
                f'{m.get("title")} ({year_from_date(m.get("release_date"))})': m
                for m in results[:10]
            }
            chosen_label = st.selectbox("Multiple matches found — pick one:", list(options.keys()))
            main_movie_stub = options[chosen_label]
        else:
            main_movie_stub = results[0]

        main_id = main_movie_stub["id"]
        details = get_movie_details(main_id) or main_movie_stub

        # ── Main movie hero section ──────────────────────────────────
        st.markdown('<div class="hero-box">', unsafe_allow_html=True)
        hero_cols = st.columns([1, 2.3])

        with hero_cols[0]:
            poster = poster_url(details.get("poster_path"))
            if poster:
                st.image(poster, use_container_width=True)
            else:
                st.markdown('<div class="placeholder-poster">🎬</div>', unsafe_allow_html=True)

        with hero_cols[1]:
            st.markdown(f"### {details.get('title', 'Unknown Title')}")
            genres_list = ", ".join(g["name"] for g in details.get("genres", [])) or "N/A"
            st.markdown(f"**Genres:** {genres_list}")
            st.markdown(f"**Release Date:** {details.get('release_date', 'N/A')}")
            st.markdown(f'<span class="badge-rating">⭐ TMDB {details.get("vote_average", 0):.1f}/10</span>',
                        unsafe_allow_html=True)
            st.markdown("")
            st.markdown(f"**Overview:** {details.get('overview', 'No description available.')}")
            st.markdown("---")
            st.markdown("**Rate this movie:**")
            render_star_rating(main_id, "hero")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── AI-driven recommendations ────────────────────────────────
        st.markdown('<div class="section-header"><h2>🤖 AI-Driven Recommendations</h2></div>',
                    unsafe_allow_html=True)
        st.caption(f"Because you searched for **{details.get('title')}**")

        with st.spinner("Finding movies you'll love…"):
            recs = get_recommendations(main_id)[:12]

        if not recs:
            st.info("No similar movies found for this title yet.")
        else:
            render_movie_grid(recs, cols=4, key_prefix=f"rec_{main_id}")

    st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# CATEGORIZED GENRE BROWSING
# ──────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header"><h2>🎭 Browse by Genre</h2></div>', unsafe_allow_html=True)

genre_tabs = st.tabs(list(GENRES.keys()))

for tab, (genre_name, genre_id) in zip(genre_tabs, GENRES.items()):
    with tab:
        st.markdown(f"#### Top Trending — {genre_name}")
        with st.spinner(f"Loading {genre_name} movies…"):
            genre_movies = get_movies_by_genre(genre_id)[:12]

        render_movie_grid(genre_movies, cols=4, key_prefix=f"genre_{genre_id}")

# ──────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#555;font-size:0.8rem;'>"
    "CineMatch AI · Real-time recommendations powered by TMDb · Built with Streamlit"
    "</p>",
    unsafe_allow_html=True,
)