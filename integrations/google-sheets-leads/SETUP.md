# Google Sheets lead capture: setup (about 5 minutes)

**Sheet:** *MarginPulse Leads (Website Enquiries)* (create it in Google Sheets, or use the one already created for you). The sheet ID is the long string in its URL between `/d/` and `/edit`.
Leads are written server-side by a Google Apps Script web app, so no credentials appear in the public website.

## 1. Add the script
1. Open the sheet → **Extensions → Apps Script**.
2. Delete the placeholder code and paste the contents of `Code.gs` from this folder. Replace `PASTE_YOUR_SHEET_ID_HERE` with your sheet ID.
3. Optional: set `NOTIFY_EMAIL` to receive an email for each new lead.
4. Select the function **`setup`** and click **Run**. Approve the permissions (Sheets, and Mail only if you set `NOTIFY_EMAIL`). This renames the tab to `Leads`, writes the header row, adds a Status dropdown and formatting.

## 2. Deploy as a web app
1. **Deploy → New deployment → Web app**.
2. *Execute as:* **Me**. *Who has access:* **Anyone**. Click **Deploy**.
3. Copy the **Web app URL** (it ends in `/exec`).

## 3. Connect the website
Open `js/config.js` and paste the URL:

```js
leadSheetEndpoint: "https://script.google.com/macros/s/XXXXXXXX/exec",
```

Redeploy the site. Submit a test enquiry and confirm a new row appears with Status `New`.

## 4. Check the connection
Open the web app URL in a browser: you should see `{"ok":true,"service":"marginpulse-lead-capture"}`.

## Changing the script later
After editing `Code.gs`, use **Deploy → Manage deployments → Edit → Version: New version**. The URL stays the same.

## What the script does
- Validates required fields, email format and consent; trims and length-limits every field.
- Ignores bot submissions (hidden honeypot field) and blocks repeat submissions from the same email for 30 seconds.
- Prefixes any value starting with `=`, `+`, `-` or `@` so it cannot run as a spreadsheet formula.
- Uses a lock so simultaneous submissions do not overwrite each other.

## Privacy and limits
- Enquiries contain personal data (name, email, company). Restrict sharing of the sheet to people who need it, and cover retention and deletion in your Privacy Notice.
- "Anyone" access applies to the **web app** that accepts posts, not to the sheet itself. The sheet stays private to you unless you share it.
- The endpoint URL is public by design (it is in the website code). The honeypot, validation and rate limit reduce spam but do not make it spam-proof; if abuse appears, add a CAPTCHA or move to a server-side function.
- Apps Script has daily quotas (including a limit on notification emails; see Google's Apps Script quotas page). They are normally ample for an enquiry form, but check them if you expect high volume.
