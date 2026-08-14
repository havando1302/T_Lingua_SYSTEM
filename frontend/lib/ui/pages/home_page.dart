import 'package:flutter/material.dart';
import '../../controllers/translate_controller.dart';
import '../../controllers/settings_controller.dart';
import '../../core/app_localizations.dart';

// Widgets
import '../widgets/home/top_bar.dart';
import '../widgets/home/language_selector.dart';
import '../widgets/home/mic_button.dart';
import '../widgets/home/translate_card.dart';

// Screens
import 'chat_screen.dart';
import 'history_screen.dart';
import 'setting_screen.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // [NEW] Tách riêng 2 logic: Home có messages riêng, Chat có messages riêng
  late final TranslationLogic _homeLogic;
  late final TranslationLogic _chatLogic;

  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _homeLogic = TranslationLogic(); // [NEW] Logic riêng cho trang Home
    _chatLogic = TranslationLogic(); // [NEW] Logic riêng cho trang Chat
  }

  @override
  void dispose() {
    _homeLogic.dispose(); // [NEW]
    _chatLogic.dispose(); // [NEW]
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // [NEW] Lắng nghe cả 2 logic để rebuild khi bất kỳ cái nào thay đổi
    return AnimatedBuilder(
      animation: Listenable.merge([
        _homeLogic,
        _chatLogic,
        AppLocalizations.instance,
        SettingsController.instance,
      ]),
      builder: (context, _) {
        // SỬA TẠI ĐÂY: Truyền callback đổi index về 0 (Home) khi bấm nút back ở màn History
        final List<Widget> pages = [
          _buildHomeContent(),
          ChatScreen(
            logic: _chatLogic,
            onBackToHome: () {
              setState(() {
                _selectedIndex = 0; // Quay về tab đầu tiên (Home)
              });
            },
          ),
          HistoryScreen(
            onBackToHome: () {
              setState(() {
                _selectedIndex = 0; // Quay về tab đầu tiên (Home)
              });
            },
          ),
        ];

        return Scaffold(
          // Background xám trắng nhẹ
          backgroundColor: const Color(0xFFF5F5F7),

          body: SafeArea(
            child: IndexedStack(index: _selectedIndex, children: pages),
          ),

          bottomNavigationBar: _buildBottomBar(),
        );
      },
    );
  }

  // ================= HOME CONTENT =================

  Widget _buildHomeContent() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          TopBar(
            onHistoryPressed: () {
              setState(() {
                _selectedIndex = 2;
              });
            },
            onSettingsPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
            },
          ),

          const SizedBox(height: 20),

          LanguageSelector(logic: _homeLogic), // [NEW] Home dùng _homeLogic riêng

          const Spacer(),

          const SizedBox(height: 30),

          MicButton(
            isListening: _homeLogic.isRecording, // [NEW]
            onTap: _homeLogic.toggleRecording, // [NEW]
          ),

          const SizedBox(height: 40),

          TranslateCard(
            speechText: _homeLogic.messages.isNotEmpty ? _homeLogic.messages.last.text : '', // [NEW]
            translatedText: _homeLogic.messages.isNotEmpty ? _homeLogic.messages.last.translation : '', // [NEW]
            isListening: _homeLogic.isRecording, // [NEW]
            onPlay: _homeLogic.playLastAudio, // [NEW]
            onCopy: _homeLogic.copyTranslation, // [NEW]
            onSave: _homeLogic.saveTranslation, // [NEW]
            onFlag: () async {
              if (_homeLogic.messages.isNotEmpty) {
                try {
                  await _homeLogic.flagMessage(_homeLogic.messages.last.id);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Đã báo lỗi bản dịch này! Hệ thống sẽ kiểm tra và khắc phục.'))
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Không thể báo lỗi, vui lòng thử lại.'))
                    );
                  }
                }
              }
            },
          ),

          const Spacer(),
        ],
      ),
    );
  }

  // ================= BOTTOM NAVIGATION =================

  Widget _buildBottomBar() {
    return Container(
      margin: const EdgeInsets.only(left: 25, right: 25, bottom: 20),

      height: 70,

      decoration: BoxDecoration(
        color: Colors.white,

        borderRadius: BorderRadius.circular(35),

        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),

      child: ClipRRect(
        borderRadius: BorderRadius.circular(35),

        child: BottomNavigationBar(
          currentIndex: _selectedIndex,

          onTap: (index) {
            setState(() {
              _selectedIndex = index;
            });
          },

          backgroundColor: Colors.white,

          type: BottomNavigationBarType.fixed,

          selectedItemColor: Colors.blueAccent,

          unselectedItemColor: Colors.grey,

          showSelectedLabels: false,
          showUnselectedLabels: false,

          elevation: 0,

          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_rounded, size: 26),
              label: 'Home',
            ),

            BottomNavigationBarItem(
              icon: Icon(Icons.chat_bubble_outline_rounded, size: 24),
              label: 'Chat',
            ),

            BottomNavigationBarItem(
              icon: Icon(Icons.history_rounded, size: 26),
              label: 'History',
            ),
          ],
        ),
      ),
    );
  }
}
