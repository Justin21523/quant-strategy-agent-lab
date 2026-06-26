# ADR-0001: Start as a modular monolith

- Status: Accepted
- Date: 2026-06-25

Use one modular FastAPI backend and one modular Vanilla JavaScript frontend. This keeps local development teachable and refactoring cheap while preserving boundaries for future extraction. Microservices are not justified yet.
