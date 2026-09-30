import 'package:flutter/material.dart';

import '../../controllers/translate_controller.dart';
import '../../controllers/settings_controller.dart';
import '../widgets/chat/chat_bubble.dart';
import '../widgets/chat/dual_mic_bar.dart';
import '../../core/app_localizations.dart';

class ChatScreen extends StatefulWidget {
  final TranslationLogic logic;
  final VoidCallback? onBackToHome;
  const ChatScreen({super.key, required this.logic, this.onBackToHome});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ScrollController _scrollController = ScrollController();

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([
        widget.logic,
        AppLocalizations.instance,
        SettingsController.instance,
      ]),
      builder: (context, _) {
        final messages = widget.logic.messages;

        // Auto-scroll whenever widget rebuilds (due to messages updating)
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _scrollToBottom();
        });

        return Column(
          children: [
            // 1. Header của trang Chat (Tùy chỉnh lại cho hợp nền tối)
            _buildHeader(),
            if (widget.logic.errorMessage != null)
              Text(
                widget.logic.errorMessage!,
                style: const TextStyle(color: Colors.red),
              ),

            // 2. Danh sách tin nhắn (Cuộn vô tận)
            Expanded(
              child: Container(
                decoration: const BoxDecoration(
                  color: Colors
                      .white, // Giữ nền trắng cho khu vực chat giống ảnh mẫu
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: ClipRRect(
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 20,
                    ),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      return ChatBubble(message: messages[index]);
                    },
                  ),
                ),
              ),
            ),

            // 3. Thanh điều khiển Mic (Nằm dưới cùng)
            DualMicBar(logic: widget.logic),
          ],
        );
      },
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.only(top: 20, bottom: 20, left: 10, right: 10),
      child: Row(
        children: [
          IconButton(
            tooltip: tr('back'),
            icon: const Icon(
              Icons.arrow_back_ios_new,
              color: Color.fromARGB(255, 0, 0, 0),
              size: 20,
            ),
            onPressed: () {
              if (widget.onBackToHome != null) {
                widget.onBackToHome!();
              }
            },
          ),
          const SizedBox(width: 5),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tr('conversation'),
                  style: const TextStyle(
                    color: Color.fromARGB(255, 0, 0, 0),
                    fontWeight: FontWeight.bold,
                    fontSize: 20,
                  ),
                ),
                Text(
                  tr('vi_en'),
                  style: TextStyle(
                    color: const Color.fromARGB(
                      255,
                      0,
                      0,
                      0,
                    ).withValues(alpha: 0.6),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
