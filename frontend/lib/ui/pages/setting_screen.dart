import 'package:flutter/material.dart';
import '../../controllers/settings_controller.dart';
import '../../core/app_localizations.dart';

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

        String getGenderLabel(String gender) {
          switch (gender) {
            case 'Male':
              return tr('male');
            default:
              return tr('female');
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
          body: Column(
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
                  onSelected: (val) => settings.setVoiceSpeed(val),
                ),
              ),
              _buildSettingItem(
                tr('voice_gender'),
                getGenderLabel(settings.voiceGender),
                onTap: () => _showSelectionBottomSheet<String>(
                  context: context,
                  title: tr('voice_gender'),
                  options: ['Male', 'Female'],
                  selectedValue: settings.voiceGender,
                  optionLabel: getGenderLabel,
                  onSelected: (val) => settings.setVoiceGender(val),
                ),
              ),
              _buildSettingItem(
                tr('default_language'),
                getLanguageLabel(settings.language),
                onTap: () => _showSelectionBottomSheet<String>(
                  context: context,
                  title: tr('default_language'),
                  options: ['vi', 'en'],
                  selectedValue: settings.language,
                  optionLabel: getLanguageLabel,
                  onSelected: (val) => settings.setLanguage(val),
                ),
              ),
              _buildSettingItem(
                tr('ai_mode'),
                tr('standard'),
                onTap: null, // AI Mode chỉ hiển thị, không xử lý
              ),

              const Spacer(),

              // Thông tin phiên bản ở dưới cùng
              const Text(
                "Voice Translate AI",
                style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w500),
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
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          optionLabel(option),
                          style: TextStyle(
                            color: const Color(0xFF1E293B),
                            fontSize: 16,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
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

  Widget _buildSettingItem(String title, String subtitle, {VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(25),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
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
            const Icon(Icons.arrow_forward_ios, color: Colors.grey, size: 16),
          ],
        ),
      ),
    );
  }
}
