import 'package:flutter/material.dart';

class AppLocalizations extends ChangeNotifier {
  static final AppLocalizations instance = AppLocalizations._internal();
  AppLocalizations._internal();

  String _locale = 'vi';
  String get locale => _locale;

  final Map<String, Map<String, String>> _localizedValues = {
    'vi': {
      'settings': 'Cài đặt',
      'voice_speed': 'Tốc độ giọng nói',
      'voice_gender': 'Giới tính giọng nói',
      'default_language': 'Ngôn ngữ mặc định',
      'ai_mode': 'Chế độ AI',
      'history': 'Lịch sử',
      'conversation': 'Hội thoại',
      'voice_translator': 'T-Lingua',
      'you_said': 'Bạn nói',
      'translation': 'Bản dịch',
      'play': 'Phát',
      'copy': 'Sao chép',
      'save': 'Lưu',
      'close': 'Đóng',
      'original': 'Bản gốc',
      'translated': 'Bản dịch',
      'translating': 'Đang dịch...',
      'history_empty': 'Lịch sử trống',
      'listening': 'Đang nghe...',
      'slow': 'Chậm',
      'normal': 'Bình thường',
      'fast': 'Nhanh',
      'male': 'Nam',
      'female': 'Nữ',
      'vietnamese': 'Tiếng Việt',
      'english': 'Tiếng Anh',
      'standard': 'Tiêu chuẩn',
      'version': 'Phiên bản',
      'deleted_success': 'Đã xóa thành công',
      'added_success': 'Đã thêm thành công',
      'vi_en': 'Tiếng Việt ↔ Tiếng Anh',
    },
    'en': {
      'settings': 'Settings',
      'voice_speed': 'Voice Speed',
      'voice_gender': 'Voice Gender',
      'default_language': 'Default Language',
      'ai_mode': 'AI Mode',
      'history': 'History',
      'conversation': 'Conversation',
      'voice_translator': 'T-Lingua',
      'you_said': 'You said',
      'translation': 'Translation',
      'play': 'Play',
      'copy': 'Copy',
      'save': 'Save',
      'close': 'Close',
      'original': 'Original',
      'translated': 'Translation',
      'translating': 'Translating...',
      'history_empty': 'History is empty',
      'listening': 'Listening...',
      'slow': 'Slow',
      'normal': 'Normal',
      'fast': 'Fast',
      'male': 'Male',
      'female': 'Female',
      'vietnamese': 'Vietnamese',
      'english': 'English',
      'standard': 'Standard',
      'version': 'Version',
      'deleted_success': 'Deleted successfully',
      'added_success': 'Added successfully',
      'vi_en': 'Vietnamese ↔ English',
    },
  };

  void init(String initialLocale) {
    _locale = initialLocale;
  }

  String tr(String key) {
    return _localizedValues[_locale]?[key] ?? key;
  }

  void setLocale(String lang) {
    if (lang != 'vi' && lang != 'en') return;
    _locale = lang;
    notifyListeners();
  }
}

// Global helper function for easier localization calls
String tr(String key) => AppLocalizations.instance.tr(key);
