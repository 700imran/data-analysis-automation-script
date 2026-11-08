/**
 * MarginPulse website lead capture -> Google Sheet.
 * Deploy as a Web app (Execute as: Me, Who has access: Anyone). See SETUP.md.
 * The spreadsheet is written server-side; no credentials are exposed in the public website.
 */
const SPREADSHEET_ID = 'PASTE_YOUR_SHEET_ID_HERE'; // the long ID in the sheet URL: docs.google.com/spreadsheets/d/<ID>/edit
const SHEET_NAME = 'Leads';
const NOTIFY_EMAIL = '';          // optional: e-mail address that receives a notification for each new lead
const RATE_LIMIT_SECONDS = 30;    // same e-mail cannot submit again within this window
const STATUS_OPTIONS = ['New', 'Contacted', 'Qualified', 'Proposal sent', 'Won', 'Lost', 'Not a fit'];

const HEADERS = ['Lead ID', 'Received At (UTC)', 'Submitted At (browser)', 'Status', 'Name', 'Email', 'Company', 'Role', 'Country', 'Industry',
  'Employees', 'Data Source', 'Priority', 'Challenge', 'Reporting Frequency', 'Start Timeline', 'Consent', 'Page URL',
  'UTM Source', 'UTM Medium', 'UTM Campaign', 'Owner', 'Follow-up Date', 'Notes'];

const LIMITS = { name: 100, email: 150, company: 150, role: 60, country: 60, industry: 80, employees: 30, system: 60, objective: 80, challenge: 1200, frequency: 30, timeline: 40, source: 500, utm: 100 };

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    const body = e && e.postData && e.postData.contents ? e.postData.contents : '';
    if (body.length > 20000) return json_({ ok: false, error: 'payload_too_large' });
    let d;
    try { d = JSON.parse(body); } catch (err) { return json_({ ok: false, error: 'invalid_json' }); }

    if (d.website) return json_({ ok: true, id: 'ignored' });   // honeypot: real visitors never fill this hidden field

    const name = clean_(d.name, LIMITS.name), email = clean_(d.email, LIMITS.email).toLowerCase(), company = clean_(d.company, LIMITS.company);
    const country = clean_(d.country, LIMITS.country), industry = clean_(d.industry, LIMITS.industry), objective = clean_(d.objective, LIMITS.objective);
    const challenge = clean_(d.challenge, LIMITS.challenge);
    if (!name || !company || !country || !industry || !objective || !challenge) return json_({ ok: false, error: 'missing_required_fields' });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return json_({ ok: false, error: 'invalid_email' });
    if (d.consent !== true) return json_({ ok: false, error: 'consent_required' });

    const cache = CacheService.getScriptCache();
    const rlKey = 'rl_' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, email)).slice(0, 40);
    if (cache.get(rlKey)) return json_({ ok: false, error: 'too_many_requests' });
    cache.put(rlKey, '1', RATE_LIMIT_SECONDS);

    const sheet = getSheet_();
    const id = 'ML-' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd') + '-' + Utilities.getUuid().slice(0, 4).toUpperCase();
    const row = [id, new Date(), clean_(d.submittedAt, 40), 'New', name, email, company, clean_(d.role, LIMITS.role), country, industry,
      clean_(d.employees, LIMITS.employees), clean_(d.system, LIMITS.system), objective, challenge, clean_(d.frequency, LIMITS.frequency),
      clean_(d.timeline, LIMITS.timeline), 'Yes', clean_(d.source, LIMITS.source), clean_(d.utm_source, LIMITS.utm), clean_(d.utm_medium, LIMITS.utm),
      clean_(d.utm_campaign, LIMITS.utm), '', '', ''];
    sheet.appendRow(row.map(guardFormula_));

    if (NOTIFY_EMAIL) {
      MailApp.sendEmail(NOTIFY_EMAIL, 'New MarginPulse enquiry: ' + company,
        ['Lead ID: ' + id, 'Name: ' + name, 'Email: ' + email, 'Company: ' + company, 'Country: ' + country, 'Industry: ' + industry,
         'Priority: ' + objective, 'Challenge: ' + challenge].join('\n'));
    }
    return json_({ ok: true, id: id });
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: 'server_error' });
  } finally {
    try { lock.releaseLock(); } catch (e2) {}
  }
}

function doGet() { return json_({ ok: true, service: 'marginpulse-lead-capture' }); }   // health check

/** Run once from the Apps Script editor: creates/renames the tab, writes headers, formatting and the Status dropdown. */
function setup() {
  const sheet = getSheet_();
  sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold').setBackground('#06283B').setFontColor('#FFFFFF');
  sheet.setFrozenRows(1);
  sheet.getRange(2, 2, sheet.getMaxRows() - 1, 1).setNumberFormat('yyyy-mm-dd hh:mm');
  sheet.getRange(2, 4, sheet.getMaxRows() - 1, 1).setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(STATUS_OPTIONS, true).setAllowInvalid(false).build());
  sheet.getRange(2, 23, sheet.getMaxRows() - 1, 1).setNumberFormat('yyyy-mm-dd');
  sheet.setColumnWidths(1, HEADERS.length, 140); sheet.setColumnWidth(14, 380);
  sheet.getRange(2, 14, sheet.getMaxRows() - 1, 1).setWrap(true);
  SpreadsheetApp.flush();
}

function getSheet_() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) { sheet = ss.getSheets()[0]; sheet.setName(SHEET_NAME); }
  if (sheet.getLastRow() === 0) sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  return sheet;
}
function clean_(v, max) { return String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max || 200); }
function guardFormula_(v) { return (typeof v === 'string' && /^[=+\-@]/.test(v)) ? "'" + v : v; }   // block spreadsheet formula injection
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
