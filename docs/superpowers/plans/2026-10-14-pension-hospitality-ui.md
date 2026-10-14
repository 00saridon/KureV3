# Pension Hospitality UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a responsive hotel-style customer reservation UI and protected administrator operations UI.

**Architecture:** A React/Vite SPA uses a typed API client and auth context. Customer pages consume room, reservation, and QnA routes; administrator pages consume protected operational routes and render no data until admin authorization succeeds.

**Tech Stack:** React, TypeScript, Vite, React Router, Vitest, Testing Library, CSS.

**Spec:** `docs/superpowers/specs/2026-10-14-pension-hospitality-ui-design.md`

## Global Constraints

- Use an independent navy, ivory, and gold hospitality visual system; do not copy Hilton logos or layouts.
- Reference Lotte Resort Sokcho CDN image URLs without committing image files.
- Use Korean UI copy, labelled inputs, keyboard-accessible controls, and WCAG AA contrast.
- Keep administrator routes protected and responsive layouts usable on mobile.

## Review Focus

- An unauthenticated visitor opening `/admin` sees no reservation or customer data.
- A failed room-image request preserves room name, price, and reservation CTA.
- A mobile viewport keeps reservation inputs and submit controls usable.
- A QnA fallback response renders no empty source section.
- A non-admin API response shows a Korean authorization error rather than a blank dashboard.

---

### Task 1: Vite foundation and hospitality shell

**Files:** Create `pension-qna/frontend/index.html`, `src/main.tsx`, `src/App.tsx`, `src/styles.css`, `src/pages/HomePage.tsx`; modify `package.json`; test `src/App.test.tsx`.

**Produces:** `App` with public navigation, responsive header, image-backed room-card shell, and `<Outlet />` routes.

- [ ] Write `App.test.tsx` asserting `screen.getByRole('link', { name: '객실' })` and `screen.getByRole('link', { name: 'QnA' })` exist.
- [ ] Run `npm test -- --run src/App.test.tsx`; expect failure because the app does not exist.
- [ ] Create the Vite entry point, Router routes, navy/ivory/gold CSS tokens, accessible navigation, and `HomePage` hero/search/card layout; use `img` alt text and an error fallback background.
- [ ] Run `npm test -- --run src/App.test.tsx`; expect pass.
- [ ] Commit with `git commit -m "feat: add hospitality customer shell"`.

### Task 2: Customer booking and QnA pages

**Files:** Create `src/api/client.ts`, `src/pages/RoomDetailPage.tsx`, `src/pages/ReservationPage.tsx`, `src/pages/QnaPage.tsx`; modify `src/App.tsx`; test `src/pages/ReservationPage.test.tsx`, `src/pages/QnaPage.test.tsx`.

**Consumes:** `GET /rooms`, `GET /rooms/{id}`, `POST /reservations`, and `POST /qna/ask`.

- [ ] Write a reservation test that submits dates and asserts `예약번호: PEN-` after a mocked successful API response; write a QnA test that asserts the fallback text has no `관련 안내` heading.
- [ ] Run `npm test -- --run src/pages/ReservationPage.test.tsx src/pages/QnaPage.test.tsx`; expect failure because pages do not exist.
- [ ] Implement typed request helpers, labelled reservation inputs, Korean error display, confirmation code rendering, QnA answer/source cards, and mobile single-column styles.
- [ ] Run the two test files; expect pass.
- [ ] Commit with `git commit -m "feat: add booking and qna customer pages"`.

### Task 3: Administrator operations UI

**Files:** Create `src/auth/AuthProvider.tsx`, `src/pages/AdminDashboardPage.tsx`, `src/pages/AdminReservationsPage.tsx`, `src/pages/AdminFaqPage.tsx`; modify `src/App.tsx`, `src/api/client.ts`; test `src/pages/AdminDashboardPage.test.tsx`.

**Consumes:** authenticated `/admin` KPI, reservation, room, FAQ, and reindex endpoints. **Produces:** protected `/admin/*` routes.

- [ ] Write tests asserting an unauthenticated `/admin` route displays `관리자 로그인이 필요합니다.` and an authorized dashboard displays `오늘의 예약` and `FAQ 색인`.
- [ ] Run `npm test -- --run src/pages/AdminDashboardPage.test.tsx`; expect failure because admin pages do not exist.
- [ ] Implement auth context, route guard, KPI cards, filterable reservation table, room activation/price controls, FAQ editor, and reindex status message. Render Korean 403 errors without dashboard data.
- [ ] Run the administrator test and full `npm test -- --run`; expect pass.
- [ ] Commit with `git commit -m "feat: add protected admin operations UI"`.

## Self-Review

- Tasks 1–2 implement the customer layout, image references, booking, QnA, Korean copy, and mobile behavior; Task 3 implements administrator operations and authorization.
- Every route and component named by a later task is defined by its owning task.
- Each Review Focus condition has a corresponding Task 1–3 test.
