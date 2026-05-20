# GitHub Pages Configuration

**AIOS MVP Documentation Site Setup**

---

## Overview

GitHub Pages serves the AIOS MVP documentation at: **https://aios-mvp.pages.github.io**

## Quick Setup (Manual — One-time)

1. **Go to Repository Settings**
   - Navigate to: https://github.com/Gruszkoland/AIOS-MVP/settings/pages
   - Or: Settings → Pages (left sidebar)

2. **Configure Source**
   - **Build and deployment:**
     - Source: `Deploy from a branch`
     - Branch: `main`
     - Folder: `/ (root)` or `/docs` (depends on mdbook build output)

3. **Save**
   - Click "Save"
   - GitHub will build and deploy automatically (takes ~1-2 minutes)

4. **Verify**
   - Visit: https://aios-mvp.pages.github.io
   - You should see the documentation homepage

---

## Automatic Deployment (via GitHub Actions)

The `doc-build.yml` workflow automatically:

1. **Builds documentation** on push to `main`
2. **Runs spell check** and **link validation**
3. **Generates mdbook output**
4. **Deploys to GitHub Pages**

### Workflow File

See `.github/workflows/doc-build.yml`:

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/book
    cname: aios-mvp.pages.github.io  # optional: custom domain
```

### Build Process

```
docs/
├── book.toml          (mdbook config)
├── src/
│   ├── SUMMARY.md     (navigation)
│   ├── chapter-1.md
│   └── ...
└── src/diagrams/      (Mermaid diagrams)
```

**Commands:**
```bash
mdbook build docs/              # Build to docs/book/
mdbook serve docs/              # Preview at localhost:3000
```

---

## Custom Domain (Optional)

If using custom domain (e.g., `docs.adrion369.dev`):

1. **Add DNS record:**
   ```
   CNAME docs.adrion369.dev → aios-mvp.pages.github.io
   ```

2. **Configure in Settings:**
   - Settings → Pages → Custom domain
   - Enter: `docs.adrion369.dev`

3. **Verify:**
   - ✅ Check mark appears = DNS verified
   - Site now accessible at: `https://docs.adrion369.dev`

---

## Documentation Structure

```
/docs/
├── README.md                          (index)
├── ARCHITECTURE_VISUAL.md             (technical overview)
├── EXECUTIVE_ARCHITECTURE_SUMMARY.md  (non-technical summary)
├── KPI_DASHBOARD.md                   (metrics & tracking)
├── MASTER_RISK_MATRIX.md              (risk assessment)
├── diagrams/                          (Mermaid diagrams)
│   ├── 01-orchestrator-guardians.mermaid
│   ├── 02-decision-flow.mermaid
│   ├── 03-genesis-record-chain.mermaid
│   └── 04-162d-space-topology.mermaid
└── templates/                         (sales templates)
    └── loi-template.md
```

---

## Testing Documentation Locally

```bash
# Install mdbook
cargo install mdbook

# Build docs
mdbook build docs/

# Preview (opens http://localhost:3000)
mdbook serve docs/

# Test links
npm install -g markdown-link-check
markdown-link-check docs/**/*.md -c .mlc.config.json
```

---

## Troubleshooting

### Pages Not Deploying

1. **Check workflow status:**
   - Actions → doc-build.yml → Latest run
   - Look for red ✗ or green ✓

2. **Common issues:**
   - Branch name typo (should be `main`)
   - Output folder path incorrect
   - mdbook build failed (check logs)

3. **Re-trigger:**
   ```bash
   git commit --allow-empty -m "chore: trigger pages rebuild"
   git push origin main
   ```

### DNS Issues (Custom Domain)

1. **Verify CNAME record:**
   ```bash
   nslookup docs.adrion369.dev
   # Should resolve to: aios-mvp.pages.github.io
   ```

2. **Clear cache:**
   - Wait 5-10 minutes for DNS propagation
   - Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### 404 Errors

1. **Check file exists:**
   ```bash
   ls -la docs/book/en/
   # Look for index.html
   ```

2. **Check SUMMARY.md:**
   - All links in SUMMARY.md must point to existing files
   - Paths are relative to `docs/src/`

---

## Search Functionality

mdbook includes **built-in search**:

- Searches document titles and content
- Enabled by default in `book.toml`
- No external service required

---

## Continuous Improvement

### Adding Pages

1. Create new `.md` file in `docs/src/`
2. Add to `SUMMARY.md` navigation
3. Push to `main` → auto-deploy

### Updating Diagrams

1. Edit `.mermaid` files in `docs/diagrams/`
2. Push to `main` → diagram-validate.yml runs
3. Site updates automatically

### Performance

- GitHub Pages CDN caches static files
- Propagation: 5-10 seconds globally
- Suitable for 100k+ monthly visitors

---

## Resources

- **mdbook documentation:** https://rust-lang.github.io/mdBook/
- **GitHub Pages docs:** https://docs.github.com/en/pages
- **Mermaid diagram syntax:** https://mermaid.js.org/

---

**For questions:** Open [GitHub Discussion](https://github.com/Gruszkoland/AIOS-MVP/discussions) in "Documentation" category.
