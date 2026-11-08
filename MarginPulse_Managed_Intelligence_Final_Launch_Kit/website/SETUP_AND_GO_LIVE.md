# MarginPulse Managed Intelligence — Website setup and go-live

## Current status

The static client-facing website is built. It includes the service pages, responsive layout, navigation, privacy notice, website terms, enquiry qualification form and client-facing copy. It has **not** been deployed and the form has **not** been connected to a receiving inbox because the owner has not yet supplied a verified inbox or form endpoint.

Do not advertise the enquiry form as live until the real submission test below passes.

## 1. Connect enquiry delivery (recommended: Formspree)

1. Create a form with a provider such as Formspree using an email inbox that is actively monitored by the service operator.
2. Complete the provider's email / ownership verification and anti-spam setup.
3. Copy the public form endpoint. It will look similar to `https://formspree.io/f/xxxxxxxx`.
4. Open `js/config.js` and set:

```js
window.MARGINPULSE_CONFIG = {
  contactEmail: "your-monitored-inbox@example.com",
  formEndpoint: "https://formspree.io/f/YOUR_FORM_ID",
  instagramUrl: "https://www.instagram.com/YOUR_HANDLE/",
  linkedinUrl: ""
};
```

5. Do not put passwords, private API keys, Supabase service-role keys, database credentials or other secrets in `config.js`. It is public browser code.
6. Deploy the site only after this configuration is complete.

The website JavaScript sends the qualification fields as JSON with an `Accept: application/json` header. Confirm that the selected provider accepts this request format. If your provider requires a different format, adapt and test `js/app.js` before going live.

## 2. End-to-end test

Submit a real test enquiry with a controlled test address and fictional business details. Verify all of the following:

- The browser displays a confirmed success state only after a successful provider response.
- The submission appears in the provider dashboard.
- The notification reaches the monitored inbox (check spam / quarantine too).
- Name, email, company, country, industry, objective, challenge and consent are present.
- A failed request displays an error and does not falsely claim success.
- Confidential financial records cannot be uploaded through this public enquiry form.
- The privacy notice and contact address match the actual operating setup.

Delete the test submission if appropriate under the provider's retention controls and record the test date in the Operations Control Centre Launch Checklist.

## 3. Publish the static site

### Vercel

1. Put the contents of this `website` directory in a repository (or upload them using the static-site workflow).
2. Import the repository into Vercel and select framework preset `Other`.
3. Leave the build command blank and set the output directory to `.` when the website files are at the repository root.
4. Deploy and test the generated URL.
5. Add the chosen domain / subdomain in Vercel and apply the DNS records shown by Vercel.
6. Verify HTTPS, redirect behaviour, mobile layout and all navigation links.

### Cloudflare Pages

1. Create a Pages project from the repository or use direct upload.
2. Set the project root to the folder containing `index.html`.
3. Use no framework build command and set the output directory to `.`.
4. Deploy, attach the chosen domain / subdomain and apply the DNS records shown by Cloudflare.
5. Verify HTTPS, mobile layout, privacy / terms pages and lead capture.

Suggested service subdomain: `managed.marginpulse.in`, only if the operator controls the domain and chooses to use it. No DNS changes have been made.

## 4. Secure client-data transfer

The website enquiry form is for qualification details only. It is not a client portal and must not accept bank statements, ledgers, invoice exports, payroll or customer transaction files. After the parties agree scope, confidentiality, data authority and access rules, select a client-specific restricted storage / transfer channel. Record the selected channel and approved users in the Operations Control Centre.

## 5. Go-live checklist

- [ ] Verified monitored inbox / lead form endpoint configured.
- [ ] Real test enquiry successfully received and logged.
- [ ] Provider identity and contact details completed in privacy / terms and client documents.
- [ ] Legal and privacy documents reviewed for the actual jurisdictions and technology stack.
- [ ] Site deployed and chosen domain / subdomain connected.
- [ ] HTTPS active; pages and mobile layout checked.
- [ ] Instagram / LinkedIn URLs confirmed and updated.
- [ ] Website claims match the service that can currently be delivered.
- [ ] Public enquiry form clearly states not to submit confidential financial data.

Use the Launch Checklist tab in `MarginPulse_Operations_Control_Centre.xlsx` to record status and evidence.
