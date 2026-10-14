from .db.models import FaqEntry, Room

LOTTE_SOKCHO_SOURCE = "https://resort.lottehotel.com/resort-sokcho/en/room/hotel-deluxe-suite-doubledouble"
ROOMS = [
    ('오션 스위트', '롯데리조트 속초 공식 객실 이미지가 연결된 바다 전망 4인 객실', 4, 180000, 'https://img.lotteresort.com/upload/image/20260604/fbbfa74c-f56b-4849-b059-3dd407805ddd.jpg'),
    ('포레스트 패밀리', '롯데리조트 속초 공식 객실 이미지가 연결된 6인 객실', 6, 220000, 'https://img.lotteresort.com/upload/image/20260604/e67d68c1-7d61-4c4f-8b90-81dd4f879d05.jpg'),
    ('가든 스튜디오', '롯데리조트 속초 공식 객실 이미지가 연결된 2인 객실', 2, 120000, 'https://img.lotteresort.com/upload/image/20260604/2d946cfe-0534-4acf-9e7e-048da3c55a1a.jpg'),
]
FAQS = [('체크인은 몇 시인가요?', '체크인은 오후 3시, 체크아웃은 오전 11시입니다.'), ('반려동물 동반이 가능한가요?', '객실별 정책을 확인해 주세요.'), ('바비큐를 이용할 수 있나요?', '사전 예약으로 바비큐 시설을 이용할 수 있습니다.'), ('주차가 가능한가요?', '투숙객은 무료 주차장을 이용할 수 있습니다.'), ('예약 취소는 어떻게 하나요?', '회원은 내 예약에서, 비회원은 예약번호와 전화번호로 취소할 수 있습니다.')]


def seed_database(session):
    if not session.query(Room).count():
        session.add_all([Room(name=n, description=d, capacity=c, base_price=p, image_url=i) for n, d, c, p, i in ROOMS])
    if not session.query(FaqEntry).count():
        session.add_all([FaqEntry(question=q, answer=a, source_text=f'{q} {a}') for q, a in FAQS])
    session.commit()
