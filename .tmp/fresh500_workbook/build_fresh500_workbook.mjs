import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workspace = "C:/Du_an/T_Langua_Test";
const outputDir = path.join(workspace, "outputs", "fresh500_evaluation_20261014");
const raw = JSON.parse(await fs.readFile(path.join(outputDir, "fresh_500_results.json"), "utf8"));
const translationRows = raw.translation_rows;
const speechRows = raw.speech_rows;

if (!Array.isArray(translationRows) || translationRows.length !== 500) {
  throw new Error(`Expected 500 translation rows, got ${translationRows?.length}`);
}
if (!Array.isArray(speechRows) || speechRows.length !== 500) {
  throw new Error(`Expected 500 speech rows, got ${speechRows?.length}`);
}

const avg = (items, getter) => items.reduce((sum, item) => sum + getter(item), 0) / items.length;
const quantile = (items, getter, ratio) => {
  const values = items.map(getter).sort((a, b) => a - b);
  const position = (values.length - 1) * ratio;
  const low = Math.floor(position);
  const high = Math.min(low + 1, values.length - 1);
  return values[low] + (values[high] - values[low]) * (position - low);
};
const speechAccuracy = (items) => {
  const errors = items.reduce((sum, item) => sum + Number(item.word_errors), 0);
  const words = items.reduce((sum, item) => sum + Number(item.reference_words), 0);
  return Math.max(0, 1 - errors / words);
};

const byDirection = [
  { label: "Việt → Anh", source: "vi" },
  { label: "Anh → Việt", source: "en" },
].map(({ label, source }) => {
  const tr = translationRows.filter((row) => row.source_lang === source);
  const sp = speechRows.filter((row) => row.source_lang === source);
  return {
    label,
    translationLatency: avg(tr, (row) => Number(row.latency_ms)),
    translationF1: avg(tr, (row) => Number(row.token_f1)),
    speechLatency: avg(sp, (row) => Number(row.latency_ms)),
    speechAccuracy: speechAccuracy(sp),
  };
});

const domains = [...new Set(translationRows.map((row) => row.domain))];
const byDomain = domains.map((domain) => {
  const tr = translationRows.filter((row) => row.domain === domain);
  const sp = speechRows.filter((row) => row.domain === domain);
  return [
    domain,
    tr.length,
    avg(tr, (row) => Number(row.latency_ms)),
    avg(tr, (row) => Number(row.token_f1)),
    avg(sp, (row) => Number(row.latency_ms)),
    speechAccuracy(sp),
  ];
});

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Tổng quan");
const evidence = workbook.worksheets.add("Minh_chứng_500");
const translation = workbook.worksheets.add("Dịch_500");
const speech = workbook.worksheets.add("STT_500");
const method = workbook.worksheets.add("Phương pháp");
const fontFamily = "Arial";
const darkBlue = "#1F4E78";
const midBlue = "#5B9BD5";
const lightBlue = "#D9EAF7";
const paleYellow = "#FFF2CC";
const paleGreen = "#E2F0D9";
const paleRed = "#FCE4D6";
const gray = "#667085";

for (const sheet of [summary, evidence, translation, speech, method]) {
  sheet.showGridLines = false;
}
summary.getRange("A1:V48").format.font = { name: fontFamily, size: 10, color: "#1F2937" };
summary.getRange("A1:V48").format.verticalAlignment = "center";
evidence.getRange("A1:AA504").format.font = { name: fontFamily, size: 10, color: "#1F2937" };
evidence.getRange("A1:AA504").format.verticalAlignment = "center";
translation.getRange("A1:O501").format.font = { name: fontFamily, size: 10, color: "#1F2937" };
translation.getRange("A1:O501").format.verticalAlignment = "center";
speech.getRange("A1:P501").format.font = { name: fontFamily, size: 10, color: "#1F2937" };
speech.getRange("A1:P501").format.verticalAlignment = "center";
method.getRange("A1:B21").format.font = { name: fontFamily, size: 10, color: "#1F2937" };
method.getRange("A1:B21").format.verticalAlignment = "center";

// ----- Summary -----
summary.getRange("A1").values = [["ĐÁNH GIÁ HỆ THỐNG DỊCH & NHẬN DẠNG GIỌNG NÓI — 500 CÂU MỚI"]];
summary.getRange("A1:V1").format = {
  fill: darkBlue,
  font: { name: fontFamily, size: 15, bold: true, color: "#FFFFFF" },
  rowHeight: 30,
};
summary.getRange("A2").values = [["Ngày chạy: 14/10/2026 | 250 Việt→Anh + 250 Anh→Việt | GPU cục bộ | số liệu từng câu ở hai tab chi tiết"]];
summary.getRange("A2:V2").format.font = { name: fontFamily, size: 10, italic: true, color: gray };

summary.getRange("A3:B7").values = [
  ["NGƯỠNG ĐÁNH GIÁ (có thể chỉnh)", "Giá trị"],
  ["Độ trễ dịch tối đa (ms)", 1000],
  ["Độ trễ STT tối đa (ms)", 1000],
  ["F1 dịch tối thiểu", 0.70],
  ["Độ chính xác từ STT tối thiểu", 0.80],
];
summary.getRange("A3:B3").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
summary.getRange("B4:B7").format.fill = paleYellow;
summary.getRange("B4:B5").format.numberFormat = "0";
summary.getRange("B6:B7").format.numberFormat = "0.0%";
summary.getRange("A3:B7").format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };

summary.getRange("A9:D9").values = [["CHỈ SỐ TỔNG HỢP", "Kết quả", "Mục tiêu", "Đánh giá"]];
summary.getRange("A9:D9").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
summary.getRange("A10:A20").values = [
  ["Số câu kiểm thử"], ["Dịch — trung bình (ms)"], ["Dịch — P50 (ms)"], ["Dịch — P95 (ms)"],
  ["Dịch — F1 từ"], ["Dịch — chrF"], ["Dịch — tỷ lệ đạt tốc độ"],
  ["STT — trung bình (ms)"], ["STT — P50 (ms)"], ["STT — P95 (ms)"], ["STT — độ chính xác từ TB/câu"],
];
summary.getRange("B10:B20").formulas = [
  ["=COUNTA('Dịch_500'!A2:A501)"],
  ["=AVERAGE('Dịch_500'!G2:G501)"],
  [`=${raw.translation_summary.latency_ms.p50}`],
  [`=${raw.translation_summary.latency_ms.p95}`],
  ["=AVERAGE('Dịch_500'!J2:J501)"],
  ["=AVERAGE('Dịch_500'!K2:K501)"],
  ["=COUNTIF('Dịch_500'!I2:I501,\"Đạt\")/500"],
  ["=AVERAGE('STT_500'!G2:G501)"],
  [`=${raw.speech_summary.latency_ms.p50}`],
  [`=${raw.speech_summary.latency_ms.p95}`],
  ["=AVERAGE('STT_500'!L2:L501)"],
];
summary.getRange("C10:C20").formulas = [
  ["=500"], ["=$B$4"], ["=$B$4"], ["=$B$4"], ["=$B$6"], ["=$B$6"], ["=1"],
  ["=$B$5"], ["=$B$5"], ["=$B$5"], ["=$B$7"],
];
summary.getRange("D10:D20").formulas = [
  ["=IF(B10=C10,\"Đủ\",\"Thiếu\")"],
  ["=IF(B11<=C11,\"Đạt\",\"Chưa đạt\")"], ["=IF(B12<=C12,\"Đạt\",\"Chưa đạt\")"],
  ["=IF(B13<=C13,\"Đạt\",\"Chưa đạt\")"], ["=IF(B14>=C14,\"Đạt\",\"Chưa đạt\")"],
  ["=IF(B15>=C15,\"Đạt\",\"Chưa đạt\")"], ["=IF(B16>=0.8,\"Đạt\",\"Chưa đạt\")"],
  ["=IF(B17<=C17,\"Đạt\",\"Chưa đạt\")"], ["=IF(B18<=C18,\"Đạt\",\"Chưa đạt\")"],
  ["=IF(B19<=C19,\"Đạt\",\"Chưa đạt\")"], ["=IF(B20>=C20,\"Đạt\",\"Chưa đạt\")"],
];
summary.getRange("B11:C13").format.numberFormat = "0.0";
summary.getRange("B14:C16").format.numberFormat = "0.0%";
summary.getRange("B17:C19").format.numberFormat = "0.0";
summary.getRange("B20:C20").format.numberFormat = "0.0%";
summary.getRange("A9:D20").format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
summary.getRange("D10:D20").conditionalFormats.add("containsText", { text: "Chưa đạt", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });
summary.getRange("D10:D20").conditionalFormats.add("containsText", { text: "Đạt", format: { fill: paleGreen, font: { color: "#006100", bold: true } } });

summary.getRange("G3:K5").values = [
  ["Chiều/ngôn ngữ", "Dịch TB (ms)", "F1 dịch", "STT TB (ms)", "Chính xác từ STT"],
  ...byDirection.map((row) => [row.label, row.translationLatency, row.translationF1, row.speechLatency, row.speechAccuracy]),
];
summary.getRange("G3:K3").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
summary.getRange("H4:H5").format.numberFormat = "0.0";
summary.getRange("I4:I5").format.numberFormat = "0.0%";
summary.getRange("J4:J5").format.numberFormat = "0.0";
summary.getRange("K4:K5").format.numberFormat = "0.0%";

const latencyChart = summary.charts.add("bar", [summary.getRange("G3:G5"), summary.getRange("H3:H5"), summary.getRange("J3:J5")]);
latencyChart.title = "Độ trễ trung bình theo ngôn ngữ";
latencyChart.titleTextStyle.typeface = fontFamily;
latencyChart.titleTextStyle.fontSize = 12;
latencyChart.legend = { position: "top", textStyle: { typeface: fontFamily } };
latencyChart.xAxis = { axisType: "textAxis", textStyle: { typeface: fontFamily, fontSize: 10 } };
latencyChart.yAxis = { numberFormatCode: "0", numberFormatSourceLinked: false, textStyle: { typeface: fontFamily } };
latencyChart.setPosition("G8", "N20");

const qualityChart = summary.charts.add("bar", [summary.getRange("G3:G5"), summary.getRange("I3:I5"), summary.getRange("K3:K5")]);
qualityChart.title = "Độ chính xác theo ngôn ngữ";
qualityChart.titleTextStyle.typeface = fontFamily;
qualityChart.titleTextStyle.fontSize = 12;
qualityChart.legend = { position: "top", textStyle: { typeface: fontFamily } };
qualityChart.xAxis = { axisType: "textAxis", textStyle: { typeface: fontFamily, fontSize: 10 } };
qualityChart.yAxis = { numberFormatCode: "0%", numberFormatSourceLinked: false, textStyle: { typeface: fontFamily } };
qualityChart.setPosition("O8", "V20");

summary.getRange("A22:F42").values = [
  ["LĨNH VỰC", "Số câu", "Dịch TB (ms)", "F1 dịch", "STT TB (ms)", "Chính xác từ STT"],
  ...byDomain,
];
summary.getRange("A22:F22").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
summary.getRange("C23:C42").format.numberFormat = "0.0";
summary.getRange("D23:D42").format.numberFormat = "0.0%";
summary.getRange("E23:E42").format.numberFormat = "0.0";
summary.getRange("F23:F42").format.numberFormat = "0.0%";
summary.tables.add("A22:F42", true, "DomainSummaryTable");

summary.getRange("A44:B48").values = [
  ["KẾT LUẬN NHANH", "Chi tiết"],
  ["Tốc độ dịch", `Trung bình ${raw.translation_summary.latency_ms.mean.toFixed(1)} ms; P95 ${raw.translation_summary.latency_ms.p95.toFixed(1)} ms.`],
  ["Chất lượng dịch tự động", `F1 ${(raw.translation_summary.mean_token_f1 * 100).toFixed(2)}%; chrF ${(raw.translation_summary.mean_chrf * 100).toFixed(2)}%; giữ số/mã ${(raw.translation_summary.mean_numeric_fidelity * 100).toFixed(2)}%.`],
  ["Tốc độ STT", `Trung bình ${raw.speech_summary.latency_ms.mean.toFixed(1)} ms; P95 ${raw.speech_summary.latency_ms.p95.toFixed(1)} ms; RTF ${raw.speech_summary.mean_realtime_factor.toFixed(3)}.`],
  ["Độ chính xác STT", `Theo từ ${(raw.speech_summary.corpus_word_accuracy_capped * 100).toFixed(2)}%; theo ký tự ${(raw.speech_summary.corpus_char_accuracy_capped * 100).toFixed(2)}%.`],
];
summary.getRange("A44:B44").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
summary.getRange("B45:B48").format.wrapText = true;
summary.getRange("A44:B48").format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
summary.getRange("A:A").format.columnWidth = 30;
summary.getRange("B:B").format.columnWidth = 24;
summary.getRange("C:D").format.columnWidth = 14;
summary.getRange("G:G").format.columnWidth = 18;
summary.getRange("H:K").format.columnWidth = 15;
summary.getRange("A44:A48").format.columnWidth = 28;
summary.getRange("B44:B48").format.columnWidth = 80;

// ----- Combined 500-row evidence -----
for (let index = 0; index < 500; index += 1) {
  if (translationRows[index].case_id !== speechRows[index].case_id) {
    throw new Error(`Mismatched evidence IDs at row ${index + 1}`);
  }
}

evidence.getRange("A1").values = [["MINH CHỨNG KIỂM THỬ 500 CÂU"]];
evidence.getRange("A1:AA1").format = {
  fill: darkBlue,
  font: { name: fontFamily, size: 15, bold: true, color: "#FFFFFF" },
  rowHeight: 30,
};
evidence.getRange("A2").values = [["Giọng nói gốc là câu đã dùng để tổng hợp âm thanh VITS sạch 16 kHz. Lần chạy này xử lý âm thanh trong bộ nhớ nên không có đường dẫn WAV riêng cho từng câu."]];
evidence.getRange("A2:AA2").format.font = { name: fontFamily, size: 10, italic: true, color: gray };
evidence.getRange("A2:AA2").format.rowHeight = 24;

const evidenceHeaders = [
  "ID", "Chiều dịch", "Lĩnh vực", "Bản chuẩn gốc", "Bản dịch chuẩn tham chiếu",
  "Bản sau dịch qua model", "Khớp dịch F1", "Khớp dịch chrF", "Khớp dịch tổng hợp",
  "Dịch khớp tuyệt đối", "Giữ số/mã", "Độ trễ dịch (ms)", "Điểm tốc độ dịch",
  "Giọng nói gốc (câu đã phát)", "Điều kiện âm thanh", "Thời lượng âm thanh (s)",
  "Văn bản sau nhận diện", "WER", "Độ khớp theo từ", "CER", "Độ khớp theo ký tự",
  "STT khớp tuyệt đối", "Độ trễ nhận diện (ms)", "RTF", "Điểm tốc độ nhận diện",
  "Kết quả dịch", "Kết quả nhận diện",
];
evidence.getRange("A4:AA4").values = [evidenceHeaders];
evidence.getRange("A5:H504").values = translationRows.map((row) => [
  row.case_id,
  row.source_lang === "vi" ? "Việt → Anh" : "Anh → Việt",
  row.domain,
  row.source,
  row.reference,
  row.hypothesis,
  Number(row.token_f1),
  Number(row.chrf),
]);
evidence.getRange("J5:L504").values = translationRows.map((row) => [
  Number(row.exact_match), Number(row.numeric_fidelity), Number(row.latency_ms),
]);
evidence.getRange("N5:R504").values = speechRows.map((row) => [
  row.reference,
  "VITS sạch, 16 kHz, tổng hợp FP32",
  Number(row.duration_seconds),
  row.hypothesis,
  Number(row.wer),
]);
evidence.getRange("T5:T504").values = speechRows.map((row) => [Number(row.cer)]);
evidence.getRange("V5:X504").values = speechRows.map((row) => [
  Number(row.exact_match), Number(row.latency_ms), Number(row.realtime_factor),
]);
evidence.getRange("I5:I504").formulas = translationRows.map((_, index) => [`=AVERAGE(G${index + 5}:H${index + 5})`]);
evidence.getRange("M5:M504").formulas = translationRows.map((_, index) => [`=MIN(1,'Tổng quan'!$B$4/L${index + 5})`]);
evidence.getRange("S5:S504").formulas = speechRows.map((_, index) => [`=MAX(0,1-R${index + 5})`]);
evidence.getRange("U5:U504").formulas = speechRows.map((_, index) => [`=MAX(0,1-T${index + 5})`]);
evidence.getRange("Y5:Y504").formulas = speechRows.map((_, index) => [`=MIN(1,'Tổng quan'!$B$5/W${index + 5})`]);
evidence.getRange("Z5:Z504").formulas = translationRows.map((_, index) => [`=IF(I${index + 5}>='Tổng quan'!$B$6,\"Đạt\",\"Cần xem\")`]);
evidence.getRange("AA5:AA504").formulas = speechRows.map((_, index) => [`=IF(S${index + 5}>='Tổng quan'!$B$7,\"Đạt\",\"Cần xem\")`]);

evidence.getRange("A4:AA4").format = {
  fill: darkBlue,
  font: { name: fontFamily, bold: true, color: "#FFFFFF" },
  wrapText: true,
  horizontalAlignment: "center",
  rowHeight: 42,
};
evidence.getRange("D5:F504").format.wrapText = true;
evidence.getRange("N5:Q504").format.wrapText = true;
evidence.getRange("A5:AA504").format.rowHeight = 48;
evidence.getRange("G5:K504").format.numberFormat = "0.0%";
evidence.getRange("L5:L504").format.numberFormat = "0.0";
evidence.getRange("M5:M504").format.numberFormat = "0.0%";
evidence.getRange("P5:P504").format.numberFormat = "0.000";
evidence.getRange("R5:V504").format.numberFormat = "0.0%";
evidence.getRange("W5:W504").format.numberFormat = "0.0";
evidence.getRange("X5:X504").format.numberFormat = "0.000";
evidence.getRange("Y5:Y504").format.numberFormat = "0.0%";
evidence.getRange("A:A").format.columnWidth = 20;
evidence.getRange("B:B").format.columnWidth = 14;
evidence.getRange("C:C").format.columnWidth = 18;
evidence.getRange("D:F").format.columnWidth = 44;
evidence.getRange("G:M").format.columnWidth = 14;
evidence.getRange("N:N").format.columnWidth = 44;
evidence.getRange("O:O").format.columnWidth = 25;
evidence.getRange("P:P").format.columnWidth = 16;
evidence.getRange("Q:Q").format.columnWidth = 44;
evidence.getRange("R:Y").format.columnWidth = 15;
evidence.getRange("Z:AA").format.columnWidth = 16;
evidence.freezePanes.freezeRows(4);
evidence.freezePanes.freezeColumns(3);
evidence.tables.add("A4:AA504", true, "Evidence500Table");
evidence.getRange("I5:I504").conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
evidence.getRange("S5:S504").conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
evidence.getRange("U5:U504").conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
evidence.getRange("Z5:AA504").conditionalFormats.add("containsText", { text: "Cần xem", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });

// ----- Translation details -----
const translationHeaders = ["ID", "Chiều dịch", "Lĩnh vực", "Câu nguồn", "Bản dịch chuẩn", "Kết quả hệ thống", "Độ trễ (ms)", "Điểm tốc độ", "Đạt tốc độ", "F1 theo từ", "chrF", "Khớp tuyệt đối", "Giữ số/mã", "Điểm dịch chuẩn", "Đạt chất lượng"];
translation.getRange("A1:O1").values = [translationHeaders];
translation.getRange("A2:G501").values = translationRows.map((row) => [
  row.case_id,
  row.source_lang === "vi" ? "Việt → Anh" : "Anh → Việt",
  row.domain,
  row.source,
  row.reference,
  row.hypothesis,
  Number(row.latency_ms),
]);
translation.getRange("J2:M501").values = translationRows.map((row) => [
  Number(row.token_f1), Number(row.chrf), Number(row.exact_match), Number(row.numeric_fidelity),
]);
translation.getRange("H2:H501").formulas = translationRows.map((_, index) => [`=MIN(1,'Tổng quan'!$B$4/G${index + 2})`]);
translation.getRange("I2:I501").formulas = translationRows.map((_, index) => [`=IF(G${index + 2}<='Tổng quan'!$B$4,\"Đạt\",\"Chưa đạt\")`]);
translation.getRange("N2:N501").formulas = translationRows.map((_, index) => [`=AVERAGE(J${index + 2}:K${index + 2})`]);
translation.getRange("O2:O501").formulas = translationRows.map((_, index) => [`=IF(N${index + 2}>='Tổng quan'!$B$6,\"Đạt\",\"Chưa đạt\")`]);
translation.getRange("A1:O1").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" }, wrapText: true, rowHeight: 32 };
translation.getRange("D2:F501").format.wrapText = true;
translation.getRange("G2:G501").format.numberFormat = "0.0";
translation.getRange("H2:H501").format.numberFormat = "0.0%";
translation.getRange("J2:N501").format.numberFormat = "0.0%";
translation.getRange("A2:O501").format.rowHeight = 42;
translation.getRange("A:A").format.columnWidth = 20;
translation.getRange("B:B").format.columnWidth = 14;
translation.getRange("C:C").format.columnWidth = 18;
translation.getRange("D:F").format.columnWidth = 44;
translation.getRange("G:O").format.columnWidth = 14;
translation.freezePanes.freezeRows(1);
translation.freezePanes.freezeColumns(3);
translation.tables.add("A1:O501", true, "Translation500Table");
translation.getRange("H2:H501").conditionalFormats.add("dataBar", { color: midBlue, gradient: true, thresholds: ["min", "max"] });
translation.getRange("N2:N501").conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
translation.getRange("I2:I501").conditionalFormats.add("containsText", { text: "Chưa đạt", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });
translation.getRange("O2:O501").conditionalFormats.add("containsText", { text: "Chưa đạt", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });

// ----- Speech details -----
const speechHeaders = ["ID", "Ngôn ngữ", "Lĩnh vực", "Câu nguồn chuẩn", "Kết quả nhận dạng", "Thời lượng âm thanh (s)", "Độ trễ STT (ms)", "RTF", "Điểm tốc độ", "Đạt tốc độ", "WER", "Độ chính xác từ", "CER", "Độ chính xác ký tự", "Khớp tuyệt đối", "Đạt chất lượng"];
speech.getRange("A1:P1").values = [speechHeaders];
speech.getRange("A2:H501").values = speechRows.map((row) => [
  row.case_id,
  row.source_lang === "vi" ? "Tiếng Việt" : "Tiếng Anh",
  row.domain,
  row.reference,
  row.hypothesis,
  Number(row.duration_seconds),
  Number(row.latency_ms),
  Number(row.realtime_factor),
]);
speech.getRange("K2:K501").values = speechRows.map((row) => [Number(row.wer)]);
speech.getRange("M2:M501").values = speechRows.map((row) => [Number(row.cer)]);
speech.getRange("O2:O501").values = speechRows.map((row) => [Number(row.exact_match)]);
speech.getRange("I2:I501").formulas = speechRows.map((_, index) => [`=MIN(1,'Tổng quan'!$B$5/G${index + 2})`]);
speech.getRange("J2:J501").formulas = speechRows.map((_, index) => [`=IF(G${index + 2}<='Tổng quan'!$B$5,\"Đạt\",\"Chưa đạt\")`]);
speech.getRange("L2:L501").formulas = speechRows.map((_, index) => [`=MAX(0,1-K${index + 2})`]);
speech.getRange("N2:N501").formulas = speechRows.map((_, index) => [`=MAX(0,1-M${index + 2})`]);
speech.getRange("P2:P501").formulas = speechRows.map((_, index) => [`=IF(L${index + 2}>='Tổng quan'!$B$7,\"Đạt\",\"Chưa đạt\")`]);
speech.getRange("A1:P1").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" }, wrapText: true, rowHeight: 32 };
speech.getRange("D2:E501").format.wrapText = true;
speech.getRange("F2:G501").format.numberFormat = "0.000";
speech.getRange("H2:H501").format.numberFormat = "0.000";
speech.getRange("I2:I501").format.numberFormat = "0.0%";
speech.getRange("K2:O501").format.numberFormat = "0.0%";
speech.getRange("A2:P501").format.rowHeight = 42;
speech.getRange("A:A").format.columnWidth = 20;
speech.getRange("B:B").format.columnWidth = 14;
speech.getRange("C:C").format.columnWidth = 18;
speech.getRange("D:E").format.columnWidth = 48;
speech.getRange("F:P").format.columnWidth = 14;
speech.freezePanes.freezeRows(1);
speech.freezePanes.freezeColumns(3);
speech.tables.add("A1:P501", true, "Speech500Table");
speech.getRange("I2:I501").conditionalFormats.add("dataBar", { color: midBlue, gradient: true, thresholds: ["min", "max"] });
speech.getRange("L2:L501").conditionalFormats.add("colorScale", { colors: ["#F8696B", "#FFEB84", "#63BE7B"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
speech.getRange("J2:J501").conditionalFormats.add("containsText", { text: "Chưa đạt", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });
speech.getRange("P2:P501").conditionalFormats.add("containsText", { text: "Chưa đạt", format: { fill: paleRed, font: { color: "#C00000", bold: true } } });

// ----- Methodology -----
method.getRange("A1:H1").format = { fill: darkBlue, font: { name: fontFamily, size: 15, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
method.getRange("A1").values = [["PHƯƠNG PHÁP, CÔNG THỨC VÀ GIỚI HẠN"]];
method.getRange("A3:B15").values = [
  ["Mục", "Mô tả"],
  ["Bộ dữ liệu", "500 câu mới, duy nhất: 250 Việt→Anh và 250 Anh→Việt; 20 lĩnh vực, mỗi lĩnh vực 25 câu."],
  ["Dịch", "facebook/nllb-200-distilled-1.3B, beam 1, đo tuần tự sau một lần làm nóng."],
  ["Điểm tốc độ dịch", "MIN(100%, ngưỡng độ trễ dịch / độ trễ thực tế từng câu)."],
  ["F1 theo từ", "So khớp tập từ đã chuẩn hóa giữa bản dịch hệ thống và bản dịch chuẩn; thể hiện theo %."],
  ["chrF", "F1 n-gram ký tự bậc 1–6 giữa bản dịch hệ thống và bản dịch chuẩn; thể hiện theo %."],
  ["Điểm dịch chuẩn", "Trung bình cộng F1 theo từ và chrF của từng câu."],
  ["Âm thanh STT", "Tạo sạch bằng VITS FP32 từ chính câu nguồn, đưa về 16 kHz và qua tiền xử lý âm thanh sản xuất."],
  ["Nhận dạng", "openai/whisper-large-v3-turbo, revision cố định, FP16 trên GPU, beam 1."],
  ["WER", "Số thao tác thay/thêm/xóa từ chia cho số từ chuẩn. Độ chính xác từ = MAX(0, 1 − WER)."],
  ["CER", "Số thao tác thay/thêm/xóa ký tự chia cho số ký tự chuẩn. Độ chính xác ký tự = MAX(0, 1 − CER)."],
  ["RTF", "Thời gian nhận dạng chia cho thời lượng âm thanh. RTF < 1 nghĩa là nhanh hơn thời gian thực."],
  ["Ngưỡng", "Các ô màu vàng trên tab Tổng quan là đầu vào có thể chỉnh; trạng thái từng dòng tự tính lại."],
];
method.getRange("A3:B3").format = { fill: darkBlue, font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
method.getRange("A4:A15").format.fill = lightBlue;
method.getRange("A3:B15").format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
method.getRange("B4:B15").format.wrapText = true;
method.getRange("A:A").format.columnWidth = 26;
method.getRange("B:B").format.columnWidth = 100;
method.getRange("A4:B15").format.rowHeight = 38;
method.getRange("A17:B21").values = [
  ["GIỚI HẠN", "Ảnh hưởng"],
  ["Giọng nói tổng hợp", "Không đại diện đầy đủ cho người nói thật, vùng miền, tiếng ồn, micro hoặc phòng."],
  ["Tham chiếu dịch có kiểm soát", "Được xây dựng theo mẫu song ngữ và chưa qua hai chuyên gia ngôn ngữ độc lập."],
  ["Điểm tự động", "F1/chrF/WER/CER không phát hiện hết lỗi nghĩa nghiêm trọng hoặc độ tự nhiên của câu."],
  ["Khuyến nghị", "Trước nghiệm thu sản xuất, bổ sung ít nhất 100 câu thu âm người thật và chấm dịch mù bởi hai người."],
];
method.getRange("A17:B17").format = { fill: "#9C6500", font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
method.getRange("A18:A21").format.fill = paleYellow;
method.getRange("B18:B21").format.wrapText = true;
method.getRange("A17:B21").format.borders = { preset: "outside", style: "thin", color: "#9CA3AF" };
method.getRange("A18:B21").format.rowHeight = 42;

workbook.recalculate();

// Verify that an editable threshold changes the linked per-row status, then restore it.
const originalSttThreshold = summary.getRange("B7").values[0][0];
summary.getRange("B7").values = [[0]];
workbook.recalculate();
if (evidence.getRange("AA5").values[0][0] !== "Đạt") {
  throw new Error("Evidence status did not react to the STT accuracy threshold");
}
summary.getRange("B7").values = [[originalSttThreshold]];
workbook.recalculate();

const errorRanges = [
  [summary, "B10:D20"],
  [evidence, "I5:AA504"],
  [translation, "H2:O501"],
  [speech, "I2:P501"],
];
for (const [sheet, address] of errorRanges) {
  const values = sheet.getRange(address).values;
  const errors = values.flat().filter((value) => typeof value === "string" && /^#(REF|DIV\/0|VALUE|NAME|N\/A|NUM|NULL)/.test(value));
  if (errors.length) throw new Error(`${sheet.name}!${address} contains formula errors: ${errors.slice(0, 5).join(", ")}`);
}

const inspect = await workbook.inspect({
  kind: "workbook,sheet,table,formula",
  maxChars: 12000,
  tableMaxRows: 5,
  tableMaxCols: 8,
  options: { maxResults: 80 },
});
const formulaErrorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(
  path.join(outputDir, "workbook_inspection.txt"),
  `${inspect.ndjson ?? String(inspect)}\n${formulaErrorScan.ndjson ?? String(formulaErrorScan)}`,
  "utf8",
);

const renderConfigs = [
  ["Tổng quan", "A1:V48", 1],
  ["Minh_chứng_500", "A1:AA22", 0.75],
  ["Dịch_500", "A1:O20", 0.75],
  ["STT_500", "A1:P20", 0.75],
  ["Phương pháp", "A1:B21", 1],
];
for (const [sheetName, range, scale] of renderConfigs) {
  const preview = await workbook.render({ sheetName, range, scale, format: "png" });
  const safeName = sheetName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9_]+/g, "_");
  await fs.writeFile(path.join(outputDir, `preview_${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "Minh_chung_kiem_thu_500_cau.xlsx"));
console.log(JSON.stringify({
  workbook: path.join(outputDir, "Minh_chung_kiem_thu_500_cau.xlsx"),
  sheets: ["Tổng quan", "Minh_chứng_500", "Dịch_500", "STT_500", "Phương pháp"],
  translationRows: translationRows.length,
  speechRows: speechRows.length,
}, null, 2));
