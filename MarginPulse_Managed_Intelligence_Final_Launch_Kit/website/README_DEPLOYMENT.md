# MarginPulse Managed Intelligence website

Static, responsive client-facing website using the MarginPulse navy / teal / emerald brand palette.

## Included pages and interactions

- `index.html`: service overview, analysis coverage, deliverables, workflow, pilot explanation, qualification form and FAQs.
- `privacy.html`: editable privacy notice draft.
- `terms.html`: editable website terms draft.
- Mobile navigation, anchor navigation, FAQ accordions, required-field validation and enquiry submission handling.
- `assets/`: current MarginPulse Managed Intelligence logo and browser icon.
- `css/styles.css`: responsive styles.
- `js/app.js`: navigation, date and form logic.
- `js/config.js`: public contact and lead endpoint settings.

## Important: connect lead delivery before publishing

The enquiry form validates and works in preview mode. It will **not transmit leads** until a real contact email or form endpoint is configured in `js/config.js`.

Example configuration using a verified FormSubmit endpoint:

```js
window.MARGINPULSE_CONFIG = {
  contactEmail: "your-monitored-business-email@example.com",
  formEndpoint: "https://formsubmit.co/ajax/your-monitored-business-email@example.com",
  instagramUrl: "",
  linkedinUrl: ""
};
```

FormSubmit may require an initial email activation. Alternatively, use a Formspree endpoint or your own server endpoint that accepts a JSON `POST`. Test a submission end-to-end and confirm the lead reaches the intended inbox / CRM before going live.

If only `contactEmail` is set, submitting the form opens a prefilled email draft; the visitor must still press Send. If both values are blank, preview mode validates the enquiry and downloads a JSON file locally. This is for testing only, not live lead capture.

Do not put private API keys, database service keys or credentials in `js/config.js`. This file is public in the browser.

## Do not collect financial records through the public form

The form collects business qualification details only. It is not a file upload or secure client portal. Do not add bank statements, invoice records, payroll, customer transaction exports, passwords or tokens to this form. After a signed scope and confidentiality arrangements, agree an appropriate private transfer channel with the client.

## Deploy to Vercel

1. Create a repository and upload the **contents of this `website` folder**.
2. In Vercel, import the repository and select framework preset `Other`.
3. Set build command to blank / none and output directory to `.` (or use the repository root if it contains these website files directly).
4. Deploy the static site.
5. Add the chosen domain or subdomain in Vercel and complete the DNS records shown by Vercel.
6. Test desktop and mobile layouts, every navigation link, privacy / terms pages and form delivery.

Suggested service subdomain: `managed.marginpulse.in` (only if you choose to use it and control the DNS). This kit has not been deployed and no DNS changes have been made.

## Deploy to Cloudflare Pages

1. Create a Pages project from the repository or use direct upload.
2. Set the project root to the folder containing `index.html`.
3. Use no framework build command; output directory is the website root (`.`).
4. Add the chosen custom domain and apply the DNS instructions displayed by Cloudflare.
5. Complete the same end-to-end tests as above.

## Pre-launch checklist

- [ ] Complete provider legal name and privacy contact in `privacy.html`.
- [ ] Complete operator identity and contact details in `terms.html`.
- [ ] Connect and verify the form endpoint / monitored email.
- [ ] Test an actual lead submission and verify receipt.
- [ ] Check that no confidential financial data can be submitted via the public enquiry form.
- [ ] Confirm all website claims accurately describe the service currently deliverable.
- [ ] Review website terms and privacy notice with qualified counsel for the actual jurisdictions and technologies used.
- [ ] Add social profile links only after those profiles are active and owned by the brand.
- [ ] Deploy and verify SSL / custom domain.
