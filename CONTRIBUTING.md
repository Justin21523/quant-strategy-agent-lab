# Contributing

Use short-lived branches:

- `feat/<scope>-<description>`
- `fix/<scope>-<description>`
- `docs/<description>`
- `chore/<description>`

Use Conventional Commit-style subjects:

```text
feat(market): add normalized OHLCV endpoint
fix(router): preserve route after refresh
test(indicators): cover RSI warm-up behavior
docs(dsl): document crossover semantics
```

Before committing:

```bash
make check
```
