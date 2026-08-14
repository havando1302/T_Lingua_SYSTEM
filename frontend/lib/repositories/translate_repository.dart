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
    required String clientId,
  }) {
    return ApiService.flagTranslation(
      sourceText: sourceText,
      translatedText: translatedText,
      clientId: clientId,
    );
  }
}
