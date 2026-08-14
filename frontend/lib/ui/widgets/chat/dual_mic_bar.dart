import 'package:flutter/material.dart';
import '../../../controllers/translate_controller.dart';
import '../../../core/app_localizations.dart';

class DualMicBar extends StatefulWidget {
  final TranslationLogic logic;
  const DualMicBar({super.key, required this.logic});

  @override
  State<DualMicBar> createState() => _DualMicBarState();
}

class _DualMicBarState extends State<DualMicBar> {
  int _activeMic = 0; // 0 = không mic nào, 1 cho Việt, 2 cho Anh

  // [NEW] Đổi từ long-press sang tap-to-toggle (giống mic ở Home)
  void _toggleMic(int id) {
    if (_activeMic == id) {
      // [NEW] Bấm lần 2 vào cùng mic → tắt mic
      setState(() => _activeMic = 0);
      widget.logic.stopRecording();
    } else {
      // [NEW] Nếu đang ghi mic khác → dừng trước, rồi bật mic mới
      if (_activeMic != 0) {
        widget.logic.stopRecording();
      }
      setState(() => _activeMic = id);
      if (id == 1) {
        // Mic Việt Nam → dịch sang tiếng Anh
        widget.logic.startRecording(sourceLang: 'vi', targetLang: 'eng_Latn', isMe: true);
      } else {
        // Mic Tiếng Anh → dịch sang tiếng Việt
        widget.logic.startRecording(sourceLang: 'en', targetLang: 'vie_Latn', isMe: false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade100)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildMicButton(1, tr('vietnamese'), "🇻🇳", Colors.green),
          _buildMicButton(2, tr('english'), "🇺🇸", Colors.indigo),
        ],
      ),
    );
  }

  Widget _buildMicButton(int id, String label, String flag, Color activeColor) {
    bool isActive = _activeMic == id;

    return GestureDetector(
      // [NEW] Thay onLongPressStart/End bằng onTap đơn giản
      onTap: () => _toggleMic(id),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: isActive ? activeColor : activeColor.withOpacity(0.7),
              shape: BoxShape.circle,
              boxShadow: isActive
                  ? [
                      BoxShadow(
                        color: activeColor.withOpacity(0.4),
                        blurRadius: 15,
                        spreadRadius: 2,
                      ),
                    ]
                  : [],
            ),
            child: const Icon(Icons.mic, color: Colors.white, size: 30),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(flag, style: const TextStyle(fontSize: 14)),
              const SizedBox(width: 5),
              Text(
                // [NEW] Hiển thị trạng thái đang nghe
                isActive ? tr('listening') : label,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: isActive ? activeColor : const Color(0xFF334155),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
