import 'package:flutter/material.dart';
import '../../../core/app_localizations.dart';

class MicButton extends StatefulWidget {
  final bool? isListening;
  final VoidCallback? onTap;
  final bool isBusy;

  const MicButton({
    super.key,
    this.isListening,
    this.onTap,
    this.isBusy = false,
  });

  @override
  State<MicButton> createState() => _MicButtonState();
}

class _MicButtonState extends State<MicButton> {
  // Biến trạng thái để kiểm tra xem có đang nghe hay không
  bool isListening = false;

  void _toggleListening() {
    if (widget.onTap != null) {
      widget.onTap!();
      return;
    }
    setState(() {
      isListening = !isListening;
    });
  }

  @override
  Widget build(BuildContext context) {
    final listening = widget.isListening ?? isListening;
    return Column(
      mainAxisSize:
          MainAxisSize.min, // Giúp khối này chỉ chiếm diện tích vừa đủ
      children: [
        // Phần Mic
        Tooltip(
          message: tr(
            listening || widget.isBusy ? 'stop_microphone' : 'tap_to_speak',
          ),
          child: Semantics(
            button: true,
            label: tr(
              listening || widget.isBusy ? 'stop_microphone' : 'tap_to_speak',
            ),
            child: InkWell(
              onTap: _toggleListening,
              customBorder: const CircleBorder(),
              child: AnimatedContainer(
                duration: const Duration(
                  milliseconds: 300,
                ), // Hiệu ứng chuyển màu mượt mà
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  // Nếu đang nghe thì hiện màu đỏ, không thì hiện Gradient cũ
                  gradient: listening
                      ? const LinearGradient(
                          colors: [Colors.red, Colors.redAccent],
                        )
                      : const LinearGradient(
                          colors: [
                            Color.fromARGB(255, 246, 59, 199),
                            Color(0xFF2563EB),
                          ],
                        ),
                  boxShadow: [
                    BoxShadow(
                      // Đổi màu bóng đổ khi đang nghe để đồng bộ
                      color: listening
                          ? Colors.red.withValues(alpha: 0.5)
                          : const Color.fromARGB(
                              255,
                              225,
                              233,
                              11,
                            ).withValues(alpha: 0.5),
                      blurRadius: 30,
                      spreadRadius: listening
                          ? 10
                          : 5, // Tăng độ lan khi đang nghe
                    ),
                  ],
                ),
                child: widget.isBusy
                    ? const Padding(
                        padding: EdgeInsets.all(30),
                        child: CircularProgressIndicator(color: Colors.white),
                      )
                    : Icon(
                        listening ? Icons.stop : Icons.mic,
                        size: 40,
                        color: Colors.white,
                      ),
              ),
            ),
          ),
        ),

        const SizedBox(height: 16), // Khoảng cách giữa Mic và Chữ
        // Phần Chữ
        Text(
          tr(
            widget.isBusy
                ? 'microphone_connecting'
                : listening
                ? 'listening'
                : 'tap_to_speak',
          ),
          style: TextStyle(
            color: listening
                ? const Color.fromARGB(255, 243, 30, 30)
                : const Color.fromARGB(255, 0, 0, 0),
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
