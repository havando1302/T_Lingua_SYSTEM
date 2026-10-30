# -*- coding: utf-8 -*-
"""
Generate professional Visual Paradigm / Enterprise Architect styled UML Class Diagrams
for T-Lingua thesis report.
Outputs high-res PNG and SVG files to C:\\Du_an\\T_Langua_Test\\docs\\img.
"""
import os
import subprocess

IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img"
os.makedirs(IMG_DIR, exist_ok=True)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def render_html_to_png(html_content, out_png_path, width=1500, height=1050):
    tmp_html = out_png_path.replace(".png", "_temp.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--screenshot={out_png_path}",
        f"--window-size={width},{height}",
        f"file:///{tmp_html}"
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(tmp_html):
        try:
            os.remove(tmp_html)
        except Exception:
            pass
    print(f"Rendered: {out_png_path} ({os.path.getsize(out_png_path)/1024:.1f} KB)")

# CSS Template for Visual Paradigm Style
VP_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: #FFFFFF;
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #0F172A;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
  }
  .canvas {
    position: relative;
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
  /* UML Class Box (Visual Paradigm style) */
  .uml-class {
    position: absolute;
    background: #FFFFFF;
    border: 1.5px solid #1E293B;
    border-radius: 2px;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.12);
    font-size: 11px;
    display: flex;
    flex-direction: column;
  }
  .uml-header {
    background: #E2E8F0;
    border-bottom: 1.5px solid #1E293B;
    padding: 6px 10px;
    text-align: center;
    font-weight: 700;
    font-size: 12px;
    color: #0F172A;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .uml-stereotype {
    font-size: 10px;
    font-style: italic;
    font-weight: normal;
    color: #475569;
  }
  .uml-section {
    padding: 6px 10px;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 11px;
    line-height: 1.45;
  }
  .uml-attributes {
    border-bottom: 1px solid #94A3B8;
    background: #FFFFFF;
  }
  .uml-methods {
    background: #FAFAFA;
  }
  .uml-item {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .vis-public { color: #0284C7; font-weight: bold; margin-right: 2px; }
  .vis-private { color: #DC2626; font-weight: bold; margin-right: 2px; }
  .vis-package { color: #D97706; font-weight: bold; margin-right: 2px; }

  /* SVG Canvas for Lines */
  .line-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }
  .relation-label {
    font-size: 10.5px;
    font-family: 'Segoe UI', Arial, sans-serif;
    fill: #1E293B;
    font-weight: 600;
  }
  .cardinality {
    font-size: 10.5px;
    font-family: Consolas, monospace;
    fill: #334155;
    font-weight: bold;
  }
  .watermark {
    position: absolute;
    bottom: 10px;
    right: 15px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #94A3B8;
    font-weight: 600;
  }
  .watermark-logo {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #0284C7;
  }
  .title-badge {
    position: absolute;
    top: 15px;
    left: 20px;
    font-size: 14px;
    font-weight: 800;
    color: #1B365D;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: #F8FAFC;
    padding: 6px 14px;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
  }
"""

def build_diagram_3_2():
    """Hình 3.2: Sơ đồ mô hình lớp tổng quát hệ thống T-Lingua (Global Class Diagram)"""
    w, h = 1720, 1040
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E293B"/>
      </marker>
      <marker id="diamond" viewBox="0 0 12 12" refX="12" refY="6" markerWidth="8" markerHeight="8" orient="auto">
        <path d="M 0 6 L 6 0 L 12 6 L 6 12 z" fill="#1E293B"/>
      </marker>
      <marker id="open-diamond" viewBox="0 0 12 12" refX="12" refY="6" markerWidth="8" markerHeight="8" orient="auto">
        <path d="M 0 6 L 6 0 L 12 6 L 6 12 z" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.5"/>
      </marker>
    </defs>

    <!-- 1. User -> AuthSession (1 -> 0..*) -->
    <line x1="290" y1="160" x2="390" y2="160" stroke="#1E293B" stroke-width="1.5"/>
    <text x="340" y="152" class="relation-label" text-anchor="middle">khởi tạo phiên</text>
    <text x="296" y="175" class="cardinality">1</text>
    <text x="368" y="175" class="cardinality">0..*</text>

    <!-- 2. User -> ApiKey (1 -> 0..*) -->
    <line x1="290" y1="310" x2="390" y2="310" stroke="#1E293B" stroke-width="1.5"/>
    <text x="340" y="302" class="relation-label" text-anchor="middle">sở hữu khóa</text>
    <text x="296" y="325" class="cardinality">1</text>
    <text x="368" y="325" class="cardinality">0..*</text>

    <!-- 3. User -> AuditLog (1 -> 0..*) -->
    <line x1="175" y1="315" x2="175" y2="400" stroke="#1E293B" stroke-width="1.5"/>
    <text x="185" y="358" class="relation-label">ghi vết tác nhân</text>
    <text x="156" y="335" class="cardinality">1</text>
    <text x="152" y="388" class="cardinality">0..*</text>

    <!-- 4. TranslationLog -> PipelineMetric (1 -> 1..*) -->
    <line x1="960" y1="160" x2="1060" y2="160" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1010" y="152" class="relation-label" text-anchor="middle">đo kiểm vi mô</text>
    <text x="966" y="175" class="cardinality">1</text>
    <text x="1034" y="175" class="cardinality">1..*</text>

    <!-- 5. TranslationLog -> AudioAsset (1 -> 1..1) -->
    <line x1="840" y1="315" x2="840" y2="400" stroke="#1E293B" stroke-width="1.5"/>
    <text x="850" y="358" class="relation-label">lưu tệp âm thanh</text>
    <text x="822" y="335" class="cardinality">1</text>
    <text x="816" y="388" class="cardinality">1..1</text>

    <!-- 6. TranslationLog -> QualityReview (1 -> 0..1) -->
    <polyline points="840,70 840,45 1520,45 1520,70" fill="none" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1180" y="39" class="relation-label" text-anchor="middle">gắn cờ thẩm định chất lượng</text>
    <text x="846" y="65" class="cardinality">1</text>
    <text x="1496" y="65" class="cardinality">0..1</text>

    <!-- 7. QualityReview -> User (Reviewer) -->
    <polyline points="1540,70 1540,18 175,18 175,70" fill="none" stroke="#1E293B" stroke-width="1.5"/>
    <text x="520" y="13" class="relation-label" text-anchor="middle">thẩm định bởi Reviewer</text>
    <text x="182" y="65" class="cardinality">1</text>
    <text x="1546" y="65" class="cardinality">0..*</text>

    <!-- 8. SessionActor -> RealtimeSession (1 -> 1) -->
    <line x1="1300" y1="480" x2="1400" y2="480" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1350" y="472" class="relation-label" text-anchor="middle">quản lý phiên WS</text>
    <text x="1306" y="495" class="cardinality">1</text>
    <text x="1388" y="495" class="cardinality">1</text>

    <!-- 9. SessionActor -> ModelManager (gọi suy luận GPU) -->
    <line x1="1180" y1="610" x2="1180" y2="710" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrow)"/>
    <text x="1190" y="660" class="relation-label">gọi suy luận GPU</text>

    <!-- 10. TrainingDataset -> TrainingJob (1 -> 0..*) -->
    <line x1="290" y1="790" x2="390" y2="790" stroke="#1E293B" stroke-width="1.5"/>
    <text x="340" y="782" class="relation-label" text-anchor="middle">dữ liệu nạp</text>
    <text x="296" y="805" class="cardinality">1</text>
    <text x="368" y="805" class="cardinality">0..*</text>

    <!-- 11. TrainingJob -> ModelArtifact (1 -> 1) -->
    <line x1="620" y1="790" x2="720" y2="790" stroke="#1E293B" stroke-width="1.5"/>
    <text x="670" y="782" class="relation-label" text-anchor="middle">sản sinh gói</text>
    <text x="626" y="805" class="cardinality">1</text>
    <text x="706" y="805" class="cardinality">1</text>

    <!-- 12. ModelArtifact -> ModelManager (1..* -> 1) -->
    <line x1="960" y1="790" x2="1060" y2="790" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1010" y="782" class="relation-label" text-anchor="middle">nạp trọng số</text>
    <text x="966" y="805" class="cardinality">1..*</text>
    <text x="1046" y="805" class="cardinality">1</text>

    <!-- 13. ModelDeployment -> ModelManager (1 -> 1) -->
    <line x1="1400" y1="790" x2="1300" y2="790" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1350" y="782" class="relation-label" text-anchor="middle">định tuyến</text>
    <text x="1382" y="805" class="cardinality">1</text>
    <text x="1310" y="805" class="cardinality">1</text>

    <!-- 14. ModelArtifact -> ModelDeployment (tham chiếu Active/Canary) -->
    <polyline points="840,905 840,950 1520,950 1520,920" fill="none" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1180" y="944" class="relation-label" text-anchor="middle">tham chiếu Active/Canary</text>
    <text x="846" y="925" class="cardinality">1..*</text>
    <text x="1496" y="935" class="cardinality">1</text>
  </svg>

  <!-- ================= TIER 1: AUTH, TRANSLATION, TELEMETRY, QUALITY ================= -->
  <!-- CLASS 1: User -->
  <div class="uml-class" style="top: 70px; left: 60px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>User</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> username: string</div>
      <div class="uml-item"><span class="vis-private">-</span> password_hash: string</div>
      <div class="uml-item"><span class="vis-public">+</span> role: string</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> mfa_enabled: bool</div>
      <div class="uml-item"><span class="vis-private">-</span> mfa_secret_encrypted: str</div>
      <div class="uml-item"><span class="vis-public">+</span> token_version: int</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_password(pwd): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> verify_totp(code): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> has_role(role): bool</div>
    </div>
  </div>

  <!-- CLASS 2: AuthSession -->
  <div class="uml-class" style="top: 70px; left: 390px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuthSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string (UUID) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-private">-</span> token_hash: string</div>
      <div class="uml-item"><span class="vis-public">+</span> scopes: string (JSON)</div>
      <div class="uml-item"><span class="vis-public">+</span> mfa_verified: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: datetime</div>
      <div class="uml-item"><span class="vis-public">+</span> revoked_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> is_valid(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> revoke(): void</div>
    </div>
  </div>

  <!-- CLASS 3: ApiKey -->
  <div class="uml-class" style="top: 300px; left: 390px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ApiKey</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> name: string</div>
      <div class="uml-item"><span class="vis-public">+</span> key_prefix: string</div>
      <div class="uml-item"><span class="vis-private">-</span> key_hash: string</div>
      <div class="uml-item"><span class="vis-public">+</span> created_by_user_id: int</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify(raw_key): bool</div>
    </div>
  </div>

  <!-- CLASS 4: TranslationLog -->
  <div class="uml-class" style="top: 70px; left: 720px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TranslationLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> client_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: string</div>
      <div class="uml-item"><span class="vis-public">+</span> translated_text: string</div>
      <div class="uml-item"><span class="vis-public">+</span> latency: float</div>
      <div class="uml-item"><span class="vis-public">+</span> is_flagged: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> is_reviewed: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> flag_for_qa(reason): void</div>
      <div class="uml-item"><span class="vis-public">+</span> to_json(): dict</div>
    </div>
  </div>

  <!-- CLASS 5: PipelineMetric -->
  <div class="uml-class" style="top: 70px; left: 1060px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>PipelineMetric</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> turn_id: string (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> stt_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> translate_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> tts_total_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> end_to_end_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> is_sla_breached(): bool</div>
    </div>
  </div>

  <!-- CLASS 6: QualityReview -->
  <div class="uml-class" style="top: 70px; left: 1400px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>QualityReview</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> reviewer_user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> adequacy: int</div>
      <div class="uml-item"><span class="vis-public">+</span> fluency: int</div>
      <div class="uml-item"><span class="vis-public">+</span> error_category: string</div>
      <div class="uml-item"><span class="vis-public">+</span> corrected_text: string</div>
      <div class="uml-item"><span class="vis-public">+</span> consent_for_training: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> approve(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> export_to_dataset(): void</div>
    </div>
  </div>

  <!-- ================= TIER 2: AUDIT, AUDIO, REALTIME ACTOR & SESSION ================= -->
  <!-- CLASS 7: AuditLog -->
  <div class="uml-class" style="top: 400px; left: 60px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuditLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> actor_user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> actor_username: string</div>
      <div class="uml-item"><span class="vis-public">+</span> action: string</div>
      <div class="uml-item"><span class="vis-public">+</span> resource_type: string</div>
      <div class="uml-item"><span class="vis-public">+</span> details: string (JSON)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> log_event(): void</div>
    </div>
  </div>

  <!-- CLASS 8: AudioAsset -->
  <div class="uml-class" style="top: 400px; left: 720px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AudioAsset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> file_name: string (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> owner_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: datetime</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> is_expired(): bool</div>
    </div>
  </div>

  <!-- CLASS 9: SessionActor -->
  <div class="uml-class" style="top: 400px; left: 1060px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Realtime Actor&gt;&gt;</span>
      <span>SessionActor</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> session_id: string</div>
      <div class="uml-item"><span class="vis-private">-</span> mic_mutex: asyncio.Lock</div>
      <div class="uml-item"><span class="vis-private">-</span> vad_stream: WebRtcVadStream</div>
      <div class="uml-item"><span class="vis-public">+</span> current_turn: TurnMetadata</div>
      <div class="uml-item"><span class="vis-private">-</span> queues: PipelineQueues</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> receive_audio_chunk(chunk): void</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_start(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_end(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> acquire_mic_lock(side): bool</div>
    </div>
  </div>

  <!-- CLASS 10: RealtimeSession -->
  <div class="uml-class" style="top: 400px; left: 1400px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;In-Memory Session&gt;&gt;</span>
      <span>RealtimeSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> session_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string</div>
      <div class="uml-item"><span class="vis-public">+</span> mode: SessionMode</div>
      <div class="uml-item"><span class="vis-public">+</span> is_alive: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> send_json(dict): void</div>
      <div class="uml-item"><span class="vis-public">+</span> send_binary(bytes): void</div>
    </div>
  </div>

  <!-- ================= TIER 3: MLOPS, DATASET, TRAINING, MODEL & DEPLOYMENT ================= -->
  <!-- CLASS 11: TrainingDataset -->
  <div class="uml-class" style="top: 710px; left: 60px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingDataset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string (UUID) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> name: string (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> task: string</div>
      <div class="uml-item"><span class="vis-public">+</span> version: string</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_count: int</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: string</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> freeze(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
    </div>
  </div>

  <!-- CLASS 12: TrainingJob -->
  <div class="uml-class" style="top: 710px; left: 390px; width: 230px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingJob</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string (UUID) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> dataset_id: string (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> base_model: string</div>
      <div class="uml-item"><span class="vis-public">+</span> output_version: string</div>
      <div class="uml-item"><span class="vis-public">+</span> lora_r: int</div>
      <div class="uml-item"><span class="vis-public">+</span> learning_rate: float</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string</div>
      <div class="uml-item"><span class="vis-public">+</span> progress_percent: float</div>
      <div class="uml-item"><span class="vis-public">+</span> train_loss: float</div>
      <div class="uml-item"><span class="vis-public">+</span> val_loss: float</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> start_gpu_worker(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> emit_loss_event(): void</div>
    </div>
  </div>

  <!-- CLASS 13: ModelArtifact -->
  <div class="uml-class" style="top: 710px; left: 720px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelArtifact</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string (UUID) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> version: string (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: string</div>
      <div class="uml-item"><span class="vis-public">+</span> storage_uri: string</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: string</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string</div>
      <div class="uml-item"><span class="vis-public">+</span> metrics_json: string</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> validate(): bool</div>
    </div>
  </div>

  <!-- CLASS 14: ModelManager -->
  <div class="uml-class" style="top: 710px; left: 1060px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Singleton&gt;&gt;</span>
      <span>ModelManager</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-private">-</span> instance: ModelManager</div>
      <div class="uml-item"><span class="vis-public">+</span> device: torch.device</div>
      <div class="uml-item"><span class="vis-private">-</span> loaded_adapters: dict</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_stt_model(session): Whisper</div>
      <div class="uml-item"><span class="vis-public">+</span> get_nmt_model(session): NLLB</div>
      <div class="uml-item"><span class="vis-public">+</span> reload_routing_config(): void</div>
    </div>
  </div>

  <!-- CLASS 15: ModelDeployment -->
  <div class="uml-class" style="top: 710px; left: 1400px; width: 240px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelDeployment</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: string (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> active_model: string</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_model: string</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_percent: int</div>
      <div class="uml-item"><span class="vis-public">+</span> previous_active_model: str</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> set_canary(model, pct): void</div>
      <div class="uml-item"><span class="vis-public">+</span> rollback(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> promote(): void</div>
    </div>
  </div>

</div>
</body></html>
"""
    import shutil
    out_png_3_2 = os.path.join(IMG_DIR, "hinh_3_2_mo_hinh_lop_tong_quat.png")
    render_html_to_png(html, out_png_3_2, width=1780, height=1100)
    out_png_3_1 = os.path.join(IMG_DIR, "hinh_3_1_mo_hinh_lop_tong_quat.png")
    shutil.copyfile(out_png_3_2, out_png_3_1)
    print(f"Copied to: {out_png_3_1}")

def build_diagram_3_3():
    """Hình 3.3: Mô hình lớp tài khoản, người dùng, phân quyền và bảo mật (Auth & Security)"""
    w, h = 1100, 910
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E293B"/>
      </marker>
    </defs>

    <!-- RoleEnum -> User -->
    <line x1="210" y1="180" x2="280" y2="180" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="3"/>
    <text x="245" y="172" class="relation-label" text-anchor="middle">vai trò</text>

    <!-- User -> AuthSession (1 -> 0..*) -->
    <line x1="600" y1="150" x2="710" y2="150" stroke="#1E293B" stroke-width="1.5"/>
    <text x="655" y="142" class="relation-label" text-anchor="middle">khởi tạo 1-N</text>
    <text x="606" y="165" class="cardinality">1</text>
    <text x="686" y="165" class="cardinality">0..*</text>

    <!-- User -> ApiKey (1 -> 0..*) -->
    <line x1="600" y1="365" x2="710" y2="365" stroke="#1E293B" stroke-width="1.5"/>
    <text x="655" y="357" class="relation-label" text-anchor="middle">sở hữu 1-N</text>
    <text x="606" y="380" class="cardinality">1</text>
    <text x="686" y="380" class="cardinality">0..*</text>

    <!-- User -> AuditLog (1 -> 0..*) : Exact border-to-border connection (y1=418 to y2=510) -->
    <line x1="440" y1="418" x2="440" y2="510" stroke="#1E293B" stroke-width="1.5"/>
    <text x="450" y="468" class="relation-label">ghi vết tác nhân 1-N</text>
    <text x="418" y="438" class="cardinality">1</text>
    <text x="412" y="498" class="cardinality">0..*</text>

    <!-- User -> SystemSetting (Admin configure) -->
    <polyline points="600,400 655,400 655,730 710,730" fill="none" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrow)"/>
    <text x="655" y="585" class="relation-label" text-anchor="middle">cấu hình</text>
  </svg>

  <!-- RoleEnum -->
  <div class="uml-class" style="top: 130px; left: 50px; width: 160px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;enumeration&gt;&gt;</span>
      <span>RoleEnum</span>
    </div>
    <div class="uml-section uml-attributes" style="border-bottom: none;">
      <div class="uml-item">ADMIN</div>
      <div class="uml-item">SENIOR_ADMIN</div>
      <div class="uml-item">AUDITOR</div>
      <div class="uml-item">REVIEWER</div>
      <div class="uml-item">TRANSLATOR</div>
    </div>
  </div>

  <!-- User -->
  <div class="uml-class" style="top: 50px; left: 280px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>User</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> username: String(64) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> email: String(128)</div>
      <div class="uml-item"><span class="vis-private">-</span> hashed_password: String(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> role: Enum(RoleEnum)</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> is_verified: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> mfa_enabled: Boolean</div>
      <div class="uml-item"><span class="vis-private">-</span> mfa_secret: String(64)</div>
      <div class="uml-item"><span class="vis-private">-</span> failed_login_attempts: Integer</div>
      <div class="uml-item"><span class="vis-private">-</span> locked_until: DateTime</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
      <div class="uml-item"><span class="vis-public">+</span> updated_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_password(raw_pwd): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> set_password(new_pwd): void</div>
      <div class="uml-item"><span class="vis-public">+</span> verify_totp(totp_code): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> has_permission(perm): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> record_failed_login(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> reset_failed_logins(): void</div>
    </div>
  </div>

  <!-- AuthSession -->
  <div class="uml-class" style="top: 50px; left: 710px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuthSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-private">-</span> token_hash: String(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> ip_address: String(45)</div>
      <div class="uml-item"><span class="vis-public">+</span> user_agent: String(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: DateTime</div>
      <div class="uml-item"><span class="vis-public">+</span> is_revoked: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> is_valid(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> revoke(): void</div>
    </div>
  </div>

  <!-- ApiKey -->
  <div class="uml-class" style="top: 340px; left: 710px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ApiKey</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> key_prefix: String(8)</div>
      <div class="uml-item"><span class="vis-private">-</span> key_hash: String(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> label: String(100)</div>
      <div class="uml-item"><span class="vis-public">+</span> rate_limit_rpm: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: DateTime</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_key(raw_key): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> check_rate_limit(redis): bool</div>
    </div>
  </div>

  <!-- SystemSetting -->
  <div class="uml-class" style="top: 660px; left: 710px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>SystemSetting</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> key: string(100) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> value: text</div>
      <div class="uml-item"><span class="vis-public">+</span> description: string</div>
      <div class="uml-item"><span class="vis-public">+</span> updated_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_value(key: str): str</div>
      <div class="uml-item"><span class="vis-public">+</span> set_value(key: str, val: str): void</div>
    </div>
  </div>

  <!-- AuditLog -->
  <div class="uml-class" style="top: 510px; left: 280px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuditLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> actor_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> action: String(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> resource_type: String(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> resource_id: String(64)</div>
      <div class="uml-item"><span class="vis-private">-</span> payload_before: JSON</div>
      <div class="uml-item"><span class="vis-private">-</span> payload_after: JSON</div>
      <div class="uml-item"><span class="vis-public">+</span> ip_address: String(45)</div>
      <div class="uml-item"><span class="vis-public">+</span> timestamp: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> log_event(actor, action, res): AuditLog</div>
    </div>
  </div>

</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_3_mo_hinh_lop_tai_khoan_bao_mat.png")
    render_html_to_png(html, out_png, width=1160, height=970)

def build_diagram_3_4():
    """Hình 3.4: Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry"""
    w, h = 1120, 740
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- InputMode -> TranslationLog -->
    <line x1="200" y1="180" x2="270" y2="180" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="3"/>
    <text x="235" y="172" class="relation-label" text-anchor="middle">chế độ</text>

    <!-- TranslationLog -> PipelineMetric (1 -> 1..*) -->
    <line x1="590" y1="160" x2="710" y2="160" stroke="#1E293B" stroke-width="1.5"/>
    <text x="650" y="152" class="relation-label" text-anchor="middle">đo kiểm vi mô 1-N</text>
    <text x="596" y="175" class="cardinality">1</text>
    <text x="684" y="175" class="cardinality">1..*</text>

    <!-- TranslationLog -> AudioAsset (1 -> 1) : Exact border-to-border connection -->
    <line x1="430" y1="306" x2="430" y2="420" stroke="#1E293B" stroke-width="1.5"/>
    <text x="440" y="368" class="relation-label">lưu trữ audio 1-1</text>
    <text x="408" y="325" class="cardinality">1</text>
    <text x="408" y="408" class="cardinality">1</text>
  </svg>

  <!-- InputModeEnum -->
  <div class="uml-class" style="top: 130px; left: 50px; width: 150px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;enumeration&gt;&gt;</span>
      <span>InputMode</span>
    </div>
    <div class="uml-section uml-attributes" style="border-bottom: none;">
      <div class="uml-item">VOICE_STREAM</div>
      <div class="uml-item">TEXT_PROMPT</div>
      <div class="uml-item">CONVERSATION</div>
      <div class="uml-item">FILE_IMPORT</div>
    </div>
  </div>

  <!-- TranslationLog -->
  <div class="uml-class" style="top: 50px; left: 270px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TranslationLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> session_id: String(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> turn_index: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: String(10)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: String(10)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> target_text: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> confidence_score: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> is_flagged: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> flag_issue(reason): void</div>
      <div class="uml-item"><span class="vis-public">+</span> to_dict(): dict</div>
    </div>
  </div>

  <!-- PipelineMetric -->
  <div class="uml-class" style="top: 50px; left: 710px; width: 330px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>PipelineMetric</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_latency_ms: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> stt_latency_ms: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> nmt_latency_ms: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> tts_latency_ms: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> e2e_latency_ms: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> model_version_stt: String(50)</div>
      <div class="uml-item"><span class="vis-public">+</span> model_version_nmt: String(50)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> calculate_e2e(): float</div>
    </div>
  </div>

  <!-- AudioAsset -->
  <div class="uml-class" style="top: 420px; left: 270px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AudioAsset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_path: String(500)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_size_bytes: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> duration_ms: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_rate: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> channels: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> format: String(10)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_audio_bytes(): bytes</div>
      <div class="uml-item"><span class="vis-public">+</span> delete_physical_file(): bool</div>
    </div>
  </div>

</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_4_mo_hinh_lop_dich_thuat_telemetry.png")
    render_html_to_png(html, out_png, width=1180, height=800)

def build_diagram_3_5():
    """Hình 3.5: Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)"""
    w, h = 1240, 560
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E293B"/>
      </marker>
    </defs>

    <!-- QualityReview -> TrainingAudioAsset (1 -> 0..1) -->
    <line x1="390" y1="280" x2="480" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="435" y="272" class="relation-label" text-anchor="middle">gán nhãn audio 1-1</text>
    <text x="396" y="295" class="cardinality">1</text>
    <text x="456" y="295" class="cardinality">0..1</text>

    <!-- QualityReview -> TranslationMemoryEntry : Exact border-to-border arched connection -->
    <polyline points="225,90 225,40 1020,40 1020,90" fill="none" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrow)"/>
    <text x="622" y="32" class="relation-label" text-anchor="middle">chuẩn hóa trích xuất từ vựng TM</text>
    <text x="1028" y="82" class="cardinality">0..*</text>
  </svg>

  <!-- QualityReview -->
  <div class="uml-class" style="top: 90px; left: 60px; width: 330px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>QualityReview</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> reviewer_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> mqm_score: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> error_category: String(50)</div>
      <div class="uml-item"><span class="vis-public">+</span> severity: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> corrected_text: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> feedback_note: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> status: Enum(ReviewStatus)</div>
      <div class="uml-item"><span class="vis-public">+</span> reviewed_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> approve_and_export(split_tag): TrainingDataset</div>
      <div class="uml-item"><span class="vis-public">+</span> reject(reason): void</div>
    </div>
  </div>

  <!-- TrainingAudioAsset -->
  <div class="uml-class" style="top: 200px; left: 480px; width: 300px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingAudioAsset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_name: String(40) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: String(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> duration_ms: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_rate: Integer = 16000</div>
      <div class="uml-item"><span class="vis-public">+</span> channels: Integer = 1</div>
      <div class="uml-item"><span class="vis-public">+</span> uploaded_by: String(36) (FK)</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
    </div>
  </div>

  <!-- TranslationMemoryEntry -->
  <div class="uml-class" style="top: 90px; left: 860px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TranslationMemoryEntry</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: String(500)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_text: String(500)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: String(10)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: String(10)</div>
      <div class="uml-item"><span class="vis-public">+</span> domain: String(50)</div>
      <div class="uml-item"><span class="vis-public">+</span> match_count: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> created_by: String(36) (FK)</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> increment_match(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> normalize_text(): void</div>
    </div>
  </div>

</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_5_mo_hinh_lop_bo_nho_dich_qa.png")
    render_html_to_png(html, out_png, width=1300, height=620)

def build_diagram_3_6():
    """Hình 3.6: Mô hình lớp MLOps, huấn luyện và vòng đời mô hình (Training Center & Lifecycle)"""
    w, h = 1620, 820
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- 1. TrainingDataset -> TrainingJob (1 -> 0..*) -->
    <line x1="360" y1="170" x2="450" y2="170" stroke="#1E293B" stroke-width="1.5"/>
    <text x="405" y="162" class="relation-label" text-anchor="middle">nạp dữ liệu 1-N</text>
    <text x="366" y="185" class="cardinality">1</text>
    <text x="426" y="185" class="cardinality">0..*</text>

    <!-- 2. TrainingJob -> ModelArtifact (1 -> 1) -->
    <line x1="770" y1="170" x2="860" y2="170" stroke="#1E293B" stroke-width="1.5"/>
    <text x="815" y="162" class="relation-label" text-anchor="middle">xuất artifact 1-1</text>
    <text x="776" y="185" class="cardinality">1</text>
    <text x="844" y="185" class="cardinality">1</text>

    <!-- 3. ModelArtifact -> ModelDeployment (1..* -> 1) -->
    <line x1="1170" y1="170" x2="1260" y2="170" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1215" y="162" class="relation-label" text-anchor="middle">định tuyến</text>
    <text x="1176" y="185" class="cardinality">1..*</text>
    <text x="1244" y="185" class="cardinality">1</text>

    <!-- 4. TrainingJob -> TrainingJobEvent (1 -> 1..*) : Exact border-to-border (y1=482 to y2=570) -->
    <line x1="610" y1="482" x2="610" y2="570" stroke="#1E293B" stroke-width="1.5"/>
    <text x="620" y="528" class="relation-label">phát sự kiện loss 1-N</text>
    <text x="588" y="502" class="cardinality">1</text>
    <text x="578" y="558" class="cardinality">1..*</text>

    <!-- 5. ModelDeployment -> DeploymentEvent (1 -> 0..*) : Exact border-to-border (y1=290 to y2=400) -->
    <line x1="1415" y1="290" x2="1415" y2="400" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1425" y="348" class="relation-label">ghi lịch sử canary 1-N</text>
    <text x="1392" y="310" class="cardinality">1</text>
    <text x="1386" y="388" class="cardinality">0..*</text>
  </svg>

  <!-- TrainingDataset -->
  <div class="uml-class" style="top: 50px; left: 50px; width: 310px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingDataset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> version: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> description: String(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_count: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> split_ratio: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_uri: String(500)</div>
      <div class="uml-item"><span class="vis-public">+</span> checksum_sha256: String(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> is_frozen: Boolean</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> freeze(): None</div>
      <div class="uml-item"><span class="vis-public">+</span> get_splits(): tuple</div>
    </div>
  </div>

  <!-- TrainingJob -->
  <div class="uml-class" style="top: 50px; left: 450px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingJob</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> dataset_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> model_component: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> base_model_name: String(100)</div>
      <div class="uml-item"><span class="vis-public">+</span> lora_r: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> lora_alpha: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> learning_rate: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> batch_size: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> epochs: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> status: Enum(JobStatus)</div>
      <div class="uml-item"><span class="vis-public">+</span> progress_percent: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> current_epoch: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> current_step: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> train_loss: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> val_loss: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> bleu_score: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> error_message: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> started_at: DateTime</div>
      <div class="uml-item"><span class="vis-public">+</span> finished_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> start(): None</div>
      <div class="uml-item"><span class="vis-public">+</span> update_progress(step, loss, lr): None</div>
      <div class="uml-item"><span class="vis-public">+</span> complete(artifact): None</div>
      <div class="uml-item"><span class="vis-public">+</span> cancel(): None</div>
    </div>
  </div>

  <!-- TrainingJobEvent -->
  <div class="uml-class" style="top: 570px; left: 450px; width: 320px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingJobEvent</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> job_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> level: String(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> event_type: String(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> message: String(1000)</div>
      <div class="uml-item"><span class="vis-public">+</span> metrics_json: Text</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> to_ws_payload(): dict</div>
    </div>
  </div>

  <!-- ModelArtifact -->
  <div class="uml-class" style="top: 50px; left: 860px; width: 310px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelArtifact</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> job_id: String(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> artifact_uri: String(500)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_size_bytes: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256_hash: String(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> test_bleu: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> test_chrf: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> status: Enum(ArtifactStatus)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> promote_to_candidate(): None</div>
    </div>
  </div>

  <!-- ModelDeployment -->
  <div class="uml-class" style="top: 50px; left: 1260px; width: 310px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelDeployment</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: String(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: String(20)</div>
      <div class="uml-item"><span class="vis-public">+</span> active_model_id: String(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_model_id: String(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_percent: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> previous_active_model_id: String(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> updated_by: String(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> updated_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> set_canary(canary_id, pct): None</div>
      <div class="uml-item"><span class="vis-public">+</span> promote_canary(): None</div>
      <div class="uml-item"><span class="vis-public">+</span> rollback(): None</div>
    </div>
  </div>

  <!-- DeploymentEvent -->
  <div class="uml-class" style="top: 400px; left: 1260px; width: 310px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>DeploymentEvent</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: String(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> from_artifact: String(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> to_artifact: String(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> strategy: String(24)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_percent: int</div>
      <div class="uml-item"><span class="vis-public">+</span> requested_by_user_id: int</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: DateTime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> to_audit_payload(): dict</div>
    </div>
  </div>

</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_6_mo_hinh_lop_mlops_vong_doi_mo_hinh.png")
    render_html_to_png(html, out_png, width=1680, height=880)

def build_diagram_3_7():
    """Hình 3.7: Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử (In-Memory Actor Pipeline)"""
    w, h = 1530, 660
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E293B"/>
      </marker>
    </defs>

    <!-- 1. SessionActor -> RealtimeSession (1 -> 1) -->
    <line x1="350" y1="150" x2="440" y2="150" stroke="#1E293B" stroke-width="1.5"/>
    <text x="395" y="142" class="relation-label" text-anchor="middle">điều phối phiên 1-1</text>
    <text x="356" y="165" class="cardinality">1</text>
    <text x="424" y="165" class="cardinality">1</text>

    <!-- 2. SessionActor -> WebRtcVadStream (1 -> 1) : Exact border-to-border (y1=284 to y2=380) -->
    <line x1="200" y1="284" x2="200" y2="380" stroke="#1E293B" stroke-width="1.5"/>
    <text x="210" y="336" class="relation-label">lọc âm VAD 1-1</text>
    <text x="182" y="304" class="cardinality">1</text>
    <text x="182" y="370" class="cardinality">1</text>

    <!-- 3. SessionActor -> TurnMetadata (1 -> 1..*) -->
    <polyline points="350,220 395,220 395,450 440,450" fill="none" stroke="#1E293B" stroke-width="1.5"/>
    <text x="395" y="340" class="relation-label" text-anchor="middle">theo dõi turn 1-N</text>
    <text x="356" y="215" class="cardinality">1</text>
    <text x="418" y="445" class="cardinality">1..*</text>

    <!-- 4. SessionActor -> ModelManager (gọi suy luận GPU) : Arched top connection -->
    <polyline points="200,60 200,22 975,22 975,60" fill="none" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrow)"/>
    <text x="585" y="16" class="relation-label" text-anchor="middle">gọi suy luận GPU</text>

    <!-- 5. ModelManager -> Workers (cấp phát) -->
    <line x1="1130" y1="130" x2="1240" y2="90" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="1130" y1="160" x2="1240" y2="230" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="1130" y1="190" x2="1240" y2="370" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1155" y="130" class="relation-label">cấp phát</text>
  </svg>

  <!-- SessionActor -->
  <div class="uml-class" style="top: 60px; left: 50px; width: 300px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Realtime Actor&gt;&gt;</span>
      <span>SessionActor</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> session: RealtimeSession</div>
      <div class="uml-item"><span class="vis-private">-</span> vad_stream: WebRtcVadStream</div>
      <div class="uml-item"><span class="vis-private">-</span> mic_mutex: asyncio.Lock</div>
      <div class="uml-item"><span class="vis-public">+</span> current_turn: Optional[TurnMetadata]</div>
      <div class="uml-item"><span class="vis-private">-</span> queues: PipelineQueues</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> receive_audio_chunk(chunk): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_start(): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_end(audio): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> dispatch_translation(text): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> dispatch_synthesis(text): Coroutine</div>
    </div>
  </div>

  <!-- RealtimeSession -->
  <div class="uml-class" style="top: 60px; left: 440px; width: 290px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;In-Memory Session&gt;&gt;</span>
      <span>RealtimeSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> session_id: String</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: Optional[String]</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: String</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: String</div>
      <div class="uml-item"><span class="vis-public">+</span> mode: Enum(SessionMode)</div>
      <div class="uml-item"><span class="vis-private">-</span> websocket: WebSocket</div>
      <div class="uml-item"><span class="vis-public">+</span> is_alive: Boolean</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> send_json(data): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> send_binary(pcm_bytes): Coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> close(code: int): Coroutine</div>
    </div>
  </div>

  <!-- TurnMetadata -->
  <div class="uml-class" style="top: 380px; left: 440px; width: 290px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Value Object&gt;&gt;</span>
      <span>TurnMetadata</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> turn_id: String</div>
      <div class="uml-item"><span class="vis-public">+</span> turn_index: Integer</div>
      <div class="uml-item"><span class="vis-public">+</span> speaker_side: String</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: String</div>
      <div class="uml-item"><span class="vis-public">+</span> target_text: String</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_start_time: Float</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_end_time: Float</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_e2e_latency(): Float</div>
    </div>
  </div>

  <!-- WebRtcVadStream -->
  <div class="uml-class" style="top: 380px; left: 50px; width: 300px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Audio Processing&gt;&gt;</span>
      <span>WebRtcVadStream</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> sample_rate: Integer = 16000</div>
      <div class="uml-item"><span class="vis-public">+</span> frame_duration_ms: Integer = 30</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_mode: Integer = 3</div>
      <div class="uml-item"><span class="vis-public">+</span> silence_threshold_ms: Integer</div>
      <div class="uml-item"><span class="vis-private">-</span> audio_buffer: bytearray</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> process_chunk(chunk_bytes): List[VadEvent]</div>
      <div class="uml-item"><span class="vis-public">+</span> reset(): None</div>
    </div>
  </div>

  <!-- ModelManager -->
  <div class="uml-class" style="top: 60px; left: 820px; width: 310px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Singleton Resource Manager&gt;&gt;</span>
      <span>ModelManager</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-private">-</span> _instance: ModelManager (Static)</div>
      <div class="uml-item"><span class="vis-private">-</span> loaded_models: Dict[str, Any]</div>
      <div class="uml-item"><span class="vis-public">+</span> device: torch.device</div>
      <div class="uml-item"><span class="vis-private">-</span> active_routing: Dict[str, ModelDeployment]</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_instance(): ModelManager</div>
      <div class="uml-item"><span class="vis-public">+</span> get_stt_model(session_id): WhisperModel</div>
      <div class="uml-item"><span class="vis-public">+</span> get_nmt_model(session_id): NLLBModel</div>
      <div class="uml-item"><span class="vis-public">+</span> get_tts_model(lang): VITSModel</div>
      <div class="uml-item"><span class="vis-public">+</span> reload_deployment_config(): None</div>
    </div>
  </div>

  <!-- Workers -->
  <div class="uml-class" style="top: 50px; left: 1240px; width: 230px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>STTWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: WhisperModel</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ transcribe(audio): str</div></div>
  </div>
  <div class="uml-class" style="top: 190px; left: 1240px; width: 230px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>TransWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: NLLBModel + LoRA</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ translate(text): str</div></div>
  </div>
  <div class="uml-class" style="top: 330px; left: 1240px; width: 230px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>TTSWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: MMS VITS</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ synthesize(text): bytes</div></div>
  </div>

</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_7_mo_hinh_lop_realtime_actor_pipeline.png")
    render_html_to_png(html, out_png, width=1590, height=720)

def main():
    print("=" * 60)
    print("GENERATING ALL 6 UML CLASS DIAGRAMS (VISUAL PARADIGM STYLE)")
    print("=" * 60)
    build_diagram_3_2()
    build_diagram_3_3()
    build_diagram_3_4()
    build_diagram_3_5()
    build_diagram_3_6()
    build_diagram_3_7()
    print("=" * 60)
    print("ALL DIAGRAMS SUCCESSFULLY GENERATED IN docs/img")
    print("=" * 60)

if __name__ == "__main__":
    main()
