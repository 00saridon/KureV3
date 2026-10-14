from app.db.models import FaqEntry, Room
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.seed import seed_database


def test_seed_creates_active_rooms_and_faqs():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        seed_database(session)
        assert session.query(Room).filter_by(is_active=True).count() >= 3
        assert session.query(FaqEntry).filter_by(is_active=True).count() >= 5
