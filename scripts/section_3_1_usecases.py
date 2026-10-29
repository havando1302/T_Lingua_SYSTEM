# -*- coding: utf-8 -*-
"""
Module providing 3.1: Dac ta cac ca su dung (Use Case) for T-Lingua report.
Includes all 18 Use Cases in detailed standard tabular format matching [DALN]2210.
"""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from scripts.docx_utils import (
    add_paragraph, add_heading_2, add_heading_3, add_caption,
    set_cell_background, set_cell_margins, set_table_borders,
    PRIMARY_COLOR, HEADER_BG_HEX, ZEBRA_BG_HEX
)

def render_use_case_table(doc, uc_data):
    """
    uc_data = {
        'id_name': 'UC1.1 - Dịch giọng nói một chiều thời gian thực',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '5/10/2026',
        'desc': '...',
        'primary_actor': 'Người dùng ứng dụng di động',
        'secondary_actor': 'Máy chủ xử lý (FastAPI) và chuỗi xử lý trí tuệ nhân tạo (AI)',
        'trigger': 'Người dùng chọn chiều dịch và nhấn nút micrô trên Trang chủ.',
        'pre_cond': ['...'],
        'post_cond': ['...'],
        'main_flow': ['...'],
        'alt_flow': ['...'],
        'exceptions': ['...'],
        'priority': 'Cao',
        'business_rules': ['...'],
        'assumptions': ['...']
    }
    """
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    rows_def = [
        ("Số và tên Use Case", uc_data['id_name']),
        ("Người tạo / Ngày tạo", f"Người tạo: {uc_data['creator']}    |    Ngày tạo: {uc_data['date']}"),
        ("Mô tả", uc_data['desc']),
        ("Tác nhân chính", uc_data['primary_actor']),
        ("Tác nhân phụ", uc_data['secondary_actor']),
        ("Sự kiện kích hoạt", uc_data['trigger']),
        ("Tiền điều kiện", "\n".join(f"- {c}" for c in uc_data['pre_cond'])),
        ("Hậu điều kiện", "\n".join(f"- {c}" for c in uc_data['post_cond'])),
        ("Luồng thông thường", "\n".join(f"{i+1}. {step}" for i, step in enumerate(uc_data['main_flow']))),
        ("Luồng thay thế", "\n".join(f"- {step}" for step in uc_data['alt_flow'])),
        ("Các ngoại lệ", "\n".join(f"- {step}" for step in uc_data['exceptions'])),
        ("Độ ưu tiên", uc_data['priority']),
        ("Các quy tắc nghiệp vụ", "\n".join(f"- {rule}" for rule in uc_data['business_rules'])),
        ("Các giả thuyết", "\n".join(f"- {assump}" for assump in uc_data.get('assumptions', ['Hệ thống Backend và kết nối mạng hoạt động bình thường.'])))
    ]
    
    for idx, (label, content) in enumerate(rows_def):
        row = table.add_row()
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        
        # Col widths: 2.2 inches & 4.6 inches (total 6.8 inches)
        cell_lbl.width = Inches(2.0)
        cell_val.width = Inches(4.8)
        
        set_cell_margins(cell_lbl, top=80, bottom=80, left=120, right=120)
        set_cell_margins(cell_val, top=80, bottom=80, left=120, right=120)
        
        # Zebra shading
        if idx % 2 == 0:
            set_cell_background(cell_lbl, "EBF1F6")
            set_cell_background(cell_val, "FAFCFD")
        else:
            set_cell_background(cell_lbl, "F0F4F8")
            set_cell_background(cell_val, "FFFFFF")
            
        p_lbl = cell_lbl.paragraphs[0]
        p_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_lbl.paragraph_format.space_after = Pt(2)
        p_lbl.paragraph_format.space_before = Pt(2)
        p_lbl.paragraph_format.line_spacing = 1.15
        r_lbl = p_lbl.add_run(label)
        r_lbl.bold = True
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(11)
        r_lbl.font.color.rgb = PRIMARY_COLOR
        
        p_val = cell_val.paragraphs[0]
        p_val.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_val.paragraph_format.space_after = Pt(2)
        p_val.paragraph_format.space_before = Pt(2)
        p_val.paragraph_format.line_spacing = 1.15
        r_val = p_val.add_run(content)
        r_val.font.name = "Times New Roman"
        r_val.font.size = Pt(11)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def render_section_3_1(doc):
    add_heading_2(doc, "3.1. Đặc tả các ca sử dụng (Use Case)")
    
    add_paragraph(doc, 
        "Dựa trên kết quả phân tích yêu cầu tại Chương 2, hệ thống T-Lingua bao gồm 7 nhóm ca sử dụng nghiệp vụ "
        "chính (từ UC1 đến UC7) với tổng cộng 18 ca sử dụng chi tiết. Mỗi ca sử dụng được đặc tả tường minh theo "
        "chuẩn mực tài liệu kỹ thuật công nghệ thông tin gồm: mã và tên ca sử dụng, người tạo, ngày tạo, mô tả "
        "tổng quát, tác nhân chính/phụ, sự kiện kích hoạt, tiền điều kiện, hậu điều kiện, luồng xử lý thông thường "
        "(kèm các bước tuần tự), luồng thay thế, các trường hợp ngoại lệ, độ ưu tiên, các quy tắc nghiệp vụ ràng "
        "buộc và các giả thuyết hệ thống liên quan."
    )
    
    # 3.1.1 Nhóm UC1
    add_heading_3(doc, "3.1.1. Nhóm UC1 - Dịch giọng nói và hội thoại")
    
    add_caption(doc, "Bảng 3.1. Đặc tả UC1.1 - Dịch giọng nói một chiều thời gian thực")
    render_use_case_table(doc, {
        'id_name': 'UC1.1 - Dịch giọng nói một chiều thời gian thực',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng nói tiếng Việt hoặc tiếng Anh và nhận kết quả gồm văn bản nhận dạng, bản dịch sang ngôn ngữ còn lại và âm thanh tổng hợp được phát gần thời gian thực.',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'Máy chủ xử lý (FastAPI Backend) và chuỗi xử lý AI Pipeline (VAD, Whisper, TM/NLLB, MMS VITS)',
        'trigger': 'Người dùng chọn chiều dịch (Việt -> Anh hoặc Anh -> Việt) và nhấn giữ nút micrô trên Trang chủ.',
        'pre_cond': [
            'Ứng dụng di động đã được cấp quyền truy cập micrô trên thiết bị.',
            'Phiên khách (Guest Session) đã được hệ thống cấp token xác thực còn hiệu lực.',
            'Thiết bị kết nối Internet ổn định và mở thành công kênh WebSocket tới máy chủ (/ws/realtime).',
            'Chiều dịch hợp lệ đã được xác định trước khi bắt đầu thu âm.'
        ],
        'post_cond': [
            'Văn bản nhận dạng (STT) và văn bản dịch được hiển thị đồng bộ trên thẻ dịch.',
            'Luồng âm thanh tổng hợp (TTS) được truyền về theo từng đoạn và tự động phát lại.',
            'Mỗi lượt dịch được cấp turn_id độc lập để chống nhầm lẫn kết quả bất đồng bộ.',
            'Bản ghi lịch sử được lưu vào cơ sở dữ liệu cục bộ Hive nếu người dùng bật tính năng lưu lịch sử.'
        ],
        'main_flow': [
            'Ứng dụng kiểm tra và bảo đảm token phiên khách hợp lệ.',
            'Ứng dụng thiết lập kết nối WebSocket tới /ws/realtime, gửi frame cấu hình khởi tạo (PCM 16kHz mono 16-bit) và gửi thông điệp start_turn.',
            'Người dùng nói vào micrô; ứng dụng thu âm và truyền liên tục các đoạn âm thanh nhị phân (binary audio chunks).',
            'Tầng Realtime tiếp nhận, bộ WebRtcVadStream phát hiện tiếng nói và đưa audio vào hàng đợi STT (STT Queue).',
            'STT Worker tiếp nhận audio, áp dụng lọc nhiễu DeepFilterNet (khi kích hoạt) và gọi mô hình Whisper/Faster-Whisper để chuyển đổi giọng nói thành văn bản.',
            'Kết quả nhận dạng được chuyển sang Translation Queue. Translation Worker kiểm tra Translation Memory và Cache; nếu không có kết quả khớp, hệ thống gọi mô hình NLLB-200 để dịch.',
            'Văn bản dịch được chuyển tiếp vào TTS Queue. TTS Worker sử dụng mô hình MMS VITS để tổng hợp giọng nói đích và truyền các audio chunks về ứng dụng.',
            'Máy chủ phát thông điệp turn_complete. Ứng dụng hoàn tất hiển thị và phát âm thanh cho người dùng.'
        ],
        'alt_flow': [
            'Không phát hiện được giọng nói (VAD không nhận diện speech): Hệ thống bỏ qua, không đưa vào hàng đợi AI và thông báo người dùng ghi âm lại.',
            'Hệ thống đang bận hoặc hàng đợi STT/Translation đầy: Máy chủ gửi thông điệp status: busy, ứng dụng hiển thị trạng thái hệ thống bận và cho phép người dùng thử lại.',
            'Người dùng chủ động nhấn hủy lượt (cancel_turn): Hệ thống hủy tác vụ trong hàng đợi, SessionActor đánh dấu turn_id vào cancelled_turns và bỏ qua các kết quả tính toán trễ.',
            'Người dùng thay đổi cấu hình chiều ngôn ngữ: Cấu hình mới được ghi nhận vào pending_config và áp dụng cho lượt kế tiếp.'
        ],
        'exceptions': [
            'Mất kết nối mạng hoặc kết nối WebSocket bị ngắt đột ngột: Ứng dụng hiển thị thông báo lỗi kết nối và tự động thử kết nối lại.',
            'Mô hình AI suy luận bị lỗi hoặc quá thời gian xử lý: Máy chủ trả về lỗi kèm error_stage và mã turn_id, ứng dụng thông báo lỗi cụ thể cho người dùng.',
            'Phiên khách hết hạn trong quá trình làm việc: Hệ thống từ chối kết nối (code 4401/4403), ứng dụng tự động yêu cầu cấp phiên mới.',
            'Định dạng âm thanh đầu vào không đúng chuẩn PCM 16kHz mono: Hệ thống trả mã lỗi và từ chối xử lý.'
        ],
        'priority': 'Cao (Chức năng cốt lõi của hệ thống)',
        'business_rules': [
            'Hệ thống chỉ hỗ trợ hai chiều dịch Việt <-> Anh trong phạm vi nghiên cứu của đồ án.',
            'Định dạng âm thanh truyền qua WebSocket bắt buộc là PCM mono, tần số lấy mẫu 16 kHz, độ phân giải 16-bit.',
            'Kết quả trả về của một lượt đã bị hủy tuyệt đối không được phát ra loa hoặc ghi đè sang lượt mới.',
            'Dịch vụ xử lý giọng nói thời gian thực chỉ phục vụ người dùng có token phiên khách hoặc JWT hợp lệ mang đủ phạm vi translate và audio.'
        ],
        'assumptions': [
            'Thiết bị người dùng có micrô và loa ngoài hoạt động tốt.',
            'Hạ tầng máy chủ đảm bảo tài nguyên suy luận AI với GPU hoặc CPU đủ cấu hình.'
        ]
    })
    
    add_caption(doc, "Bảng 3.2. Đặc tả UC1.2 - Hội thoại song ngữ hai chiều")
    render_use_case_table(doc, {
        'id_name': 'UC1.2 - Hội thoại song ngữ hai chiều',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép hai người nói tiếng Việt và tiếng Anh thực hiện các lượt hội thoại luân phiên trực tiếp trên màn hình Chat. Mỗi lượt giữ cố định người nói, chiều dịch và turn_id riêng biệt.',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'Máy chủ xử lý (FastAPI Backend) và chuỗi xử lý AI Pipeline',
        'trigger': 'Người dùng mở màn hình Hội thoại (Chat Screen) và một trong hai người nhấn giữ micrô tương ứng.',
        'pre_cond': [
            'Các điều kiện tiên quyết của UC1.1 đã được thỏa mãn.',
            'Giao diện màn hình Hội thoại đã được khởi tạo với thanh micrô kép DualMicBar.',
            'Hệ thống xác định được đối tượng đang phát biểu (me hoặc partner).'
        ],
        'post_cond': [
            'Các lượt hội thoại được xếp tuần tự vào danh sách tin nhắn ChatBubble.',
            'Mỗi lượt hiển thị rõ văn bản nguồn, văn bản dịch và nút nghe lại âm thanh.',
            'Khi đổi người nói, lượt tiếp theo tự động đảo ngược chiều ngôn ngữ.'
        ],
        'main_flow': [
            'Người A (nói tiếng Việt) nhấn giữ micrô "Tôi (VI)".',
            'Ứng dụng tạo lượt mới, cố định speaker="me", source_lang="vi", target_lang="eng_Latn" và truyền start_turn.',
            'Người A nói, âm thanh gửi tới máy chủ; hệ thống thực hiện VAD -> Whisper -> NLLB -> MMS VITS.',
            'Máy chủ trả về kết quả dịch; ứng dụng hiển thị bong bóng chat của Người A và phát âm thanh tiếng Anh để Người B nghe.',
            'Người B (nói tiếng Anh) nhấn giữ micrô "Đối tác (EN)".',
            'Ứng dụng tạo lượt mới, cố định speaker="partner", chiều dịch Anh -> Việt và truyền start_turn.',
            'Máy chủ xử lý và trả kết quả bản dịch tiếng Việt cho lượt của Người B.',
            'Ứng dụng hiển thị bong bóng chat của Người B và phát âm thanh tiếng Việt để Người A nghe. Quá trình tiếp diễn luân phiên.'
        ],
        'alt_flow': [
            'Người dùng chuyển màn hình khi đang thu âm: Hệ thống tự động ngắt thu âm và giải phóng micrô.',
            'Một lượt bị hủy giữa chừng: Hệ thống chỉ hủy lượt đó, phiên kết nối WebSocket vẫn duy trì cho lượt kế tiếp.',
            'Người dùng đổi cấu hình trước khi bắt đầu lượt: Cấu hình mới áp dụng cho lượt phát biểu ngay sau đó.'
        ],
        'exceptions': [
            'Thao tác hai micrô cạnh tranh cùng lúc: Ứng dụng áp dụng bộ kiểm soát mic độc quyền (MicStateMachine), chỉ cho phép một micrô hoạt động tại một thời điểm.',
            'Kết quả đến muộn sau khi người đối thoại đã bấm nói lượt mới: Kết quả cũ được ghi nhận đúng lượt tương ứng nhưng không chiếm quyền phát âm thanh của lượt mới.',
            'Máy chủ quá tải: Hiển thị thông báo trạng thái bận và giữ nguyên lịch sử hội thoại hiện có.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Mỗi lượt hội thoại bắt buộc phải có turn_id duy nhất và gán đúng vai trò speaker ("me" hoặc "partner").',
            'Vai trò người nói và chiều dịch không được phép thay đổi trong lúc một lượt đang được xử lý.',
            'Ứng dụng phải khóa micrô còn lại khi một micrô đang trong trạng thái ghi âm.'
        ],
        'assumptions': [
            'Hai người dùng giao tiếp trực tiếp tại cùng một không gian vật lý chia sẻ chung một thiết bị di động.'
        ]
    })
    
    add_caption(doc, "Bảng 3.3. Đặc tả UC1.3 - Tương tác với kết quả dịch")
    render_use_case_table(doc, {
        'id_name': 'UC1.3 - Tương tác với kết quả dịch',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Sau khi lượt dịch hoàn tất, người dùng có thể phát lại âm thanh, sao chép bản dịch, lưu bản dịch vào mục yêu thích hoặc gắn cờ (flag) kết quả nghi ngờ sai để đưa vào hàng đợi kiểm soát chất lượng (QA).',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'Bộ lưu trữ cục bộ (Hive Box) và Phân hệ QA trên Backend',
        'trigger': 'Một bản dịch hoàn chỉnh đang được hiển thị trên thẻ dịch của Trang chủ.',
        'pre_cond': [
            'Lượt dịch đã hoàn tất và có bản dịch hiển thị trên giao diện.',
            'Để phát lại âm thanh, ứng dụng đã nhận được dữ liệu âm thanh hoặc file âm thanh khả dụng.',
            'Để gắn cờ bản dịch, phiên khách phải còn hiệu lực kết nối tới Backend.'
        ],
        'post_cond': [
            'Thao tác tương ứng được hoàn thành (phát âm thanh, sao chép vào clipboard, lưu trữ hoặc gắn cờ).',
            'Nếu gắn cờ thành công, bản ghi dịch xuất hiện trong hàng đợi QA của Web Admin kèm trạng thái is_flagged=True.'
        ],
        'main_flow': [
            'Người dùng nhấn vào một trong các nút thao tác trên thẻ kết quả dịch.',
            'Nếu chọn Phát lại: AudioPlayerService phát lại âm thanh tổng hợp theo tốc độ cấu hình hiện tại.',
            'Nếu chọn Sao chép: Hệ thống sao chép chuỗi văn bản dịch vào bộ nhớ tạm (Clipboard) của hệ điều hành và hiển thị thông báo "Đã sao chép".',
            'Nếu chọn Lưu yêu thích: Bản ghi được cập nhật thuộc tính isFavorite=true trong cơ sở dữ liệu Hive.',
            'Nếu chọn Gắn cờ báo sai: Ứng dụng gửi request POST /api/flag-translation kèm văn bản nhận dạng, bản dịch, cặp ngôn ngữ, model_source và audio_token (nếu có).',
            'Backend tiếp nhận, đánh dấu is_flagged=True vào bảng translation_logs và lưu trữ audio asset tương ứng nếu người dùng đồng ý.'
        ],
        'alt_flow': [
            'Chức năng lưu lịch sử đang tắt: Ứng dụng hiển thị thông báo hỏi người dùng có muốn bật tính năng lưu lịch sử để lưu bản dịch không.',
            'Bản dịch đã được gắn cờ trước đó: Hệ thống thông báo bản dịch này đã được ghi nhận vào hàng đợi kiểm tra.'
        ],
        'exceptions': [
            'File âm thanh tổng hợp bị lỗi hoặc không tải được: Ứng dụng hiển thị thông báo "Không thể phát âm thanh".',
            'Yêu cầu gắn cờ thất bại do mất mạng: Hệ thống hiển thị thông báo "Lỗi gửi phản hồi, vui lòng thử lại sau".'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Chỉ cho phép gắn cờ khi bản dịch đã có kết quả hoàn chỉnh.',
            'Dữ liệu gắn cờ chỉ được chuyển vào hàng đợi QA, tuyệt đối không được tự động đưa thẳng vào tập huấn luyện mô hình.',
            'Dữ liệu lịch sử cục bộ tuân thủ chính sách bảo vệ quyền riêng tư của người dùng.'
        ]
    })
    
    # 3.1.2 Nhóm UC2
    add_heading_3(doc, "3.1.2. Nhóm UC2 - Lịch sử và cấu hình ứng dụng")
    
    add_caption(doc, "Bảng 3.4. Đặc tả UC2.1 - Quản lý lịch sử dịch")
    render_use_case_table(doc, {
        'id_name': 'UC2.1 - Quản lý lịch sử dịch',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng xem lại danh sách các bản dịch đã thực hiện trên thiết bị di động, xem chi tiết từng lượt dịch, lọc theo thời gian và xóa từng bản ghi khi cần thiết.',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'Bộ lưu trữ cục bộ trên thiết bị (Hive Local Storage)',
        'trigger': 'Người dùng mở mục Lịch sử (History) từ thanh điều hướng ứng dụng.',
        'pre_cond': [
            'Ứng dụng đã khởi tạo thành công Hive Storage Box.',
            'Chức năng lưu lịch sử đã được bật và người dùng đã thực hiện dịch thuật trước đó.'
        ],
        'post_cond': [
            'Danh sách lịch sử được tải và sắp xếp theo thứ tự thời gian giảm dần.',
            'Bản ghi bị xóa sẽ được loại bỏ vĩnh viễn khỏi bộ nhớ máy người dùng.',
            'Dữ liệu xem lịch sử không bị gửi về máy chủ nhằm đảm bảo quyền riêng tư.'
        ],
        'main_flow': [
            'Người dùng nhấn vào biểu tượng Lịch sử trên thanh điều hướng.',
            'HistoryController kích hoạt HistoryStorageService để đọc dữ liệu từ Hive Box.',
            'Danh sách các bản dịch hiển thị dưới dạng thẻ (HistoryCard) gồm: văn bản gốc, văn bản dịch, chiều ngôn ngữ, thời gian và biểu tượng yêu thích.',
            'Người dùng có thể cuộn để xem danh sách hoặc nhấn vào một thẻ để mở rộng nội dung chi tiết.',
            'Người dùng vuốt hoặc nhấn biểu tượng thùng rác để xóa một bản ghi; danh sách tự động cập nhật ngay lập tức.'
        ],
        'alt_flow': [
            'Bộ nhớ chưa có bản ghi nào: Hệ thống hiển thị giao diện thông báo trạng thái "Chưa có lịch sử dịch".',
            'Chức năng lưu lịch sử đang bị tắt: Hiển thị thông báo tính năng lưu lịch sử đang tắt kèm nút kích hoạt.'
        ],
        'exceptions': [
            'Lỗi đọc ghi bộ nhớ thiết bị: Ứng dụng thông báo "Không thể truy xuất lịch sử" và giữ nguyên trạng thái an toàn gần nhất.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Dữ liệu lịch sử người dùng cuối hoàn toàn được lưu cục bộ trên thiết bị (Local-first privacy).',
            'Việc lưu lịch sử chỉ được thực hiện khi người dùng đã chủ động xác nhận đồng ý.',
            'Thời hạn lưu trữ lịch sử được tự động dọn dẹp theo cấu hình tại Cài đặt ứng dụng.'
        ]
    })
    
    add_caption(doc, "Bảng 3.5. Đặc tả UC2.2 - Quản lý bản dịch yêu thích")
    render_use_case_table(doc, {
        'id_name': 'UC2.2 - Quản lý bản dịch yêu thích',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng đánh dấu hoặc bỏ đánh dấu một bản ghi dịch là yêu thích để nhanh chóng tra cứu lại các câu đàm thoại thông dụng.',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'Bộ lưu trữ cục bộ trên thiết bị (Hive Local Storage)',
        'trigger': 'Người dùng nhấn vào biểu tượng ngôi sao/trái tim yêu thích trên thẻ dịch.',
        'pre_cond': [
            'Bản ghi dịch đã tồn tại trong bộ nhớ lịch sử cục bộ.'
        ],
        'post_cond': [
            'Thuộc tính isFavorite của bản ghi được đảo trạng thái và lưu bền vững.',
            'Tab danh sách bản dịch yêu thích được cập nhật tương ứng.'
        ],
        'main_flow': [
            'Người dùng chọn một bản ghi dịch trên Trang chủ hoặc trong Màn hình Lịch sử.',
            'Người dùng nhấn vào biểu tượng Yêu thích.',
            'HistoryController cập nhật trường isFavorite trong Hive Box tương ứng với bản ghi đó.',
            'Giao diện thay đổi trạng thái hiển thị biểu tượng (tô màu biểu tượng).'
        ],
        'alt_flow': [
            'Người dùng nhấn thay đổi trạng thái nhiều lần liên tiếp: Lần thao tác cuối cùng được áp dụng và lưu trữ.'
        ],
        'exceptions': [
            'Bản ghi vừa bị xóa trước khi bấm yêu thích: Hệ thống thông báo lỗi bản ghi không tồn tại.'
        ],
        'priority': 'Trung bình',
        'business_rules': [
            'Trạng thái yêu thích chỉ là thuộc tính mở rộng của bản ghi lịch sử cục bộ, không làm thay đổi nội dung dịch gốc.'
        ]
    })
    
    add_caption(doc, "Bảng 3.6. Đặc tả UC2.3 - Cấu hình ứng dụng")
    render_use_case_table(doc, {
        'id_name': 'UC2.3 - Cấu hình ứng dụng',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng thiết lập các tùy chọn cá nhân hóa trải nghiệm: tốc độ phát giọng nói, ngôn ngữ mặc định, bật/tắt lưu lịch sử cục bộ, thời hạn lưu giữ lịch sử, xóa toàn bộ lịch sử và đăng xuất phiên khách.',
        'primary_actor': 'Người dùng ứng dụng di động (ACT01)',
        'secondary_actor': 'SettingsController và AuthSessionService',
        'trigger': 'Người dùng mở màn hình Cài đặt (Settings Screen) từ menu điều hướng.',
        'pre_cond': [
            'Ứng dụng di động đang trong trạng thái hoạt động.'
        ],
        'post_cond': [
            'Các tham số cài đặt mới được lưu vào bộ nhớ cục bộ và có hiệu lực ngay lập tức.',
            'Nếu đăng xuất, phiên khách cục bộ bị hủy và ứng dụng yêu cầu cấp phiên mới.'
        ],
        'main_flow': [
            'Người dùng truy cập màn hình Cài đặt.',
            'Người dùng điều chỉnh tốc độ giọng nói (Chậm 0.75x, Bình thường 1.0x, Nhanh 1.25x).',
            'Người dùng chọn ngôn ngữ mặc định khi khởi động ứng dụng (Việt hoặc Anh).',
            'Người dùng bật hoặc tắt tùy chọn lưu lịch sử dịch cục bộ.',
            'Người dùng thiết lập thời hạn lưu giữ lịch sử (1, 3, 7, 14 hoặc 30 ngày).',
            'Người dùng có thể chọn "Xóa toàn bộ lịch sử", hệ thống hiển thị hộp thoại xác nhận trước khi xóa sạch dữ liệu trong Hive Box.',
            'Người dùng có thể chọn "Đăng xuất phiên khách" để làm mới danh tính kết nối.'
        ],
        'alt_flow': [
            'Các tùy chọn mở rộng đang trong quá trình phát triển (như đổi giọng nam/nữ, AI Engine mode): Ứng dụng hiển thị nhãn "Chưa khả dụng trong phiên bản hiện tại" để tránh gây hiểu nhầm.'
        ],
        'exceptions': [
            'Lỗi ghi bộ nhớ cấu hình: Ứng dụng hiển thị thông báo lỗi lưu cài đặt và khôi phục giá trị mặc định.'
        ],
        'priority': 'Trung bình',
        'business_rules': [
            'Tốc độ phát âm chỉ áp dụng cho bộ phát âm thanh (AudioPlayerService) phía client, không ảnh hưởng mô hình TTS trên máy chủ.',
            'Việc bật lưu lịch sử bắt buộc phải có bước xác nhận đồng ý của người dùng.'
        ]
    })
    
    print("UC1 and UC2 rendered.")

def render_section_3_1_part2(doc):
    # 3.1.3 Nhóm UC3
    add_heading_3(doc, "3.1.3. Nhóm UC3 - Xác thực và hồ sơ quản trị")
    
    add_caption(doc, "Bảng 3.7. Đặc tả UC3.1 - Đăng nhập hệ thống quản trị")
    render_use_case_table(doc, {
        'id_name': 'UC3.1 - Đăng nhập hệ thống quản trị',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Nhân viên nghiệp vụ, Quản trị viên và Quản trị cấp cao đăng nhập vào Web Admin bằng tên đăng nhập và mật khẩu. Đối với tài khoản đặc quyền, hệ thống bắt buộc xác thực mã OTP thời gian thực (TOTP MFA) trước khi cấp phiên làm việc.',
        'primary_actor': 'Nhân viên nghiệp vụ (ACT02) / Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ xác thực Backend FastAPI, Thư viện mật mã BCrypt / PyOTP, Cơ sở dữ liệu',
        'trigger': 'Người dùng truy cập trang Đăng nhập Web Admin (/admin/login) và gửi biểu mẫu xác thực.',
        'pre_cond': [
            'Tài khoản quản trị đã tồn tại trong cơ sở dữ liệu và ở trạng thái is_active=True.',
            'Máy chủ FastAPI và cơ sở dữ liệu đang vận hành bình thường.',
            'Nếu tài khoản kích hoạt MFA, người dùng đã cài đặt ứng dụng Authenticator để lấy mã TOTP.'
        ],
        'post_cond': [
            'Nếu đăng nhập thành công: Hệ thống cấp cặp Access Token JWT và Refresh Token HttpOnly Cookie, lưu AuthSession và điều hướng giao diện theo vai trò.',
            'Nếu đăng nhập thất bại: Hệ thống ghi nhật ký cảnh báo và từ chối cấp quyền truy cập.'
        ],
        'main_flow': [
            'Người dùng nhập tên đăng nhập và mật khẩu trên giao diện Web Admin.',
            'FastAPI kiểm tra giới hạn tần suất yêu cầu (Rate Limiter) để ngăn ngừa tấn công brute-force.',
            'Hệ thống truy vấn người dùng trong bảng users; xác thực mật khẩu bằng hàm băm BCrypt.',
            'Hệ thống kiểm tra trạng thái tài khoản is_active và chính sách xác thực nhiều yếu tố (MFA).',
            'Nếu tài khoản yêu cầu MFA và chưa cung cấp mã: Máy chủ trả về mã trạng thái MFA Challenge yêu cầu nhập mã TOTP 6 chữ số.',
            'Người dùng nhập mã TOTP; hệ thống xác minh mã bằng thuật toán RFC 6238 kèm chống phát lại (anti-replay counter).',
            'Hệ thống tạo phiên AuthSession, phát hành JWT Access Token và thiết lập Refresh Cookie an toàn.',
            'Giao diện Web Admin lưu thông tin phiên và điều hướng người dùng tới Bảng điều khiển tương ứng với vai trò được cấp.'
        ],
        'alt_flow': [
            'Sai tên đăng nhập hoặc mật khẩu: Hệ thống áp dụng dummy hash để chống tấn công phân tích thời gian (timing attack) và trả về thông báo lỗi chung "Thông tin đăng nhập không hợp lệ".',
            'Tài khoản bị vô hiệu hóa (is_active=False): Hệ thống từ chối đăng nhập và thông báo tài khoản đã bị khóa.',
            'Mã TOTP không chính xác hoặc đã hết hạn: Hệ thống từ chối cấp phiên và yêu cầu nhập lại mã mới.'
        ],
        'exceptions': [
            'Cơ sở dữ liệu tạm thời không khả dụng: Trả về lỗi 503 Service Unavailable.',
            'Người dùng gửi quá số lần đăng nhập cho phép: Hệ thống trả mã lỗi 429 Too Many Requests kèm thời gian khóa tạm thời.'
        ],
        'priority': 'Cao (Bảo mật cốt lõi của phân hệ quản trị)',
        'business_rules': [
            'Mật khẩu tuyệt đối không được lưu dưới dạng văn bản rõ, bắt buộc băm bằng BCrypt với chi phí tính toán (salt rounds) chuẩn.',
            'Quyền truy cập cuối cùng phải được kiểm soát bằng RBAC tại tầng API Backend, không chỉ phụ thuộc vào việc ẩn nút trên giao diện.',
            'Phiên đăng nhập có thời hạn cụ thể và có thể bị Quản trị cấp cao thu hồi tức thời.'
        ]
    })
    
    add_caption(doc, "Bảng 3.8. Đặc tả UC3.2 - Xem hồ sơ và đăng xuất")
    render_use_case_table(doc, {
        'id_name': 'UC3.2 - Xem hồ sơ và đăng xuất',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng đã đăng nhập xem thông tin tài khoản cá nhân, vai trò, mã định danh public_id, trạng thái MFA và thực hiện đăng xuất an toàn khỏi hệ thống.',
        'primary_actor': 'Người dùng Web Admin (ACT02, ACT03, ACT04)',
        'secondary_actor': 'AuthService của Backend và Kho lưu trữ AuthSession',
        'trigger': 'Người dùng nhấn vào mục Hồ sơ cá nhân hoặc chọn nút Đăng xuất trên thanh điều hướng.',
        'pre_cond': [
            'Người dùng đã đăng nhập và sở hữu Access Token hợp lệ.'
        ],
        'post_cond': [
            'Thông tin hồ sơ hiển thị đầy đủ và chính xác.',
            'Khi đăng xuất, phiên AuthSession bị đánh dấu revoked_at, cookie refresh bị xóa và token bị vô hiệu hóa.'
        ],
        'main_flow': [
            'Web Admin gửi request GET /admin/me kèm Bearer Token.',
            'Backend giải mã token, kiểm tra tính hợp lệ và trả về thông tin: username, role, public_id, created_at, mfa_enabled.',
            'Giao diện hiển thị chi tiết hồ sơ người dùng.',
            'Khi người dùng bấm "Đăng xuất": Giao diện gửi request POST /api/auth/logout.',
            'Backend cập nhật thời điểm revoked_at cho AuthSession và xóa Refresh Cookie.',
            'Web Admin xóa sạch token trong bộ nhớ trình duyệt và chuyển hướng về trang Đăng nhập.'
        ],
        'alt_flow': [
            'Mạng bị ngắt khi bấm đăng xuất: Giao diện vẫn chủ động xóa token cục bộ để đảm bảo an toàn cho máy trạm.'
        ],
        'exceptions': [
            'Token đã hết hạn trước khi đăng xuất: Hệ thống tự động chuyển về trang Đăng nhập.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Không bao giờ trả về password_hash, mfa_secret hoặc các thông tin nhạy cảm trong response hồ sơ.',
            'Hệ thống phải hỗ trợ thu hồi phiên đăng nhập tức thời trên máy chủ.'
        ]
    })
    
    # 3.1.4 Nhóm UC4
    add_heading_3(doc, "3.1.4. Nhóm UC4 - Từ điển và đánh giá chất lượng")
    
    add_caption(doc, "Bảng 3.9. Đặc tả UC4.1 - Tra cứu và xuất Từ điển")
    render_use_case_table(doc, {
        'id_name': 'UC4.1 - Tra cứu và xuất Từ điển',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng Web Admin tra cứu các cặp câu dịch chuẩn trong Bộ nhớ dịch (Translation Memory), lọc theo cặp ngôn ngữ, tìm kiếm theo từ khóa và xuất dữ liệu ra file CSV phục vụ kiểm toán.',
        'primary_actor': 'Nhân viên nghiệp vụ (ACT02) / Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Translation Memory của Backend',
        'trigger': 'Người dùng truy cập trang Từ điển trên Web Admin.',
        'pre_cond': [
            'Người dùng đã đăng nhập và có quyền đọc dữ liệu từ điển.'
        ],
        'post_cond': [
            'Danh sách cặp dịch hiển thị theo phân trang và bộ lọc.',
            'File CSV được tải về chứa đúng các bản ghi khớp với điều kiện tra cứu.'
        ],
        'main_flow': [
            'Web Admin gửi yêu cầu lấy danh sách cặp dịch kèm tham số trang, từ khóa và cặp ngôn ngữ.',
            'Backend kiểm tra quyền hạn, thực hiện truy vấn bảng translation_memory_entries.',
            'Hệ thống trả về danh sách các cặp câu kèm thông tin: văn bản gốc, văn bản chuẩn hóa, bản dịch, trạng thái phê duyệt và thời gian.',
            'Người dùng xem danh sách, lọc cặp ngôn ngữ (Việt -> Anh hoặc Anh -> Việt).',
            'Người dùng nhấn nút "Xuất CSV", hệ thống tạo luồng dữ liệu file CSV chuẩn UTF-8 và tải về máy.'
        ],
        'alt_flow': [
            'Không có kết quả khớp với từ khóa: Giao diện hiển thị trạng thái "Không tìm thấy cặp từ điển phù hợp".'
        ],
        'exceptions': [
            'Lỗi truy vấn cơ sở dữ liệu: Hệ thống thông báo lỗi và yêu cầu tải lại trang.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Nhân viên nghiệp vụ có quyền xem và xuất CSV nhưng không có quyền thêm, sửa, xóa cặp từ điển.',
            'Dữ liệu văn bản nguồn khi lưu trong TM phải qua bước chuẩn hóa chuỗi (normalization version).'
        ]
    })
    
    add_caption(doc, "Bảng 3.10. Đặc tả UC4.2 - Cập nhật Từ điển")
    render_use_case_table(doc, {
        'id_name': 'UC4.2 - Cập nhật Từ điển',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị cấp cao thêm từng cặp dịch mới, xóa cặp dịch cũ hoặc nhập hàng loạt cặp dịch từ file CSV/XLSX vào Translation Memory.',
        'primary_actor': 'Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Translation Memory và Bộ đệm Translation Cache',
        'trigger': 'Quản trị cấp cao chọn thêm cặp dịch, xóa mục hoặc tải file dữ liệu lên trang Từ điển.',
        'pre_cond': [
            'Đã đăng nhập bằng tài khoản Quản trị cấp cao (vai trò superadmin).',
            'Dữ liệu cặp câu nguồn - đích hợp lệ và ngôn ngữ nguồn khác ngôn ngữ đích.'
        ],
        'post_cond': [
            'Cặp dịch mới được lưu vào translation_memory_entries ở trạng thái phê duyệt (is_approved=True).',
            'Bộ nhớ cache dịch thuật liên quan tự động bị xóa (invalidation) để cập nhật kết quả mới.'
        ],
        'main_flow': [
            'Quản trị cấp cao chọn phương thức cập nhật: Thêm thủ công hoặc Nhập file CSV/XLSX.',
            'Nếu thêm thủ công: Nhập văn bản nguồn, văn bản dịch và chọn cặp ngôn ngữ.',
            'Nếu nhập file: Chọn file bảng tính; Backend sử dụng defusedxml/openpyxl an toàn để phân tích file.',
            'Backend kiểm tra cú pháp, loại bỏ ký tự độc hại, chuẩn hóa văn bản nguồn.',
            'Lưu các bản ghi vào bảng translation_memory_entries với owner_id="global:approved".',
            'Hệ thống ghi nhận sự kiện vào AuditLog và làm mới giao diện Từ điển.'
        ],
        'alt_flow': [
            'Cặp câu đã tồn tại trong từ điển: Hệ thống cập nhật bản dịch mới thay thế hoặc giữ nguyên tùy theo cấu hình xung đột.'
        ],
        'exceptions': [
            'File tải lên sai định dạng hoặc vượt quá kích thước cho phép (5MB): Hệ thống báo lỗi và từ chối xử lý.',
            'Quyền hạn người dùng không đủ: Trả mã lỗi 403 Forbidden.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Chỉ có vai trò Superadmin mới có quyền ghi/sửa/xóa Từ điển dùng chung của hệ thống.',
            'Mỗi thay đổi từ điển phải lập tức xóa bộ đệm (cache invalidation) để luồng dịch AI nhận diện ngay.'
        ]
    })
    
    add_caption(doc, "Bảng 3.11. Đặc tả UC4.3 - Đánh giá và hiệu chỉnh chất lượng bản dịch")
    render_use_case_table(doc, {
        'id_name': 'UC4.3 - Đánh giá và hiệu chỉnh chất lượng bản dịch',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Nhân viên nghiệp vụ và Quản trị viên duyệt danh sách các lượt dịch trong hàng đợi QA (đặc biệt là các bản ghi bị người dùng gắn cờ), kiểm tra văn bản nhận dạng STT và bản dịch, chấm điểm Adequacy/Fluency, phân loại lỗi và hiệu chỉnh kết quả dịch.',
        'primary_actor': 'Nhân viên nghiệp vụ (ACT02) / Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Kho lưu trữ QualityReview, TranslationLog và Audio Storage',
        'trigger': 'Người đánh giá mở trang Kiểm soát chất lượng (QA) trên Web Admin.',
        'pre_cond': [
            'Người dùng đã đăng nhập và sở hữu quyền QA Reviewer.',
            'Có các bản ghi dịch trong hàng đợi QA cần được đánh giá.'
        ],
        'post_cond': [
            'Bản ghi QualityReview được tạo mới hoặc cập nhật.',
            'Bản ghi translation_logs được đánh dấu is_reviewed=True.',
            'Văn bản gốc nhận dạng và bản dịch gốc vẫn được lưu giữ nguyên trạng để phục vụ kiểm toán đối chiếu.'
        ],
        'main_flow': [
            'Web Admin tải danh sách các bản ghi cần QA (ưu tiên các bản ghi có is_flagged=True).',
            'Người đánh giá chọn một bản ghi cụ thể để xem chi tiết.',
            'Hệ thống hiển thị: câu nhận dạng STT gốc, câu dịch NLLB gốc, độ trễ và file âm thanh nguồn (nếu có).',
            'Người đánh giá nghe âm thanh, đối chiếu và nhập văn bản nhận dạng chuẩn (corrected_source_text) hoặc bản dịch chuẩn (corrected_text).',
            'Người đánh giá chấm điểm Độ đầy đủ ý nghĩa (Adequacy: 1-5), Độ trôi chảy (Fluency: 1-5), chọn nhóm lỗi (sai thuật ngữ, ngữ pháp, thiếu từ, biến dạng ý nghĩa) và đánh dấu lỗi nghiêm trọng nếu có.',
            'Chọn lĩnh vực nội dung (domain: general, medical, travel, technical...).',
            'Nhấn nút "Lưu đánh giá"; Backend ghi nhận vào bảng quality_reviews và đánh dấu is_reviewed=True trong translation_logs.'
        ],
        'alt_flow': [
            'Bản dịch gốc hoàn toàn chính xác: Người đánh giá chọn trạng thái "Bản dịch đúng", không nhập câu sửa và chấm điểm tối đa.'
        ],
        'exceptions': [
            'Bản ghi không tồn tại hoặc đã bị người khác xử lý: Hệ thống thông báo và cập nhật lại hàng đợi.'
        ],
        'priority': 'Rất cao (Trực tiếp xây dựng nguồn dữ liệu cải tiến mô hình AI)',
        'business_rules': [
            'Nội dung gốc do AI sinh ra (raw output) tuyệt đối không được ghi đè, bắt buộc bảo toàn để so sánh.',
            'Nhân viên nghiệp vụ chỉ được phân quyền xử lý trong hàng đợi QA, không được xem toàn bộ dữ liệu nhạy cảm khác của hệ thống.'
        ]
    })
    
    add_caption(doc, "Bảng 3.12. Đặc tả UC4.4 - Chuẩn bị dữ liệu kiểm soát chất lượng (QA) cho huấn luyện")
    render_use_case_table(doc, {
        'id_name': 'UC4.4 - Chuẩn bị dữ liệu kiểm soát chất lượng (QA) cho huấn luyện',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người đánh giá chất lượng xác định một bản ghi QA có đủ điều kiện làm dữ liệu huấn luyện cho mô hình NLLB hoặc Whisper hay không. Hệ thống đồng thời kiểm tra sự đồng ý của người dùng (Consent), trạng thái làm sạch thông tin nhận dạng cá nhân (PII) và phân bổ tập train/val/test.',
        'primary_actor': 'Nhân viên nghiệp vụ (ACT02) / Quản trị viên (ACT03)',
        'secondary_actor': 'Dịch vụ Training Control và Bảng QualityReview',
        'trigger': 'Trong quá trình hoàn thiện đánh giá QA, người dùng thiết lập mục đích sử dụng dữ liệu cho AI.',
        'pre_cond': [
            'Bản ghi dịch đã hoàn thành bước chấm điểm và hiệu chỉnh QA.',
            'Có thông tin về trạng thái đồng ý sử dụng dữ liệu của người dùng.'
        ],
        'post_cond': [
            'Bản ghi QualityReview cập nhật các cờ use_for_nllb, use_for_whisper, pii_status, whisper_split, nllb_split.',
            'Dữ liệu đủ điều kiện sẵn sàng để Trung tâm huấn luyện gom thành Dataset.'
        ],
        'main_flow': [
            'Người đánh giá kiểm tra trạng thái đồng ý (consent_for_training) của người dùng nguồn.',
            'Kiểm tra và xác nhận trạng thái lọc thông tin định danh cá nhân (pii_status: clean, redacted hoặc rejected).',
            'Nếu dữ liệu văn bản dịch đạt chuẩn: Đánh dấu use_for_nllb=True và chỉ định tập phân bổ (nllb_split: train, validation hoặc test).',
            'Nếu có kèm file âm thanh nguồn chất lượng cao: Đánh dấu use_for_whisper=True và chỉ định tập phân bổ (whisper_split: train, validation hoặc test).',
            'Lưu thông tin vào hệ thống; Trung tâm huấn luyện thống kê số mẫu khả dụng trong báo cáo tổng quan.'
        ],
        'alt_flow': [
            'Bản ghi chứa thông tin cá nhân nhạy cảm chưa thể làm sạch: Đặt pii_status="rejected", hệ thống tự động khóa không cho phép dùng cho huấn luyện.'
        ],
        'exceptions': [
            'Bản ghi đánh dấu dùng cho Whisper nhưng thiếu file âm thanh hợp lệ: Hệ thống từ chối lưu cờ use_for_whisper.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Chỉ các bản ghi có consent_for_training=True và pii_status="clean" mới được phép gom vào Dataset huấn luyện.',
            'Tập validation và test phải được phân tách độc lập, không được phép trùng lặp với tập train.'
        ]
    })
    
    print("UC3 and UC4 rendered.")

def render_section_3_1_part3(doc):
    # 3.1.5 Nhóm UC5
    add_heading_3(doc, "3.1.5. Nhóm UC5 - Giám sát và lịch sử hệ thống")
    
    add_caption(doc, "Bảng 3.13. Đặc tả UC5.1 - Xem Bảng điều khiển và Thống kê")
    render_use_case_table(doc, {
        'id_name': 'UC5.1 - Xem Bảng điều khiển và Thống kê',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép người dùng Web Admin theo dõi các chỉ số tổng quan thời gian thực, lưu lượng dịch thuật, tỷ lệ gắn cờ lỗi, độ trễ xử lý từng công đoạn (Queue, STT, Translation, TTS, End-to-End) và các phân vị P50, P90, P99.',
        'primary_actor': 'Nhân viên nghiệp vụ (ACT02) / Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Telemetry, Bảng pipeline_metrics và translation_logs',
        'trigger': 'Người dùng truy cập trang Dashboard hoặc Analytics trên Web Admin.',
        'pre_cond': [
            'Đã đăng nhập hệ thống và có quyền xem báo cáo thống kê.'
        ],
        'post_cond': [
            'Các số liệu đo lường và biểu đồ chuỗi thời gian được hiển thị đầy đủ, trực quan mà không làm biến đổi dữ liệu nghiệp vụ.'
        ],
        'main_flow': [
            'Web Admin gửi request GET /admin/metrics/dashboard và /admin/metrics/pipeline.',
            'Backend tổng hợp các chỉ số: tổng lượt dịch, tỷ lệ gắn cờ lỗi, độ trễ trung bình, tài nguyên CPU/GPU.',
            'Hệ thống tính toán các phân vị độ trễ P50, P90, P99 của chuỗi suy luận AI dựa trên bảng pipeline_metrics.',
            'Giao diện hiển thị các thẻ số liệu thống kê (KPI Cards) và biểu đồ trực quan biến động theo thời gian.',
            'Người dùng có thể chọn bộ lọc khoảng thời gian (1 giờ, 24 giờ, 7 ngày, 30 ngày) để cập nhật lại số liệu.'
        ],
        'alt_flow': [
            'Chưa có dữ liệu đo kiểm trong khoảng thời gian đã chọn: Hệ thống hiển thị biểu đồ rỗng kèm thông báo thích hợp.'
        ],
        'exceptions': [
            'Dịch vụ đo lường Telemetry tạm thời quá tải: Hệ thống hiển thị số liệu từ snapshot gần nhất và báo trạng thái chậm cập nhật.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Nhân viên nghiệp vụ chỉ được xem báo cáo thống kê tổng hợp, không được xem chi tiết thông tin hệ thống hạ tầng nhạy cảm.',
            'Các chỉ số P50/P90/P99 phải phản ánh chính xác dữ liệu đo thực tế của pipeline.'
        ]
    })
    
    add_caption(doc, "Bảng 3.14. Đặc tả UC5.2 - Tra cứu lịch sử hệ thống")
    render_use_case_table(doc, {
        'id_name': 'UC5.2 - Tra cứu lịch sử hệ thống',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị viên và Quản trị cấp cao tra cứu toàn bộ lịch sử các lượt dịch đã phát sinh trên máy chủ Backend để điều tra vận hành và đối chiếu chất lượng.',
        'primary_actor': 'Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Bảng dữ liệu translation_logs trên máy chủ',
        'trigger': 'Người dùng truy cập trang Lịch sử hệ thống (History) trên Web Admin.',
        'pre_cond': [
            'Đã đăng nhập với vai trò Quản trị viên hoặc Quản trị cấp cao.'
        ],
        'post_cond': [
            'Danh sách nhật ký dịch trên server hiển thị theo điều kiện phân trang, lọc và tìm kiếm.'
        ],
        'main_flow': [
            'Hệ thống xác thực vai trò người dùng (yêu cầu tối thiểu vai trò admin).',
            'Web Admin gửi yêu cầu tải nhật ký dịch từ Backend.',
            'Backend kiểm tra quyền hạn và truy vấn bảng translation_logs.',
            'Hệ thống hiển thị danh sách gồm: mã phiên, câu nguồn, câu dịch, chiều ngôn ngữ, độ trễ, nguồn kết quả (model/TM), trạng thái gắn cờ và thời gian.',
            'Người dùng có thể lọc theo trạng thái gắn cờ, khoảng thời gian hoặc tìm kiếm theo từ khóa.'
        ],
        'alt_flow': [
            'Không có bản ghi nào: Hiển thị bảng trống kèm thông báo.'
        ],
        'exceptions': [
            'Tài khoản Employee cố gắng truy cập trái phép: Hệ thống từ chối với mã lỗi 403 Forbidden.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Lịch sử hệ thống trên Web Admin lưu trữ tập trung trên Backend, hoàn toàn độc lập với lịch sử lưu cục bộ trên điện thoại của người dùng.',
            'Nhân viên nghiệp vụ (Employee) bị nghiêm cấm truy cập toàn bộ nhật ký hệ thống để đảm bảo bảo mật dữ liệu.'
        ]
    })
    
    # 3.1.6 Nhóm UC6
    add_heading_3(doc, "3.1.6. Nhóm UC6 - Quản trị hệ thống")
    
    add_caption(doc, "Bảng 3.15. Đặc tả UC6.1 - Quản lý người dùng")
    render_use_case_table(doc, {
        'id_name': 'UC6.1 - Quản lý người dùng',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị cấp cao xem danh sách tài khoản, tìm kiếm, tạo tài khoản mới, cập nhật vai trò, khóa/mở khóa tài khoản, đặt lại mật khẩu và thu hồi phiên đăng nhập đang hoạt động.',
        'primary_actor': 'Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Security, Bảng users, auth_sessions và audit_logs',
        'trigger': 'Quản trị cấp cao mở trang Quản lý người dùng (Users) trên Web Admin.',
        'pre_cond': [
            'Người dùng đã đăng nhập với vai trò Quản trị cấp cao (superadmin).'
        ],
        'post_cond': [
            'Tài khoản được thêm mới, cập nhật hoặc vô hiệu hóa theo yêu cầu.',
            'Hành động quản trị được ghi lại đầy đủ vào nhật ký kiểm toán (AuditLog).'
        ],
        'main_flow': [
            'Quản trị cấp cao truy cập trang Người dùng, hệ thống hiển thị danh sách tài khoản quản trị.',
            'Để tạo mới: Nhập username, mật khẩu tạm thời (tối thiểu 12 ký tự) và chọn vai trò (Employee hoặc Admin).',
            'Backend băm mật khẩu bằng BCrypt, tạo bản ghi User mới với public_id duy nhất.',
            'Để khóa tài khoản: Quản trị viên chuyển trạng thái is_active=False; Backend lập tức thu hồi toàn bộ AuthSession của tài khoản đó.',
            'Để reset phiên: Nhấn "Reset Sessions", Backend tăng token_version của User khiến mọi token hiện tại bị vô hiệu hóa.',
            'Hệ thống lưu vết hành động vào bảng audit_logs và làm mới danh sách.'
        ],
        'alt_flow': [
            'Tên đăng nhập đã tồn tại: Hệ thống thông báo lỗi trùng lặp và yêu cầu chọn tên khác.',
            'Thao tác xóa tài khoản: Chuyển thành vô hiệu hóa logic (is_active=False) để bảo tồn toàn vẹn dữ liệu kiểm toán.'
        ],
        'exceptions': [
            'Quản trị viên tự khóa chính tài khoản của mình: Hệ thống ngăn chặn hành vi để bảo vệ tính vận hành.'
        ],
        'priority': 'Rất cao',
        'business_rules': [
            'Chỉ duy nhất Quản trị cấp cao (Superadmin) mới có quyền quản lý người dùng.',
            'Tuyệt đối không xóa vật lý bản ghi tài khoản đã phát sinh dữ liệu trong hệ thống.',
            'Mật khẩu mới bắt buộc phải đáp ứng chính sách độ phức tạp và độ dài an toàn.'
        ]
    })
    
    add_caption(doc, "Bảng 3.16. Đặc tả UC6.2 - Quản lý khóa API")
    render_use_case_table(doc, {
        'id_name': 'UC6.2 - Quản lý khóa API',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị cấp cao tạo mới, theo dõi, thu hồi hoặc luân chuyển (rotate) các khóa truy cập API dùng cho việc tích hợp hệ thống bên ngoài, quản lý phạm vi quyền (scopes) và thời hạn hiệu lực.',
        'primary_actor': 'Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Security, Bảng api_keys và audit_logs',
        'trigger': 'Quản trị cấp cao mở trang Quản lý khóa API (API Keys) trên Web Admin.',
        'pre_cond': [
            'Người dùng đã đăng nhập với vai trò Quản trị cấp cao.'
        ],
        'post_cond': [
            'Khóa API mới được phát hành an toàn; mã khóa thô chỉ hiển thị duy nhất một lần.',
            'Khóa bị thu hồi không còn khả năng xác thực vào các dịch vụ Backend.'
        ],
        'main_flow': [
            'Quản trị cấp cao mở trang Khóa API và nhấn "Tạo khóa mới".',
            'Nhập tên mô tả khóa, chọn phạm vi quyền (ví dụ: translate, audio, dictionary:read), và ngày hết hạn.',
            'Backend sinh chuỗi ngẫu nhiên có độ dài bảo mật cao, tạo key_hash (SHA-256) và lưu vào bảng api_keys.',
            'Hệ thống hiển thị khóa API đầy đủ trên màn hình kèm cảnh báo người dùng sao chép ngay vì khóa sẽ không được hiển thị lại.',
            'Khi cần thu hồi: Nhấn "Thu hồi", Backend cập nhật revoked_at và chuyển is_active=False.',
            'Hệ thống ghi nhận sự kiện vào nhật ký kiểm toán AuditLog.'
        ],
        'alt_flow': [
            'Luân chuyển khóa (Rotate Key): Hệ thống sinh khóa mới với cùng scopes và vô hiệu hóa khóa cũ.'
        ],
        'exceptions': [
            'Lỗi tạo khóa hoặc lỗi cơ sở dữ liệu: Hệ thống thông báo lỗi thao tác.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Khóa API thô không bao giờ được lưu trữ trong cơ sở dữ liệu (chỉ lưu trữ giá trị băm key_hash).',
            'Mỗi khóa API bắt buộc phải gắn với danh sách phạm vi quyền (scopes) rõ ràng.'
        ]
    })
    
    add_caption(doc, "Bảng 3.17. Đặc tả UC6.3 - Quản lý cấu hình hệ thống")
    render_use_case_table(doc, {
        'id_name': 'UC6.3 - Quản lý cấu hình hệ thống',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị cấp cao điều chỉnh các tham số vận hành của hệ thống được công bố (như kích thước buffer âm thanh, ngưỡng VAD, timeout, kích hoạt DeepFilterNet, tỷ lệ Canary...).',
        'primary_actor': 'Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Bảng system_settings, PolicySettings và audit_logs',
        'trigger': 'Quản trị cấp cao mở trang Cài đặt hệ thống (Settings) trên Web Admin.',
        'pre_cond': [
            'Đã đăng nhập với vai trò Quản trị cấp cao.'
        ],
        'post_cond': [
            'Các tham số hợp lệ được cập nhật vào cơ sở dữ liệu và có hiệu lực vận hành.',
            'Lịch sử thay đổi được ghi nhận trong AuditLog.'
        ],
        'main_flow': [
            'Web Admin tải danh sách các tham số cấu hình hiện tại từ GET /admin/settings.',
            'Quản trị viên xem xét và thay đổi giá trị của các tham số được phép sửa.',
            'Nhấn nút "Lưu thay đổi", Web Admin gửi request PUT /admin/settings/{key}.',
            'Backend kiểm tra định dạng dữ liệu và phạm vi giá trị hợp lệ của từng tham số.',
            'Backend lưu giá trị mới vào bảng system_settings và ghi nhật ký kiểm toán.',
            'Giao diện thông báo lưu thành công và cập nhật trạng thái hiển thị.'
        ],
        'alt_flow': [
            'Giá trị nhập vào nằm ngoài khoảng cho phép: Hệ thống cảnh báo lỗi validation và giữ nguyên giá trị cũ.'
        ],
        'exceptions': [
            'Lỗi cơ sở dữ liệu khi cập nhật: Thông báo lỗi và không áp dụng cấu hình mới.'
        ],
        'priority': 'Cao',
        'business_rules': [
            'Chỉ những thiết lập được Backend công bố danh mục mới được phép chỉnh sửa qua giao diện.',
            'Các thông số bí mật như JWT Secret, Master Encryption Key không được phép lưu trữ hoặc chỉnh sửa qua bảng cấu hình này.'
        ]
    })
    
    # 3.1.7 Nhóm UC7
    add_heading_3(doc, "3.1.7. Nhóm UC7 - Huấn luyện và quản lý mô hình")
    
    add_caption(doc, "Bảng 3.18. Đặc tả UC7.1 - Quản lý tập dữ liệu huấn luyện")
    render_use_case_table(doc, {
        'id_name': 'UC7.1 - Quản lý tập dữ liệu huấn luyện',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị viên và Quản trị cấp cao xem số lượng mẫu QA đủ điều kiện, xem trước dữ liệu, tạo tập dữ liệu huấn luyện (Dataset snapshot), kiểm tra tính hợp lệ và thực hiện đóng băng (freeze) kèm mã băm SHA-256 trước khi đưa vào huấn luyện mô hình.',
        'primary_actor': 'Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Dịch vụ Training Control, Bảng training_datasets và quality_reviews',
        'trigger': 'Người dùng mở Trung tâm huấn luyện (Training Center) và chọn tạo Dataset mới.',
        'pre_cond': [
            'Đã đăng nhập với vai trò Quản trị viên hoặc Quản trị cấp cao.',
            'Hệ thống đã tích lũy đủ các mẫu QA có consent_for_training=True và pii_status="clean".'
        ],
        'post_cond': [
            'Tập dữ liệu TrainingDataset được tạo thành công với version, số mẫu, đường dẫn tệp JSONL và mã SHA-256.',
            'Dataset ở trạng thái "frozen" là bất biến (immutable), sẵn sàng phục vụ các Training Job.'
        ],
        'main_flow': [
            'Quản trị viên mở Trung tâm huấn luyện, xem thống kê số mẫu QA đủ điều kiện.',
            'Chọn tác vụ (nllb hoặc whisper) và nhấn "Xem trước dữ liệu (Preview)".',
            'Backend truy vấn các bản ghi QA thỏa mãn điều kiện và trả về danh sách mẫu xem trước.',
            'Quản trị viên nhấn "Tạo Dataset từ QA", nhập tên dataset và phiên bản (ví dụ: nllb-v1.0).',
            'Backend tổng hợp các mẫu, tạo file training JSONL, chia tập train/validation/test.',
            'Hệ thống tự động kích hoạt kiểm tra tính hợp lệ (Validation): kiểm tra mẫu trống, mẫu trùng, độ dài token.',
            'Quản trị viên nhấn "Đóng băng (Freeze)", hệ thống tính toán mã băm SHA-256 của file dữ liệu, chuyển trạng thái sang "frozen".'
        ],
        'alt_flow': [
            'Dữ liệu xem trước không đủ số lượng mẫu tối thiểu: Hệ thống cảnh báo và từ chối tạo dataset.',
            'Tải tập dữ liệu lên từ file ngoài: Người dùng tải file JSONL, hệ thống xác thực định dạng trước khi lưu.'
        ],
        'exceptions': [
            'Lỗi ghi tệp trên đĩa lưu trữ hoặc lỗi phân quyền: Hệ thống thông báo lỗi tạo dữ liệu.'
        ],
        'priority': 'Rất cao (Nền tảng kiểm soát quy trình học máy MLOps)',
        'business_rules': [
            'Dataset đã đóng băng (frozen) tuyệt đối không được phép chỉnh sửa hoặc bổ sung mẫu mới.',
            'Mã băm SHA-256 bắt buộc phải được tính toán để đảm bảo tính toàn vẹn và khả năng tái lập thực nghiệm.'
        ]
    })
    
    add_caption(doc, "Bảng 3.19. Đặc tả UC7.2 - Quản lý tiến trình huấn luyện")
    render_use_case_table(doc, {
        'id_name': 'UC7.2 - Quản lý tiến trình huấn luyện',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép Quản trị viên khởi tạo và theo dõi tiến trình huấn luyện tinh chỉnh mô hình bằng phương pháp LoRA (cho NLLB hoặc Whisper), theo dõi thời gian thực các chỉ số loss, epoch, bước huấn luyện, log sự kiện và thu nhận gói mô hình (ModelArtifact) khi hoàn tất.',
        'primary_actor': 'Quản trị viên (ACT03) / Quản trị cấp cao (ACT04)',
        'secondary_actor': 'Standalone Training Worker, Bảng training_jobs và training_job_events',
        'trigger': 'Người dùng chọn Dataset đã đóng băng và nhấn "Bắt đầu huấn luyện".',
        'pre_cond': [
            'Tập dữ liệu lựa chọn đang ở trạng thái "frozen".',
            'Mô hình nền nằm trong danh sách hỗ trợ (ví dụ: facebook/nllb-200-distilled-1.3B hoặc openai/whisper-small).',
            'Tài nguyên GPU phục vụ huấn luyện sẵn sàng và không bị xung đột với luồng inference.'
        ],
        'post_cond': [
            'Tiến trình TrainingJob được ghi nhận và chuyển qua các trạng thái: queued -> running -> completed.',
            'Khi thành công: Sinh ra ModelArtifact đã merge kèm trọng số LoRA và cập nhật cơ sở dữ liệu.'
        ],
        'main_flow': [
            'Quản trị viên chọn tác vụ (nllb hoặc whisper), chọn Dataset đã freeze, chọn mô hình nền và cấu hình LoRA (rank r, alpha, learning rate, epoch).',
            'Nhập phiên bản đầu ra (output_version) và nhấn "Tạo Job".',
            'Backend kiểm tra tính hợp lệ và ghi nhận TrainingJob ở trạng thái "queued".',
            'Tiến trình độc lập Training Worker phát hiện job mới, tiếp nhận công việc, chuyển trạng thái sang "running".',
            'Worker thực hiện nạp dataset, huấn luyện LoRA, định kỳ ghi nhận train_loss, validation_loss và phát sự kiện tiến độ qua Server-Sent Events (SSE).',
            'Quản trị viên theo dõi tiến độ và biểu đồ suy giảm loss trên Web Admin.',
            'Khi huấn luyện xong, worker tự động thực hiện merge trọng số LoRA vào mô hình nền, lưu file model.safetensors, tính mã SHA-256 và tạo bản ghi ModelArtifact ở trạng thái "candidate".'
        ],
        'alt_flow': [
            'Người dùng yêu cầu hủy tiến trình (Cancel Job): Backend đánh dấu cancel_requested_at, worker nhận diện tín hiệu, dừng vòng lặp huấn luyện an toàn và chuyển trạng thái sang "cancelled".'
        ],
        'exceptions': [
            'Lỗi tràn bộ nhớ GPU (CUDA Out Of Memory): Worker bắt ngoại lệ, ghi mã lỗi CUDA_OOM vào TrainingJob và dừng an toàn.',
            'Worker bị mất kết nối: Hệ thống tự động đánh dấu job bị lỗi sau khi hết thời gian chờ heartbeat.'
        ],
        'priority': 'Rất cao',
        'business_rules': [
            'Hệ thống quản trị chỉ cho phép phương pháp tinh chỉnh tham số hiệu quả (PEFT - LoRA) trên các mô hình nền tảng có sẵn.',
            'Tiến trình huấn luyện bắt buộc phải chạy tách biệt với tiến trình phục vụ suy luận thời gian thực để chống xung đột tài nguyên GPU.'
        ]
    })
    
    add_caption(doc, "Bảng 3.20. Đặc tả UC7.3 - Quản lý gói và phiên bản mô hình")
    render_use_case_table(doc, {
        'id_name': 'UC7.3 - Quản lý gói và phiên bản mô hình',
        'creator': 'Nhóm phát triển T-Lingua',
        'date': '05/10/2026',
        'desc': 'Cho phép theo dõi các gói mô hình ứng viên (ModelArtifact) sinh ra từ huấn luyện và cho phép Quản trị cấp cao điều khiển chu trình triển khai: thử nghiệm Canary theo tỷ lệ phần trăm người dùng, nâng cấp thành mô hình chính thức (Promote) hoặc quay xe tức thì (Rollback) về phiên bản cũ.',
        'primary_actor': 'Quản trị viên (Xem) / Quản trị cấp cao (Triển khai)',
        'secondary_actor': 'Bảng model_artifacts, model_deployments và deployment_events',
        'trigger': 'Một ModelArtifact mới được hoàn thành hoặc Quản trị cấp cao truy cập chức năng Triển khai mô hình.',
        'pre_cond': [
            'ModelArtifact tồn tại ở trạng thái hợp lệ và đã vượt qua kiểm định kỹ thuật.',
            'Thao tác thay đổi mô hình bắt buộc phải do tài khoản có vai trò Quản trị cấp cao thực hiện.'
        ],
        'post_cond': [
            'Cấu hình ModelDeployment được cập nhật (active_model, canary_model, canary_percent).',
            'Sự kiện triển khai được ghi vào deployment_events và audit_logs.'
        ],
        'main_flow': [
            'Web Admin hiển thị danh sách các gói mô hình kèm thông số: component, version, base_model, kích thước, SHA-256 và trạng thái.',
            'Quản trị cấp cao chọn một mô hình ứng viên (candidate).',
            'Quản trị cấp cao thiết lập chế độ Canary Deployment: chọn mô hình ứng viên làm canary_model và chỉ định tỷ lệ lưu lượng (ví dụ: 10% hoặc 20%).',
            'Hệ thống áp dụng điều hướng lưu lượng: các phiên dịch realtime sẽ được phân bổ xác suất theo tỷ lệ canary đã định.',
            'Hệ thống theo dõi độ trễ và tỷ lệ lỗi của phiên bản canary trên Dashboard.',
            'Nếu đạt tiêu chuẩn: Quản trị cấp cao nhấn "Promote to Active"; mô hình canary trở thành active_model chính thức, mô hình cũ được lưu vào previous_active_model.',
            'Nếu phát hiện lỗi hoặc suy giảm chất lượng: Quản trị cấp cao nhấn "Rollback"; hệ thống khôi phục ngay lập tức phiên bản previous_active_model.'
        ],
        'alt_flow': [
            'Hủy bỏ thử nghiệm Canary: Quản trị cấp cao đặt canary_percent=0 và xóa canary_model.'
        ],
        'exceptions': [
            'Không có phiên bản trước đó để rollback: Hệ thống cảnh báo không thể thực hiện thao tác.',
            'Tài khoản không đủ thẩm quyền: Trả mã lỗi 403 Forbidden.'
        ],
        'priority': 'Rất cao (Đảm bảo độ tin cậy và không gián đoạn dịch vụ)',
        'business_rules': [
            'Tuyệt đối không đưa mô hình mới vào làm Active Model ngay lập tức mà phải trải qua quy trình đánh giá ứng viên và thử nghiệm Canary.',
            'Mọi hành động thay đổi cấu hình mô hình phục vụ đều phải ghi vết kiểm toán phục vụ truy cứu trách nhiệm.'
        ]
    })
    
    print("UC5, UC6, UC7 rendered.")

def build_section_3_1(doc):
    """Builds complete Section 3.1 containing all 18 Use Cases."""
    render_section_3_1(doc)
    render_section_3_1_part2(doc)
    render_section_3_1_part3(doc)

