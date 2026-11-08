# Website deployment

The website lives at the **repository root** (`index.html`, `privacy.html`, `terms.html`, `404.html`, `css/`, `js/`, `assets/`). See the root `README.md` for Vercel, GitHub Pages, Netlify and Cloudflare Pages settings, and `integrations/google-sheets-leads/SETUP.md` for lead capture.

## Files
- `js/config.js`: public settings (`leadSheetEndpoint`, `formEndpoint`, `contactEmail`, social links). Never put credentials here: it is public in the browser.
- `js/app.js`: interactions (navigation, scroll effects, expandable coverage areas, FAQ, form validation and submission).
- `js/boot.js`: marks the page as JavaScript-enabled (kept separate so a strict Content-Security-Policy can be used).
- `_headers` / `vercel.json`: security headers including the Content-Security-Policy. If you add another external service, allow its domain in `connect-src`.

## Local preview
Run `python -m http.server 8000` from the repository root and open `http://localhost:8000`. On localhost the form runs in preview mode (nothing is stored unless `leadSheetEndpoint` is set).
