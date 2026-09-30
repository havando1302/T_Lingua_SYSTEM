import 'package:flutter/material.dart';
import '/models/chat_message.dart';
import '../../../core/app_localizations.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Column(
        crossAxisAlignment: message.isMe
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        children: [
          Opacity(
            opacity: message.isDraft ? 0.7 : 1.0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              decoration: BoxDecoration(
                // Cả hai phía đều dùng nền xanh tím
                color: message.isMe
                    ? const Color(0xFF6366F1)
                    : const Color(0xFF818CF8),
                borderRadius: BorderRadius.circular(22).copyWith(
                  bottomRight: message.isMe
                      ? const Radius.circular(4)
                      : const Radius.circular(22),
                  bottomLeft: message.isMe
                      ? const Radius.circular(22)
                      : const Radius.circular(4),
                ),
              ),
              child: Text(
                message.text,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          // Phần văn bản dịch — bọc trong bubble nhạt hơn
          if (message.translation.isNotEmpty || message.isDraft)
            Container(
              margin: const EdgeInsets.only(top: 6),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              decoration: BoxDecoration(
                color: message.isMe
                    ? const Color(0xFFE0E7FF)
                    : const Color(0xFFE2E8F0),
                borderRadius: BorderRadius.circular(18).copyWith(
                  topRight: message.isMe
                      ? const Radius.circular(4)
                      : const Radius.circular(18),
                  topLeft: message.isMe
                      ? const Radius.circular(18)
                      : const Radius.circular(4),
                ),
              ),
              child: Text(
                message.translation.isEmpty
                    ? tr('translating')
                    : message.translation,
                style: const TextStyle(
                  color: Color(0xFF0F172A),
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
