import 'package:flutter/material.dart';

class AppLocalizations extends ChangeNotifier {
  static final AppLocalizations instance = AppLocalizations._internal();
  AppLocalizations._internal();

  String _locale = 'vi';
  String get locale => _locale;

  final Map<String, Map<String, String>> _localizedValues = {
    'vi': {
      'server_busy':
          'Máy chủ đang bận. Hãy đợi các câu đã nhận dịch xong rồi nói lại câu cuối.',
      'stt_unavailable': 'Chưa thể nhận diện giọng nói lúc này. Hãy thử lại.',
      'no_speech_detected':
          'Chưa nhận diện được lời nói. Hãy nói rõ hơn rồi thử lại.',
      'translation_unavailable': 'Chưa thể dịch lúc này. Hãy thử lại.',
      'tts_unavailable': 'Bản dịch đã sẵn sàng nhưng chưa thể tạo âm thanh.',
      'home': 'Trang chủ',
      'back': 'Quay lại',
      'flag': 'Báo lỗi',
      'flag_success': 'Đã gửi báo lỗi bản dịch.',
      'flag_failed': 'Không thể báo lỗi. Vui lòng thử lại.',
      'saved_success': 'Đã lưu vào lịch sử trên thiết bị.',
      'already_saved': 'Bản dịch này đã có trong lịch sử.',
      'nothing_to_save': 'Chưa có bản dịch hoàn tất để lưu.',
      'history_disabled': 'Chưa bật lưu lịch sử.',
      'history_save_failed': 'Không thể lưu lịch sử. Hãy thử lại.',
      'copied_success': 'Đã sao chép bản dịch.',
      'copy_failed': 'Không thể sao chép. Hãy thử lại.',
      'audio_not_ready': 'Âm thanh chưa sẵn sàng. Hãy đợi bản dịch hoàn tất.',
      'stop_microphone': 'Dừng microphone',
      'tap_to_speak': 'Chạm để nói',
      'microphone_connecting': 'Đang mở mic… Chạm để hủy',
      'microphone_denied':
          'Chưa có quyền microphone. Hãy cấp quyền trong cài đặt trình duyệt hoặc thiết bị rồi thử lại.',
      'microphone_connection_error':
          'Không thể mở microphone hoặc kết nối. Kiểm tra thiết bị và mạng rồi thử lại.',
      'connection_interrupted': 'Kết nối đã gián đoạn. Hãy bật mic lại.',
      'swap_languages': 'Đổi chiều dịch',
      'add_favorite': 'Thêm yêu thích',
      'remove_favorite': 'Bỏ yêu thích',
      'delete': 'Xóa',
      'load_more': 'Tải thêm',
      'history_removed': 'Mục lịch sử này đã bị xóa hoặc hết thời hạn lưu.',
      'voice_unavailable': 'Hiện dùng giọng mặc định; chưa hỗ trợ chọn Nam/Nữ.',
      'local_history': 'Lưu lịch sử trên thiết bị',
      'history_privacy':
          'Mặc định tắt. Lịch sử được lưu không mã hóa trên thiết bị.',
      'enable_history': 'Bật lưu lịch sử?',
      'history_consent':
          'Bản dịch này và các bản dịch tiếp theo sẽ được lưu không mã hóa trên thiết bị và tự xóa theo thời hạn đã chọn. Lịch sử từ phiên bản cũ chỉ bị xóa khi bạn yêu cầu.',
      'retention': 'Thời hạn lưu',
      'retention_new': 'Áp dụng cho lịch sử mới',
      'days': 'ngày',
      'clear_history': 'Xóa toàn bộ lịch sử',
      'clear_history_hint': 'Bao gồm dữ liệu cũ trước khi nâng cấp',
      'clear_history_confirm': 'Xóa lịch sử?',
      'clear_history_warning':
          'Thao tác này xóa toàn bộ lịch sử trên thiết bị và không thể hoàn tác.',
      'logout': 'Kết thúc phiên khách',
      'logout_hint': 'Phiên mới được tạo khi bạn dịch tiếp',
      'cancel': 'Hủy',
      'agree': 'Đồng ý',
      'update_failed': 'Không thể cập nhật. Hãy thử lại.',
      'update_success': 'Đã cập nhật.',
      'session_inactive': 'Phiên đã tạm dừng.',
      'session_closed': 'Kết nối đã kết thúc. Hãy bật mic lại.',
      'session_expired': 'Phiên đã kết thúc. Hãy bật mic lại.',
      'session_handshake': 'Không thể xác thực kết nối. Hãy thử lại.',
      'session_timeout': 'Máy chủ phản hồi quá chậm. Hãy thử lại.',
      'session_network': 'Không thể kết nối máy chủ.',
      'session_guest_denied': 'Không thể tạo phiên khách. Hãy thử lại sau.',
      'session_contract': 'Phản hồi máy chủ không hợp lệ.',
      'session_cancelled': 'Phiên đã kết thúc.',
      'session_unauthorized': 'Phiên đã hết hạn. Hãy thực hiện lại thao tác.',
      'session_forbidden': 'Phiên này không có quyền thực hiện thao tác.',
      'session_request_failed': 'Yêu cầu chưa thành công. Hãy thử lại.',
      'settings': 'Cài đặt',
      'voice_speed': 'Tốc độ giọng nói',
      'voice_gender': 'Giới tính giọng nói',
      'default_language': 'Ngôn ngữ ứng dụng',
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
      'server_busy':
          'The server is busy. Wait for accepted sentences to finish, then repeat the last sentence.',
      'stt_unavailable':
          'Speech recognition is unavailable right now. Please try again.',
      'no_speech_detected':
          'No speech was detected. Speak clearly and try again.',
      'translation_unavailable':
          'Translation is unavailable right now. Please try again.',
      'tts_unavailable':
          'The translation is ready but audio could not be generated.',
      'home': 'Home',
      'back': 'Back',
      'flag': 'Report',
      'flag_success': 'Translation report sent.',
      'flag_failed': 'Could not report this translation. Please try again.',
      'saved_success': 'Saved to history on this device.',
      'already_saved': 'This translation is already in history.',
      'nothing_to_save': 'There is no completed translation to save.',
      'history_disabled': 'History saving is disabled.',
      'history_save_failed': 'Could not save history. Please try again.',
      'copied_success': 'Translation copied.',
      'copy_failed': 'Could not copy. Please try again.',
      'audio_not_ready':
          'Audio is not ready yet. Wait for the translation to finish.',
      'stop_microphone': 'Stop microphone',
      'tap_to_speak': 'Tap to speak',
      'microphone_connecting': 'Opening mic… Tap to cancel',
      'microphone_denied':
          'Microphone permission is denied. Allow access in your browser or device settings, then try again.',
      'microphone_connection_error':
          'Could not open the microphone or connection. Check your device and network, then try again.',
      'connection_interrupted':
          'Connection interrupted. Tap the microphone to try again.',
      'swap_languages': 'Swap translation direction',
      'add_favorite': 'Add to favorites',
      'remove_favorite': 'Remove from favorites',
      'delete': 'Delete',
      'load_more': 'Load more',
      'history_removed': 'This history item was deleted or expired.',
      'voice_unavailable':
          'The default voice is used. Male/Female selection is not available yet.',
      'local_history': 'Save history on this device',
      'history_privacy':
          'Off by default. History is stored unencrypted on this device.',
      'enable_history': 'Enable history saving?',
      'history_consent':
          'This and future translations will be stored unencrypted on this device and removed after the selected retention period. History from older versions is only deleted when you request it.',
      'retention': 'Retention period',
      'retention_new': 'Applies to new history',
      'days': 'days',
      'clear_history': 'Delete all history',
      'clear_history_hint': 'Includes history saved before upgrading',
      'clear_history_confirm': 'Delete history?',
      'clear_history_warning':
          'This deletes all history on this device and cannot be undone.',
      'logout': 'End guest session',
      'logout_hint': 'A new session is created when you translate again',
      'cancel': 'Cancel',
      'agree': 'Agree',
      'update_failed': 'Could not update. Please try again.',
      'update_success': 'Updated.',
      'session_inactive': 'Session paused.',
      'session_closed': 'Connection closed. Tap the microphone to try again.',
      'session_expired': 'Session ended. Tap the microphone to try again.',
      'session_handshake':
          'Could not authenticate the connection. Please try again.',
      'session_timeout': 'The server is taking too long. Please try again.',
      'session_network': 'Could not connect to the server.',
      'session_guest_denied':
          'Could not create a guest session. Please try again later.',
      'session_contract': 'The server returned an invalid response.',
      'session_cancelled': 'Session ended.',
      'session_unauthorized': 'Session expired. Please try the action again.',
      'session_forbidden': 'This session cannot perform this action.',
      'session_request_failed': 'The request failed. Please try again.',
      'settings': 'Settings',
      'voice_speed': 'Voice Speed',
      'voice_gender': 'Voice Gender',
      'default_language': 'App Language',
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
