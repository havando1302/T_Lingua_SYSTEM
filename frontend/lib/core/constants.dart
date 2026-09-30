import 'package:flutter/foundation.dart';

class ApiEndpointConfig {
  final Uri baseUri;
  ApiEndpointConfig(String value, {bool release = kReleaseMode})
    : baseUri = _validate(value, release);

  static Uri _validate(String value, bool release) {
    final uri = Uri.tryParse(value);
    if (uri == null ||
        !uri.hasAuthority ||
        uri.host.isEmpty ||
        !{'http', 'https'}.contains(uri.scheme) ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        !{'', '/'}.contains(uri.path) ||
        (release && uri.scheme != 'https')) {
      throw const FormatException(
        'API_BASE_URL must be an HTTP(S) origin; release requires HTTPS.',
      );
    }
    return uri.replace(path: '');
  }

  Uri endpoint(String path) {
    if (!path.startsWith('/') || path.startsWith('//')) {
      throw ArgumentError('Invalid API path.');
    }
    return baseUri.replace(path: path);
  }

  Uri get socketUri => baseUri.replace(
    scheme: baseUri.scheme == 'https' ? 'wss' : 'ws',
    path: '/ws/realtime',
  );
}

final apiEndpointConfig = ApiEndpointConfig(
  const String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  ),
);
String get httpBaseUrl => apiEndpointConfig.baseUri.toString();
String get wsBaseUrl => apiEndpointConfig.socketUri.toString();

const int audioSampleRate = 16000;
const int audioChannels = 1;
const int audioSampleWidth = 2;
