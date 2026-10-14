from datetime import date

from app.db.models import Reservation, Room, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base


def test_reservation_persists_member_and_booking_details():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        user = User(
            email="member@example.com",
            password_hash="hashed-password",
            name="회원",
            phone="01012345678",
        )
        room = Room(name="테스트 객실", description="테스트", capacity=2, base_price=100000)
        session.add_all([user, room])
        session.flush()
        reservation = Reservation(
            reservation_code="PEN-TEST-0001",
            room_id=room.id,
            user_id=user.id,
            guest_name="회원",
            guest_phone="01012345678",
            check_in=date(2030, 1, 1),
            check_out=date(2030, 1, 2),
            guest_count=2,
            total_price=100000,
            status="confirmed",
        )
        session.add(reservation)
        session.commit()

        saved = session.get(Reservation, reservation.id)
        assert saved is not None
        assert saved.user_id == user.id
        assert saved.status == "confirmed"
