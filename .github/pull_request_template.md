## Summary

<!-- 1-3 bullet points describing the change -->

-

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring (no functional change)
- [ ] Documentation
- [ ] Infrastructure / CI
- [ ] Security hardening

## Test plan

- [ ] Unit tests added/updated
- [ ] `python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80` passes
- [ ] `go test ./... -v` passes (if Go changes)
- [ ] Manual verification: <!-- describe steps -->

## Guardian Laws impact

<!-- Which Guardian Laws (G1-G9) does this change affect? -->
<!-- CRITICAL laws (G7 Privacy, G8 Nonmaleficence) require explicit review -->

- [ ] No Guardian Laws impacted
- [ ] Laws impacted: <!-- e.g. G7 Privacy — added input sanitization -->

## Checklist

- [ ] I have read the file(s) before editing
- [ ] No hardcoded secrets (using `settings.*` or `os.getenv()`)
- [ ] SQL uses parameterized queries (`?` placeholders)
- [ ] New POST endpoints have rate limiting (`is_allowed()`)
- [ ] Type hints on new functions
