# Website go-live checklist

1. Complete `privacy.html` and `terms.html` (legal name, contact, retention) and have them reviewed professionally.
2. Deploy the Google Apps Script (`integrations/google-sheets-leads/SETUP.md`) and set `leadSheetEndpoint` in `js/config.js`.
3. Deploy the site (root `README.md`), connect the domain and confirm HTTPS.
4. Submit a test enquiry from a phone and a laptop; confirm a new row appears in the sheet with Status `New`, and that the success message shows a reference.
5. Add `og:image` (absolute URL) and a canonical URL in `index.html`; check the link preview in WhatsApp and LinkedIn.
6. Restrict sharing of the lead sheet to people who need it, and set a retention period matching the Privacy Notice.
7. Decide who monitors new leads and how quickly they respond.
