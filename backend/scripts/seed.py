"""CineMatch Database Seeder.

Seeds movies, demo profiles (Neel, Nitin, Mukesh), ratings, and sample watchlists.
Supports MovieLens parquet files with seamless fallback to an embedded dataset
containing 24 starter movies + 17 companion movies required for persona ratings.
Works idempotently on both PostgreSQL and SQLite.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

# Add backend directory to sys.path so app modules are discoverable
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine, ensure_schema_exists
from app.models import Movie, Profile, Rating, User, UserList
from app.core.security import hash_password
from app.services.tmdb import (
    resolve_poster_url,
    resolve_backdrop_url,
    generate_deterministic_synopsis,
    generate_deterministic_credits,
    _normalize_genres,
    TMDB_ID_MAP,
    KNOWN_TMDB_POSTERS,
    KNOWN_TMDB_BACKDROPS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cinematch.seeder")

# =====================================================================
# EMBEDDED DATASET (24 Starter Movies + 17 Companion Persona Titles)
# =====================================================================

STARTER_MOVIES_DATA: List[Dict[str, Any]] = [
    {
        "id": 2571, "title": "The Matrix (1999)", "title_raw": "The Matrix", "year": 1999,
        "genres": ["Action", "Sci-Fi"], "tmdb_id": 603, "item_idx": 1, "vote_average": 4.3, "vote_count": 2590,
        "director": "Lana & Lilly Wachowski", "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
        "runtime": 136, "synopsis": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
        "poster_path": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 260, "title": "Star Wars: Episode IV - A New Hope (1977)", "title_raw": "Star Wars: Episode IV - A New Hope", "year": 1977,
        "genres": ["Action", "Adventure", "Sci-Fi"], "tmdb_id": 11, "item_idx": 3, "vote_average": 4.5, "vote_count": 2991,
        "director": "George Lucas", "cast": ["Mark Hamill", "Harrison Ford", "Carrie Fisher"],
        "runtime": 121, "synopsis": "Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee and two droids to save the galaxy from the Empire's world-destroying battle station.",
        "poster_path": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1196, "title": "Star Wars: Episode V - The Empire Strikes Back (1980)", "title_raw": "Star Wars: Episode V - The Empire Strikes Back", "year": 1980,
        "genres": ["Action", "Adventure", "Sci-Fi"], "tmdb_id": 1891, "item_idx": 6, "vote_average": 4.6, "vote_count": 2990,
        "director": "Irvin Kershner", "cast": ["Mark Hamill", "Harrison Ford", "Carrie Fisher"],
        "runtime": 124, "synopsis": "After the Rebels are brutally overpowered by the Empire, Luke Skywalker begins Jedi training with Yoda while his friends are pursued across the galaxy.",
        "poster_path": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 589, "title": "Terminator 2: Judgment Day (1991)", "title_raw": "Terminator 2: Judgment Day", "year": 1991,
        "genres": ["Action", "Sci-Fi", "Thriller"], "tmdb_id": 280, "item_idx": 2, "vote_average": 4.4, "vote_count": 2649,
        "director": "James Cameron", "cast": ["Arnold Schwarzenegger", "Linda Hamilton", "Edward Furlong"],
        "runtime": 137, "synopsis": "A cyborg, identical to the one who failed to kill Sarah Connor, must now protect her ten-year-old son John from an even more advanced, shape-shifting cyborg.",
        "poster_path": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1240, "title": "The Terminator (1984)", "title_raw": "The Terminator", "year": 1984,
        "genres": ["Action", "Sci-Fi"], "tmdb_id": 218, "item_idx": 4, "vote_average": 4.2, "vote_count": 2100,
        "director": "James Cameron", "cast": ["Arnold Schwarzenegger", "Michael Biehn", "Linda Hamilton"],
        "runtime": 107, "synopsis": "A human soldier is sent from 2029 to 1984 to stop an almost invulnerable cyborg killing machine from executing a young woman whose unborn son will save mankind.",
        "poster_path": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 318, "title": "The Shawshank Redemption (1994)", "title_raw": "The Shawshank Redemption", "year": 1994,
        "genres": ["Drama"], "tmdb_id": 278, "item_idx": 5, "vote_average": 4.8, "vote_count": 2227,
        "director": "Frank Darabont", "cast": ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
        "runtime": 142, "synopsis": "Over the course of several years, two convicts form a friendship, seeking consolation and, ultimately, redemption through basic compassion.",
        "poster_path": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 858, "title": "The Godfather (1972)", "title_raw": "The Godfather", "year": 1972,
        "genres": ["Crime", "Drama"], "tmdb_id": 238, "item_idx": 7, "vote_average": 4.7, "vote_count": 2400,
        "director": "Francis Ford Coppola", "cast": ["Marlon Brando", "Al Pacino", "James Caan"],
        "runtime": 175, "synopsis": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
        "poster_path": "https://images.unsplash.com/photo-1509281373149-e957c6296406?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1509281373149-e957c6296406?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1945, "title": "Titanic (1997)", "title_raw": "Titanic", "year": 1997,
        "genres": ["Drama", "Romance"], "tmdb_id": 597, "item_idx": 8, "vote_average": 4.1, "vote_count": 2250,
        "director": "James Cameron", "cast": ["Leonardo DiCaprio", "Kate Winslet", "Billy Zane"],
        "runtime": 194, "synopsis": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
        "poster_path": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 356, "title": "Forrest Gump (1994)", "title_raw": "Forrest Gump", "year": 1994,
        "genres": ["Comedy", "Drama", "Romance"], "tmdb_id": 13, "item_idx": 9, "vote_average": 4.5, "vote_count": 2194,
        "director": "Robert Zemeckis", "cast": ["Tom Hanks", "Robin Wright", "Gary Sinise"],
        "runtime": 142, "synopsis": "The history of the United States from the 1950s to the '70s unfolds from the perspective of an Alabama man with an IQ of 75.",
        "poster_path": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 912, "title": "Casablanca (1942)", "title_raw": "Casablanca", "year": 1942,
        "genres": ["Drama", "Romance", "War"], "tmdb_id": 289, "item_idx": 10, "vote_average": 4.6, "vote_count": 2069,
        "director": "Michael Curtiz", "cast": ["Humphrey Bogart", "Ingrid Bergman", "Paul Henreid"],
        "runtime": 102, "synopsis": "A cynical expatriate American cafe owner struggles to decide whether or not to help his former lover and her fugitive husband escape the Nazis in French Morocco.",
        "poster_path": "https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 296, "title": "Pulp Fiction (1994)", "title_raw": "Pulp Fiction", "year": 1994,
        "genres": ["Crime", "Drama"], "tmdb_id": 680, "item_idx": 11, "vote_average": 4.6, "vote_count": 2500,
        "director": "Quentin Tarantino", "cast": ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
        "runtime": 154, "synopsis": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "poster_path": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 593, "title": "The Silence of the Lambs (1991)", "title_raw": "The Silence of the Lambs", "year": 1991,
        "genres": ["Crime", "Thriller"], "tmdb_id": 274, "item_idx": 12, "vote_average": 4.5, "vote_count": 2100,
        "director": "Jonathan Demme", "cast": ["Jodie Foster", "Anthony Hopkins", "Lawrence A. Bonney"],
        "runtime": 118, "synopsis": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer.",
        "poster_path": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1198, "title": "Raiders of the Lost Ark (1981)", "title_raw": "Raiders of the Lost Ark", "year": 1981,
        "genres": ["Action", "Adventure"], "tmdb_id": 85, "item_idx": 13, "vote_average": 4.5, "vote_count": 2300,
        "director": "Steven Spielberg", "cast": ["Harrison Ford", "Karen Allen", "Paul Freeman"],
        "runtime": 115, "synopsis": "In 1936, archaeologist and adventurer Indiana Jones is hired by the U.S. government to find the Ark of the Covenant before Adolf Hitler's Nazis can obtain its awesome powers.",
        "poster_path": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1210, "title": "Star Wars: Episode VI - Return of the Jedi (1983)", "title_raw": "Star Wars: Episode VI - Return of the Jedi", "year": 1983,
        "genres": ["Action", "Adventure", "Sci-Fi"], "tmdb_id": 1892, "item_idx": 14, "vote_average": 4.3, "vote_count": 2400,
        "director": "Richard Marquand", "cast": ["Mark Hamill", "Harrison Ford", "Carrie Fisher"],
        "runtime": 131, "synopsis": "After a daring mission to rescue Han Solo from Jabba the Hutt, the Rebels dispatch to Endor to destroy the second Death Star.",
        "poster_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 480, "title": "Jurassic Park (1993)", "title_raw": "Jurassic Park", "year": 1993,
        "genres": ["Action", "Adventure", "Sci-Fi"], "tmdb_id": 329, "item_idx": 15, "vote_average": 4.2, "vote_count": 2200,
        "director": "Steven Spielberg", "cast": ["Sam Neill", "Laura Dern", "Jeff Goldblum"],
        "runtime": 127, "synopsis": "A pragmatic paleontologist touring an almost complete theme park on an island in Central America is tasked with protecting a couple of kids after a power failure causes the cloned dinosaurs to run loose.",
        "poster_path": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1270, "title": "Back to the Future (1985)", "title_raw": "Back to the Future", "year": 1985,
        "genres": ["Comedy", "Sci-Fi"], "tmdb_id": 105, "item_idx": 16, "vote_average": 4.4, "vote_count": 2250,
        "director": "Robert Zemeckis", "cast": ["Michael J. Fox", "Christopher Lloyd", "Lea Thompson"],
        "runtime": 116, "synopsis": "Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past in a time-traveling DeLorean invented by his close friend, the eccentric scientist Doc Brown.",
        "poster_path": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1, "title": "Toy Story (1995)", "title_raw": "Toy Story", "year": 1995,
        "genres": ["Animation", "Children's", "Comedy"], "tmdb_id": 862, "item_idx": 0, "vote_average": 4.3, "vote_count": 2077,
        "director": "John Lasseter", "cast": ["Tom Hanks", "Tim Allen", "Don Rickles"],
        "runtime": 81, "synopsis": "A cowboy doll is profoundly threatened and jealous when a new spaceman action figure supplants him as top toy in a boy's room.",
        "poster_path": "https://images.unsplash.com/photo-1535572290543-960a8046f5af?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1535572290543-960a8046f5af?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 2396, "title": "Shakespeare in Love (1998)", "title_raw": "Shakespeare in Love", "year": 1998,
        "genres": ["Comedy", "Romance"], "tmdb_id": 1934, "item_idx": 17, "vote_average": 4.1, "vote_count": 2100,
        "director": "John Madden", "cast": ["Gwyneth Paltrow", "Joseph Fiennes", "Geoffrey Rush"],
        "runtime": 123, "synopsis": "The world's greatest playwright, William Shakespeare, is young, out of ideas and short of cash, but meets his ideal woman and is inspired to write one of his most famous plays.",
        "poster_path": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1721, "title": "Titanic (1953)", "title_raw": "Titanic", "year": 1953,
        "genres": ["Drama", "Romance"], "tmdb_id": 16535, "item_idx": 18, "vote_average": 3.8, "vote_count": 2050,
        "director": "Jean Negulesco", "cast": ["Clifton Webb", "Barbara Stanwyck", "Robert Wagner"],
        "runtime": 98, "synopsis": "An unhappily married couple struggle to deal with their problems while on board the ill-fated Titanic.",
        "poster_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 50, "title": "The Usual Suspects (1995)", "title_raw": "The Usual Suspects", "year": 1995,
        "genres": ["Crime", "Thriller"], "tmdb_id": 629, "item_idx": 19, "vote_average": 4.5, "vote_count": 2150,
        "director": "Bryan Singer", "cast": ["Kevin Spacey", "Gabriel Byrne", "Chazz Palminteri"],
        "runtime": 106, "synopsis": "A sole survivor tells of the twisty events leading up to a horrific gun battle on a boat, which began when five criminals met at a seemingly random police lineup.",
        "poster_path": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 527, "title": "Schindler's List (1993)", "title_raw": "Schindler's List", "year": 1993,
        "genres": ["Drama", "War"], "tmdb_id": 424, "item_idx": 20, "vote_average": 4.7, "vote_count": 2304,
        "director": "Steven Spielberg", "cast": ["Liam Neeson", "Ralph Fiennes", "Ben Kingsley"],
        "runtime": 195, "synopsis": "In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce after witnessing their persecution by the Nazis.",
        "poster_path": "https://images.unsplash.com/photo-1519791883288-dc8bd696e667?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1519791883288-dc8bd696e667?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1097, "title": "E.T. the Extra-Terrestrial (1982)", "title_raw": "E.T. the Extra-Terrestrial", "year": 1982,
        "genres": ["Children's", "Drama", "Sci-Fi"], "tmdb_id": 601, "item_idx": 21, "vote_average": 4.1, "vote_count": 2000,
        "director": "Steven Spielberg", "cast": ["Henry Thomas", "Drew Barrymore", "Peter Coyote"],
        "runtime": 115, "synopsis": "A troubled child summons the courage to help a friendly alien escape Earth and return to his home planet.",
        "poster_path": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 1617, "title": "L.A. Confidential (1997)", "title_raw": "L.A. Confidential", "year": 1997,
        "genres": ["Crime", "Film-Noir", "Mystery"], "tmdb_id": 2118, "item_idx": 22, "vote_average": 4.4, "vote_count": 2050,
        "director": "Curtis Hanson", "cast": ["Kevin Spacey", "Russell Crowe", "Guy Pearce"],
        "runtime": 138, "synopsis": "As corruption grows in 1950s Los Angeles, three policemen - one strait-laced, one brutal, and one sleazy - investigate a series of murders with their own brand of justice.",
        "poster_path": "https://images.unsplash.com/photo-1486572788966-cfd3d0f58871?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1486572788966-cfd3d0f58871?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "id": 2762, "title": "The Sixth Sense (1999)", "title_raw": "The Sixth Sense", "year": 1999,
        "genres": ["Thriller"], "tmdb_id": 745, "item_idx": 23, "vote_average": 4.4, "vote_count": 2150,
        "director": "M. Night Shyamalan", "cast": ["Bruce Willis", "Haley Joel Osment", "Toni Collette"],
        "runtime": 107, "synopsis": "A child psychologist starts treating a young boy who claims to see dead people.",
        "poster_path": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
    },
]

COMPANION_MOVIES_DATA: List[Dict[str, Any]] = [
    # Neel's companion rated titles
    {"id": 541, "title": "Blade Runner (1982)", "title_raw": "Blade Runner", "year": 1982, "genres": ["Action", "Sci-Fi", "Thriller"], "tmdb_id": 78, "item_idx": 24, "vote_average": 4.4, "vote_count": 1500, "director": "Ridley Scott", "cast": ["Harrison Ford", "Rutger Hauer", "Sean Young"], "runtime": 117},
    {"id": 1036, "title": "Die Hard (1988)", "title_raw": "Die Hard", "year": 1988, "genres": ["Action", "Thriller"], "tmdb_id": 562, "item_idx": 25, "vote_average": 4.3, "vote_count": 1600, "director": "John McTiernan", "cast": ["Bruce Willis", "Alan Rickman", "Bonnie Bedelia"], "runtime": 132},
    {"id": 1200, "title": "Aliens (1986)", "title_raw": "Aliens", "year": 1986, "genres": ["Action", "Sci-Fi", "Thriller"], "tmdb_id": 679, "item_idx": 26, "vote_average": 4.4, "vote_count": 1700, "director": "James Cameron", "cast": ["Sigourney Weaver", "Michael Biehn", "Carrie Henn"], "runtime": 137},
    {"id": 1214, "title": "Alien (1979)", "title_raw": "Alien", "year": 1979, "genres": ["Action", "Sci-Fi", "Horror"], "tmdb_id": 348, "item_idx": 27, "vote_average": 4.5, "vote_count": 1800, "director": "Ridley Scott", "cast": ["Sigourney Weaver", "Tom Skerritt", "John Hurt"], "runtime": 117},
    {"id": 1527, "title": "The Fifth Element (1997)", "title_raw": "The Fifth Element", "year": 1997, "genres": ["Action", "Sci-Fi"], "tmdb_id": 18, "item_idx": 28, "vote_average": 4.1, "vote_count": 1400, "director": "Luc Besson", "cast": ["Bruce Willis", "Milla Jovovich", "Gary Oldman"], "runtime": 126},
    {"id": 1573, "title": "Face/Off (1997)", "title_raw": "Face/Off", "year": 1997, "genres": ["Action", "Sci-Fi", "Thriller"], "tmdb_id": 754, "item_idx": 29, "vote_average": 3.9, "vote_count": 1200, "director": "John Woo", "cast": ["John Travolta", "Nicolas Cage", "Joan Allen"], "runtime": 138},
    {"id": 1580, "title": "Men in Black (1997)", "title_raw": "Men in Black", "year": 1997, "genres": ["Action", "Comedy", "Sci-Fi"], "tmdb_id": 607, "item_idx": 30, "vote_average": 4.1, "vote_count": 1500, "director": "Barry Sonnenfeld", "cast": ["Tommy Lee Jones", "Will Smith", "Linda Fiorentino"], "runtime": 98},
    {"id": 1610, "title": "The Hunt for Red October (1990)", "title_raw": "The Hunt for Red October", "year": 1990, "genres": ["Action", "Thriller"], "tmdb_id": 1669, "item_idx": 31, "vote_average": 4.0, "vote_count": 1100, "director": "John McTiernan", "cast": ["Sean Connery", "Alec Baldwin", "Scott Glenn"], "runtime": 135},
    {"id": 1653, "title": "Gattaca (1997)", "title_raw": "Gattaca", "year": 1997, "genres": ["Drama", "Sci-Fi", "Thriller"], "tmdb_id": 782, "item_idx": 32, "vote_average": 4.1, "vote_count": 1100, "director": "Andrew Niccol", "cast": ["Ethan Hawke", "Uma Thurman", "Jude Law"], "runtime": 106},
    {"id": 1682, "title": "The Truman Show (1998)", "title_raw": "The Truman Show", "year": 1998, "genres": ["Comedy", "Drama", "Sci-Fi"], "tmdb_id": 37165, "item_idx": 33, "vote_average": 4.3, "vote_count": 1400, "director": "Peter Weir", "cast": ["Jim Carrey", "Ed Harris", "Laura Linney"], "runtime": 103},
    # Nitin's companion rated titles
    {"id": 1193, "title": "One Flew Over the Cuckoo's Nest (1975)", "title_raw": "One Flew Over the Cuckoo's Nest", "year": 1975, "genres": ["Drama"], "tmdb_id": 510, "item_idx": 34, "vote_average": 4.5, "vote_count": 1700, "director": "Milos Forman", "cast": ["Jack Nicholson", "Louise Fletcher", "Will Sampson"], "runtime": 133},
    {"id": 1221, "title": "The Godfather: Part II (1974)", "title_raw": "The Godfather: Part II", "year": 1974, "genres": ["Crime", "Drama"], "tmdb_id": 240, "item_idx": 35, "vote_average": 4.7, "vote_count": 1900, "director": "Francis Ford Coppola", "cast": ["Al Pacino", "Robert De Niro", "Robert Duvall"], "runtime": 202},
    {"id": 1968, "title": "Breakfast at Tiffany's (1961)", "title_raw": "Breakfast at Tiffany's", "year": 1961, "genres": ["Drama", "Romance"], "tmdb_id": 164, "item_idx": 36, "vote_average": 4.0, "vote_count": 900, "director": "Blake Edwards", "cast": ["Audrey Hepburn", "George Peppard", "Patricia Neal"], "runtime": 115},
    {"id": 2028, "title": "Saving Private Ryan (1998)", "title_raw": "Saving Private Ryan", "year": 1998, "genres": ["Action", "Drama", "War"], "tmdb_id": 857, "item_idx": 37, "vote_average": 4.6, "vote_count": 1800, "director": "Steven Spielberg", "cast": ["Tom Hanks", "Matt Damon", "Tom Sizemore"], "runtime": 169},
    {"id": 2064, "title": "Roger & Me (1989)", "title_raw": "Roger & Me", "year": 1989, "genres": ["Documentary", "Drama"], "tmdb_id": 13809, "item_idx": 38, "vote_average": 3.9, "vote_count": 400, "director": "Michael Moore", "cast": ["Michael Moore", "Roger B. Smith"], "runtime": 91},
    {"id": 2324, "title": "Life Is Beautiful (1997)", "title_raw": "Life Is Beautiful", "year": 1997, "genres": ["Comedy", "Drama", "War"], "tmdb_id": 637, "item_idx": 39, "vote_average": 4.6, "vote_count": 1600, "director": "Roberto Benigni", "cast": ["Roberto Benigni", "Nicoletta Braschi", "Giorgio Cantarini"], "runtime": 116},
    {"id": 2572, "title": "10 Things I Hate About You (1999)", "title_raw": "10 Things I Hate About You", "year": 1999, "genres": ["Comedy", "Romance"], "tmdb_id": 4951, "item_idx": 40, "vote_average": 4.0, "vote_count": 1100, "director": "Gil Junger", "cast": ["Heath Ledger", "Julia Stiles", "Joseph Gordon-Levitt"], "runtime": 97},
]

ALL_EMBEDDED_MOVIES = STARTER_MOVIES_DATA + COMPANION_MOVIES_DATA

EMBEDDED_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "neel",
        "name": "Neel",
        "avatar": "/avatars/neel.png",
        "bio": "Action & Sci-Fi enthusiast. Loves cyberpunk worlds, space operas, and mind-bending thrillers.",
        "taste_cluster": "Action / Sci-Fi",
        "user_idx": 2955,
        "is_demo": True,
        "is_cold_start": False,
    },
    {
        "id": "nitin",
        "name": "Nitin",
        "avatar": "/avatars/nitin.png",
        "bio": "Drama & Romance enthusiast. Drawn to character-driven storytelling, timeless romance, and emotional journeys.",
        "taste_cluster": "Drama / Romance",
        "user_idx": 2583,
        "is_demo": True,
        "is_cold_start": False,
    },
    {
        "id": "mukesh",
        "name": "Mukesh",
        "avatar": "/avatars/mukesh.png",
        "bio": "New cinephile building my movie profile. Cold-start user discovering new favorites.",
        "taste_cluster": "Cold Start",
        "user_idx": None,
        "is_demo": True,
        "is_cold_start": True,
        "ratings_count": 0,
    },
]

EMBEDDED_RATINGS: Dict[str, Dict[int, float]] = {
    "neel": {
        2571: 5.0, 589: 5.0, 260: 4.5, 1196: 4.5, 1210: 4.0, 1240: 4.5, 480: 4.0,
        1580: 4.0, 541: 4.5, 1036: 4.0, 1200: 4.5, 1214: 4.5, 1270: 4.5, 1527: 4.0,
        1573: 4.0, 1610: 4.0, 1653: 4.0, 1682: 4.0,
    },
    "nitin": {
        318: 5.0, 527: 5.0, 1721: 4.5, 912: 5.0, 356: 4.5, 1193: 4.5, 1221: 5.0,
        1945: 4.5, 1968: 4.5, 2028: 5.0, 2064: 4.5, 2324: 4.5, 2396: 4.5, 2572: 4.0,
    },
    "mukesh": {},
}


def _find_data_file(filename: str) -> Optional[Path]:
    """Locate data file in standard workspace paths, returning None if missing."""
    candidates = [
        Path.cwd() / "data" / "processed" / filename,
        backend_dir.parent / "data" / "processed" / filename,
        Path("/home/yoogkadu/Documents/SEM 5/ML project/data/processed") / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def sanitize_database_movie_media(db: Session) -> int:
    """Sanitize all existing movies in DB, eliminating legacy SVG data URIs and synthetic IDs."""
    movies = db.query(Movie).all()
    sanitized_count = 0
    for m in movies:
        dirty = False
        # Normalize tmdb_id if synthetic or unmapped
        if (m.tmdb_id is None or m.tmdb_id >= 100000) and m.id in TMDB_ID_MAP:
            m.tmdb_id = TMDB_ID_MAP[m.id]
            dirty = True
        elif m.tmdb_id is None:
            m.tmdb_id = m.id
            dirty = True

        # Sanitize poster_path
        if not m.poster_path or "data:image/svg" in m.poster_path or "<svg" in m.poster_path or m.poster_path.endswith(".svg"):
            m.poster_path = resolve_poster_url(movie_id=m.id, tmdb_id=m.tmdb_id)
            dirty = True

        # Sanitize backdrop_path
        if not m.backdrop_path or "data:image/svg" in m.backdrop_path or "<svg" in m.backdrop_path or m.backdrop_path.endswith(".svg"):
            m.backdrop_path = resolve_backdrop_url(movie_id=m.id, tmdb_id=m.tmdb_id)
            dirty = True

        if dirty:
            sanitized_count += 1

    if sanitized_count > 0:
        db.commit()
        logger.info("Sanitized %d existing movie rows in database (zero SVGs)", sanitized_count)
    return sanitized_count


def seed_movies(db: Session, reset: bool = False, force: bool = False) -> int:
    """Seed movies catalog from MovieLens processed parquet or embedded dataset."""
    existing_count = db.query(Movie).count()
    if existing_count > 0 and not (reset or force):
        logger.info("Found %d existing movies in DB, ensuring records are sanitized...", existing_count)
        sanitize_database_movie_media(db)
        return existing_count

    if (reset or force) and existing_count > 0:
        logger.info("Reset/force requested: clearing existing ratings, user_lists, and movies...")
        db.query(Rating).delete()
        db.query(UserList).delete()
        db.query(Movie).delete()
        db.commit()

    modern_json_path = Path(__file__).resolve().parent / "modern_movies_dataset.json"
    movie_objects: List[Movie] = []
    seen_ids = set()

    if modern_json_path.is_file():
        logger.info("Loading modern trending and top-rated movies from %s", modern_json_path)
        import json as _json
        with open(modern_json_path, "r", encoding="utf-8") as _f:
            modern_list = _json.load(_f)

        item_counter = 0
        for item in modern_list:
            mid = int(item["id"])
            if mid in seen_ids:
                continue
            seen_ids.add(mid)

            movie_objects.append(
                Movie(
                    id=mid,
                    movie_lens_id=mid,
                    title=item["title"],
                    title_raw=item.get("title_raw", item["title"]),
                    year=item.get("year"),
                    genres=item.get("genres", ["Drama"]),
                    synopsis=item.get("synopsis") or item.get("overview"),
                    overview=item.get("overview") or item.get("synopsis"),
                    poster_path=item.get("poster_path"),
                    backdrop_path=item.get("backdrop_path"),
                    tmdb_id=item.get("tmdb_id", mid),
                    item_idx=item_counter,
                    vote_average=item.get("vote_average", 7.5),
                    vote_count=item.get("vote_count", 500),
                    director=item.get("director", "Acclaimed Director"),
                    cast=item.get("cast", []),
                    runtime=item.get("runtime", 120),
                )
            )
            item_counter += 1

        # Also ensure benchmark IDs exist for backward-compatible test fixtures
        for item in ALL_EMBEDDED_MOVIES:
            mid = item["id"]
            if mid in seen_ids:
                continue
            seen_ids.add(mid)

            canonical_tmdb = item.get("tmdb_id") or TMDB_ID_MAP.get(mid, mid)
            real_poster = KNOWN_TMDB_POSTERS.get(canonical_tmdb) or resolve_poster_url(movie_id=mid, tmdb_id=canonical_tmdb)
            real_backdrop = KNOWN_TMDB_BACKDROPS.get(canonical_tmdb) or resolve_backdrop_url(movie_id=mid, tmdb_id=canonical_tmdb)

            movie_objects.append(
                Movie(
                    id=mid,
                    movie_lens_id=mid,
                    title=item["title"],
                    title_raw=item.get("title_raw", item["title"]),
                    year=item.get("year"),
                    genres=item.get("genres", []),
                    synopsis=item.get("synopsis"),
                    overview=item.get("synopsis"),
                    poster_path=real_poster,
                    backdrop_path=real_backdrop,
                    tmdb_id=canonical_tmdb,
                    item_idx=item_counter,
                    vote_average=item.get("vote_average", 4.0),
                    vote_count=item.get("vote_count", 2000),
                    director=item.get("director", "Renowned Director"),
                    cast=item.get("cast", []),
                    runtime=item.get("runtime", 120),
                )
            )
            item_counter += 1
    else:
        logger.info("modern_movies_dataset.json not found; fallback to embedded dataset (%d titles)...", len(ALL_EMBEDDED_MOVIES))
        for item in ALL_EMBEDDED_MOVIES:
            mid = item["id"]
            title = item["title"]
            year = item.get("year")
            genres_list = item.get("genres", [])
            canonical_tmdb_id = item.get("tmdb_id") or TMDB_ID_MAP.get(mid, mid)
            poster = resolve_poster_url(movie_id=mid, tmdb_id=canonical_tmdb_id)
            backdrop = resolve_backdrop_url(movie_id=mid, tmdb_id=canonical_tmdb_id)
            synopsis = item.get("synopsis") or generate_deterministic_synopsis(title, year=year, genres=genres_list, movie_id=mid)
            credits_info = generate_deterministic_credits(genres=genres_list, movie_id=mid)

            movie_objects.append(
                Movie(
                    id=mid,
                    movie_lens_id=mid,
                    title=title,
                    title_raw=item.get("title_raw", title),
                    year=year,
                    genres=genres_list,
                    synopsis=synopsis,
                    overview=synopsis,
                    poster_path=poster,
                    backdrop_path=backdrop,
                    tmdb_id=canonical_tmdb_id,
                    item_idx=item.get("item_idx"),
                    vote_average=item.get("vote_average", credits_info["vote_average"]),
                    vote_count=item.get("vote_count", credits_info["vote_count"]),
                    director=item.get("director", credits_info["director"]),
                    cast=item.get("cast", credits_info["cast"]),
                    runtime=item.get("runtime", credits_info["runtime"]),
                )
            )

    # Batch insert movies
    batch_size = 500
    for i in range(0, len(movie_objects), batch_size):
        db.add_all(movie_objects[i : i + batch_size])
        db.flush()
    db.commit()

    total_inserted = db.query(Movie).count()
    logger.info("Successfully seeded %d movies into cinematch.movies", total_inserted)
    return total_inserted


def seed_profiles_and_ratings(db: Session, reset: bool = False, force: bool = False) -> Dict[str, Any]:
    """Seed demo profiles (Neel, Nitin, Mukesh) and pre-load ratings."""
    train_path = _find_data_file("train.parquet")
    train_df = None
    if train_path is not None:
        logger.info("Reading train ratings from %s", train_path)
        train_df = pd.read_parquet(train_path)
    else:
        logger.info("train.parquet not found; using embedded ratings for demo personas")

    results = {}

    for p_spec in EMBEDDED_PROFILES:
        pid = p_spec["id"]
        profile = db.query(Profile).filter(Profile.id == pid).first()

        if profile is None:
            profile = Profile(
                id=pid,
                name=p_spec["name"],
                avatar=p_spec["avatar"],
                bio=p_spec["bio"],
                taste_cluster=p_spec["taste_cluster"],
                user_idx=p_spec["user_idx"],
                is_demo=p_spec["is_demo"],
                is_cold_start=p_spec["is_cold_start"],
                ratings_count=0,
            )
            db.add(profile)
            db.flush()
        elif reset or force:
            profile.name = p_spec["name"]
            profile.avatar = p_spec["avatar"]
            profile.bio = p_spec["bio"]
            profile.taste_cluster = p_spec["taste_cluster"]
            profile.user_idx = p_spec["user_idx"]
            profile.is_demo = p_spec["is_demo"]
            profile.is_cold_start = p_spec["is_cold_start"]
            profile.ratings_count = 0
            db.query(Rating).filter(Rating.profile_id == pid).delete()
            db.flush()

        existing_rating_movie_ids = {
            r.movie_id
            for r in db.query(Rating.movie_id).filter(Rating.profile_id == pid).all()
        }

        ratings_to_add: List[Rating] = []

        valid_movie_map = {m.id: m.item_idx for m in db.query(Movie.id, Movie.item_idx).all()}

        if train_df is not None and profile.user_idx is not None:
            user_ratings = train_df[train_df["user_idx"] == profile.user_idx]
            for _, r_row in user_ratings.iterrows():
                mid = int(r_row["movie_id"])
                if mid in existing_rating_movie_ids or mid not in valid_movie_map:
                    continue
                score = float(r_row["rating"])
                ratings_to_add.append(
                    Rating(
                        profile_id=pid,
                        movie_id=mid,
                        rating=score,
                        item_idx=valid_movie_map.get(mid),
                    )
                )

        # Fallback to embedded persona ratings or modern catalog starter ratings
        if not ratings_to_add and not profile.is_cold_start:
            persona_ratings = EMBEDDED_RATINGS.get(pid, {})
            for mid, score in persona_ratings.items():
                if mid in existing_rating_movie_ids or mid not in valid_movie_map:
                    continue
                ratings_to_add.append(
                    Rating(
                        profile_id=pid,
                        movie_id=mid,
                        rating=score,
                        item_idx=valid_movie_map.get(mid),
                    )
                )

            # If still needs ratings to achieve calibrated state (>= 6)
            if len(ratings_to_add) < 6:
                sample_mids = list(valid_movie_map.keys())[:10]
                for smid in sample_mids:
                    if smid not in existing_rating_movie_ids and not any(r.movie_id == smid for r in ratings_to_add):
                        ratings_to_add.append(
                            Rating(
                                profile_id=pid,
                                movie_id=smid,
                                rating=4.5,
                                item_idx=valid_movie_map.get(smid),
                            )
                        )
                    if len(ratings_to_add) >= 8:
                        break

        if ratings_to_add:
            db.add_all(ratings_to_add)
            db.flush()

        total_ratings = db.query(Rating).filter(Rating.profile_id == pid).count()
        profile.ratings_count = total_ratings
        profile.is_cold_start = (total_ratings < 6)
        db.commit()

        results[pid] = {
            "name": profile.name,
            "ratings_count": profile.ratings_count,
            "is_cold_start": profile.is_cold_start,
            "user_idx": profile.user_idx,
        }
        logger.info(
            "Profile '%s' ready: ratings_count=%d, is_cold_start=%s",
            pid,
            profile.ratings_count,
            profile.is_cold_start,
        )

    return results


def seed_demo_user_lists(db: Session, reset: bool = False, force: bool = False) -> None:
    """Pre-seed sample watchlists for demo profiles."""
    if reset or force:
        db.query(UserList).filter(UserList.profile_id.in_(["neel", "nitin"])).delete(synchronize_session=False)
        db.commit()
    else:
        existing = db.query(UserList).count()
        if existing > 0:
            return

    sample_lists = [
        UserList(profile_id="neel", movie_id=2571, list_type="watchlist"),  # The Matrix
        UserList(profile_id="neel", movie_id=260, list_type="favorites"),   # Star Wars: Ep IV
        UserList(profile_id="nitin", movie_id=1721, list_type="watchlist"), # Titanic
        UserList(profile_id="nitin", movie_id=318, list_type="favorites"),  # Shawshank Redemption
    ]
    movie_ids = {m[0] for m in db.query(Movie.id).all()}
    valid_items = [item for item in sample_lists if item.movie_id in movie_ids]

    if valid_items:
        db.add_all(valid_items)
        db.commit()
        logger.info("Seeded %d sample user_list items", len(valid_items))


def seed_users(db: Session, reset: bool = False, force: bool = False) -> Dict[str, Any]:
    """Seed default demo user accounts (alex@cinematch.io, demo@cinematch.io, etc.).
    
    Ensures that standard user accounts exist with hashed passwords and matching companion Profiles.
    """
    user_count = db.query(User).count()
    if user_count > 0 and not (reset or force):
        logger.info("Found %d existing users in DB, skipping user seeding", user_count)
        return {"existing_users": user_count}

    if (reset or force) and user_count > 0:
        logger.info("Reset/force requested: clearing existing users...")
        db.query(User).delete()
        db.commit()

    demo_users_data = [
        {
            "id": "alex",
            "email": "alex@cinematch.io",
            "password": "Password123!",
            "name": "Alex Morgan",
            "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&q=80",
            "ratings_count": 0,
            "is_cold_start": True,
        },
        {
            "id": "demo",
            "email": "demo@cinematch.io",
            "password": "Password123!",
            "name": "Demo User",
            "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=256&q=80",
            "ratings_count": 0,
            "is_cold_start": True,
        },
        {
            "id": "neel",
            "email": "neel@cinematch.io",
            "password": "Password123!",
            "name": "Neel",
            "avatar": "/avatars/neel.png",
            "ratings_count": 18,
            "is_cold_start": False,
        },
        {
            "id": "nitin",
            "email": "nitin@cinematch.io",
            "password": "Password123!",
            "name": "Nitin",
            "avatar": "/avatars/nitin.png",
            "ratings_count": 14,
            "is_cold_start": False,
        },
        {
            "id": "mukesh",
            "email": "mukesh@cinematch.io",
            "password": "Password123!",
            "name": "Mukesh",
            "avatar": "/avatars/mukesh.png",
            "ratings_count": 0,
            "is_cold_start": True,
        },
    ]

    created_users = []
    for u_data in demo_users_data:
        existing = db.query(User).filter(User.email == u_data["email"]).first()
        if existing is None:
            user = User(
                id=u_data["id"],
                email=u_data["email"],
                hashed_password=hash_password(u_data["password"]),
                name=u_data["name"],
                avatar=u_data["avatar"],
                ratings_count=u_data["ratings_count"],
                is_cold_start=u_data["is_cold_start"],
            )
            db.add(user)
            created_users.append(u_data["email"])

            # Ensure matching Profile entity for FK integrity
            profile = db.query(Profile).filter(Profile.id == u_data["id"]).first()
            if profile is None:
                profile = Profile(
                    id=u_data["id"],
                    name=u_data["name"],
                    avatar=u_data["avatar"],
                    bio=f"CineMatch account for {u_data['name']}",
                    ratings_count=u_data["ratings_count"],
                    is_cold_start=u_data["is_cold_start"],
                    is_demo=True,
                )
                db.add(profile)

    db.commit()
    logger.info("Seeded %d demo users: %s", len(created_users), created_users)
    return {"created": created_users, "total": db.query(User).count()}


def seed_database(db: Optional[Session] = None, force: bool = False, reset: bool = False) -> Dict[str, Any]:
    """Execute complete database seeding pipeline cleanly.
    
    Callable both from CLI and on FastAPI startup lifespan.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        ensure_schema_exists(engine)
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)

        is_force = force or reset
        movie_count = seed_movies(db, reset=is_force, force=is_force)
        sanitize_database_movie_media(db)
        user_results = seed_users(db, reset=is_force, force=is_force)
        profile_results = seed_profiles_and_ratings(db, reset=is_force, force=is_force)
        seed_demo_user_lists(db, reset=is_force, force=is_force)

        return {
            "status": "success",
            "movies_count": movie_count,
            "users": user_results,
            "profiles": profile_results,
        }
    finally:
        if should_close:
            db.close()


def main() -> None:
    """CLI entry point for database seeding."""
    reset = "--reset" in sys.argv or "--force" in sys.argv
    try:
        logger.info("=== Starting CineMatch Database Seeding (reset=%s) ===", reset)
        results = seed_database(force=reset, reset=reset)
        logger.info("=== Seeding Completed Successfully ===")
        logger.info("Total Movies: %d", results["movies_count"])
        for pid, pdata in results["profiles"].items():
            logger.info(
                "Profile '%s' (%s): ratings=%d, cold_start=%s",
                pid,
                pdata["name"],
                pdata["ratings_count"],
                pdata["is_cold_start"],
            )
    except Exception as exc:
        logger.error("Seeding failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
