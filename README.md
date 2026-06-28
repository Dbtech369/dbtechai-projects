# dbtechai-projects

**Central hub for all AI automation projects.**  
Built by Daniel Barth (Dbtech369) with Veronica.

---

## 📦 Project Index

### 🟢 Live / Deployed

| Project | URL | Status |
|---------|-----|--------|
| **Oceanna Site Command Center** | [oceanna.dbtechai.com](https://oceanna.dbtechai.com) | ✅ Live on Cloudflare Pages |
| **Email Bot (Carlo — $49/mo)** | For his insurance business | ✅ Running |

### 🟡 In Progress / Needs Finishing

| Project | Folder | What It Needs |
|---------|--------|---------------|
| **Email Bot SaaS** | `email-bot/` | Landing page deployed, demo email active, prospect pipeline contacted |
| **RV Doc** | `rvdoc/` | CLI works, Flask web UI built — needs deployment to Cloudflare Pages or Lenovo laptop |
| **Desktop Agent** | `desktop-agent/` | Old Claude automation project — needs overhaul or archive |

### 🔬 Experiments

| Project | Folder | Description |
|---------|--------|-------------|
| **Cyber-Obsidian** | `experiments/cyber-obsidian/` | p5.js visual project — cyberpunk chess? |
| **Grandmaster Chess** | `experiments/chess/` | Chess visualizer with pieces.js + script.js |
| **Music/DJ Apps** | `experiments/music-dj/` | beat-pad, dj-crate, neon-mix — fun web music tools |
| **Metabolic Support** | *(not yet copied)* | Landing pages, Pinterest/TikTok content — never launched |

### 📊 Business Pipeline

| File | Contents |
|------|----------|
| `research/local_service_businesses.csv` | 20 local businesses researched |
| `research/real_estate_agencies_research.csv` | Real estate agency prospects |
| `email-bot/copy/email-sequence-*.md` | 5-day cold email drip campaign |

---

## 🏗️ Infrastructure

| Resource | Details |
|----------|---------|
| **Domain** | dbtechai.com — Cloudflare DNS |
| **Hosting** | Cloudflare Pages (free, global CDN) |
| **Server** | Lenovo laptop (192.168.12.243) — currently Pi-hole only |
| **Email (primary)** | gmailassisant4u@gmail.com |
| **Email (hostinger)** | wwwwebworks77@gmail.com |
| **GitHub** | [Dbtech369](https://github.com/Dbtech369) |
| **Cloudflare** | API token in /tmp (scope: Workers/Pages on dbtechai.com) |

---

## 🧭 Quick Deploy Guide

Any static HTML project → Cloudflare Pages:
```
# Already have a project folder? Push to GitHub and it auto-deploys.
# Or deploy manually:
npx wrangler pages deploy ./project-folder --project-name project-name
# Then add custom domain: project-name.dbtechai.com
```

Any project needing a backend → Lenovo laptop (Pi-hole box):
- SSH in, set up Python/Node service
- Run as systemd service or tmux session
- Expose via Cloudflare Tunnel if needed

---

## 📝 Project Philosophy

- **Email → Voice → Website Chat** upsell ladder ($49/$149/$299)
- **80%+ margins** (pay-as-you-go Claude API)
- **First customer**: Carlo at $49/mo
- **Demo strategy**: boomerang — send a test email, get an auto-reply instantly

---

*Last updated: June 28, 2026*
