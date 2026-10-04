$ErrorActionPreference = "Stop"

$projectRoot = if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    (Get-Location).Path
} else {
    Split-Path -Parent $PSScriptRoot
}
$outputPath = Join-Path $projectRoot "docs\Bao_cao_tien_do_T-Lingua_25-08_den_24-09-2026.docx"

$wdCollapseEnd = 0
$wdPageBreak = 7
$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdAlignParagraphRight = 2
$wdAlignParagraphJustify = 3
$wdAlignVerticalCenter = 1
$wdLineSpaceSingle = 0
$wdFieldPage = 33
$wdFormatDocumentDefault = 16
$wdOrientPortrait = 0
$wdPaperA4 = 7

function Get-WordColor([int]$red, [int]$green, [int]$blue) {
    return $red + ($green * 256) + ($blue * 65536)
}

$navy = Get-WordColor 31 78 121
$blue = Get-WordColor 47 117 181
$teal = Get-WordColor 15 107 120
$green = Get-WordColor 112 173 71
$amber = Get-WordColor 255 192 0
$red = Get-WordColor 192 0 0
$lightBlue = Get-WordColor 217 234 247
$lightGreen = Get-WordColor 226 240 217
$lightAmber = Get-WordColor 255 242 204
$lightRed = Get-WordColor 244 204 204
$lightGray = Get-WordColor 242 242 242
$white = Get-WordColor 255 255 255
$darkGray = Get-WordColor 68 68 68

$word = $null
$document = $null

function Add-Paragraph {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [string]$Style = "Normal",
        [int]$Alignment = 3,
        [switch]$Bold,
        [switch]$Italic,
        [int]$Color = -1,
        [double]$SpaceAfter = 6,
        [double]$SpaceBefore = 0,
        [double]$FontSize = 0
    )
    $start = $document.Content.End - 1
    $range = $document.Range($start, $start)
    $range.InsertAfter($Text)
    $range.SetRange($start, $start + $Text.Length)
    try { $range.Style = $document.Styles.Item($Style) } catch { }
    $range.ParagraphFormat.Alignment = $Alignment
    $range.ParagraphFormat.SpaceAfter = $SpaceAfter
    $range.ParagraphFormat.SpaceBefore = $SpaceBefore
    $range.ParagraphFormat.LineSpacingRule = $wdLineSpaceSingle
    if ($Bold) { $range.Font.Bold = 1 }
    if ($Italic) { $range.Font.Italic = 1 }
    if ($Color -ge 0) { $range.Font.Color = $Color }
    if ($FontSize -gt 0) { $range.Font.Size = $FontSize }
    $range.InsertParagraphAfter()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
}

function Add-Heading {
    param([string]$Text, [int]$Level = 1)
    Add-Paragraph -Text $Text -Style "Heading $Level" -Alignment $wdAlignParagraphLeft -SpaceBefore $(if ($Level -eq 1) { 14 } else { 8 }) -SpaceAfter 5
}

function Add-Bullets {
    param([string[]]$Items)
    foreach ($item in $Items) {
        $start = $document.Content.End - 1
        $range = $document.Range($start, $start)
        $range.InsertAfter($item)
        $range.SetRange($start, $start + $item.Length)
        $range.Style = $document.Styles.Item("Normal")
        $range.ParagraphFormat.Alignment = $wdAlignParagraphJustify
        $range.ParagraphFormat.SpaceAfter = 4
        $range.ListFormat.ApplyBulletDefault()
        $range.InsertParagraphAfter()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
    }
}

function Add-NumberedItems {
    param([string[]]$Items)
    foreach ($item in $Items) {
        $start = $document.Content.End - 1
        $range = $document.Range($start, $start)
        $range.InsertAfter($item)
        $range.SetRange($start, $start + $item.Length)
        $range.Style = $document.Styles.Item("Normal")
        $range.ParagraphFormat.Alignment = $wdAlignParagraphJustify
        $range.ParagraphFormat.SpaceAfter = 4
        $range.ListFormat.ApplyNumberDefault()
        $range.InsertParagraphAfter()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
    }
}

function Add-Callout {
    param([string]$Text, [int]$FillColor = $lightBlue, [int]$TextColor = $darkGray)
    $start = $document.Content.End - 1
    $range = $document.Range($start, $start)
    $range.InsertAfter($Text)
    $range.SetRange($start, $start + $Text.Length)
    $range.Font.Name = "Aptos"
    $range.Font.Size = 10
    $range.Font.Bold = 1
    $range.Font.Color = $TextColor
    $range.ParagraphFormat.Alignment = $wdAlignParagraphJustify
    $range.ParagraphFormat.LeftIndent = 14
    $range.ParagraphFormat.RightIndent = 14
    $range.ParagraphFormat.SpaceBefore = 6
    $range.ParagraphFormat.SpaceAfter = 6
    $range.Shading.BackgroundPatternColor = $FillColor
    $range.InsertParagraphAfter()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
}

function Add-PageBreak {
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $range.InsertBreak($wdPageBreak)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
}

function Add-Table {
    param(
        [Parameter(Mandatory = $true)][string[]]$Headers,
        [Parameter(Mandatory = $true)][object[]]$Rows,
        [int[]]$Widths = @(),
        [int]$HeaderColor = $navy,
        [int[]]$StatusColumnColors = @()
    )
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $table = $document.Tables.Add($range, $Rows.Count + 1, $Headers.Count)
    $table.Borders.Enable = 1
    $table.AllowAutoFit = $true
    $table.Rows.Alignment = 0
    $table.Range.Font.Name = "Aptos"
    $table.Range.Font.Size = 8.5
    $table.Range.ParagraphFormat.SpaceAfter = 2
    $table.Range.ParagraphFormat.SpaceBefore = 1
    $table.Range.Cells.VerticalAlignment = $wdAlignVerticalCenter

    for ($column = 1; $column -le $Headers.Count; $column++) {
        $cell = $table.Cell(1, $column)
        $cell.Range.Text = $Headers[$column - 1]
        $cell.Range.Font.Bold = 1
        $cell.Range.Font.Color = $white
        $cell.Range.ParagraphFormat.Alignment = $wdAlignParagraphCenter
        $cell.Shading.BackgroundPatternColor = $HeaderColor
    }
    for ($row = 0; $row -lt $Rows.Count; $row++) {
        for ($column = 0; $column -lt $Headers.Count; $column++) {
            $value = if ($null -eq $Rows[$row][$column]) { "" } else { [string]$Rows[$row][$column] }
            $cell = $table.Cell($row + 2, $column + 1)
            $cell.Range.Text = $value
            $cell.Range.ParagraphFormat.Alignment = if ($column -eq 0) { $wdAlignParagraphLeft } else { $wdAlignParagraphJustify }
            if (($row % 2) -eq 1) { $cell.Shading.BackgroundPatternColor = $lightGray }
        }
    }
    if ($Widths.Count -eq $Headers.Count) {
        for ($column = 1; $column -le $Headers.Count; $column++) {
            try { $table.Columns.Item($column).PreferredWidth = $Widths[$column - 1] } catch { }
        }
    }
    $after = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $after.InsertParagraphAfter()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($after)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
    return $table
}

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Add()

    $document.PageSetup.PaperSize = $wdPaperA4
    $document.PageSetup.Orientation = $wdOrientPortrait
    $document.PageSetup.TopMargin = $word.CentimetersToPoints(2.0)
    $document.PageSetup.BottomMargin = $word.CentimetersToPoints(1.8)
    $document.PageSetup.LeftMargin = $word.CentimetersToPoints(2.2)
    $document.PageSetup.RightMargin = $word.CentimetersToPoints(1.8)

    $normal = $document.Styles.Item("Normal")
    $normal.Font.Name = "Aptos"
    $normal.Font.Size = 10.5
    $normal.ParagraphFormat.Alignment = $wdAlignParagraphJustify
    $normal.ParagraphFormat.SpaceAfter = 6
    $normal.ParagraphFormat.LineSpacing = 14

    $heading1 = $document.Styles.Item("Heading 1")
    $heading1.Font.Name = "Aptos Display"
    $heading1.Font.Size = 15
    $heading1.Font.Bold = 1
    $heading1.Font.Color = $navy
    $heading1.ParagraphFormat.KeepWithNext = $true

    $heading2 = $document.Styles.Item("Heading 2")
    $heading2.Font.Name = "Aptos Display"
    $heading2.Font.Size = 12
    $heading2.Font.Bold = 1
    $heading2.Font.Color = $teal
    $heading2.ParagraphFormat.KeepWithNext = $true

    $section = $document.Sections.Item(1)
    $header = $section.Headers.Item(1).Range
    $header.Text = "T-LINGUA  |  BÁO CÁO TIẾN ĐỘ 25/08–24/09/2026"
    $header.Font.Name = "Aptos"
    $header.Font.Size = 8
    $header.Font.Color = $darkGray
    $header.ParagraphFormat.Alignment = $wdAlignParagraphRight
    $footer = $section.Footers.Item(1).Range
    $footer.Text = "Tài liệu nội bộ — Trang "
    $footer.Font.Name = "Aptos"
    $footer.Font.Size = 8
    $footer.ParagraphFormat.Alignment = $wdAlignParagraphCenter
    $pageFieldRange = $footer.Duplicate
    $pageFieldRange.Collapse($wdCollapseEnd)
    [void]$footer.Fields.Add($pageFieldRange, $wdFieldPage)

    # Trang bìa
    Add-Paragraph -Text "T-LINGUA" -Alignment $wdAlignParagraphCenter -Bold -Color $teal -FontSize 16 -SpaceBefore 80 -SpaceAfter 18
    Add-Paragraph -Text "BÁO CÁO TIẾN ĐỘ DỰ ÁN`nHỆ THỐNG AI DỊCH THUẬT" -Alignment $wdAlignParagraphCenter -Bold -Color $navy -FontSize 24 -SpaceAfter 20
    Add-Paragraph -Text "Giai đoạn: 25/08/2026 – 24/09/2026" -Alignment $wdAlignParagraphCenter -Bold -Color $blue -FontSize 14 -SpaceAfter 8
    Add-Paragraph -Text "Ngày lập báo cáo: 25/09/2026" -Alignment $wdAlignParagraphCenter -Italic -Color $darkGray -FontSize 10.5 -SpaceAfter 40
    Add-Table -Headers @("Thông tin", "Nội dung") -Rows @(
        @("Dự án", "T-Lingua — hệ thống dịch văn bản và hội thoại Việt–Anh"),
        @("Thành viên", "Hà Văn Đô; Nguyễn Quang Thọ"),
        @("Nền tảng", "Flutter frontend; FastAPI/WebSocket backend; React Admin"),
        @("Phạm vi báo cáo", "Kết quả thực hiện từ 25/08 đến hết 24/09/2026"),
        @("Phạm vi chứng thực", "Snapshot mã nguồn, log kiểm thử và benchmark được đối chiếu ngay sau mốc chốt")
    ) -Widths @(110, 340) | Out-Null
    Add-Paragraph -Text "Mức độ lưu hành: Nội bộ dự án" -Alignment $wdAlignParagraphCenter -Italic -Color $darkGray -SpaceBefore 45
    Add-PageBreak

    Add-Heading -Text "TÓM TẮT ĐIỀU HÀNH" -Level 1
    Add-Paragraph -Text "Trong giai đoạn 25/08–24/09/2026, nhóm tập trung vào bốn hướng: (1) đánh giá và chuẩn hóa nền tảng sẵn có; (2) hoàn thiện backend, bảo mật và pipeline realtime; (3) xây dựng hệ thống quản trị tập trung; (4) thiết lập phương pháp đo chất lượng và hiệu năng dịch. Kết quả kỹ thuật cho thấy hệ thống đã có cấu trúc rõ hơn, các luồng quản trị trọng yếu đã hình thành, cơ chế xác thực/phân quyền được củng cố và bộ chứng thực có thể tái lập đã được tạo."
    Add-Paragraph -Text "Tại thời điểm chốt 24/09, dự án đã đạt phần lớn mục tiêu nền tảng và MVP quản trị nhưng chưa thể coi là hoàn tất chất lượng production. Những khoảng trống chính gồm đánh giá độc lập của hai người chấm, chất lượng thuật ngữ, WER trên tiếng nói, TTS MOS, tải đồng thời/soak nhiều giờ và bằng chứng Git về ngày hoàn thành từng thay đổi. Một số hạng mục kỹ thuật được hoàn thiện hoặc chạy kiểm chứng trong ngày 25/09 và được ghi riêng, không hồi tố thành kết quả trước deadline."
    Add-Callout -Text "KẾT LUẬN NGẮN: Đạt kỹ thuật có điều kiện. Hệ thống đủ cơ sở để chuyển sang giai đoạn Quality Gate, Performance Gate, tích hợp và UAT; chưa đủ cơ sở tuyên bố sẵn sàng production."

    Add-Heading -Text "Phạm vi và nguyên tắc ghi nhận" -Level 2
    Add-Bullets -Items @(
        "Mốc báo cáo: từ 00:00 ngày 25/08/2026 đến 23:59 ngày 24/09/2026.",
        "Số liệu kiểm chứng mới nhất được lấy từ artifact trong docs/progress_2026-09-24/evidence và .phase1-artifacts/progress_2026-09-24.",
        "Artifact tạo sau 24/09 chỉ chứng minh trạng thái snapshot và kết quả lần chạy đó; không tự chứng minh hạng mục đã hoàn tất trước mốc chốt.",
        "Git chỉ có commit gần nhất ngày 14/08/2026 và snapshot ghi nhận 213 mục worktree thay đổi/chưa theo dõi. Vì vậy chưa thể dùng lịch sử Git để xác định ngày hoàn thành hoặc tác giả của từng thay đổi.",
        "Các chỉ số benchmark local không được diễn giải thành SLA hoặc capacity production."
    )

    Add-Heading -Text "1. LÀM ĐƯỢC NHỮNG GÌ?" -Level 1
    Add-Heading -Text "1.1. Quản trị dự án và kiến trúc" -Level 2
    Add-Bullets -Items @(
        "Xác định phạm vi MVP, ngoài phạm vi, RACI, Definition of Done, backlog và ma trận truy vết yêu cầu.",
        "Mô tả luồng người dùng admin, kiến trúc mục tiêu và hợp đồng REST/WebSocket, bao gồm mã lỗi và ranh giới xác thực.",
        "Lập inventory 227 tệp nguồn, 45 route và 32 hình dạng sự kiện server; mỗi tệp snapshot có SHA-256 để đối chiếu.",
        "Hoàn thiện kế hoạch tổng thể 25/08–30/10/2026 với các mốc Quality Gate, Performance Gate, tích hợp, UAT và bàn giao."
    )

    Add-Heading -Text "1.2. Backend, bảo mật và realtime" -Level 2
    Add-Bullets -Items @(
        "Củng cố session/JWT, API key theo scope, phân quyền theo vai trò, rate limit, CORS/host, giới hạn payload và cách ly dữ liệu theo owner.",
        "Chuẩn hóa pipeline theo turn ID và session state; sử dụng VAD, hàng đợi STT–dịch–TTS, backpressure, telemetry và xử lý kết quả đến muộn.",
        "Bổ sung health/readiness, logging có cấu trúc, cache có version/invalidation và Translation Memory theo đúng chiều ngôn ngữ/owner.",
        "Sửa quy trình cleanup WebSocket để hủy và chờ sender task kết thúc, loại bỏ lỗi CancelledError quan sát được khi đóng kết nối."
    )

    Add-Heading -Text "1.3. Admin web" -Level 2
    Add-Bullets -Items @(
        "Hoàn thiện các nhóm trang Login, Dashboard, Analytics, Users, API Keys, Dictionary, History, QA và Settings.",
        "Áp dụng route guard theo role, tìm kiếm, lọc, phân trang, responsive và các trạng thái loading/empty/error.",
        "Hỗ trợ quản lý người dùng, khóa/mở tài khoản, reset phiên, quản lý API key, từ điển, lịch sử, đánh giá chất lượng và audit.",
        "Các phần rotate API key, sửa role/mật khẩu, xuất dữ liệu QA/từ điển, model canary/promote/rollback được đối chiếu hoặc hoàn thiện bổ sung ngày 25/09; không tính hồi tố cho 24/09."
    )

    Add-Heading -Text "1.4. Flutter frontend" -Level 2
    Add-Bullets -Items @(
        "Hoàn thiện controller/repository cho dịch, lịch sử, cài đặt; quản lý phiên, WebSocket, audio stream/player và state machine microphone.",
        "Tăng tính nhất quán của trạng thái kết nối, ghi âm, phát âm thanh, retry và phản hồi lỗi.",
        "Static analysis sau khi cấp đúng quyền ghi cache cho Dart Analysis Server cho kết quả No issues found."
    )

    Add-Heading -Text "1.5. Đo chất lượng và hiệu năng" -Level 2
    Add-Bullets -Items @(
        "Tạo baseline pilot 30 câu hai chiều Việt–Anh bằng model facebook/nllb-200-distilled-1.3B chạy local trên GPU.",
        "Sau đối chiếu mốc chốt, mở rộng benchmark lên 500 câu thuộc 10 miền và 100 audio sạch/nhiễu; lưu cả dữ liệu từng case và summary.",
        "Đo pipeline warm local STT–NLLB–TTS, A/B beam 1 và beam 3, cProfile và soak 200 lượt.",
        "Tạo phiếu 100 case × 2 reviewer cho adequacy, fluency và taxonomy lỗi; điểm người chấm chưa được tự động điền."
    )

    Add-Heading -Text "2. CHỨNG THỰC" -Level 1
    Add-Paragraph -Text "Báo cáo dùng bốn lớp chứng thực độc lập: snapshot mã nguồn có hash; regression và kiểm thử tự động; dữ liệu benchmark thô kèm summary; tài liệu quản trị và kế hoạch. Các lớp này cho phép kiểm tra lại trạng thái kỹ thuật, nhưng không thay thế commit/tag có ngày và review khi cần chứng minh lịch sử thực hiện."

    Add-Table -Headers @("Nhóm chứng thực", "Kết quả xác nhận", "File/đường dẫn chính") -Rows @(
        @("Inventory", "227 tệp; 45 route; hash SHA-256", ".phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json"),
        @("Regression", "7/7 probe đạt", ".phase1-artifacts/progress_2026-09-24/regression_results_v3.json"),
        @("Backend", "121/121 test đạt ở lần kiểm chứng mới nhất", "docs/progress_2026-09-24/evidence/backend_full_tests.log"),
        @("Admin build", "Production build đạt", "docs/progress_2026-09-24/evidence/admin_build.log"),
        @("Admin lint", "Đạt; còn 2 cảnh báo Fast Refresh không chặn", "docs/progress_2026-09-24/evidence/admin_lint.log"),
        @("Admin browser", "21/21 test đạt ở lần kiểm chứng mới nhất", "docs/progress_2026-09-24/evidence/admin_browser_tests.log"),
        @("Flutter", "Static analysis đạt, không phát hiện lỗi", "docs/progress_2026-09-24/evidence/flutter_analyze.log"),
        @("Dịch pilot", "30 case và kết quả từng câu", "docs/progress_2026-09-24/evidence/translation_baseline_cases.csv"),
        @("Dịch v2", "500 case; latency và chỉ số chất lượng", "docs/progress_2026-09-24/evidence/translation_benchmark_v2_cases.csv"),
        @("Giọng nói", "100 audio sạch/nhiễu; latency và WER", "docs/progress_2026-09-24/evidence/speech_benchmark_v2_cases.csv"),
        @("Pipeline", "10 lượt warm local; profile từng chặng", "docs/progress_2026-09-24/evidence/full_pipeline_benchmark_summary.json"),
        @("A/B & soak", "Beam 1/3; 200 lượt soak", "docs/progress_2026-09-24/evidence/inference_ab_soak_summary.json"),
        @("Tổng hợp kiểm thử", "Trạng thái, lệnh chạy, thời lượng và hash log", "docs/progress_2026-09-24/evidence/verification_summary.json")
    ) -Widths @(95, 150, 245) | Out-Null

    Add-Heading -Text "3. GHI CHÚ FILE CHỨNG THỰC KÈM TÀI LIỆU" -Level 1
    Add-Paragraph -Text "Toàn bộ đường dẫn trong báo cáo là đường dẫn tương đối tính từ thư mục gốc T_Langua_Test. File Word này không nhúng dữ liệu thô để tránh tăng dung lượng và tránh làm mất khả năng đối chiếu; thư mục evidence là phần đi kèm bắt buộc khi bàn giao báo cáo."
    Add-NumberedItems -Items @(
        "Giữ nguyên cấu trúc docs/progress_2026-09-24/evidence khi sao chép hoặc nộp tài liệu.",
        "Dùng verification_summary.json để xem lệnh chạy, exit code, thời lượng và SHA-256 của từng log kiểm thử.",
        "Dùng các file *_summary.json để đọc số tổng hợp; dùng *_cases.csv để kiểm tra từng mẫu nguồn, tham chiếu, kết quả và latency.",
        "Hai file *.prof là dữ liệu cProfile máy đọc; file *.txt cùng tên là bản dễ đọc cho người rà soát.",
        "human_evaluation_v2_two_reviewers.csv chỉ là phiếu đã chuẩn bị. Chỉ coi là chứng thực người thật sau khi hai reviewer chấm độc lập, ghi tên/ngày và ký xác nhận.",
        "Không công bố thư mục snapshot ra ngoài khi chưa rà soát secret/PII; inventory loại trừ các tên file bí mật thông dụng nhưng không phải công cụ quét secret toàn diện."
    )

    Add-Heading -Text "4. VIỆC ĐÃ ĐẠT ĐƯỢC / CHƯA ĐẠT ĐƯỢC" -Level 1
    $statusTable = Add-Table -Headers @("Hạng mục", "Trạng thái", "Đánh giá và điều kiện") -Rows @(
        @("Phạm vi, RACI, DoD, kiến trúc", "ĐẠT", "Đã văn bản hóa; cần chữ ký nếu dùng làm biên bản chính thức."),
        @("Backend auth/RBAC/isolation", "ĐẠT KỸ THUẬT", "Kiểm thử tự động đạt; chưa thay thế pentest/dependency scan."),
        @("Pipeline realtime", "ĐẠT KỸ THUẬT", "Có turn/session/queue/backpressure; cần tải đồng thời production-like."),
        @("Admin MVP", "ĐẠT CÓ ĐIỀU KIỆN", "Các trang chính build/test đạt; một số control hoàn thiện ngày 25/09."),
        @("Flutter static analysis", "ĐẠT SAU ĐỐI CHIẾU", "No issues found sau khi xử lý quyền cache analyzer."),
        @("Regression lỗi trọng yếu", "ĐẠT", "7/7 probe đạt."),
        @("Baseline dịch pilot", "ĐẠT", "30 câu; chỉ là pilot, không đại diện production."),
        @("Benchmark 500 câu", "HOÀN THIỆN BỔ SUNG", "Chạy sau mốc chốt; corpus template có kiểm soát."),
        @("Độ đúng thuật ngữ", "CHƯA ĐẠT", "74,29%, thấp hơn mục tiêu 95%."),
        @("STT WER", "CHƯA ĐẠT", "WER chung 39,68%; cần audio người thật và tối ưu."),
        @("Đánh giá 2 reviewer", "CHƯA ĐẠT", "Phiếu đã tạo nhưng chưa có điểm/ký xác nhận độc lập."),
        @("TTS MOS", "CHƯA ĐẠT", "Chưa có người nghe độc lập và biên bản chấm."),
        @("Performance local", "ĐẠT BASELINE", "Có p50/p95/p99; không gồm network/queue hoặc tải đồng thời."),
        @("Capacity/soak production", "CHƯA ĐẠT", "Soak mới 200 lượt local, chưa đạt mốc 4 giờ/tải mục tiêu."),
        @("Truy vết bằng Git", "CHƯA ĐẠT", "Worktree chưa sạch, không có commit trong kỳ báo cáo.")
    ) -Widths @(140, 100, 250)
    for ($row = 2; $row -le $statusTable.Rows.Count; $row++) {
        $text = $statusTable.Cell($row, 2).Range.Text
        if ($text -like "*CHƯA ĐẠT*") { $statusTable.Cell($row, 2).Shading.BackgroundPatternColor = $lightRed }
        elseif ($text -like "*ĐẠT*" -and $text -notlike "*ĐIỀU KIỆN*" -and $text -notlike "*BASELINE*" -and $text -notlike "*SAU*") { $statusTable.Cell($row, 2).Shading.BackgroundPatternColor = $lightGreen }
        else { $statusTable.Cell($row, 2).Shading.BackgroundPatternColor = $lightAmber }
        $statusTable.Cell($row, 2).Range.Font.Bold = 1
    }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($statusTable)

    Add-Callout -Text "Đánh giá chung đến mốc 24/09: phần nền tảng và MVP đạt đáng kể; quality gate, đánh giá người thật và capacity production chưa đạt. Trạng thái phù hợp nhất là 'Đạt kỹ thuật có điều kiện'." -FillColor $lightAmber

    Add-Heading -Text "5. MỤC ĐÍCH CỦA TRANG WEB ADMIN" -Level 1
    Add-Paragraph -Text "Admin web là trung tâm vận hành và kiểm soát hệ thống T-Lingua. Đây không phải giao diện dịch dành cho người dùng cuối; nhiệm vụ của nó là giúp quản trị viên, reviewer và người vận hành nhìn thấy trạng thái hệ thống, quản lý quyền truy cập, kiểm soát chất lượng và thực hiện thay đổi có truy vết."
    Add-Bullets -Items @(
        "Quản trị truy cập: đăng nhập, role, session, API key, scope, khóa/mở người dùng và thu hồi quyền.",
        "Theo dõi vận hành: Dashboard/Analytics hiển thị request, lỗi, latency, throughput, ngôn ngữ và phản hồi chất lượng.",
        "Quản lý tri thức dịch: Dictionary và Translation Memory giúp duy trì thuật ngữ, cặp ngôn ngữ và ngữ cảnh tổ chức.",
        "Kiểm soát chất lượng: History và QA hỗ trợ tìm lỗi, chấm adequacy/fluency, phân loại lỗi, sửa bản dịch và xuất dữ liệu.",
        "Kiểm soát thay đổi: Settings/Models cho phép cấu hình whitelist, active/canary, promote/rollback và xem version.",
        "Truy vết và tuân thủ: Audit log ghi nhận ai đã làm gì, trên đối tượng nào và vào thời điểm nào.",
        "Giảm phụ thuộc thao tác trực tiếp vào cơ sở dữ liệu hoặc máy chủ, nhờ đó giảm rủi ro vận hành và dễ phân quyền trách nhiệm."
    )

    Add-Heading -Text "6. CẢI THIỆN ĐỘ DỊCH NHƯ THẾ NÀO?" -Level 1
    Add-Paragraph -Text "Chiến lược cải thiện không chỉ đổi model. Dự án kết hợp tiền xử lý, kiểm soát thuật ngữ, Translation Memory, lựa chọn cấu hình suy luận, phản hồi con người và đo lường có phiên bản. Mọi thay đổi chất lượng phải qua Performance Gate; mọi tối ưu tốc độ phải qua Quality Gate."
    Add-Table -Headers @("Biện pháp", "Cách thực hiện", "Tác dụng mong đợi") -Rows @(
        @("Chuẩn hóa đầu vào", "Chuẩn hóa dấu câu, khoảng trắng, dấu phẩy thập phân; giới hạn hallucination STT", "Giảm lỗi hình thức và sai số/số tiền."),
        @("Bảo toàn entity/số", "Tạo case riêng cho tên riêng, ngày giờ, đơn vị, số liệu", "Giảm lỗi nghiêm trọng về ý nghĩa."),
        @("Glossary/Dictionary", "Thuật ngữ theo domain và chiều ngôn ngữ; review trước khi dùng chung", "Tăng độ đúng thuật ngữ từ mức 74,29% hướng tới ≥95%."),
        @("Translation Memory", "Exact/fuzzy match, cô lập owner, direction-aware, ngưỡng chống match mơ hồ", "Tái sử dụng bản dịch tốt mà không lẫn tenant/chiều dịch."),
        @("Cache có kiểm soát", "Key gồm owner/ngôn ngữ/version; invalidation khi glossary/model đổi", "Tăng tốc nhưng tránh trả kết quả cũ hoặc sai phạm vi."),
        @("A/B cấu hình", "So sánh beam 1 và beam 3 trên cùng bộ case", "Chọn beam 1 vì p95 thấp hơn trong khi chrF gần tương đương."),
        @("Human QA", "Hai reviewer chấm adequacy, fluency, lỗi và mức nghiêm trọng", "Phát hiện lỗi ngữ nghĩa mà token-F1/BLEU không phản ánh."),
        @("Feedback loop", "Bản sửa đã duyệt mới được đưa vào glossary/TM và benchmark hồi quy", "Biến lỗi thực tế thành dữ liệu cải thiện có kiểm soát."),
        @("STT/TTS", "Audio người thật, accent, môi trường nhiễu; tuning VAD/denoise; MOS độc lập", "Giảm WER và tăng tự nhiên của hội thoại."),
        @("Canary/rollback", "Triển khai model/cấu hình theo version, theo dõi metric rồi promote hoặc rollback", "Cải thiện an toàn, tránh làm giảm chất lượng diện rộng.")
    ) -Widths @(100, 210, 180) | Out-Null

    Add-Heading -Text "Số liệu hiện tại và khoảng trống chất lượng" -Level 2
    Add-Bullets -Items @(
        "Benchmark 500 câu: BLEU có smoothing 56,925; chrF 74,867; token-F1 0,7871; độ đúng thuật ngữ 650/875 = 74,29%.",
        "STT trên 100 audio tổng hợp: WER sạch 39,03%; WER nhiễu 15 dB 40,33%; WER chung 39,68%.",
        "Các con số tự động chỉ là chỉ báo. Chưa có kết luận chất lượng production trước khi hoàn tất corpus tự nhiên và chấm độc lập của con người."
    )

    Add-Heading -Text "7. MỤC TIÊU VÀ KẾ HOẠCH TIẾP THEO" -Level 1
    Add-Table -Headers @("Thời gian mục tiêu", "Mục tiêu", "Đầu ra/điều kiện hoàn thành") -Rows @(
        @("25–27/09", "Chốt Admin RC", "Đóng cảnh báo còn lại; review RBAC; smoke 100% luồng Login/Dashboard/Users/Keys/Dictionary/History/QA/Settings."),
        @("Đến 05/10", "Quality Gate", "Hai reviewer chấm/ký; tăng accuracy thuật ngữ lên ≥95%; WER sạch ≤12%, nhiễu ≤20% hoặc cải thiện tương đối ≥15%; có TTS MOS."),
        @("Đến 10/10", "Performance Gate", "Text p95 ≤1,2 giây; voice p95 ≤2,5 giây; success ≥99,5%; soak ≥4 giờ, không OOM, error <0,5%."),
        @("01–15/10", "Tích hợp frontend–backend", "Khóa API contract v1; E2E Flutter/admin/backend; kiểm thử reconnect, cancel, timeout, offline và lỗi quyền."),
        @("12–23/10", "Regression, bảo mật và UAT", "0 lỗi Critical/High chưa xử lý; hồi quy P0 100%, P1 ≥95%; UAT có biên bản và danh sách known issues."),
        @("24–27/10", "Staging và rehearsal", "Deploy đúng artifact; migration; health/smoke; metric/alert; backup/restore/rollback rehearsal đạt."),
        @("28–30/10", "Đào tạo, Go/No-Go và bàn giao", "Runbook vận hành; đào tạo; biên bản Go/No-Go; release notes; ký bàn giao.")
    ) -Widths @(85, 125, 280) | Out-Null

    Add-Heading -Text "Ưu tiên hành động ngay" -Level 2
    Add-NumberedItems -Items @(
        "Đóng gói snapshot bằng commit/tag, code review và biên bản xác nhận để khôi phục truy vết thời gian/tác giả.",
        "Hoàn tất 100 case × 2 reviewer; phân tích lỗi theo domain, chiều dịch, entity/số và thuật ngữ.",
        "Bổ sung glossary theo domain và chạy lại benchmark đã khóa; không thay dataset giữa hai lần so sánh.",
        "Thu thập audio người thật có đồng ý sử dụng, đa accent/thiết bị/mức nhiễu; chạy WER và TTS MOS.",
        "Chạy load/soak production-like có network, queue, worker và database mục tiêu; đo p50/p95/p99, error và memory.",
        "Đóng cảnh báo lint, rà soát dependency/security, diễn tập backup–restore và rollback trước UAT."
    )

    Add-Heading -Text "8. KẾT LUẬN" -Level 1
    Add-Paragraph -Text "Giai đoạn 25/08–24/09 đã tạo được nền tảng kỹ thuật và quản trị quan trọng cho T-Lingua: kiến trúc rõ hơn, backend và realtime an toàn hơn, admin web bao phủ các luồng vận hành chính, Flutter có luồng dịch/hội thoại hoàn chỉnh hơn và hệ thống bắt đầu có bằng chứng định lượng. Bộ chứng thực sau mốc chốt cho thấy kiểm thử tự động đạt và pipeline local hoạt động ổn định trong phạm vi đo."
    Add-Paragraph -Text "Tuy vậy, dự án chưa đạt điều kiện production vì chất lượng thuật ngữ và WER còn dưới mục tiêu, đánh giá hai reviewer/TTS MOS chưa hoàn tất, chưa có tải đồng thời và soak nhiều giờ, và lịch sử Git chưa chứng minh được thời điểm/tác giả thay đổi. Giai đoạn tiếp theo cần ưu tiên Quality Gate, Performance Gate và truy vết phát hành thay vì mở rộng thêm tính năng."

    Add-PageBreak
    Add-Heading -Text "PHỤ LỤC A — BẢNG SỐ LIỆU KIỂM CHỨNG MỚI NHẤT" -Level 1
    Add-Table -Headers @("Chỉ số", "Kết quả", "Diễn giải/giới hạn") -Rows @(
        @("Inventory", "227 tệp; 45 route; 32 server event shapes", "Snapshot tĩnh, không phải OpenAPI runtime."),
        @("Regression", "7/7 đạt", "Probe cô lập; không bao phủ toàn bộ HTTP/WS/GPU."),
        @("Backend test", "121/121 đạt; 35,495 giây test runner", "Có cảnh báo dự kiến và 1 cảnh báo dependency TestClient."),
        @("Admin browser", "21/21 đạt", "Browser test theo kịch bản dự án."),
        @("Admin build/lint", "Build đạt; lint đạt với 2 cảnh báo", "Cảnh báo Fast Refresh không chặn build."),
        @("Flutter analyze", "No issues found", "Kết quả sau khi cho analyzer ghi cache AppData."),
        @("Dịch v2", "500 case", "250 Việt→Anh; 250 Anh→Việt; 10 domain template."),
        @("Latency NLLB", "Mean 483,109 ms; p50 450,364; p95 743,579; p99 853,838", "Warm local GPU; không gồm network/queue."),
        @("Chất lượng NLLB", "BLEU 56,925; chrF 74,867; token-F1 0,7871", "BLEU add-one smoothing; chỉ so sánh cùng script."),
        @("Thuật ngữ", "650/875 = 74,29%", "Chưa đạt mục tiêu 95%."),
        @("Audio", "100 mẫu: 50 sạch, 50 nhiễu 15 dB", "TTS tổng hợp, chưa đại diện người thật."),
        @("WER", "Sạch 39,03%; nhiễu 40,33%; chung 39,68%", "Chưa đạt quality gate."),
        @("Full pipeline", "p95 1.175,470 ms; 1,036 turn/giây tuần tự", "10 lượt warm local; không có network/queue."),
        @("GPU pipeline", "Đỉnh 3.306 MB", "RTX 3050 Laptop GPU 6 GB."),
        @("A/B", "Beam 1 p95 767,597 ms; beam 3 p95 983,532 ms", "50 case/cấu hình; chọn beam 1."),
        @("Soak", "200/200; không OOM; tăng bộ nhớ 0 MB", "Chỉ 116,429 giây, không phải soak 4 giờ."),
        @("Admin API", "Dashboard p95 15,650 ms; QA p95 20,135; Users p95 18,108", "TestClient + SQLite in-memory; tuần tự, không phải capacity production.")
    ) -Widths @(105, 170, 215) | Out-Null

    Add-PageBreak
    Add-Heading -Text "PHỤ LỤC B — DANH MỤC FILE CHỨNG THỰC" -Level 1
    Add-Table -Headers @("STT", "File", "Nội dung") -Rows @(
        @("01", ".phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json", "Inventory, route, event shape, Git và môi trường."),
        @("02", ".phase1-artifacts/progress_2026-09-24/regression_results_v3.json", "Kết quả 7 regression probe và SHA-256 nguồn."),
        @("03", "docs/progress_2026-09-24/evidence/verification_summary.json", "Tổng hợp kiểm thử, lệnh, exit code, thời lượng, hash log."),
        @("04", "docs/progress_2026-09-24/evidence/backend_full_tests.log", "Log 121 backend test."),
        @("05", "docs/progress_2026-09-24/evidence/admin_build.log", "Log build production admin."),
        @("06", "docs/progress_2026-09-24/evidence/admin_lint.log", "Log lint và hai cảnh báo."),
        @("07", "docs/progress_2026-09-24/evidence/admin_browser_tests.log", "Log 21 browser test."),
        @("08", "docs/progress_2026-09-24/evidence/flutter_analyze.log", "Kết quả Flutter static analysis."),
        @("09", "docs/progress_2026-09-24/evidence/translation_baseline_cases.csv", "Dữ liệu từng case baseline pilot 30 câu."),
        @("10", "docs/progress_2026-09-24/evidence/translation_baseline_summary.json", "Tổng hợp pilot model thật."),
        @("11", "docs/progress_2026-09-24/evidence/benchmark_v2_500.csv", "Corpus benchmark v2."),
        @("12", "docs/progress_2026-09-24/evidence/benchmark_v2_metadata.json", "Version/hash và metadata corpus."),
        @("13", "docs/progress_2026-09-24/evidence/translation_benchmark_v2_cases.csv", "Kết quả chi tiết 500 câu."),
        @("14", "docs/progress_2026-09-24/evidence/translation_benchmark_v2_summary.json", "Tổng hợp latency/chất lượng 500 câu."),
        @("15", "docs/progress_2026-09-24/evidence/speech_benchmark_v2_cases.csv", "Kết quả chi tiết 100 audio."),
        @("16", "docs/progress_2026-09-24/evidence/speech_benchmark_v2_summary.json", "Tổng hợp TTS/STT latency, WER, RTF."),
        @("17", "docs/progress_2026-09-24/evidence/full_pipeline_benchmark_cases.csv", "Kết quả từng lượt full pipeline."),
        @("18", "docs/progress_2026-09-24/evidence/full_pipeline_benchmark_summary.json", "Tổng hợp pipeline STT–NLLB–TTS."),
        @("19", "docs/progress_2026-09-24/evidence/full_pipeline_profile.txt", "Bản đọc cProfile full pipeline."),
        @("20", "docs/progress_2026-09-24/evidence/inference_ab_soak_summary.json", "A/B beam và soak 200 lượt."),
        @("21", "docs/progress_2026-09-24/evidence/admin_api_large_dataset_benchmark.json", "Benchmark admin API với 20.000 log, 5.001 user."),
        @("22", "docs/progress_2026-09-24/evidence/admin_api_profile.txt", "Bản đọc profile admin API."),
        @("23", "docs/progress_2026-09-24/evidence/human_evaluation_v2_two_reviewers.csv", "Phiếu 100 case × 2 reviewer; chờ chấm/ký."),
        @("24", "docs/progress_2026-09-24/PROJECT_ARTIFACTS.md", "Charter, RACI, phạm vi, kiến trúc, benchmark và DoD."),
        @("25", "docs/Ke_hoach_du_an_AI_dich_thuat_25-08_den_30-10-2026.xlsx", "Kế hoạch gốc và các mốc dự án.")
    ) -Widths @(35, 285, 170) | Out-Null

    Add-Heading -Text "PHỤ LỤC C — XÁC NHẬN" -Level 1
    Add-Paragraph -Text "Người lập báo cáo xác nhận các số liệu được trích từ file chứng thực liệt kê trong Phụ lục B; các giới hạn đã được công bố và không có số liệu đánh giá người thật nào do AI tự điền." -SpaceAfter 20
    Add-Table -Headers @("Vai trò", "Họ và tên", "Ngày", "Ký xác nhận") -Rows @(
        @("Technical Lead Backend/AI", "Hà Văn Đô", "____/____/2026", "____________________"),
        @("Frontend & Admin Lead", "Nguyễn Quang Thọ", "____/____/2026", "____________________"),
        @("Người duyệt/giảng viên", "", "____/____/2026", "____________________")
    ) -Widths @(145, 130, 90, 125) | Out-Null

    $document.Fields.Update() | Out-Null
    $document.Repaginate()
    $document.SaveAs2($outputPath, $wdFormatDocumentDefault)
    $pageCount = $document.ComputeStatistics(2)
    $wordCount = $document.ComputeStatistics(0)
    Write-Output "Created: $outputPath"
    Write-Output "Pages: $pageCount"
    Write-Output "Words: $wordCount"
}
finally {
    if ($null -ne $document) {
        try { $document.Close($false) } catch { }
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) } catch { }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch { }
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
