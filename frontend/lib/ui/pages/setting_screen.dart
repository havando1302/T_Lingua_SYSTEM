import 'package:flutter/material.dart';

import '../../controllers/settings_controller.dart';
import '../../core/app_localizations.dart';
import '../../services/history_storage_service.dart';
import '../../services/auth_session_service.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = SettingsController.instance;

    return AnimatedBuilder(
      animation: Listenable.merge([settings, AppLocalizations.instance]),
      builder: (context, child) {
        // Map stored values to localizations
        String getSpeedLabel(String speed) {
          switch (speed) {
            case 'Slow':
              return tr('slow');
            case 'Fast':
              return tr('fast');
            default:
              return tr('normal');
          }
        }

        String getLanguageLabel(String lang) {
          switch (lang) {
            case 'en':
              return tr('english');
            default:
              return tr('vietnamese');
          }
        }

        return Scaffold(
          backgroundColor: const Color(0xFFF8FAFC), // Nền xám nhạt như ảnh
          appBar: AppBar(
            backgroundColor: Colors.white,
            elevation: 0,
            leading: IconButton(
              tooltip: tr('back'),
              icon: const Icon(Icons.arrow_back, color: Color(0xFF1E293B)),
              onPressed: () => Navigator.pop(context),
            ),
            title: Text(
              tr('settings'),
              style: const TextStyle(
                color: Color(0xFF1E293B),
                fontWeight: FontWeight.bold,
                fontSize: 22,
              ),
            ),
          ),
          body: ListView(
            children: [
              const SizedBox(height: 20),
              // Danh sách các tùy chọn
              _buildSettingItem(
                tr('voice_speed'),
                getSpeedLabel(settings.voiceSpeed),
                onTap: () => _showSelectionBottomSheet<String>(
                  context: context,
                  title: tr('voice_speed'),
                  options: ['Slow', 'Normal', 'Fast'],
                  selectedValue: settings.voiceSpeed,
                  optionLabel: getSpeedLabel,
                  onSelected: (val) =>
                      _update(context, () => settings.setVoiceSpeed(val)),
                ),
              ),
              _buildSettingItem(tr('voice_gender'), tr('voice_unavailable')),
              _buildSettingItem(
                tr('default_language'),
                getLanguageLabel(settings.language),
                onTap: () => _showSelectionBottomSheet<String>(
                  context: context,
                  title: tr('default_language'),
                  options: ['vi', 'en'],
                  selectedValue: settings.language,
                  optionLabel: getLanguageLabel,
                  onSelected: (val) =>
                      _update(context, () => settings.setLanguage(val)),
                ),
              ),
              _buildSettingItem(
                tr('ai_mode'),
                tr('standard'),
                onTap: null, // AI Mode chỉ hiển thị, không xử lý
              ),

              SwitchListTile(
                title: Text(
                  tr('local_history'),
                  style: const TextStyle(color: Color(0xFF1E293B)),
                ),
                subtitle: Text(
                  tr('history_privacy'),
                  style: const TextStyle(color: Colors.grey),
                ),
                value: settings.historyEnabled,
                onChanged: (value) async {
                  if (value) {
                    final agreed = await _confirm(
                      context,
                      tr('enable_history'),
                      tr('history_consent'),
                    );
                    if (!agreed || !context.mounted) return;
                  }
                  if (context.mounted) {
                    await _update(
                      context,
                      () => settings.setHistoryEnabled(value),
                    );
                  }
                },
              ),
              _buildSettingItem(
                tr('retention'),
                '${settings.historyRetentionDays} ${tr('days')} · ${tr('retention_new')}',
                onTap: () => _showSelectionBottomSheet<int>(
                  context: context,
                  title: tr('retention'),
                  options: [1, 3, 7, 14, 30],
                  selectedValue: settings.historyRetentionDays,
                  optionLabel: (days) => '$days ${tr('days')}',
                  onSelected: (days) => _update(
                    context,
                    () => settings.setHistoryRetentionDays(days),
                  ),
                ),
              ),
              _buildSettingItem(
                tr('clear_history'),
                tr('clear_history_hint'),
                onTap: () async {
                  final agreed = await _confirm(
                    context,
                    tr('clear_history_confirm'),
                    tr('clear_history_warning'),
                  );
                  if (agreed && context.mounted) {
                    await _update(
                      context,
                      HistoryStorageService.instance.clearAllByUser,
                    );
                  }
                },
              ),
              _buildSettingItem(
                tr('logout'),
                tr('logout_hint'),
                onTap: () =>
                    _update(context, AuthSessionService.instance.logout),
              ),
              const SizedBox(height: 24),

              // Thông tin phiên bản ở dưới cùng
              const Text(
                "Voice Translate AI",
                style: TextStyle(
                  color: Colors.grey,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                "${tr('version')} 1.0.0",
                style: const TextStyle(color: Colors.grey, fontSize: 13),
              ),
              const SizedBox(height: 50),
            ],
          ),
        );
      },
    );
  }

  Future<bool> _confirm(
    BuildContext context,
    String title,
    String message,
  ) async {
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(title),
            content: Text(message),
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
        ) ??
        false;
  }

  Future<void> _update(
    BuildContext context,
    Future<void> Function() action,
  ) async {
    try {
      await action();
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..clearSnackBars()
          ..showSnackBar(
            SnackBar(
              content: Text(tr('update_success')),
              duration: const Duration(seconds: 4),
            ),
          );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..clearSnackBars()
          ..showSnackBar(
            SnackBar(
              content: Text(tr('update_failed')),
              duration: const Duration(seconds: 4),
            ),
          );
      }
    }
  }

  void _showSelectionBottomSheet<T>({
    required BuildContext context,
    required String title,
    required List<T> options,
    required T selectedValue,
    required String Function(T) optionLabel,
    required void Function(T) onSelected,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      builder: (BuildContext context) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF1E293B),
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                ),
              ),
              const SizedBox(height: 16),
              // Option List
              ...options.map((option) {
                final isSelected = option == selectedValue;
                return InkWell(
                  onTap: () {
                    onSelected(option);
                    Navigator.pop(context);
                  },
                  borderRadius: BorderRadius.circular(15),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 14,
                      horizontal: 8,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          optionLabel(option),
                          style: TextStyle(
                            color: const Color(0xFF1E293B),
                            fontSize: 16,
                            fontWeight: isSelected
                                ? FontWeight.bold
                                : FontWeight.normal,
                          ),
                        ),
                        if (isSelected)
                          const Icon(
                            Icons.check_circle_rounded,
                            color: Colors.blue,
                            size: 22,
                          )
                        else
                          const Icon(
                            Icons.radio_button_off_rounded,
                            color: Colors.grey,
                            size: 22,
                          ),
                      ],
                    ),
                  ),
                );
              }),
              const SizedBox(height: 12),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSettingItem(
    String title,
    String subtitle, {
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(25),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: const TextStyle(color: Colors.grey, fontSize: 14),
                  ),
                ],
              ),
            ),
            if (onTap != null)
              const Icon(Icons.arrow_forward_ios, color: Colors.grey, size: 16),
          ],
        ),
      ),
    );
  }
}
