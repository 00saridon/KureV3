import secrets
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Reservation, Room


class ReservationConflict(Exception):
    pass


class ReservationValidationError(Exception):
    pass


def create_reservation(
    session: Session,
    room_id: int,
    guest_name: str,
    guest_phone: str,
    check_in: date,
    check_out: date,
    guest_count: int,
    user_id: int | None,
) -> Reservation:
    room = session.get(Room, room_id)
    if room is None or not room.is_active:
        raise ReservationValidationError("예약할 수 없는 객실입니다.")
    if check_in < date.today() or check_in >= check_out or guest_count < 1 or guest_count > room.capacity:
        raise ReservationValidationError("예약 정보를 확인해 주세요.")
    conflict = session.scalar(select(Reservation).where(
        Reservation.room_id == room_id,
        Reservation.status == "confirmed",
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    ))
    if conflict is not None:
        raise ReservationConflict("이미 예약된 날짜입니다.")
    nights = (check_out - check_in).days
    reservation = Reservation(
        reservation_code="PEN-" + secrets.token_hex(5).upper(), room_id=room.id, user_id=user_id,
        guest_name=guest_name, guest_phone=guest_phone, check_in=check_in, check_out=check_out,
        guest_count=guest_count, total_price=nights * room.base_price, status="confirmed",
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation
