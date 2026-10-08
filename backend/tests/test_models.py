import pytest
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models import Movie, Profile, Rating, UserList


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_movie_model_fields_and_properties(db_session):
    """Verify movie properties and retrieval."""
    movie = db_session.query(Movie).filter(Movie.id == 1).first()
    assert movie is not None
    assert movie.title == "Toy Story"
    assert movie.year == 1995
    assert isinstance(movie.genres, list)
    assert "Animation" in movie.genres
    assert movie.poster_path.startswith("data:image/svg+xml;base64,")
    assert movie.backdrop_path.startswith("data:image/svg+xml;base64,")
    assert movie.movie_id == 1
    assert len(movie.effective_synopsis()) > 20


def test_profile_model(db_session):
    """Verify profile querying and properties."""
    neel = db_session.query(Profile).filter(Profile.id == "neel").first()
    assert neel is not None
    assert neel.name == "Neel"
    assert neel.user_idx == 2955
    assert neel.is_cold_start is False
    assert neel.ratings_count > 0

    mukesh = db_session.query(Profile).filter(Profile.id == "mukesh").first()
    assert mukesh is not None
    assert mukesh.user_idx is None
    assert mukesh.is_cold_start is True
    assert mukesh.ratings_count == 0


def test_rating_unique_constraint(db_session):
    """Verify unique constraint on (profile_id, movie_id)."""
    # Create temporary profile
    temp_profile = Profile(
        id="test_unique_user",
        name="Test User",
        avatar="/avatars/test.png",
        is_demo=False,
        is_cold_start=True,
    )
    db_session.add(temp_profile)
    db_session.flush()

    r1 = Rating(profile_id="test_unique_user", movie_id=1, rating=4.5)
    db_session.add(r1)
    db_session.flush()

    r2 = Rating(profile_id="test_unique_user", movie_id=1, rating=3.0)
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_rating_bounds_check_constraint(db_session):
    """Verify rating bounds check constraint (0.5 <= rating <= 5.0)."""
    temp_profile = Profile(
        id="test_bounds_user",
        name="Bounds User",
        avatar="/avatars/test.png",
        is_demo=False,
        is_cold_start=True,
    )
    db_session.add(temp_profile)
    db_session.flush()

    # Out of range rating (e.g. 5.5)
    invalid_rating = Rating(profile_id="test_bounds_user", movie_id=1, rating=5.5)
    db_session.add(invalid_rating)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_cascade_delete(db_session):
    """Verify cascade deletion of ratings and user_lists when profile is removed."""
    temp_profile = Profile(
        id="test_cascade_user",
        name="Cascade User",
        avatar="/avatars/test.png",
        is_demo=False,
        is_cold_start=True,
    )
    db_session.add(temp_profile)
    db_session.flush()

    rating = Rating(profile_id="test_cascade_user", movie_id=1, rating=4.0)
    user_list = UserList(profile_id="test_cascade_user", movie_id=1, list_type="watchlist")
    db_session.add_all([rating, user_list])
    db_session.flush()

    # Delete profile
    db_session.delete(temp_profile)
    db_session.flush()

    # Verify ratings and user_lists were cascade deleted
    r_count = db_session.query(Rating).filter(Rating.profile_id == "test_cascade_user").count()
    ul_count = db_session.query(UserList).filter(UserList.profile_id == "test_cascade_user").count()
    assert r_count == 0
    assert ul_count == 0
    db_session.rollback()
