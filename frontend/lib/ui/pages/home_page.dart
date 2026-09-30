import 'package:flutter/material.dart';

import '../../controllers/translate_controller.dart';
import '../../controllers/settings_controller.dart';
import '../../core/app_localizations.dart';
import '../../services/history_storage_service.dart';

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
  final TranslationLogic? homeLogic;
  final TranslationLogic? chatLogic;
  const HomePage({super.key, this.homeLogic, this.chatLogic});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // [NEW] Tách riêng 2 logic: Home có messages riêng, Chat có messages riêng
  late final TranslationLogic _homeLogic;
  late final TranslationLogic _chatLogic;

  int _selectedIndex = 0;
  bool _navigating = false;
  bool _saving = false;

  Future<void> _stopMicrophones() async {
    await _homeLogic.cancelRecording();
    await _chatLogic.cancelRecording();
  }

  Future<void> _selectPage(int index) async {
    if (_navigating || index == _selectedIndex) return;
    _navigating = true;
    try {
      await _stopMicrophones();
      if (mounted) setState(() => _selectedIndex = index);
    } finally {
      _navigating = false;
    }
  }

  Future<void> _openSettings() async {
    if (_navigating) return;
    _navigating = true;
    try {
      await _stopMicrophones();
      if (!mounted) return;
      await Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const SettingsScreen()),
      );
    } finally {
      _navigating = false;
    }
  }

  void _feedback(String key) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(tr(key))));
  }

  Future<void> _saveTranslation() async {
    if (_saving) return;
    final message = _homeLogic.messages.lastOrNull;
    setState(() => _saving = true);
    try {
      var result = await _homeLogic.saveTranslation(message: message);
      if (result == HistorySaveResult.disabled && mounted) {
        final agreed = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(tr('enable_history')),
            content: Text(tr('history_consent')),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text(tr('cancel')),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(tr('agree')),
              ),
            ],
          ),
        );
        if (agreed != true || !mounted) return;
        await SettingsController.instance.setHistoryEnabled(true);
        result = await _homeLogic.saveTranslation(message: message);
      }
      _feedback(switch (result) {
        HistorySaveResult.saved => 'saved_success',
        HistorySaveResult.alreadySaved => 'already_saved',
        HistorySaveResult.empty => 'nothing_to_save',
        HistorySaveResult.disabled => 'history_disabled',
      });
    } catch (_) {
      _feedback('history_save_failed');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _homeLogic = widget.homeLogic ?? TranslationLogic();
    _chatLogic = widget.chatLogic ?? TranslationLogic();
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
          ChatScreen(logic: _chatLogic, onBackToHome: () => _selectPage(0)),
          HistoryScreen(onBackToHome: () => _selectPage(0)),
        ];

        return PopScope(
          canPop: _selectedIndex == 0,
          onPopInvokedWithResult: (didPop, result) async {
            if (didPop) {
              await _stopMicrophones();
            } else {
              await _selectPage(0);
            }
          },
          child: Scaffold(
            // Background xám trắng nhẹ
            backgroundColor: const Color(0xFFF5F5F7),

            body: SafeArea(
              child: IndexedStack(index: _selectedIndex, children: pages),
            ),

            bottomNavigationBar: _buildBottomBar(),
          ),
        );
      },
    );
  }

  // ================= HOME CONTENT =================

  Widget _buildHomeContent() {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: IntrinsicHeight(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
                child: Column(
                  children: [
                    TopBar(
                      onHistoryPressed: () => _selectPage(2),
                      onSettingsPressed: _openSettings,
                    ),

                    const SizedBox(height: 12),
                    if (_homeLogic.errorMessage != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text(
                          _homeLogic.errorMessage!,
                          style: const TextStyle(
                            color: Colors.red,
                            fontSize: 13,
                          ),
                        ),
                      ),

                    LanguageSelector(logic: _homeLogic),

                    const SizedBox(height: 20),

                    MicButton(
                      isListening: _homeLogic.isRecording,
                      isBusy: _homeLogic.isMicBusy,
                      onTap: _homeLogic.toggleRecording,
                    ),

                    const SizedBox(height: 20),

                    TranslateCard(
                      speechText: _homeLogic.messages.isNotEmpty
                          ? _homeLogic.messages.last.text
                          : '',
                      translatedText: _homeLogic.messages.isNotEmpty
                          ? _homeLogic.messages.last.translation
                          : '',
                      isListening: _homeLogic.isRecording,
                      onPlay: () async {
                        if (!await _homeLogic.playLastAudio()) {
                          _feedback('audio_not_ready');
                        }
                      },
                      onCopy: () async {
                        try {
                          await _homeLogic.copyTranslation();
                          _feedback('copied_success');
                        } catch (_) {
                          _feedback('copy_failed');
                        }
                      },
                      onSave: _saving ? null : _saveTranslation,
                      onFlag: _homeLogic.isFlagging
                          ? null
                          : () async {
                              if (_homeLogic.messages.isNotEmpty) {
                                try {
                                  await _homeLogic.flagMessage(
                                    _homeLogic.messages.last.id,
                                  );
                                  if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(tr('flag_success')),
                                      ),
                                    );
                                  }
                                } catch (e) {
                                  if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(tr('flag_failed')),
                                      ),
                                    );
                                  }
                                }
                              }
                            },
                    ),

                    const SizedBox(height: 10),
                  ],
                ),
              ),
            ),
          ),
        );
      },
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
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),

      child: ClipRRect(
        borderRadius: BorderRadius.circular(35),

        child: BottomNavigationBar(
          currentIndex: _selectedIndex,

          onTap: _selectPage,

          backgroundColor: Colors.white,

          type: BottomNavigationBarType.fixed,

          selectedItemColor: Colors.blueAccent,

          unselectedItemColor: Colors.grey,

          showSelectedLabels: false,
          showUnselectedLabels: false,

          elevation: 0,

          items: [
            BottomNavigationBarItem(
              icon: const Icon(Icons.home_rounded, size: 26),
              label: tr('home'),
            ),

            BottomNavigationBarItem(
              icon: const Icon(Icons.chat_bubble_outline_rounded, size: 24),
              label: tr('conversation'),
            ),

            BottomNavigationBarItem(
              icon: const Icon(Icons.history_rounded, size: 26),
              label: tr('history'),
            ),
          ],
        ),
      ),
    );
  }
}
