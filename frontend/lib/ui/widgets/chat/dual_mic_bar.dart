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
  bool _switching = false;

  @override
  void initState() {
    super.initState();
    widget.logic.addListener(_onLogicChanged);
  }

  @override
  void dispose() {
    widget.logic.removeListener(_onLogicChanged);
    super.dispose();
  }

  void _onLogicChanged() {
    if (!widget.logic.isRecording && _activeMic != 0) {
      if (mounted) setState(() => _activeMic = 0);
    }
  }

  // Đổi từ long-press sang tap-to-toggle (giống mic ở Home)
  Future<void> _toggleMic(int id) async {
    if (_switching) return;
    setState(() => _switching = true);
    try {
      if (_activeMic == id) {
        // Bấm lần 2 vào cùng mic → tắt mic
        setState(() => _activeMic = 0);
        await widget.logic.stopRecording();
      } else {
        // Nếu đang ghi mic khác → dừng trước, đợi phần cứng audio giải phóng rồi bật mic mới
        if (_activeMic != 0 || widget.logic.isRecording) {
          await widget.logic.stopRecording();
          await Future.delayed(const Duration(milliseconds: 100));
        }
        if (id == 1) {
          // Mic Việt Nam → dịch sang tiếng Anh
          await widget.logic.startRecording(
            sourceLang: 'vi',
            targetLang: 'eng_Latn',
            isMe: true,
          );
        } else {
          // Mic Tiếng Anh → dịch sang tiếng Việt
          await widget.logic.startRecording(
            sourceLang: 'en',
            targetLang: 'vie_Latn',
            isMe: false,
          );
        }
        if (mounted) {
          setState(() => _activeMic = widget.logic.isRecording ? id : 0);
        }
      }
    } finally {
      if (mounted) setState(() => _switching = false);
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
          Expanded(
            child: _buildMicButton(1, tr('vietnamese'), "🇻🇳", Colors.green),
          ),
          Expanded(
            child: _buildMicButton(2, tr('english'), "🇺🇸", Colors.indigo),
          ),
        ],
      ),
    );
  }

  Widget _buildMicButton(int id, String label, String flag, Color activeColor) {
    bool isActive = _activeMic == id && widget.logic.isRecording;

    return Semantics(
      button: true,
      label: '$label: ${tr(isActive ? 'stop_microphone' : 'tap_to_speak')}',
      enabled: !_switching,
      child: InkWell(
        onTap: _switching ? null : () => _toggleMic(id),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: isActive
                    ? activeColor
                    : activeColor.withValues(alpha: 0.7),
                shape: BoxShape.circle,
                boxShadow: isActive
                    ? [
                        BoxShadow(
                          color: activeColor.withValues(alpha: 0.4),
                          blurRadius: 15,
                          spreadRadius: 2,
                        ),
                      ]
                    : [],
              ),
              child: widget.logic.isMicBusy
                  ? const SizedBox(
                      width: 30,
                      height: 30,
                      child: CircularProgressIndicator(color: Colors.white),
                    )
                  : Icon(
                      isActive ? Icons.stop : Icons.mic,
                      color: Colors.white,
                      size: 30,
                    ),
            ),
            const SizedBox(height: 8),
            Wrap(
              alignment: WrapAlignment.center,
              children: [
                Text(flag, style: const TextStyle(fontSize: 14)),
                const SizedBox(width: 5),
                Text(
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
      ),
    );
  }
}
