/**
 * Google Apps Script Webhook to automatically update Reel Status
 * 
 * Setup Instructions:
 * 1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1hID-uXSmtTGR7wJq1Xbzl9kH73OemGlHluppqM1BQ7s/edit
 * 2. Click Extensions -> Apps Script
 * 3. Delete existing code and paste this entire code
 * 4. Click 'Deploy' (top right) -> 'New deployment'
 * 5. Select type: 'Web app'
 * 6. Set Description: 'Reel Auto Status Sync'
 * 7. Set 'Execute as': 'Me'
 * 8. Set 'Who has access': 'Anyone'
 * 9. Click 'Deploy' and copy the 'Web app URL'
 * 10. Paste URL in your .env file as:
 *     GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec
 */

function doPost(e) {
  try {
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);
    var tabName = data.tab;
    var shortcode = data.shortcode;
    var status = data.status || "Posted";
    var liveLink = data.live_link || "";
    var postedDate = data.posted_date || Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd");

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(tabName);
    
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Tab not found: " + tabName
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var values = sheet.getDataRange().getValues();
    var headers = values[0];
    
    var colShortcode = -1;
    var colLink = -1;
    var colStatus = -1;
    var colSentDate = -1;

    for (var j = 0; j < headers.length; j++) {
      var h = headers[j].toString().toLowerCase().trim();
      if (h === "shortcode") colShortcode = j;
      else if (h === "reel link" || h === "link" || h === "url") colLink = j;
      else if (h === "status") colStatus = j;
      else if (h === "sent date" || h === "posted date") colSentDate = j;
    }

    if (colStatus === -1) colStatus = 8; // Default Column I (9th col)
    if (colSentDate === -1) colSentDate = 9; // Default Column J (10th col)

    var matchedRow = -1;
    for (var i = 1; i < values.length; i++) {
      var row = values[i];
      var rowShortcode = colShortcode !== -1 ? row[colShortcode].toString().trim() : "";
      var rowLink = colLink !== -1 ? row[colLink].toString().trim() : "";

      if ((shortcode && rowShortcode === shortcode) || (shortcode && rowLink.indexOf(shortcode) !== -1)) {
        matchedRow = i + 1; // 1-indexed for Sheet API
        break;
      }
    }

    if (matchedRow !== -1) {
      sheet.getRange(matchedRow, colStatus + 1).setValue(status);
      sheet.getRange(matchedRow, colSentDate + 1).setValue(postedDate);
      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        matched_row: matchedRow,
        tab: tabName,
        shortcode: shortcode
      })).setMimeType(ContentService.MimeType.JSON);
    } else {
      return ContentService.createTextOutput(JSON.stringify({
        status: "not_found",
        message: "Shortcode not found in sheet: " + shortcode
      })).setMimeType(ContentService.MimeType.JSON);
    }

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "ok",
    message: "Reel Auto Status Sync Webhook is Active!"
  })).setMimeType(ContentService.MimeType.JSON);
}
