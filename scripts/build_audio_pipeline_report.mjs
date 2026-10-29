import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";


function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error("Usage: node build_audio_pipeline_report.mjs --input payload.json --output report.xlsx [--preview-dir dir]");
    }
    result[key.slice(2)] = value;
  }
  if (!result.input || !result.output) throw new Error("--input and --output are required");
  return result;
}


async function loadArtifactTool(workspace) {
  try {
    return await import("@oai/artifact-tool");
  } catch {
    // The reusable tool can run inside this Codex workspace without adding
    // artifact-tool to the product's runtime dependencies.
  }
  const candidates = [
    process.env.ARTIFACT_TOOL_NODE_MODULES,
    path.join(workspace, ".tmp", "fresh500_workbook", "node_modules"),
    process.env.USERPROFILE
      ? path.join(process.env.USERPROFILE, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules")
      : null,
  ].filter(Boolean);
  for (const nodeModules of candidates) {
    const packageDir = path.join(nodeModules, "@oai", "artifact-tool");
    const packageFile = path.join(packageDir, "package.json");
    try {
      const packageJson = JSON.parse(await fs.readFile(packageFile, "utf8"));
      const entry = path.join(packageDir, packageJson.exports?.["."] ?? "dist/artifact_tool.mjs");
      return await import(pathToFileURL(entry).href);
    } catch {
      // Try the next known dependency location.
    }
  }
  throw new Error(
    "Không tìm thấy @oai/artifact-tool. Đặt ARTIFACT_TOOL_NODE_MODULES tới thư mục node_modules hoặc chạy với --no-xlsx."
  );
}


function excelColumn(number) {
  let value = number;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

const numberOrNull = (value) => value === null || value === undefined || value === "" ? null : Number(value);


const args = parseArgs(process.argv.slice(2));
const inputPath = path.resolve(args.input);
const outputPath = path.resolve(args.output);
const workspace = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const { SpreadsheetFile, Workbook } = await loadArtifactTool(workspace);
const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const rows = payload.rows ?? [];
if (!rows.length) throw new Error("Report payload contains no rows");

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Tổng quan");
const comparison = workbook.worksheets.add("So sánh");
const detail = workbook.worksheets.add("Chi tiết");
const method = workbook.worksheets.add("Phương pháp");
const font = "Arial";
const navy = "#1F4E78";
const blue = "#5B9BD5";
const lightBlue = "#D9EAF7";
const paleGreen = "#E2F0D9";
const paleRed = "#FCE4D6";
const paleYellow = "#FFF2CC";
const gray = "#667085";

for (const sheet of [summary, comparison, detail, method]) sheet.showGridLines = false;

const overall = payload.overall;
const created = payload.metadata?.completed_at ?? payload.metadata?.created_at ?? "";
const stageRows = [
  ["Whisper STT", overall.stt.latency_ms.mean, overall.stt.latency_ms.p95, overall.stt.word_accuracy, "Độ chính xác từ"],
  ["NLLB trực tiếp", overall.translation_direct.latency_ms.mean, overall.translation_direct.latency_ms.p95, overall.translation_direct.mean_token_f1, "F1 dịch"],
  ["NLLB sau STT", overall.translation_pipeline.latency_ms.mean, overall.translation_pipeline.latency_ms.p95, overall.translation_pipeline.mean_token_f1, "F1 đầu-cuối"],
  ["VITS TTS", overall.tts.latency_ms.mean, overall.tts.latency_ms.p95, overall.tts.mean_rtf, "RTF"],
  ["Tổng pipeline", overall.pipeline.latency_ms.mean, overall.pipeline.latency_ms.p95, overall.pipeline.mean_rtf, "RTF"],
];

summary.getRange("A2").values = [["BÁO CÁO KIỂM THỬ WHISPER → NLLB → VITS"]];
summary.getRange("A2:N2").format.font = { name: font, size: 15, bold: true, color: navy };
summary.getRange("A3:N3").format.borders = { bottom: { style: "thin", color: navy } };
summary.getRange("A4").values = [[`Ngày chạy: ${created} | ${overall.case_count} ca | ${payload.metadata?.device ?? ""} | hoàn thành ${overall.complete_count}`]];
summary.getRange("A4:N4").format.font = { name: font, size: 10, italic: true, color: gray };

summary.getRange("A6:E6").values = [["Công đoạn", "Trung bình (ms)", "P95 (ms)", "Chỉ số chất lượng", "Tên chỉ số"]];
summary.getRange("A7:E11").values = stageRows;
summary.getRange("A6:E6").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("B7:C11").format.numberFormat = "0.0";
summary.getRange("D7:D11").format.numberFormat = "0.0%";
summary.tables.add("A6:E11", true, "StageSummaryTable");

summary.getRange("G6:K6").values = [["Chiều", "Số ca", "STT TB (ms)", "F1 dịch đầu-cuối", "Pipeline TB (ms)"]];
const directionRows = Object.entries(payload.by_direction ?? {}).map(([direction, value]) => [
  direction, value.case_count, value.stt.latency_ms.mean,
  value.translation_pipeline.mean_token_f1, value.pipeline.latency_ms.mean,
]);
if (directionRows.length) summary.getRange(`G7:K${6 + directionRows.length}`).values = directionRows;
summary.getRange("G6:K6").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
if (directionRows.length) {
  summary.getRange(`I7:I${6 + directionRows.length}`).format.numberFormat = "0.0";
  summary.getRange(`J7:J${6 + directionRows.length}`).format.numberFormat = "0.0%";
  summary.getRange(`K7:K${6 + directionRows.length}`).format.numberFormat = "0.0";
  summary.tables.add(`G6:K${6 + directionRows.length}`, true, "DirectionSummaryTable");
}

const latencyChart = summary.charts.add("bar", [
  summary.getRange("A6:A11"),
  summary.getRange("B6:B11"),
  summary.getRange("C6:C11"),
]);
latencyChart.title = "Độ trễ theo công đoạn";
latencyChart.titleTextStyle.typeface = font;
latencyChart.titleTextStyle.fontSize = 12;
latencyChart.legend = { position: "top", textStyle: { typeface: font } };
latencyChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
latencyChart.yAxis = { numberFormatCode: "0", numberFormatSourceLinked: false, textStyle: { typeface: font } };
latencyChart.setPosition("G13", "N27");

summary.getRange("A14:F14").values = [["Lĩnh vực", "Số ca", "STT TB (ms)", "F1 trực tiếp", "F1 đầu-cuối", "Pipeline TB (ms)"]];
const domainRows = Object.entries(payload.by_domain ?? {}).map(([domain, value]) => [
  domain, value.case_count, value.stt.latency_ms.mean,
  value.translation_direct.mean_token_f1, value.translation_pipeline.mean_token_f1,
  value.pipeline.latency_ms.mean,
]);
if (domainRows.length) summary.getRange(`A15:F${14 + domainRows.length}`).values = domainRows;
summary.getRange("A14:F14").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
if (domainRows.length) {
  summary.getRange(`C15:C${14 + domainRows.length}`).format.numberFormat = "0.0";
  summary.getRange(`D15:E${14 + domainRows.length}`).format.numberFormat = "0.0%";
  summary.getRange(`F15:F${14 + domainRows.length}`).format.numberFormat = "0.0";
  summary.tables.add(`A14:F${14 + domainRows.length}`, true, "DomainSummaryTable");
}
summary.getRange("A:A").format.columnWidth = 25;
summary.getRange("B:E").format.columnWidth = 18;
summary.getRange("F:F").format.columnWidth = 20;
summary.getRange("G:G").format.columnWidth = 16;
summary.getRange("H:K").format.columnWidth = 17;
summary.getRange("A2:N40").format.font = { name: font, size: 10, color: "#1F2937" };
summary.getRange("A2:N2").format.font = { name: font, size: 15, bold: true, color: navy };

// Historical baseline and direct-vs-pipeline comparison.
comparison.getRange("A2").values = [["SO SÁNH VỚI ĐỢT 500 CÂU VÀ ẢNH HƯỞNG CỦA STT"]];
comparison.getRange("A2:J2").format.font = { name: font, size: 15, bold: true, color: navy };
comparison.getRange("A3:J3").format.borders = { bottom: { style: "thin", color: navy } };
comparison.getRange("A5:E5").values = [["Chỉ số", "Đơn vị", "Lần này", "Lịch sử", "Chênh lệch"]];
const comparisonRows = (payload.comparison ?? []).map((row) => [
  row.metric, row.unit, row.current, row.baseline, row.delta,
]);
if (comparisonRows.length) comparison.getRange(`A6:E${5 + comparisonRows.length}`).values = comparisonRows;
comparison.getRange("A5:E5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
if (comparisonRows.length) {
  comparison.tables.add(`A5:E${5 + comparisonRows.length}`, true, "HistoricalComparisonTable");
  for (let index = 0; index < (payload.comparison ?? []).length; index += 1) {
    const excelRow = index + 6;
    const isPercent = payload.comparison[index].unit === "%";
    comparison.getRange(`C${excelRow}:E${excelRow}`).format.numberFormat = isPercent ? "0.0%" : "0.0";
  }
}

comparison.getRange("G5:J5").values = [["Chỉ số dịch", "Trực tiếp", "Sau Whisper", "Chênh lệch"]];
comparison.getRange("G6:J9").values = [
  ["F1 theo từ", overall.translation_direct.mean_token_f1, overall.translation_pipeline.mean_token_f1, overall.translation_pipeline.mean_f1_delta_vs_direct],
  ["chrF", overall.translation_direct.mean_chrf, overall.translation_pipeline.mean_chrf, overall.translation_pipeline.mean_chrf_delta_vs_direct],
  ["Độ trễ TB (ms)", overall.translation_direct.latency_ms.mean, overall.translation_pipeline.latency_ms.mean, overall.translation_pipeline.latency_ms.mean - overall.translation_direct.latency_ms.mean],
  ["Giữ số/mã", overall.translation_direct.mean_numeric_fidelity, overall.translation_pipeline.mean_numeric_fidelity, overall.translation_pipeline.mean_numeric_fidelity - overall.translation_direct.mean_numeric_fidelity],
];
comparison.getRange("G5:J5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
comparison.getRange("H6:J7").format.numberFormat = "0.0%";
comparison.getRange("H8:J8").format.numberFormat = "0.0";
comparison.getRange("H9:J9").format.numberFormat = "0.0%";
comparison.tables.add("G5:J9", true, "PipelineImpactTable");

comparison.getRange("A18:E18").values = [["Nhóm độ dài", "Số ca", "STT TB (ms)", "F1 đầu-cuối", "Pipeline TB (ms)"]];
const lengthRows = Object.entries(payload.by_length_group ?? {}).map(([lengthGroup, value]) => [
  lengthGroup, value.case_count, value.stt.latency_ms.mean,
  value.translation_pipeline.mean_token_f1, value.pipeline.latency_ms.mean,
]);
if (lengthRows.length) comparison.getRange(`A19:E${18 + lengthRows.length}`).values = lengthRows;
comparison.getRange("A18:E18").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
if (lengthRows.length) {
  comparison.getRange(`C19:C${18 + lengthRows.length}`).format.numberFormat = "0.0";
  comparison.getRange(`D19:D${18 + lengthRows.length}`).format.numberFormat = "0.0%";
  comparison.getRange(`E19:E${18 + lengthRows.length}`).format.numberFormat = "0.0";
  comparison.tables.add(`A18:E${18 + lengthRows.length}`, true, "LengthSummaryTable");
}

const qualityChart = comparison.charts.add("bar", comparison.getRange("G5:I7"));
qualityChart.title = "Chất lượng dịch trực tiếp và đầu-cuối";
qualityChart.titleTextStyle.typeface = font;
qualityChart.titleTextStyle.fontSize = 12;
qualityChart.legend = { position: "top", textStyle: { typeface: font } };
qualityChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
qualityChart.yAxis = { numberFormatCode: "0%", numberFormatSourceLinked: false, textStyle: { typeface: font } };
qualityChart.setPosition("G12", "N27");
comparison.getRange("A:A").format.columnWidth = 30;
comparison.getRange("B:B").format.columnWidth = 12;
comparison.getRange("C:E").format.columnWidth = 16;
comparison.getRange("G:G").format.columnWidth = 24;
comparison.getRange("H:J").format.columnWidth = 16;
comparison.getRange("A2:N30").format.font = { name: font, size: 10, color: "#1F2937" };
comparison.getRange("A2:J2").format.font = { name: font, size: 15, bold: true, color: navy };

// Detailed evidence table.
const detailHeaders = [
  "Thứ tự", "ID", "Chiều", "Lĩnh vực", "Độ dài câu", "Tệp WAV", "Câu nguồn", "Bản dịch chuẩn",
  "Whisper transcript", "WER", "Chính xác từ", "STT (ms)", "STT RTF",
  "Dịch trực tiếp", "F1 trực tiếp", "chrF trực tiếp", "Dịch trực tiếp (ms)",
  "Dịch sau STT", "F1 đầu-cuối", "chrF đầu-cuối", "Dịch sau STT (ms)",
  "Δ F1", "VITS (ms)", "Âm thanh VITS (s)", "VITS RTF", "Pipeline (ms)",
  "Pipeline RTF", "Trạng thái", "Lỗi",
];
const detailRows = rows.map((row) => [
  numberOrNull(row.order), row.case_id, `${row.source_lang}->${row.target_lang}`, row.domain, row.length_group, row.wav_file,
  row.source_text, row.reference_translation, row.transcript,
  numberOrNull(row.wer), numberOrNull(row.stt_word_accuracy), numberOrNull(row.stt_ms), numberOrNull(row.stt_rtf),
  row.direct_translation, numberOrNull(row.direct_token_f1), numberOrNull(row.direct_chrf), numberOrNull(row.direct_translation_ms),
  row.pipeline_translation, numberOrNull(row.pipeline_token_f1), numberOrNull(row.pipeline_chrf), numberOrNull(row.pipeline_translation_ms),
  numberOrNull(row.translation_quality_delta_f1), numberOrNull(row.tts_ms), numberOrNull(row.tts_output_duration_seconds),
  numberOrNull(row.tts_rtf), numberOrNull(row.pipeline_ms), numberOrNull(row.pipeline_rtf), row.status, row.error ?? "",
]);
detail.getRange("A2").values = [["CHI TIẾT KẾT QUẢ TỪNG TỆP ÂM THANH"]];
detail.getRange("A2:AC2").format.font = { name: font, size: 15, bold: true, color: navy };
detail.getRange("A3:AC3").format.borders = { bottom: { style: "thin", color: navy } };
detail.getRange("A5:AC5").values = [detailHeaders];
detail.getRange(`A6:AC${5 + detailRows.length}`).values = detailRows;
detail.getRange("A5:AC5").format = {
  fill: navy,
  font: { name: font, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  rowHeight: 36,
};
detail.getRange(`A6:AC${5 + detailRows.length}`).format.font = { name: font, size: 10, color: "#1F2937" };
detail.getRange(`G6:I${5 + detailRows.length}`).format.wrapText = true;
detail.getRange(`N6:N${5 + detailRows.length}`).format.wrapText = true;
detail.getRange(`R6:R${5 + detailRows.length}`).format.wrapText = true;
detail.getRange(`J6:K${5 + detailRows.length}`).format.numberFormat = "0.0%";
detail.getRange(`L6:M${5 + detailRows.length}`).format.numberFormat = "0.000";
detail.getRange(`O6:P${5 + detailRows.length}`).format.numberFormat = "0.0%";
detail.getRange(`Q6:Q${5 + detailRows.length}`).format.numberFormat = "0.000";
detail.getRange(`S6:T${5 + detailRows.length}`).format.numberFormat = "0.0%";
detail.getRange(`U6:U${5 + detailRows.length}`).format.numberFormat = "0.000";
detail.getRange(`V6:V${5 + detailRows.length}`).format.numberFormat = "0.0%";
detail.getRange(`W6:AA${5 + detailRows.length}`).format.numberFormat = "0.000";
detail.getRange(`K6:K${5 + detailRows.length}`).conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
detail.getRange(`S6:T${5 + detailRows.length}`).conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
detail.getRange(`AB6:AB${5 + detailRows.length}`).conditionalFormats.add("containsText", { text: "error", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });
detail.tables.add(`A5:AC${5 + detailRows.length}`, true, "PipelineDetailTable");
detail.freezePanes.freezeRows(5);
detail.freezePanes.freezeColumns(5);
detail.getRange("A:A").format.columnWidth = 10;
detail.getRange("B:B").format.columnWidth = 22;
detail.getRange("C:C").format.columnWidth = 12;
detail.getRange("D:D").format.columnWidth = 20;
detail.getRange("E:E").format.columnWidth = 14;
detail.getRange("F:F").format.columnWidth = 32;
detail.getRange("G:I").format.columnWidth = 48;
detail.getRange("J:M").format.columnWidth = 14;
detail.getRange("N:N").format.columnWidth = 48;
detail.getRange("O:Q").format.columnWidth = 15;
detail.getRange("R:R").format.columnWidth = 48;
detail.getRange("S:AA").format.columnWidth = 15;
detail.getRange("AB:AB").format.columnWidth = 20;
detail.getRange("AC:AC").format.columnWidth = 40;

// Method and model provenance.
method.getRange("A2").values = [["PHƯƠNG PHÁP VÀ GIỚI HẠN"]];
method.getRange("A2:H2").format.font = { name: font, size: 15, bold: true, color: navy };
method.getRange("A3:H3").format.borders = { bottom: { style: "thin", color: navy } };
const models = payload.metadata?.models ?? {};
const loads = payload.metadata?.model_load_seconds ?? {};
const methodRows = [
  ["Luồng kiểm thử", "Đọc WAV, chuẩn hóa mono 16 kHz nếu cần, Whisper nhận dạng, NLLB dịch transcript và VITS tổng hợp bản dịch."],
  ["Whisper", `${models.whisper?.id ?? ""} @ ${models.whisper?.revision ?? ""}`],
  ["NLLB", `${models.nllb?.id ?? ""} @ ${models.nllb?.revision ?? ""}`],
  ["VITS tiếng Việt", `${models.vits?.vi?.id ?? ""} @ ${models.vits?.vi?.revision ?? ""}`],
  ["VITS tiếng Anh", `${models.vits?.en?.id ?? ""} @ ${models.vits?.en?.revision ?? ""}`],
  ["Thiết bị", `Whisper/NLLB: ${payload.metadata?.device ?? ""}; VITS: ${payload.metadata?.tts_device ?? ""}; GPU: ${payload.metadata?.gpu ?? "không"}`],
  ["Thời gian nạp mô hình", `Whisper: ${loads.whisper ?? "n.a."} s; NLLB: ${loads.nllb ?? "n.a."} s; VITS vi: ${loads.vits_vi ?? "n.a."} s; VITS en: ${loads.vits_en ?? "n.a."} s.`],
  ["WER/CER", "Khoảng cách chỉnh sửa theo từ/ký tự chia cho độ dài câu chuẩn. Độ chính xác được chặn tối thiểu ở 0%."],
  ["F1 theo từ", "F1 của tập đa hợp từ đã chuẩn hóa giữa bản dịch hệ thống và bản dịch tham chiếu."],
  ["chrF", "Trung bình F1 n-gram ký tự từ bậc 1 đến 6."],
  ["Dịch trực tiếp", "NLLB nhận câu nguồn chuẩn. Chỉ số này tương thích với cách chấm dịch của đợt 500 câu lịch sử."],
  ["Dịch đầu-cuối", "NLLB nhận transcript do Whisper tạo. Chênh lệch với dịch trực tiếp cho thấy ảnh hưởng của STT."],
  ["Latency pipeline", "Tổng latency inference ấm của Whisper, NLLB từ transcript và VITS; không gồm thời gian nạp mô hình."],
];
method.getRange("A5:B5").values = [["Mục", "Mô tả"]];
method.getRange(`A6:B${5 + methodRows.length}`).values = methodRows;
method.getRange("A5:B5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" } };
method.getRange(`A6:A${5 + methodRows.length}`).format.fill = lightBlue;
method.getRange(`B6:B${5 + methodRows.length}`).format.wrapText = true;
method.getRange(`A5:B${5 + methodRows.length}`).format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
method.getRange("A:A").format.columnWidth = 28;
method.getRange("B:B").format.columnWidth = 110;
method.getRange(`A6:B${5 + methodRows.length}`).format.rowHeight = 36;
const limitationStart = 8 + methodRows.length;
method.getRange(`A${limitationStart}:B${limitationStart}`).values = [["GIỚI HẠN", "Ảnh hưởng"]];
method.getRange(`A${limitationStart}:B${limitationStart}`).format = { fill: "#9C6500", font: { name: font, bold: true, color: "#FFFFFF" } };
const limitations = (payload.limitations ?? []).map((text, index) => [`Giới hạn ${index + 1}`, text]);
if (limitations.length) {
  method.getRange(`A${limitationStart + 1}:B${limitationStart + limitations.length}`).values = limitations;
  method.getRange(`A${limitationStart + 1}:A${limitationStart + limitations.length}`).format.fill = paleYellow;
  method.getRange(`B${limitationStart + 1}:B${limitationStart + limitations.length}`).format.wrapText = true;
  method.getRange(`A${limitationStart}:B${limitationStart + limitations.length}`).format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
  method.getRange(`A${limitationStart + 1}:B${limitationStart + limitations.length}`).format.rowHeight = 48;
}
method.getRange(`A2:H${limitationStart + limitations.length}`).format.font = { name: font, size: 10, color: "#1F2937" };
method.getRange("A2:H2").format.font = { name: font, size: 15, bold: true, color: navy };

workbook.recalculate();

const inspections = [
  ["Tổng quan", "A2:N35"],
  ["So sánh", "A2:N28"],
  ["Chi tiết", `A2:AC${Math.min(20, 5 + detailRows.length)}`],
  ["Phương pháp", `A2:B${limitationStart + limitations.length + 1}`],
];
for (const [sheetName, range] of inspections) {
  const check = await workbook.inspect({ kind: "table", range: `${sheetName}!${range}`, include: "values,formulas", tableMaxRows: 24, tableMaxCols: 28, maxChars: 9000 });
  if (!check) throw new Error(`Inspection failed for ${sheetName}`);
  const preview = await workbook.render({ sheetName, range, scale: sheetName === "Chi tiết" ? 0.65 : 1, format: "png" });
  const bytes = new Uint8Array(await preview.arrayBuffer());
  if (!bytes.length) throw new Error(`Render failed for ${sheetName}`);
  if (args["preview-dir"]) {
    await fs.mkdir(path.resolve(args["preview-dir"]), { recursive: true });
    const safeName = sheetName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9]+/g, "_");
    await fs.writeFile(path.join(path.resolve(args["preview-dir"]), `preview_${safeName}.png`), bytes);
  }
}
const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
const errorText = errorScan?.ndjson ?? String(errorScan ?? "");
if (/"matchCount"\s*:\s*[1-9]/.test(errorText)) throw new Error("Formula error scan found errors");

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ workbook: outputPath, sheets: ["Tổng quan", "So sánh", "Chi tiết", "Phương pháp"], rows: rows.length }, null, 2));
