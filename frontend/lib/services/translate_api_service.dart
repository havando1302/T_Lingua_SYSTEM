import 'dart:convert';

import 'auth_session_service.dart';

class ApiService {
  static Future<String> translate({
    required String text,
    required String sourceLang,
    required String targetLang,
  }) async {
    final response = await AuthSessionService.instance.request(
      'POST',
      '/api/translate-text',
      body: {
        'text': text,
        'source_lang': sourceLang,
        'target_lang': targetLang,
      },
    );
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic> &&
          decoded['translated_text'] is String &&
          (decoded['translated_text'] as String).trim().isNotEmpty) {
        return decoded['translated_text'];
      }
    } on FormatException {
      // Private response contents must never enter logs or exception messages.
    }
    throw const SessionException('contract', 'Phản hồi bản dịch không hợp lệ.');
  }

  static Future<void> flagTranslation({
    required String sourceText,
    required String translatedText,
    String sourceLang = 'vi',
    String targetLang = 'en',
    String inputMode = 'unknown',
    String? qaAudioToken,
  }) async {
    await AuthSessionService.instance.request(
      'POST',
      '/api/flag-translation',
      body: {
        'source_text': sourceText,
        'translated_text': translatedText,
        'source_lang': sourceLang == 'vie_Latn'
            ? 'vi'
            : sourceLang == 'eng_Latn'
            ? 'en'
            : sourceLang,
        'target_lang': targetLang == 'vie_Latn'
            ? 'vi'
            : targetLang == 'eng_Latn'
            ? 'en'
            : targetLang,
        'input_mode': inputMode,
        'qa_audio_token': ?qaAudioToken,
      },
    );
  }
}
