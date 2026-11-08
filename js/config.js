/*
  MarginPulse website configuration (public file: never put passwords, API keys or private credentials here).

  Lead delivery, in priority order:
    1. leadSheetEndpoint : Google Apps Script web-app URL that writes enquiries to the Google Sheet
                           (see integrations/google-sheets-leads/SETUP.md). Recommended.
    2. formEndpoint      : any JSON POST endpoint (Formspree: https://formspree.io/f/YOUR_FORM_ID).
    3. contactEmail      : fallback; opens the visitor's email app with the enquiry pre-filled.
*/
window.MARGINPULSE_CONFIG = {
  leadSheetEndpoint: "",
  formEndpoint: "",
  contactEmail: "",
  // Optional public social links. Leave blank to hide.
  instagramUrl: "",
  linkedinUrl: ""
};
