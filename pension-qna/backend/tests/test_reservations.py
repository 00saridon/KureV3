from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Room
from app.db.session import Base
from app.services.reservations import ReservationConflict, create_reservation


def test_overlapping_confirmed_reservation_is_rejected():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        room = Room(name="객실", description="설명", capacity=2, base_price=100000)
        session.add(room)
        session.commit()
        create_reservation(session, room.id, "예약자", "01012345678", date(2030, 8, 10), date(2030, 8, 12), 2, None)
        with pytest.raises(ReservationConflict):
            create_reservation(session, room.id, "다른 예약자", "01099999999", date(2030, 8, 11), date(2030, 8, 13), 2, None)
