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
    w, h = 1600, 1080
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.2: Sơ đồ mô hình lớp tổng quát hệ thống T-Lingua</div>

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

    <!-- User -> AuthSession -->
    <line x1="280" y1="230" x2="430" y2="230" stroke="#1E293B" stroke-width="1.5"/>
    <text x="330" y="222" class="relation-label">khởi tạo phiên</text>
    <text x="290" y="245" class="cardinality">1</text>
    <text x="410" y="245" class="cardinality">0..*</text>

    <!-- User -> ApiKey -->
    <line x1="280" y1="300" x2="430" y2="300" stroke="#1E293B" stroke-width="1.5"/>
    <text x="335" y="292" class="relation-label">sở hữu khóa</text>
    <text x="290" y="315" class="cardinality">1</text>
    <text x="410" y="315" class="cardinality">0..*</text>

    <!-- User -> AuditLog -->
    <line x1="160" y1="350" x2="160" y2="440" stroke="#1E293B" stroke-width="1.5"/>
    <text x="170" y="395" class="relation-label">ghi vết tác nhân</text>
    <text x="145" y="365" class="cardinality">1</text>
    <text x="145" y="430" class="cardinality">0..*</text>

    <!-- TranslationLog -> PipelineMetric -->
    <line x1="720" y1="260" x2="880" y2="260" stroke="#1E293B" stroke-width="1.5"/>
    <text x="765" y="252" class="relation-label">đo kiểm vi mô</text>
    <text x="730" y="275" class="cardinality">1</text>
    <text x="860" y="275" class="cardinality">1..*</text>

    <!-- TranslationLog -> AudioAsset -->
    <line x1="600" y1="380" x2="600" y2="470" stroke="#1E293B" stroke-width="1.5"/>
    <text x="610" y="425" class="relation-label">lưu tệp âm thanh</text>
    <text x="585" y="395" class="cardinality">1</text>
    <text x="585" y="460" class="cardinality">1..1</text>

    <!-- TranslationLog -> QualityReview -->
    <line x1="600" y1="130" x2="600" y2="70" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="600" y1="70" x2="1170" y2="70" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="1170" y1="70" x2="1170" y2="130" stroke="#1E293B" stroke-width="1.5"/>
    <text x="840" y="62" class="relation-label">gắn cờ thẩm định chất lượng</text>
    <text x="610" y="110" class="cardinality">1</text>
    <text x="1150" y="110" class="cardinality">0..1</text>

    <!-- QualityReview -> User (Reviewer) -->
    <line x1="1040" y1="160" x2="980" y2="160" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="980" y1="160" x2="980" y2="20" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="980" y1="20" x2="160" y2="20" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="160" y1="20" x2="160" y2="130" stroke="#1E293B" stroke-width="1.5"/>
    <text x="520" y="15" class="relation-label">thẩm định bởi Reviewer</text>
    <text x="1020" y="150" class="cardinality">0..*</text>
    <text x="170" y="125" class="cardinality">1</text>

    <!-- TrainingDataset -> TrainingJob -->
    <line x1="290" y1="780" x2="440" y2="780" stroke="#1E293B" stroke-width="1.5"/>
    <text x="325" y="772" class="relation-label">dữ liệu nạp</text>
    <text x="300" y="795" class="cardinality">1</text>
    <text x="420" y="795" class="cardinality">0..*</text>

    <!-- TrainingJob -> ModelArtifact -->
    <line x1="720" y1="780" x2="870" y2="780" stroke="#1E293B" stroke-width="1.5"/>
    <text x="755" y="772" class="relation-label">sản sinh gói mô hình</text>
    <text x="730" y="795" class="cardinality">1</text>
    <text x="850" y="795" class="cardinality">1</text>

    <!-- ModelArtifact -> ModelDeployment -->
    <line x1="1130" y1="780" x2="1270" y2="780" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1160" y="772" class="relation-label">tham chiếu Active/Canary</text>
    <text x="1140" y="795" class="cardinality">1..*</text>
    <text x="1250" y="795" class="cardinality">1</text>

    <!-- SessionActor -> RealtimeSession -->
    <line x1="1140" y1="460" x2="1270" y2="460" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1165" y="452" class="relation-label">quản lý phiên WS</text>
    <text x="1150" y="475" class="cardinality">1</text>
    <text x="1250" y="475" class="cardinality">1</text>

    <!-- SessionActor -> ModelManager -->
    <line x1="990" y1="560" x2="990" y2="650" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4"/>
    <text x="1000" y="610" class="relation-label">gọi suy luận GPU</text>
  </svg>

  <!-- CLASS: User -->
  <div class="uml-class" style="top: 130px; left: 50px; width: 230px;">
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

  <!-- CLASS: AuthSession -->
  <div class="uml-class" style="top: 150px; left: 430px; width: 230px;">
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

  <!-- CLASS: ApiKey -->
  <div class="uml-class" style="top: 260px; left: 430px; width: 230px;">
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

  <!-- CLASS: AuditLog -->
  <div class="uml-class" style="top: 440px; left: 50px; width: 230px;">
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

  <!-- CLASS: TranslationLog -->
  <div class="uml-class" style="top: 130px; left: 490px; width: 230px; z-index: 10;">
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

  <!-- CLASS: PipelineMetric -->
  <div class="uml-class" style="top: 130px; left: 880px; width: 240px;">
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

  <!-- CLASS: AudioAsset -->
  <div class="uml-class" style="top: 470px; left: 490px; width: 230px;">
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

  <!-- CLASS: QualityReview -->
  <div class="uml-class" style="top: 130px; left: 1040px; width: 250px;">
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

  <!-- CLASS: SessionActor -->
  <div class="uml-class" style="top: 400px; left: 880px; width: 260px;">
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

  <!-- CLASS: RealtimeSession -->
  <div class="uml-class" style="top: 400px; left: 1270px; width: 250px;">
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

  <!-- CLASS: ModelManager -->
  <div class="uml-class" style="top: 650px; left: 880px; width: 260px;">
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

  <!-- MLOps Pipeline Classes -->
  <!-- TrainingDataset -->
  <div class="uml-class" style="top: 720px; left: 50px; width: 240px;">
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

  <!-- TrainingJob -->
  <div class="uml-class" style="top: 700px; left: 440px; width: 280px;">
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

  <!-- ModelArtifact -->
  <div class="uml-class" style="top: 720px; left: 870px; width: 260px;">
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

  <!-- ModelDeployment -->
  <div class="uml-class" style="top: 720px; left: 1270px; width: 250px;">
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

  <!-- Watermark -->
  <div class="watermark">
    <div class="watermark-logo"></div>
    <span>Visual Paradigm Standard - T-Lingua Class Diagram</span>
  </div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_2_mo_hinh_lop_tong_quat.png")
    render_html_to_png(html, out_png, width=1640, height=1120)

def build_diagram_3_3():
    """Hình 3.3: Mô hình lớp tài khoản, người dùng, phân quyền và bảo mật (Auth & Security)"""
    w, h = 1350, 850
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.3: Mô hình lớp tài khoản, người dùng, phân quyền và bảo mật</div>

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- User -> AuthSession -->
    <line x1="430" y1="260" x2="600" y2="260" stroke="#1E293B" stroke-width="1.5"/>
    <text x="490" y="252" class="relation-label">khởi tạo 1-N</text>
    <text x="440" y="275" class="cardinality">1</text>
    <text x="580" y="275" class="cardinality">0..*</text>

    <!-- User -> ApiKey -->
    <line x1="430" y1="360" x2="600" y2="360" stroke="#1E293B" stroke-width="1.5"/>
    <text x="490" y="352" class="relation-label">sở hữu 1-N</text>
    <text x="440" y="375" class="cardinality">1</text>
    <text x="580" y="375" class="cardinality">0..*</text>

    <!-- User -> AuditLog -->
    <line x1="280" y1="480" x2="280" y2="570" stroke="#1E293B" stroke-width="1.5"/>
    <text x="290" y="530" class="relation-label">ghi vết tác nhân 1-N</text>
    <text x="265" y="500" class="cardinality">1</text>
    <text x="265" y="560" class="cardinality">0..*</text>

    <!-- User -> SystemSetting (Admin configure) -->
    <line x1="430" y1="440" x2="600" y2="520" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4"/>
    <text x="480" y="475" class="relation-label">cấu hình tham số</text>

    <!-- User -> RoleEnum -->
    <line x1="140" y1="300" x2="70" y2="300" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="3"/>
    <text x="80" y="290" class="relation-label">vai trò</text>
  </svg>

  <!-- RoleEnum -->
  <div class="uml-class" style="top: 220px; left: 40px; width: 140px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;enumeration&gt;&gt;</span>
      <span>RoleEnum</span>
    </div>
    <div class="uml-section uml-attributes" style="border-bottom: none;">
      <div class="uml-item">SUPERADMIN</div>
      <div class="uml-item">ADMIN</div>
      <div class="uml-item">REVIEWER</div>
      <div class="uml-item">EMPLOYEE</div>
    </div>
  </div>

  <!-- User -->
  <div class="uml-class" style="top: 150px; left: 160px; width: 270px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>User</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> public_id: string(36) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> username: string(64) (UQ)</div>
      <div class="uml-item"><span class="vis-private">-</span> password_hash: string(255)</div>
      <div class="uml-item"><span class="vis-public">+</span> role: string(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> mfa_enabled: bool</div>
      <div class="uml-item"><span class="vis-private">-</span> mfa_secret_encrypted: string</div>
      <div class="uml-item"><span class="vis-public">+</span> token_version: int</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_password(raw_pwd: str): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> set_password(new_pwd: str): void</div>
      <div class="uml-item"><span class="vis-public">+</span> verify_totp(totp_code: str): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> has_permission(perm: str): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> increment_token_version(): void</div>
    </div>
  </div>

  <!-- AuthSession -->
  <div class="uml-class" style="top: 150px; left: 600px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuthSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> owner_id: string(36)</div>
      <div class="uml-item"><span class="vis-private">-</span> token_hash: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> token_version: int</div>
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

  <!-- ApiKey -->
  <div class="uml-class" style="top: 310px; left: 600px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ApiKey</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> name: string(100)</div>
      <div class="uml-item"><span class="vis-public">+</span> key_prefix: string(16)</div>
      <div class="uml-item"><span class="vis-private">-</span> key_hash: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_by_user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> scopes: string (JSON)</div>
      <div class="uml-item"><span class="vis-public">+</span> is_active: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_key(raw_key: str): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> check_rate_limit(redis): bool</div>
    </div>
  </div>

  <!-- SystemSetting -->
  <div class="uml-class" style="top: 500px; left: 600px; width: 280px;">
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
  <div class="uml-class" style="top: 570px; left: 160px; width: 270px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AuditLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> actor_user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> actor_username: string(100)</div>
      <div class="uml-item"><span class="vis-public">+</span> action: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> resource_type: string(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> details: text (JSON)</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> log(actor, action, res): AuditLog</div>
    </div>
  </div>

  <div class="watermark"><div class="watermark-logo"></div><span>Visual Paradigm Standard - T-Lingua Auth</span></div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_3_mo_hinh_lop_tai_khoan_bao_mat.png")
    render_html_to_png(html, out_png, width=1400, height=890)

def build_diagram_3_4():
    """Hình 3.4: Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry"""
    w, h = 1350, 750
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.4: Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry</div>

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- TranslationLog -> PipelineMetric -->
    <line x1="450" y1="280" x2="620" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="495" y="272" class="relation-label">đo kiểm vi mô 1-N</text>
    <text x="460" y="295" class="cardinality">1</text>
    <text x="600" y="295" class="cardinality">1..*</text>

    <!-- TranslationLog -> AudioAsset -->
    <line x1="310" y1="440" x2="310" y2="520" stroke="#1E293B" stroke-width="1.5"/>
    <text x="320" y="480" class="relation-label">lưu trữ audio 1-1</text>
    <text x="290" y="460" class="cardinality">1</text>
    <text x="290" y="510" class="cardinality">1</text>

    <!-- InputModeEnum -> TranslationLog -->
    <line x1="100" y1="280" x2="160" y2="280" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="3"/>
    <text x="105" y="270" class="relation-label">chế độ</text>
  </svg>

  <!-- InputModeEnum -->
  <div class="uml-class" style="top: 230px; left: 30px; width: 130px;">
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
  <div class="uml-class" style="top: 140px; left: 160px; width: 290px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TranslationLog</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> client_id: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> translated_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> latency: float</div>
      <div class="uml-item"><span class="vis-public">+</span> model_source: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> input_mode: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> stt_model_id: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> nllb_model_id: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> is_flagged: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> is_reviewed: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> flag_issue(reason: str): void</div>
      <div class="uml-item"><span class="vis-public">+</span> mark_as_reviewed(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> to_dict(): dict</div>
    </div>
  </div>

  <!-- PipelineMetric -->
  <div class="uml-class" style="top: 140px; left: 620px; width: 300px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>PipelineMetric</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> turn_id: string(64) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> session_id_hash: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> error_stage: string(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> queue_wait_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> stt_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> translate_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> tts_first_chunk_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> tts_total_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> end_to_end_ms: float</div>
      <div class="uml-item"><span class="vis-public">+</span> audio_duration_s: float</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> calculate_e2e(): float</div>
      <div class="uml-item"><span class="vis-public">+</span> is_sla_breached(threshold=1500): bool</div>
    </div>
  </div>

  <!-- AudioAsset -->
  <div class="uml-class" style="top: 520px; left: 160px; width: 290px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>AudioAsset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> file_name: string(40) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> owner_id: string(36)</div>
      <div class="uml-item"><span class="vis-public">+</span> expires_at: datetime</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_audio_bytes(): bytes</div>
      <div class="uml-item"><span class="vis-public">+</span> is_expired(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> delete_physical_file(): bool</div>
    </div>
  </div>

  <div class="watermark"><div class="watermark-logo"></div><span>Visual Paradigm Standard - T-Lingua Telemetry</span></div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_4_mo_hinh_lop_dich_thuat_telemetry.png")
    render_html_to_png(html, out_png, width=1400, height=790)

def build_diagram_3_5():
    """Hình 3.5: Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)"""
    w, h = 1350, 750
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.5: Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)</div>

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- QualityReview -> TrainingAudioAsset -->
    <line x1="560" y1="360" x2="680" y2="360" stroke="#1E293B" stroke-width="1.5"/>
    <text x="580" y="352" class="relation-label">gán nhãn audio 1-1</text>
    <text x="565" y="375" class="cardinality">1</text>
    <text x="660" y="375" class="cardinality">0..1</text>

    <!-- QualityReview -> TranslationMemoryEntry -->
    <line x1="420" y1="140" x2="420" y2="80" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="420" y1="80" x2="800" y2="80" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="800" y1="80" x2="800" y2="140" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4"/>
    <text x="560" y="72" class="relation-label">chuẩn hóa trích xuất từ vựng TM</text>
  </svg>

  <!-- QualityReview -->
  <div class="uml-class" style="top: 140px; left: 260px; width: 300px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>QualityReview</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: int (FK, UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> reviewer_user_id: int (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> adequacy: int</div>
      <div class="uml-item"><span class="vis-public">+</span> fluency: int</div>
      <div class="uml-item"><span class="vis-public">+</span> error_category: string(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> critical_error: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> corrected_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> corrected_source_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> domain: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> consent_for_training: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> use_for_whisper: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> use_for_nllb: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> approve(split_tag: str): void</div>
      <div class="uml-item"><span class="vis-public">+</span> reject(reason: str): void</div>
      <div class="uml-item"><span class="vis-public">+</span> calculate_mqm_score(): float</div>
    </div>
  </div>

  <!-- TrainingAudioAsset -->
  <div class="uml-class" style="top: 240px; left: 680px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingAudioAsset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> translation_log_id: int (FK, UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> file_name: string(40) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> duration_ms: int</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_rate: int = 16000</div>
      <div class="uml-item"><span class="vis-public">+</span> channels: int = 1</div>
      <div class="uml-item"><span class="vis-public">+</span> uploaded_by_user_id: int (FK)</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
    </div>
  </div>

  <!-- TranslationMemoryEntry -->
  <div class="uml-class" style="top: 140px; left: 1000px; width: 290px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TranslationMemoryEntry</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> owner_id: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text_normalized: str(512)</div>
      <div class="uml-item"><span class="vis-public">+</span> translated_text: text</div>
      <div class="uml-item"><span class="vis-public">+</span> is_approved: bool</div>
      <div class="uml-item"><span class="vis-public">+</span> norm_version: int = 1</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> normalize(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> increment_match(): void</div>
    </div>
  </div>

  <div class="watermark"><div class="watermark-logo"></div><span>Visual Paradigm Standard - T-Lingua TM & QA</span></div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_5_mo_hinh_lop_bo_nho_dich_qa.png")
    render_html_to_png(html, out_png, width=1400, height=790)

def build_diagram_3_6():
    """Hình 3.6: Mô hình lớp MLOps, huấn luyện và vòng đời mô hình (Training Center & Lifecycle)"""
    w, h = 1550, 850
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.6: Mô hình lớp MLOps, huấn luyện và vòng đời mô hình</div>

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- TrainingDataset -> TrainingJob -->
    <line x1="330" y1="280" x2="440" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="350" y="272" class="relation-label">nạp dữ liệu 1-N</text>
    <text x="340" y="295" class="cardinality">1</text>
    <text x="420" y="295" class="cardinality">0..*</text>

    <!-- TrainingJob -> TrainingJobEvent -->
    <line x1="580" y1="480" x2="580" y2="570" stroke="#1E293B" stroke-width="1.5"/>
    <text x="590" y="525" class="relation-label">phát sự kiện loss 1-N</text>
    <text x="560" y="500" class="cardinality">1</text>
    <text x="560" y="560" class="cardinality">0..*</text>

    <!-- TrainingJob -> ModelArtifact -->
    <line x1="720" y1="280" x2="840" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="740" y="272" class="relation-label">xuất artifact 1-1</text>
    <text x="730" y="295" class="cardinality">1</text>
    <text x="820" y="295" class="cardinality">1</text>

    <!-- ModelArtifact -> ModelDeployment -->
    <line x1="1100" y1="280" x2="1220" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1120" y="272" class="relation-label">định tuyến</text>
    <text x="1110" y="295" class="cardinality">1..*</text>
    <text x="1200" y="295" class="cardinality">1</text>

    <!-- ModelDeployment -> DeploymentEvent -->
    <line x1="1350" y1="430" x2="1350" y2="550" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1360" y="490" class="relation-label">ghi lịch sử canary 1-N</text>
    <text x="1330" y="450" class="cardinality">1</text>
    <text x="1330" y="540" class="cardinality">0..*</text>
  </svg>

  <!-- TrainingDataset -->
  <div class="uml-class" style="top: 140px; left: 50px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingDataset</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> name: string(120) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> task: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> source_type: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> version: string(40)</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> sample_count: int</div>
      <div class="uml-item"><span class="vis-public">+</span> train_count: int</div>
      <div class="uml-item"><span class="vis-public">+</span> validation_count: int</div>
      <div class="uml-item"><span class="vis-public">+</span> test_count: int</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> storage_uri: string(300)</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> freeze(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> get_splits(): tuple</div>
    </div>
  </div>

  <!-- TrainingJob -->
  <div class="uml-class" style="top: 140px; left: 440px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingJob</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> dataset_id: string(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> task: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> base_model: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> output_version: string(80)</div>
      <div class="uml-item"><span class="vis-public">+</span> method: string(24) = 'lora'</div>
      <div class="uml-item"><span class="vis-public">+</span> config_json: text</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string(24)</div>
      <div class="uml-item"><span class="vis-public">+</span> progress_percent: float</div>
      <div class="uml-item"><span class="vis-public">+</span> train_loss: float</div>
      <div class="uml-item"><span class="vis-public">+</span> validation_loss: float</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> start_training(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> update_progress(step, loss): void</div>
      <div class="uml-item"><span class="vis-public">+</span> complete(artifact): void</div>
      <div class="uml-item"><span class="vis-public">+</span> cancel(): void</div>
    </div>
  </div>

  <!-- TrainingJobEvent -->
  <div class="uml-class" style="top: 570px; left: 440px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>TrainingJobEvent</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> job_id: string(36) (FK)</div>
      <div class="uml-item"><span class="vis-public">+</span> level: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> event_type: string(32)</div>
      <div class="uml-item"><span class="vis-public">+</span> message: string(1000)</div>
      <div class="uml-item"><span class="vis-public">+</span> metrics_json: text</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> to_ws_payload(): dict</div>
    </div>
  </div>

  <!-- ModelArtifact -->
  <div class="uml-class" style="top: 140px; left: 840px; width: 260px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelArtifact</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: string(36) (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> version: string(80) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> base_model: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> storage_uri: string(300)</div>
      <div class="uml-item"><span class="vis-public">+</span> sha256: string(64)</div>
      <div class="uml-item"><span class="vis-public">+</span> size_bytes: int</div>
      <div class="uml-item"><span class="vis-public">+</span> status: string(24)</div>
      <div class="uml-item"><span class="vis-public">+</span> metrics_json: text</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> verify_checksum(): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> promote_candidate(): void</div>
    </div>
  </div>

  <!-- ModelDeployment -->
  <div class="uml-class" style="top: 140px; left: 1220px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>ModelDeployment</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: string(32) (UQ)</div>
      <div class="uml-item"><span class="vis-public">+</span> active_model: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_model: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_percent: int = 0</div>
      <div class="uml-item"><span class="vis-public">+</span> previous_active_model: str</div>
      <div class="uml-item"><span class="vis-public">+</span> updated_by_user_id: int</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> set_canary(model, pct): void</div>
      <div class="uml-item"><span class="vis-public">+</span> promote_canary(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> rollback(): void</div>
    </div>
  </div>

  <!-- DeploymentEvent -->
  <div class="uml-class" style="top: 550px; left: 1220px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Entity&gt;&gt;</span>
      <span>DeploymentEvent</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> id: int (PK)</div>
      <div class="uml-item"><span class="vis-public">+</span> component: string(16)</div>
      <div class="uml-item"><span class="vis-public">+</span> from_artifact: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> to_artifact: string(200)</div>
      <div class="uml-item"><span class="vis-public">+</span> strategy: string(24)</div>
      <div class="uml-item"><span class="vis-public">+</span> canary_percent: int</div>
      <div class="uml-item"><span class="vis-public">+</span> requested_by_user_id: int</div>
      <div class="uml-item"><span class="vis-public">+</span> created_at: datetime</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> to_audit_payload(): dict</div>
    </div>
  </div>

  <div class="watermark"><div class="watermark-logo"></div><span>Visual Paradigm Standard - T-Lingua MLOps</span></div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_6_mo_hinh_lop_mlops_vong_doi_mo_hinh.png")
    render_html_to_png(html, out_png, width=1600, height=890)

def build_diagram_3_7():
    """Hình 3.7: Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử (In-Memory Actor Pipeline)"""
    w, h = 1500, 850
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{VP_CSS}</style></head><body>
<div class="canvas" style="width: {w}px; height: {h}px;">
  <div class="title-badge">Hình 3.7: Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử</div>

  <svg class="line-canvas" viewBox="0 0 {w} {h}">
    <!-- SessionActor -> RealtimeSession -->
    <line x1="320" y1="280" x2="450" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <text x="350" y="272" class="relation-label">điều phối phiên 1-1</text>
    <text x="330" y="295" class="cardinality">1</text>
    <text x="435" y="295" class="cardinality">1</text>

    <!-- SessionActor -> WebRtcVadStream -->
    <line x1="200" y1="440" x2="200" y2="530" stroke="#1E293B" stroke-width="1.5"/>
    <text x="210" y="485" class="relation-label">lọc âm VAD 1-1</text>
    <text x="180" y="460" class="cardinality">1</text>
    <text x="180" y="520" class="cardinality">1</text>

    <!-- SessionActor -> TurnMetadata -->
    <line x1="320" y1="360" x2="450" y2="440" stroke="#1E293B" stroke-width="1.5"/>
    <text x="350" y="395" class="relation-label">theo dõi turn 1-N</text>
    <text x="330" y="375" class="cardinality">1</text>
    <text x="435" y="455" class="cardinality">1..*</text>

    <!-- SessionActor -> ModelManager -->
    <line x1="720" y1="280" x2="850" y2="280" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4"/>
    <text x="740" y="272" class="relation-label">gọi suy luận GPU</text>
    <text x="730" y="295" class="cardinality">1</text>
    <text x="835" y="295" class="cardinality">1</text>

    <!-- ModelManager -> Workers -->
    <line x1="1130" y1="240" x2="1240" y2="180" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="1130" y1="280" x2="1240" y2="280" stroke="#1E293B" stroke-width="1.5"/>
    <line x1="1130" y1="320" x2="1240" y2="380" stroke="#1E293B" stroke-width="1.5"/>
    <text x="1145" y="210" class="relation-label">cấp phát</text>
  </svg>

  <!-- SessionActor -->
  <div class="uml-class" style="top: 150px; left: 50px; width: 270px;">
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
      <div class="uml-item"><span class="vis-public">+</span> receive_audio_chunk(c: bytes): void</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_start(): void</div>
      <div class="uml-item"><span class="vis-public">+</span> on_speech_end(audio): void</div>
      <div class="uml-item"><span class="vis-public">+</span> acquire_mic_lock(side): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> release_mic_lock(): void</div>
    </div>
  </div>

  <!-- RealtimeSession -->
  <div class="uml-class" style="top: 150px; left: 450px; width: 270px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;In-Memory Session&gt;&gt;</span>
      <span>RealtimeSession</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> session_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> user_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> source_lang: string = 'vi'</div>
      <div class="uml-item"><span class="vis-public">+</span> target_lang: string = 'en'</div>
      <div class="uml-item"><span class="vis-public">+</span> mode: SessionMode</div>
      <div class="uml-item"><span class="vis-public">+</span> is_alive: bool</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> send_json(data: dict): coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> send_binary(pcm: bytes): coroutine</div>
      <div class="uml-item"><span class="vis-public">+</span> close(code: int): coroutine</div>
    </div>
  </div>

  <!-- TurnMetadata -->
  <div class="uml-class" style="top: 380px; left: 450px; width: 270px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Value Object&gt;&gt;</span>
      <span>TurnMetadata</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> turn_id: string</div>
      <div class="uml-item"><span class="vis-public">+</span> turn_index: int</div>
      <div class="uml-item"><span class="vis-public">+</span> speaker_side: string</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_start_time: float</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_end_time: float</div>
      <div class="uml-item"><span class="vis-public">+</span> source_text: string</div>
      <div class="uml-item"><span class="vis-public">+</span> target_text: string</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_e2e_latency(): float</div>
    </div>
  </div>

  <!-- WebRtcVadStream -->
  <div class="uml-class" style="top: 530px; left: 50px; width: 270px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Audio Processing&gt;&gt;</span>
      <span>WebRtcVadStream</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-public">+</span> sample_rate: int = 16000</div>
      <div class="uml-item"><span class="vis-public">+</span> frame_duration_ms: int = 30</div>
      <div class="uml-item"><span class="vis-public">+</span> vad_mode: int = 3</div>
      <div class="uml-item"><span class="vis-public">+</span> silence_threshold_ms: int = 500</div>
      <div class="uml-item"><span class="vis-private">-</span> audio_buffer: bytearray</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> process_chunk(chunk): list</div>
      <div class="uml-item"><span class="vis-public">+</span> is_speech(frame): bool</div>
      <div class="uml-item"><span class="vis-public">+</span> reset(): void</div>
    </div>
  </div>

  <!-- ModelManager -->
  <div class="uml-class" style="top: 150px; left: 850px; width: 280px;">
    <div class="uml-header">
      <span class="uml-stereotype">&lt;&lt;Singleton Manager&gt;&gt;</span>
      <span>ModelManager</span>
    </div>
    <div class="uml-section uml-attributes">
      <div class="uml-item"><span class="vis-private">-</span> _instance: ModelManager</div>
      <div class="uml-item"><span class="vis-public">+</span> device: torch.device</div>
      <div class="uml-item"><span class="vis-private">-</span> loaded_models: dict</div>
      <div class="uml-item"><span class="vis-private">-</span> active_routing: dict</div>
    </div>
    <div class="uml-section uml-methods">
      <div class="uml-item"><span class="vis-public">+</span> get_instance(): ModelManager</div>
      <div class="uml-item"><span class="vis-public">+</span> get_stt_model(session): Whisper</div>
      <div class="uml-item"><span class="vis-public">+</span> get_nmt_model(session): NLLB</div>
      <div class="uml-item"><span class="vis-public">+</span> get_tts_model(lang): VITS</div>
      <div class="uml-item"><span class="vis-public">+</span> reload_routing(): void</div>
    </div>
  </div>

  <!-- Workers -->
  <div class="uml-class" style="top: 130px; left: 1240px; width: 220px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>STTWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: Whisper</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ transcribe(audio): str</div></div>
  </div>
  <div class="uml-class" style="top: 250px; left: 1240px; width: 220px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>TransWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: NLLB + LoRA</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ translate(text): str</div></div>
  </div>
  <div class="uml-class" style="top: 370px; left: 1240px; width: 220px;">
    <div class="uml-header"><span class="uml-stereotype">&lt;&lt;Worker&gt;&gt;</span><span>TTSWorker</span></div>
    <div class="uml-section uml-attributes"><div class="uml-item">+ model: MMS VITS</div></div>
    <div class="uml-section uml-methods"><div class="uml-item">+ synthesize(text): bytes</div></div>
  </div>

  <div class="watermark"><div class="watermark-logo"></div><span>Visual Paradigm Standard - T-Lingua Realtime Pipeline</span></div>
</div>
</body></html>
"""
    out_png = os.path.join(IMG_DIR, "hinh_3_6_mo_hinh_lop_realtime_actor_pipeline.png")
    render_html_to_png(html, out_png, width=1540, height=890)

def main():
    print("=" * 60)
    print("GENERATING ALL 6 UML CLASS DIAGRAMS (VISUAL PARADIGM STYLE)")
    print("=" * 60)
    build_diagram_3_1()
    build_diagram_3_2()
    build_diagram_3_3()
    build_diagram_3_4()
    build_diagram_3_5()
    build_diagram_3_6()
    print("=" * 60)
    print("ALL DIAGRAMS SUCCESSFULLY GENERATED IN docs/img")
    print("=" * 60)

if __name__ == "__main__":
    main()
