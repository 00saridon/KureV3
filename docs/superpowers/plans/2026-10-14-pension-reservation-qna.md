# Pension Reservation QnA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Docker-run local web service where users reserve pension rooms and receive KURE-v2-powered answers grounded in pension FAQ data.

**Architecture:** A React/Vite frontend calls a FastAPI REST API. FastAPI owns authentication, reservation transactions, and an in-memory FAQ index backed by PostgreSQL; it uses KURE-v2 MaxSim retrieval when the model can load and a deterministic text-search adapter only when the model is unavailable in local development or tests. PostgreSQL persists users, tokens, rooms, reservations, and FAQ source data. Docker Compose starts all services locally.

**Tech Stack:** React, TypeScript, Vite, FastAPI, SQLAlchemy, Alembic, PostgreSQL, PyTorch, transformers, bcrypt, PyJWT, pytest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-14-pension-reservation-qna-design.md`

## Global Constraints

- Run locally with Docker Compose; do not add cloud-only services.
- Use `nlpai-lab/KURE-v2` with `MultiVectorEncoder.encode_query`, `encode_document`, and MaxSim `similarity` whenever the model is available; use only the specified text-search adapter when local development or tests cannot load it.
- New reservations are `confirmed`; payment is explicitly out of scope.
- Persist password and refresh-token hashes only; never persist plaintext credentials or tokens.
- Allow member ownership checks and guest reservation lookup/cancellation only with reservation code plus phone number.
- Reject past or inverted dates, over-capacity requests, inactive rooms, and overlapping confirmed reservations.
- Return Korean, non-sensitive error messages to the UI.
- Return `현재 안내 정보를 준비 중입니다. 관리자에게 문의해 주세요.` with no sources when there are no active FAQ entries.

## Review Focus

- Two concurrent requests for the final available room/date range: exactly one must create a confirmed reservation.
- Adjacent stays where one checkout equals the next checkin: both reservations must be allowed.
- A member attempting to cancel another member's reservation: return 403 without revealing reservation data.
- A guest using a valid reservation code with an incorrect phone number: return the same not-found response as an invalid code.
- QnA when no active FAQ documents are indexed: return a controlled Korean fallback, not a model or tensor error.
- A duplicate registration request: return a Korean 409 response without exposing a password hash.
- An expired, malformed, or revoked refresh token: return 401 and never mint replacement tokens.
- A reservation using a past date, inverted dates, over-capacity guest count, or inactive room: reject it before creating a row.
- A fresh Docker image: install every backend runtime dependency and successfully return `/health` without relying on host packages.

---

## File Structure

```text
pension-qna/
  docker-compose.yml
  .env.example
  backend/
    Dockerfile
    requirements.txt
    alembic.ini
    app/
      main.py
      core/config.py
      core/security.py
      db/session.py
      db/models.py
      schemas.py
      services/auth.py
      services/reservations.py
      services/retrieval.py
      api/auth.py
      api/rooms.py
      api/reservations.py
      api/qna.py
      api/admin.py
      seed.py
    tests/
      conftest.py
      test_auth.py
      test_reservations.py
      test_retrieval.py
      test_api.py
  frontend/
    Dockerfile
    package.json
    src/
      api/client.ts
      auth/AuthProvider.tsx
      pages/HomePage.tsx
      pages/RoomDetailPage.tsx
      pages/ReservationPage.tsx
      pages/MyReservationsPage.tsx
      pages/GuestLookupPage.tsx
      pages/LoginPage.tsx
      pages/QnaPage.tsx
      App.tsx
```

### Task 1: Docker and application skeleton

**Files:**
- Create: `pension-qna/docker-compose.yml`, `pension-qna/.env.example`
- Create: `pension-qna/backend/Dockerfile`, `pension-qna/backend/requirements.txt`, `pension-qna/backend/app/main.py`
- Create: `pension-qna/frontend/Dockerfile`, `pension-qna/frontend/package.json`
- Test: `pension-qna/backend/tests/test_api.py`

**Interfaces:**
- Produces: `GET /health` returning `{"status": "ok"}`.

- [ ] **Step 1: Write the failing health-check test**

```python
def test_health_returns_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose run --rm backend pytest tests/test_api.py::test_health_returns_ok -v`
Expected: FAIL because the FastAPI app does not exist.

- [ ] **Step 3: Add minimal service setup**

```python
app = FastAPI(title='Pension Reservation QnA')

@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
```

Define `db` as a PostgreSQL service with a persistent volume and pass `DATABASE_URL`, `JWT_SECRET`, and `MODEL_NAME=nlpai-lab/KURE-v2` through environment variables. Pin and install `sqlalchemy`, `psycopg[binary]`, `alembic`, `bcrypt`, `PyJWT`, and the model runtime in `requirements.txt`; the image must not rely on host-installed packages. Add a Docker smoke test that runs `docker compose run --rm backend python -c "from app.db import models; from app.main import app; assert app"` before the health test.

- [ ] **Step 4: Run the health test**

Run: `docker compose run --rm backend pytest tests/test_api.py::test_health_returns_ok -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna
git commit -m "chore: scaffold pension qna services"
```

### Task 2: Persistence models and initial data

**Files:**
- Create: `pension-qna/backend/app/db/session.py`, `pension-qna/backend/app/db/models.py`, `pension-qna/backend/app/seed.py`
- Create: `pension-qna/backend/alembic.ini`, `pension-qna/backend/alembic/`
- Test: `pension-qna/backend/tests/test_reservations.py`

**Interfaces:**
- Produces: SQLAlchemy models `User`, `RefreshToken`, `Room`, `Reservation`, and `FaqEntry`.
- Produces: `seed_database(session)` creating active rooms and FAQ source text.

- [ ] **Step 1: Write the failing seed-data test**

```python
def test_seed_creates_active_room_and_faq(db_session):
    seed_database(db_session)
    assert db_session.query(Room).filter_by(is_active=True).count() >= 1
    assert db_session.query(FaqEntry).filter_by(is_active=True).count() >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose run --rm backend pytest tests/test_reservations.py::test_seed_creates_active_room_and_faq -v`
Expected: FAIL because the models and seed function do not exist.

- [ ] **Step 3: Implement models, migration, and seed data**

Use UUID primary keys. Give `Reservation` a unique `reservation_code`, nullable `user_id`, `check_in`, `check_out`, `guest_count`, `total_price`, `status`, and `cancelled_at`. Store serialized token embeddings in `FaqEntry.embedding` as JSONB. Seed at least three rooms and FAQ entries covering check-in, pets, barbecue, cancellation, and parking.

- [ ] **Step 4: Run migration and seed test**

Run: `docker compose run --rm backend alembic upgrade head && docker compose run --rm backend pytest tests/test_reservations.py::test_seed_creates_active_room_and_faq -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/backend
git commit -m "feat: add pension data models and seed data"
```

### Task 3: Authentication and member authorization

**Files:**
- Create: `pension-qna/backend/app/core/security.py`, `pension-qna/backend/app/services/auth.py`, `pension-qna/backend/app/api/auth.py`
- Modify: `pension-qna/backend/app/main.py`, `pension-qna/backend/app/schemas.py`
- Test: `pension-qna/backend/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`.
- Produces: `current_user` dependency returning the authenticated `User`.

- [ ] **Step 1: Write failing authentication tests**

```python
def test_login_returns_tokens_and_never_returns_password(client):
    client.post('/auth/register', json=REGISTER_BODY)
    response = client.post('/auth/login', json={'email': REGISTER_BODY['email'], 'password': 'secret123!'})
    assert response.status_code == 200
    assert {'access_token', 'refresh_token'} <= response.json().keys()
    assert 'password' not in response.text

def test_refresh_rejects_revoked_token(client):
    refresh_token = login_and_get_refresh_token(client)
    client.post('/auth/refresh', json={'refresh_token': refresh_token})
    response = client.post('/auth/refresh', json={'refresh_token': refresh_token})
    assert response.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm backend pytest tests/test_auth.py -v`
Expected: FAIL because authentication routes do not exist.

- [ ] **Step 3: Implement hashed credentials and rotating refresh tokens**

Use bcrypt password hashes. Hash refresh tokens with SHA-256 before database storage, revoke the presented token when issuing a replacement, sign short-lived access JWTs with PyJWT, and return only public user fields. Add tests for duplicate email (409), malformed access token (401), and refresh-token replay (401).

- [ ] **Step 4: Run authentication tests**

Run: `docker compose run --rm backend pytest tests/test_auth.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/backend
git commit -m "feat: add member authentication"
```

### Task 4: Room availability and reservation domain service

**Files:**
- Create: `pension-qna/backend/app/services/reservations.py`, `pension-qna/backend/app/api/rooms.py`, `pension-qna/backend/app/api/reservations.py`
- Modify: `pension-qna/backend/app/schemas.py`, `pension-qna/backend/app/main.py`
- Test: `pension-qna/backend/tests/test_reservations.py`

**Interfaces:**
- Produces: `create_reservation(session, request, user: User | None) -> Reservation`.
- Produces: `GET /rooms`, `GET /rooms/availability`, and `POST /reservations`.

- [ ] **Step 1: Write failing reservation tests**

```python
def test_overlapping_confirmed_reservation_is_rejected(client, active_room):
    create_reservation(client, active_room.id, '2030-08-10', '2030-08-12')
    response = create_reservation(client, active_room.id, '2030-08-11', '2030-08-13')
    assert response.status_code == 409
    assert response.json()['code'] == 'reservation_conflict'

def test_adjacent_reservations_are_allowed(client, active_room):
    assert create_reservation(client, active_room.id, '2030-08-10', '2030-08-12').status_code == 201
    assert create_reservation(client, active_room.id, '2030-08-12', '2030-08-14').status_code == 201
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm backend pytest tests/test_reservations.py::test_overlapping_confirmed_reservation_is_rejected tests/test_reservations.py::test_adjacent_reservations_are_allowed -v`
Expected: FAIL because reservation routes do not exist.

- [ ] **Step 3: Implement validated transactional creation**

Validate future dates, `check_in < check_out`, capacity, and active room. Lock the selected room with `SELECT ... FOR UPDATE`, query conflicting confirmed reservations using `existing.check_in < requested.check_out AND existing.check_out > requested.check_in`, calculate nights times `base_price`, create a unique reservation code, and commit a `confirmed` reservation.

- [ ] **Step 4: Run reservation tests**

Run: `docker compose run --rm backend pytest tests/test_reservations.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/backend
git commit -m "feat: add room availability and reservations"
```

### Task 5: Member and guest reservation management

**Files:**
- Modify: `pension-qna/backend/app/services/reservations.py`, `pension-qna/backend/app/api/reservations.py`, `pension-qna/backend/app/schemas.py`
- Test: `pension-qna/backend/tests/test_reservations.py`

**Interfaces:**
- Produces: `GET /reservations/me`, `POST /reservations/{reservation_id}/cancel`, `POST /reservations/lookup`, `POST /reservations/guest-cancel`.

- [ ] **Step 1: Write failing ownership and guest-verification tests**

```python
def test_member_cannot_cancel_another_members_reservation(client, reservation_for_other_user, auth_headers):
    response = client.post(f'/reservations/{reservation_for_other_user.id}/cancel', headers=auth_headers)
    assert response.status_code == 403

def test_guest_lookup_with_wrong_phone_is_indistinguishable_from_unknown_code(client, guest_reservation):
    wrong_phone = client.post('/reservations/lookup', json={'reservation_code': guest_reservation.reservation_code, 'phone': '01099999999'})
    unknown_code = client.post('/reservations/lookup', json={'reservation_code': 'PEN-NOT-FOUND', 'phone': '01099999999'})
    assert wrong_phone.status_code == unknown_code.status_code == 404
    assert wrong_phone.json() == unknown_code.json()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm backend pytest tests/test_reservations.py -v`
Expected: FAIL because management routes do not exist.

- [ ] **Step 3: Implement management routes**

Filter member list and cancellation by `Reservation.user_id == current_user.id`. For guests, fetch by both reservation code and normalized phone number; return one generic 404 message when either differs. Change only `confirmed` reservations to `cancelled` and set `cancelled_at`.

- [ ] **Step 4: Run management tests**

Run: `docker compose run --rm backend pytest tests/test_reservations.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/backend
git commit -m "feat: add member and guest reservation management"
```

### Task 6: KURE-v2 FAQ retrieval

**Files:**
- Create: `pension-qna/backend/app/services/retrieval.py`, `pension-qna/backend/app/api/qna.py`, `pension-qna/backend/app/api/admin.py`
- Modify: `pension-qna/backend/app/main.py`, `pension-qna/backend/app/schemas.py`, `pension-qna/backend/app/seed.py`
- Test: `pension-qna/backend/tests/test_retrieval.py`

**Interfaces:**
- Produces: `RetrievalService.search(question: str, limit: int = 3) -> list[RetrievedFaq]`.
- Produces: `POST /qna/ask` and `POST /admin/faq/reindex`.

- [ ] **Step 1: Write failing retrieval tests**

```python
def test_search_returns_faqs_in_descending_maxsim_score_order(retrieval_service):
    results = retrieval_service.search('반려견과 함께 묵을 수 있나요?')
    assert results[0].question == '반려동물 동반이 가능한가요?'
    assert [item.score for item in results] == sorted(item.score for item in results, reverse=True)

def test_empty_index_returns_korean_fallback(empty_retrieval_service):
    response = empty_retrieval_service.answer('체크인 시간은 언제인가요?')
    assert response.answer == '현재 안내 정보를 준비 중입니다. 관리자에게 문의해 주세요.'
    assert response.sources == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm backend pytest tests/test_retrieval.py -v`
Expected: FAIL because the retrieval service does not exist.

- [ ] **Step 3: Implement retrieval and controlled fallback**

Define a `Retriever` protocol with `search(question: str, limit: int) -> list[RetrievedFaq]`. Load `MultiVectorEncoder('nlpai-lab/KURE-v2')` once at app startup when available, then encode active FAQ `source_text` values with `encode_document`, encode incoming questions with `encode_query`, score with `similarity`, and return the top three answer/source pairs in descending score. When loading is unavailable in local development or tests, instantiate a deterministic text-overlap retriever implementing the same protocol. Rebuild the in-memory index through the protected reindex endpoint. Return the specified fallback when the index is empty.

- [ ] **Step 4: Run retrieval tests**

Run: `docker compose run --rm backend pytest tests/test_retrieval.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/backend
git commit -m "feat: add kure faq retrieval"
```

### Task 7: React client foundation and authentication UI

**Files:**
- Create: `pension-qna/frontend/src/api/client.ts`, `pension-qna/frontend/src/auth/AuthProvider.tsx`, `pension-qna/frontend/src/pages/LoginPage.tsx`, `pension-qna/frontend/src/App.tsx`
- Test: `pension-qna/frontend/src/pages/LoginPage.test.tsx`

**Interfaces:**
- Consumes: `/auth/register`, `/auth/login`, `/auth/refresh`.
- Produces: `useAuth()` exposing `user`, `login`, `logout`, and authenticated API requests.

- [ ] **Step 1: Write the failing login screen test**

```tsx
it('stores an access session after successful login', async () => {
  render(<LoginPage />)
  await userEvent.type(screen.getByLabelText('이메일'), 'guest@example.com')
  await userEvent.type(screen.getByLabelText('비밀번호'), 'secret123!')
  await userEvent.click(screen.getByRole('button', { name: '로그인' }))
  expect(await screen.findByText('로그인되었습니다.')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose run --rm frontend npm test -- --run LoginPage.test.tsx`
Expected: FAIL because the page and provider do not exist.

- [ ] **Step 3: Implement API client and auth routes**

Use an API base URL environment variable. Keep the access token in React memory and store the refresh token in `sessionStorage` only for this local MVP; document that this development-only choice must be replaced by an httpOnly cookie before public deployment. Add Korean validation text for invalid fields and routes for register, login, logout, and home.

- [ ] **Step 4: Run frontend authentication test**

Run: `docker compose run --rm frontend npm test -- --run LoginPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/frontend
git commit -m "feat: add web authentication flow"
```

### Task 8: Room search and reservation UI

**Files:**
- Create: `pension-qna/frontend/src/pages/HomePage.tsx`, `pension-qna/frontend/src/pages/RoomDetailPage.tsx`, `pension-qna/frontend/src/pages/ReservationPage.tsx`
- Modify: `pension-qna/frontend/src/App.tsx`, `pension-qna/frontend/src/api/client.ts`
- Test: `pension-qna/frontend/src/pages/ReservationPage.test.tsx`

**Interfaces:**
- Consumes: `/rooms`, `/rooms/availability`, `POST /reservations`.
- Produces: reservation confirmation UI displaying the server-issued code.

- [ ] **Step 1: Write the failing reservation confirmation test**

```tsx
it('shows the server reservation code after a successful reservation', async () => {
  render(<ReservationPage roomId="room-1" />)
  await userEvent.type(screen.getByLabelText('체크인'), '2030-08-10')
  await userEvent.type(screen.getByLabelText('체크아웃'), '2030-08-12')
  await userEvent.click(screen.getByRole('button', { name: '예약 완료' }))
  expect(await screen.findByText(/예약번호: PEN-/)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose run --rm frontend npm test -- --run ReservationPage.test.tsx`
Expected: FAIL because the reservation page does not exist.

- [ ] **Step 3: Implement availability and reservation screens**

Fetch rooms and availability using selected dates and guest count. Disable unavailable rooms, show capacity and price, validate dates before submission, submit the booking request, and show the returned reservation code and Korean error messages.

- [ ] **Step 4: Run reservation UI test**

Run: `docker compose run --rm frontend npm test -- --run ReservationPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/frontend
git commit -m "feat: add reservation booking screens"
```

### Task 9: Reservation management and QnA UI

**Files:**
- Create: `pension-qna/frontend/src/pages/MyReservationsPage.tsx`, `pension-qna/frontend/src/pages/GuestLookupPage.tsx`, `pension-qna/frontend/src/pages/QnaPage.tsx`
- Modify: `pension-qna/frontend/src/App.tsx`, `pension-qna/frontend/src/api/client.ts`
- Test: `pension-qna/frontend/src/pages/GuestLookupPage.test.tsx`, `pension-qna/frontend/src/pages/QnaPage.test.tsx`

**Interfaces:**
- Consumes: `/reservations/me`, member cancel, guest lookup/cancel, and `/qna/ask`.
- Produces: protected member management, verified guest management, and source-grounded QnA screens.

- [ ] **Step 1: Write failing guest and QnA tests**

```tsx
it('does not show reservation details after a failed guest lookup', async () => {
  render(<GuestLookupPage />)
  await userEvent.type(screen.getByLabelText('예약번호'), 'PEN-NOT-FOUND')
  await userEvent.type(screen.getByLabelText('전화번호'), '01099999999')
  await userEvent.click(screen.getByRole('button', { name: '예약 조회' }))
  expect(await screen.findByText('예약 정보를 찾을 수 없습니다.')).toBeInTheDocument()
  expect(screen.queryByText('예약 상세')).not.toBeInTheDocument()
})

it('renders answer and FAQ sources from QnA API', async () => {
  render(<QnaPage />)
  await userEvent.type(screen.getByLabelText('질문'), '반려동물 동반이 가능한가요?')
  await userEvent.click(screen.getByRole('button', { name: '질문하기' }))
  expect(await screen.findByText('객실별 정책을 확인해 주세요.')).toBeInTheDocument()
  expect(screen.getByText('관련 안내')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm frontend npm test -- --run GuestLookupPage.test.tsx QnaPage.test.tsx`
Expected: FAIL because the pages do not exist.

- [ ] **Step 3: Implement management and QnA pages**

Render member-owned reservations and cancellation controls. For guest management, require both values before calling the API and show no details after a generic 404. For QnA, show the Korean answer and up to three source FAQ cards; render the fallback answer without sources when returned.

- [ ] **Step 4: Run management and QnA tests**

Run: `docker compose run --rm frontend npm test -- --run GuestLookupPage.test.tsx QnaPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pension-qna/frontend
git commit -m "feat: add reservation management and qna ui"
```

### Task 10: End-to-end local verification and documentation

**Files:**
- Create: `pension-qna/README.md`
- Modify: `pension-qna/docker-compose.yml`, `pension-qna/.env.example`
- Test: `pension-qna/backend/tests/test_api.py`

**Interfaces:**
- Produces: documented `docker compose up --build` startup path and a working local MVP.

- [ ] **Step 1: Write the failing end-to-end API scenario test**

```python
def test_member_can_book_then_cancel_and_qna_returns_sources(client, auth_headers, active_room):
    reservation = client.post('/reservations', headers=auth_headers, json=valid_reservation_body(active_room.id))
    assert reservation.status_code == 201
    cancellation = client.post(f"/reservations/{reservation.json()['id']}/cancel", headers=auth_headers)
    assert cancellation.status_code == 200
    answer = client.post('/qna/ask', json={'question': '바비큐를 이용할 수 있나요?'})
    assert answer.status_code == 200
    assert len(answer.json()['sources']) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose run --rm backend pytest tests/test_api.py::test_member_can_book_then_cancel_and_qna_returns_sources -v`
Expected: FAIL until all API components are wired together.

- [ ] **Step 3: Write local operating documentation**

Document prerequisites, `.env` creation, `docker compose up --build`, database migration/seed commands, model first-download behavior, test commands, example member and guest flows, and the explicit absence of payment integration.

- [ ] **Step 4: Run full verification**

Run: `docker compose up --build -d && docker compose run --rm backend pytest -q && docker compose run --rm frontend npm test -- --run && docker compose down`
Expected: all backend and frontend tests pass and services start without errors.

- [ ] **Step 5: Commit**

```bash
git add pension-qna
git commit -m "docs: add local setup and verification guide"
```

## Self-Review

- Spec coverage: Tasks 1–2 supply Docker, PostgreSQL, models, migrations, rooms, FAQs, and seed data. Task 3 supplies member authentication. Tasks 4–5 cover creation, availability, ownership, guest lookup, cancellation, and conflict rules. Task 6 covers KURE-v2 indexing and QnA. Tasks 7–9 cover every specified browser flow. Task 10 covers local operation.
- Placeholder scan: no unresolved implementation placeholders or vague task steps remain.
- Type consistency: all backend search callers use `RetrievalService.search(question, limit)`; all booking callers use the documented reservation routes; frontend screens use those routes.
- Review focus: Tasks 1, 3, 4–6, and 10 contain the Docker dependency, authentication, validation, conflict, authorization, guest-privacy, and empty-index checks named above.
