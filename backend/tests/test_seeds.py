import pytest
from app.core.database import SessionLocal
from app.models import Movie, Profile, Rating, UserList


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_seeded_movies_count(db_session):
    """Verify that MovieLens movies catalog is seeded (3883 movies)."""
    count = db_session.query(Movie).count()
    assert count == 3883


def test_seeded_profiles(db_session):
    """Verify pre-seeded profiles: Neel, Nitin, Mukesh."""
    neel = db_session.query(Profile).filter(Profile.id == "neel").first()
    assert neel is not None
    assert neel.name == "Neel"
    assert neel.user_idx == 2955
    assert neel.is_demo is True
    assert neel.is_cold_start is False
    assert neel.ratings_count == 18

    nitin = db_session.query(Profile).filter(Profile.id == "nitin").first()
    assert nitin is not None
    assert nitin.name == "Nitin"
    assert nitin.user_idx == 2583
    assert nitin.is_demo is True
    assert nitin.is_cold_start is False
    assert nitin.ratings_count == 14

    mukesh = db_session.query(Profile).filter(Profile.id == "mukesh").first()
    assert mukesh is not None
    assert mukesh.name == "Mukesh"
    assert mukesh.user_idx is None
    assert mukesh.is_demo is True
    assert mukesh.is_cold_start is True
    assert mukesh.ratings_count == 0


def test_seeded_ratings_validity(db_session):
    """Verify ratings are linked to valid movies in cinematch.movies."""
    neel_ratings = db_session.query(Rating).filter(Rating.profile_id == "neel").all()
    assert len(neel_ratings) == 18
    for r in neel_ratings:
        assert 0.5 <= r.rating <= 5.0
        assert r.movie is not None
        assert r.movie.id == r.movie_id

    nitin_ratings = db_session.query(Rating).filter(Rating.profile_id == "nitin").all()
    assert len(nitin_ratings) == 14
    for r in nitin_ratings:
        assert 0.5 <= r.rating <= 5.0
        assert r.movie is not None
        assert r.movie.id == r.movie_id


def test_mukesh_zero_ratings(db_session):
    """Verify cold-start profile Mukesh has exactly 0 ratings."""
    mukesh_ratings = db_session.query(Rating).filter(Rating.profile_id == "mukesh").all()
    assert len(mukesh_ratings) == 0


def test_seeded_user_lists(db_session):
    """Verify sample watchlist and favorites are seeded for demo profiles."""
    lists = db_session.query(UserList).all()
    assert len(lists) >= 4
    profiles_with_lists = {ul.profile_id for ul in lists}
    assert "neel" in profiles_with_lists
    assert "nitin" in profiles_with_lists
