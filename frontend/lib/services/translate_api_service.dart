// gọi backend Python
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String _baseUrl = "http://127.0.0.1:8000";
  static const String _translatePath = "/api/translate-text";

  static Future<String> translate({
    required String text,
    required String sourceLang,
    required String targetLang,
  }) async {
    final uri = Uri.parse("$_baseUrl$_translatePath");
    final payload = {
      "text": text,
      "source_lang": sourceLang,
      "target_lang": targetLang,
    };
    final body = jsonEncode(payload);

    print("[ApiService] POST $uri");
    print("[ApiService] Request Body: $body");

    try {
      final response = await http
          .post(
            uri,
            headers: const {"Content-Type": "application/json"},
            body: body,
          )
          .timeout(const Duration(seconds: 15));

      print("[ApiService] Status Code: ${response.statusCode}");
      print("[ApiService] Response Body: ${response.body}");

      if (response.statusCode != 200) {
        throw Exception(
          "Backend error ${response.statusCode}: ${response.body}",
        );
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException("Invalid response format");
      }

      final translatedText = decoded["translated_text"];
      if (translatedText is! String || translatedText.isEmpty) {
        throw const FormatException("Missing translated_text in response");
      }

      return translatedText;
    } on TimeoutException catch (error) {
      print("[ApiService] Timeout Error: $error");
      rethrow;
    } catch (error) {
      print("[ApiService] Error: $error");
      rethrow;
    }
  }

  static Future<void> flagTranslation({
    required String sourceText,
    required String translatedText,
    required String clientId,
  }) async {
    final uri = Uri.parse("$_baseUrl/api/flag-translation");
    final payload = {
      "source_text": sourceText,
      "translated_text": translatedText,
      "client_id": clientId,
    };
    final body = jsonEncode(payload);

    try {
      final response = await http
          .post(
            uri,
            headers: const {"Content-Type": "application/json"},
            body: body,
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        throw Exception("Lỗi khi báo sai: ${response.statusCode}");
      }
    } catch (error) {
      print("[ApiService] Flag Error: $error");
      rethrow;
    }
  }
}
