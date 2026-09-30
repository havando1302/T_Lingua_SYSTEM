import '../services/translate_api_service.dart';

class TranslateRepository {
  Future<String> translateText({
    required String text,
    required String sourceLang,
    required String targetLang,
  }) {
    return ApiService.translate(
      text: text,
      sourceLang: sourceLang,
      targetLang: targetLang,
    );
  }

  Future<void> flagTranslation({
    required String sourceText,
    required String translatedText,
    String sourceLang = 'vi',
    String targetLang = 'en',
    String inputMode = 'unknown',
  }) {
    return ApiService.flagTranslation(
      sourceText: sourceText,
      translatedText: translatedText,
      sourceLang: sourceLang,
      targetLang: targetLang,
      inputMode: inputMode,
    );
  }
}
