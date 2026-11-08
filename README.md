# MarginPulse

This repository holds the MarginPulse Managed Intelligence **website** (at the repository root, ready to deploy) plus the engine, launch kit and legacy analysis scripts behind it.

## Repository map

| Path | What it is |
|---|---|
| `index.html`, `privacy.html`, `terms.html`, `404.html`, `css/`, `js/`, `assets/` | **The website.** Static, responsive, no build step. |
| `integrations/google-sheets-leads/` | Google Apps Script that stores website enquiries in a Google Sheet, plus setup steps. |
| `marginpulse_intelligence_engine/` | Analysis engine v0.1.1 (Python, FastAPI, CLI), demo datasets including an Indian INR distributor, docs and 15 tests. |
| `MarginPulse_Managed_Intelligence_Final_Launch_Kit/` | Brand assets, 15 document templates, operations tracker, dummy data, website guides. |
| `data_analysis_automation_suite/` | The original data-analysis automation scripts and notebooks (moved here unchanged; they import each other, so keep the folder together). |
| `vercel.json`, `_headers`, `netlify.toml`, `.vercelignore`, `.github/workflows/pages.yml` | Deployment settings (see below). |

## Deploy the website

Only website files should be public. The settings in this repo make sure the internal folders are **not** published.

- **Vercel:** import the repo, framework "Other", no build command, root directory `/`. `.vercelignore` excludes internal folders; `vercel.json` adds security headers.
- **GitHub Pages:** Settings → Pages → Source: **GitHub Actions**. The included workflow publishes only the site files.
- **Netlify or Cloudflare Pages:** build command and output directory come from `netlify.toml` (`_site`).
- Do **not** serve the repo root with a plain static host that has no ignore or build step, or the documents, templates and demo data would be public.

## Connect lead capture (Google Sheet)

Follow `integrations/google-sheets-leads/SETUP.md`, then paste the web-app URL into `js/config.js` as `leadSheetEndpoint`. Until that is set, the live site shows an honest "form not available" message instead of pretending to send.

## Before going live

- Replace the placeholders in `privacy.html` and `terms.html` and have them reviewed by a qualified professional for your jurisdictions.
- Set `og:image` and a canonical URL once the domain is known (social previews need an absolute image URL).
- Never commit `.env` files, tokens or client data.

## Status

The website, engine and templates are pilot-stage. Engine results are verified against independently calculated figures on the bundled synthetic datasets; see `marginpulse_intelligence_engine/README.md` and `CHANGELOG.md` for scope and known limits.
