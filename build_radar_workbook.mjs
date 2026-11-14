import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = "outputs/collector/radar.json";
const outputPath = "outputs/collector/Martech Radar.xlsx";
const previewDir = "/tmp/martech-radar-previews";
const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const workbook = Workbook.create();
const font = "Arial";
const colors = {
  ink: "#18313B",
  teal: "#176B6B",
  tealLight: "#E7F3F1",
  sand: "#F6F2E8",
  line: "#D7E0DE",
  amber: "#FFF1CC",
  red: "#FDE8E7",
  redText: "#A12C27",
  muted: "#5F6F75",
  white: "#FFFFFF",
};

function columnName(index) {
  let result = "";
  for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) {
    result = String.fromCharCode(65 + ((n - 1) % 26)) + result;
  }
  return result;
}

function typedRows(name, rows) {
  const dateHeaders = new Set([
    "Published", "First discovered", "Last successful check", "Next due", "Started UTC",
  ]);
  const headers = rows[0];
  return rows.map((row, rowIndex) => row.map((value, columnIndex) => {
    if (rowIndex === 0 || !dateHeaders.has(headers[columnIndex]) || typeof value !== "string") return value;
    if (/^\d{4}-\d{2}-\d{2}T/.test(value)) return new Date(value);
    return value;
  }));
}

const sheetNotes = {
  Inbox: "Three reviewed priorities. New candidates enter here only after evidence review and a score of at least 14/20.",
  Candidates: "Newly collected articles awaiting evidence review. Priority is provisional and is not the editorial score.",
  Library: "All collected and previously assessed stories. Reading status and notes are the fields intended for manual updates.",
  Sources: "Coverage by source. Pending access and failed checks remain visible so a gap cannot look like a successful scan.",
  Runs: "Measured collection history, including pending work, requests, downloads and runtime.",
};

const widthByHeader = {
  "Priority": 10, "Story ID": 22, "Published": 16, "Source": 18, "Headline": 52,
  "Link": 42, "Why read": 48, "Why queued": 42, "Review": 22, "Score /20": 11,
  "Topics": 24, "Evidence": 22, "Reading status": 16, "Your notes": 34,
  "Editorial review": 20, "Editorial score /20": 18, "Related story": 30,
  "Links to investigate": 38, "Collection status": 18, "Collection issue": 42,
  "First discovered": 20, "Source ID": 20, "Type": 17, "Beats": 25,
  "Check interval (hours)": 20, "Enabled": 16, "Coverage": 20,
  "Last successful check": 23, "Next due": 23, "New links total": 18,
  "Issue or detail": 58, "Entry page": 42, "Run ID": 28, "Started UTC": 22,
  "Status": 16, "Sources checked": 17, "New links": 13, "Articles extracted": 19,
  "Pending articles": 17, "HTTP requests": 15, "Downloaded MB": 16, "Seconds": 12,
  "Stop reason": 32,
};

for (const [name, rawRows] of Object.entries(payload.tables)) {
  const rows = typedRows(name, rawRows);
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.tabColor = name === "Inbox" ? colors.ink : name === "Candidates" ? colors.teal : "#92AAA8";
  const columns = rows[0].length;
  const lastColumn = columnName(columns - 1);
  const finalRow = 4 + rows.length;

  sheet.getRange("A2").values = [[name === "Inbox" ? "Martech Radar" : name]];
  sheet.getRange(`A2:${lastColumn}2`).format.borders = {
    bottom: { style: "thin", color: colors.teal },
  };
  sheet.getRange("A2").format.font = { name: font, size: 15, bold: true, color: colors.ink };
  sheet.getRange("A3").values = [[sheetNotes[name]]];
  sheet.getRange(`A3:${lastColumn}3`).format.font = { name: font, size: 10, italic: true, color: colors.muted };
  sheet.getRange(`A5:${lastColumn}${finalRow}`).values = rows;

  const used = sheet.getRange(`A2:${lastColumn}${finalRow}`);
  used.format.font = { name: font, size: 10, color: colors.ink };
  used.format.verticalAlignment = "center";
  const header = sheet.getRange(`A5:${lastColumn}5`);
  header.format = {
    fill: colors.ink,
    font: { name: font, size: 10, bold: true, color: colors.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  header.format.rowHeight = 28;
  if (rows.length > 1) {
    const body = sheet.getRange(`A6:${lastColumn}${finalRow}`);
    body.format.borders = { bottom: { style: "thin", color: colors.line } };
    body.format.rowHeight = name === "Inbox" ? 38 : 30;
  }

  rows[0].forEach((label, index) => {
    const col = columnName(index);
    sheet.getRange(`${col}2:${col}${Math.max(finalRow, 6)}`).format.columnWidth = widthByHeader[label] || 18;
    if (["Headline", "Link", "Why read", "Why queued", "Your notes", "Related story", "Links to investigate", "Issue or detail", "Collection issue", "Entry page"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.wrapText = true;
    }
    if (["Published", "First discovered", "Last successful check", "Next due", "Started UTC"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.numberFormat = "dd-mmm-yyyy";
    }
    if (["Priority", "Score /20", "Editorial score /20", "Check interval (hours)", "New links total", "Sources checked", "New links", "Articles extracted", "Pending articles", "HTTP requests"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.numberFormat = "#,##0";
    }
    if (["Downloaded MB", "Seconds"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.numberFormat = "#,##0.0";
    }
    if (["Link", "Related story", "Links to investigate", "Entry page"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.font = { name: font, size: 9, color: colors.teal };
    }
    if (["Enabled", "Coverage", "Status", "Collection status"].includes(label)) {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`).format.horizontalAlignment = "center";
    }
    if (label === "Reading status") {
      const inputRange = sheet.getRange(`${col}6:${col}${Math.max(finalRow, 505)}`);
      inputRange.format.fill = colors.amber;
      inputRange.dataValidation = { rule: { type: "list", values: ["To read", "Read", "Saved", "Skip"] } };
    }
    if (label === "Your notes") {
      sheet.getRange(`${col}6:${col}${Math.max(finalRow, 505)}`).format.fill = colors.sand;
    }
    if (["Coverage", "Status", "Collection status"].includes(label)) {
      const statusRange = sheet.getRange(`${col}6:${col}${Math.max(finalRow, 6)}`);
      statusRange.conditionalFormats.add("containsText", {
        text: "Failed", format: { fill: colors.red, font: { bold: true, color: colors.redText } },
      });
      statusRange.conditionalFormats.add("containsText", {
        text: "Partial", format: { fill: colors.amber, font: { bold: true, color: colors.ink } },
      });
      statusRange.conditionalFormats.add("containsText", {
        text: "Pending", format: { fill: colors.sand, font: { bold: true, color: colors.muted } },
      });
    }
  });

  if (name !== "Inbox") sheet.freezePanes.freezeRows(5);
  if (["Candidates", "Library"].includes(name)) sheet.freezePanes.freezeColumns(4);
  if (name === "Sources") sheet.freezePanes.freezeColumns(2);
}

workbook.recalculate();
const summary = await workbook.inspect({
  kind: "table",
  range: "Inbox!A1:I9",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 10,
  maxChars: 4500,
});
console.log(summary.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

await fs.mkdir(previewDir, { recursive: true });
for (const [name, rows] of Object.entries(payload.tables)) {
  const lastColumn = columnName(rows[0].length - 1);
  const preview = await workbook.render({
    sheetName: name,
    range: `A1:${lastColumn}${Math.min(4 + rows.length, 25)}`,
    scale: 1,
    format: "png",
  });
  await fs.writeFile(`${previewDir}/${name.toLowerCase()}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, previewDir, sheets: Object.keys(payload.tables) }));
