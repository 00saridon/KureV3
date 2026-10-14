# 펜션 예약 QnA 서비스 설계

## 목적

로컬 서버에서 실행되는 웹 서비스로, 고객이 객실을 검색하고 예약을 생성·조회·취소하며 KURE-v2 기반 QnA로 펜션 정보를 찾을 수 있게 한다. 결제 연동은 이 범위에 포함하지 않으며, 신규 예약은 즉시 `confirmed` 상태가 된다.

## 사용자와 인증

- 회원은 이메일과 비밀번호로 가입·로그인하며 JWT 액세스 토큰과 리프레시 토큰을 사용한다.
- 회원은 자신의 예약 목록을 보고 취소할 수 있다.
- 비회원은 예약번호와 전화번호가 모두 일치할 때만 예약 상세를 보고 취소할 수 있다.
- 비밀번호는 해시만 저장한다. 예약번호와 전화번호는 필요한 응답에서만 최소한으로 노출한다.

## 구성

React 프론트엔드는 REST API를 통해 FastAPI 백엔드와 통신한다. FastAPI는 인증, 객실 조회, 예약 트랜잭션, QnA 검색을 담당한다. PostgreSQL은 서비스 데이터와 FAQ 임베딩을 저장한다. Docker Compose가 프론트엔드, 백엔드, 데이터베이스를 로컬에서 함께 실행한다.

KURE-v2는 FastAPI 프로세스에서 한 번 로드한다. FAQ와 객실 안내 문서를 `encode_document`로 색인하고, 질문은 `encode_query`로 변환한다. `similarity`의 MaxSim 점수 상위 3개 문서를 답변 근거로 반환한다.

모델 가중치를 아직 내려받을 수 없거나 로딩할 수 없는 개발·테스트 환경에서는 동일한 검색 서비스 인터페이스를 유지하는 텍스트 기반 대체 검색을 사용한다. 프로덕션 또는 모델 사용이 가능한 환경에서는 반드시 KURE-v2 검색을 우선한다. 두 방식 모두 활성 FAQ만 대상으로 하고, API 응답 형식과 최대 3개의 근거 반환 규칙은 동일하다.

## 데이터 모델

### users

`id`, `email`(고유), `password_hash`, `name`, `phone`, `is_admin`, `created_at`

### refresh_tokens

`id`, `user_id`, `token_hash`, `expires_at`, `created_at`, `revoked_at`

### rooms

`id`, `name`, `description`, `capacity`, `base_price`, `image_url`, `is_active`, `created_at`

### reservations

`id`, `reservation_code`(고유), `room_id`, `user_id`(nullable), `guest_name`, `guest_phone`, `check_in`, `check_out`, `guest_count`, `total_price`, `status`, `created_at`, `cancelled_at`

`status`는 `confirmed` 또는 `cancelled`이다. `check_out`은 `check_in`보다 늦어야 한다.

### faq_entries

`id`, `category`, `question`, `answer`, `source_text`, `embedding`, `is_active`, `updated_at`

임베딩은 KURE-v2가 반환하는 가변 길이 토큰 벡터이므로 PostgreSQL에는 직렬화한 값(JSONB)으로 보관한다. 서버 시작 시 활성 FAQ를 메모리에 올려 검색한다. FAQ 수정 후에는 관리자 재색인 API가 전체 메모리 색인을 갱신한다. 대체 검색 모드에서는 임베딩을 요구하지 않으며, FAQ 원문을 메모리에 올려 검색한다.

## API

- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- `GET /rooms`, `GET /rooms/{room_id}`, `GET /rooms/availability`
- `POST /reservations`, `GET /reservations/me`, `POST /reservations/{reservation_id}/cancel`
- `POST /reservations/lookup`, `POST /reservations/guest-cancel`
- `POST /qna/ask`
- `POST /admin/faq/reindex`

회원 예약 API는 인증된 사용자 소유 여부를 확인한다. 비회원 API는 예약번호와 전화번호의 일치를 확인한다. 관리자 API는 `is_admin` 권한을 요구한다.

## 예약 규칙

예약 생성은 데이터베이스 트랜잭션 안에서 수행한다. 같은 객실의 `confirmed` 예약과 새 예약이 다음 조건으로 겹치면 생성하지 않는다.

`existing.check_in < requested.check_out AND existing.check_out > requested.check_in`

과거 날짜, 역전된 날짜, 객실 정원 초과, 비활성 객실은 모두 거부한다. 취소된 예약은 다시 취소할 수 없다. 결제 없이 예약이 생성되면 즉시 `confirmed` 상태와 고유 예약번호를 반환한다.

## 프론트엔드 화면

- 홈: 펜션 소개, 객실·날짜 검색, QnA 진입
- 객실 목록·상세: 가용성, 정원, 기준 요금, 예약 버튼
- 예약 폼·완료: 날짜·인원·예약자 입력, 예약번호 표시
- 내 예약: 로그인한 회원의 예약 목록과 취소
- 비회원 예약 조회: 예약번호·전화번호 입력 및 취소
- 회원가입·로그인
- QnA: 질문 입력, 답변, 근거 FAQ 최대 3개

## 오류 처리

백엔드는 검증 오류, 인증 실패, 권한 부족, 예약 충돌, 찾을 수 없는 데이터에 안정적인 오류 코드를 반환한다. 프론트엔드는 날짜·인원·예약 상태·로그인 문제를 사용자가 이해할 수 있는 한국어로 표시한다. 인증 정보와 상세 데이터는 오류 메시지에 포함하지 않는다. 활성 FAQ가 없으면 QnA는 `현재 안내 정보를 준비 중입니다. 관리자에게 문의해 주세요.`와 빈 근거 목록을 반환한다.

## 검증 전략

- 단위 테스트: 날짜 겹침, 총액 계산, 예약번호 생성, 검색 결과 정렬
- API 통합 테스트: 가입·로그인, 회원 예약 생성·취소, 비회원 조회·취소, 권한 검증
- 데이터베이스 테스트: 동시 예약 시 충돌 차단
- QnA 테스트: 질의 임베딩과 문서 임베딩을 사용한 상위 결과 반환
- 로컬 실행 검증: Docker Compose로 서비스·PostgreSQL 기동, 초기 객실·FAQ 데이터와 임베딩 색인 생성

## 범위 제외

- 실제 결제·환불·세금계산서
- 관리자용 UI
- 외부 예약 채널 동기화
- 이미지 업로드 저장소
