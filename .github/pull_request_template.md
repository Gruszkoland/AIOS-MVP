## 📋 PR Summary

Brief description of changes (1-3 bullet points):

-
-
-

## 🎯 Type of Change

- [ ] 🐛 Bug fix (fixes issue #___)
- [ ] ✨ New feature (closes #___)
- [ ] 📝 Documentation
- [ ] ♻️ Refactoring (no functional change)
- [ ] 🔒 Security fix
- [ ] 🚀 Performance improvement
- [ ] 🧪 Testing

## 🧪 Test Plan

- [ ] Unit tests added/updated
- [ ] `python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80` passes
- [ ] `go test ./... -v` passes (if Go changes)
- [ ] Manual verification: <!-- describe steps -->

## 🔐 Guardian Laws Impact

Which Guardian Laws (G1-G9) does this change affect?
CRITICAL laws (G7 Privacy, G8 Nonmaleficence) require explicit review.

- [ ] No Guardian Laws impacted
- [ ] Laws impacted: <!-- e.g., G7 Privacy — added input sanitization -->

| Law | Impact | Mitigation |
|-----|--------|-----------|
| G1: Unity | | |
| G2: Harmony | | |
| G3: Rhythm | | |
| G4: Causality | | |
| G5: Transparency | | |
| G6: Authenticity | | |
| G7: Privacy | | |
| G8: Nonmaleficence | | |
| G9: Sustainability | | |

## 📋 Pre-Merge Checklist

- [ ] I have read CLAUDE.md and MANIFEST.md
- [ ] I have read the file(s) before editing
- [ ] No hardcoded secrets (using `settings.*` or `os.getenv()`)
- [ ] SQL uses parameterized queries (`?` placeholders only)
- [ ] New POST endpoints have rate limiting (`is_allowed()`)
- [ ] Type hints on all new functions (return type + parameters)
- [ ] Code follows style guide (ruff check passes)
- [ ] No `unsafe` blocks without doc comments (Rust)
- [ ] No `TODO`/`FIXME` in production code
- [ ] Coverage threshold maintained (≥80%)

## 🔗 Related Issues

Closes #___ (if applicable)
Related to #___ (if applicable)

## 📸 Screenshots

(If UI changes, attach screenshots here)

## 💬 Additional Context

Any other information reviewers should know?
