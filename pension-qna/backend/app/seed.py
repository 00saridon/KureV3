from .db.models import FaqEntry, Room

ROOMS = [('오션 스위트', '바다가 보이는 4인 객실', 4, 180000), ('포레스트 패밀리', '숲 전망의 6인 객실', 6, 220000), ('가든 스튜디오', '정원 옆 2인 객실', 2, 120000)]
FAQS = [('체크인은 몇 시인가요?', '체크인은 오후 3시, 체크아웃은 오전 11시입니다.'), ('반려동물 동반이 가능한가요?', '객실별 정책을 확인해 주세요.'), ('바비큐를 이용할 수 있나요?', '사전 예약으로 바비큐 시설을 이용할 수 있습니다.'), ('주차가 가능한가요?', '투숙객은 무료 주차장을 이용할 수 있습니다.'), ('예약 취소는 어떻게 하나요?', '회원은 내 예약에서, 비회원은 예약번호와 전화번호로 취소할 수 있습니다.')]


def seed_database(session):
    if not session.query(Room).count():
        session.add_all([Room(name=n, description=d, capacity=c, base_price=p) for n, d, c, p in ROOMS])
    if not session.query(FaqEntry).count():
        session.add_all([FaqEntry(question=q, answer=a, source_text=f'{q} {a}') for q, a in FAQS])
    session.commit()
