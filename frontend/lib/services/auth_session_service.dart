import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../core/app_localizations.dart';

class SessionException implements Exception {
  final String code;
  final String _message;
  const SessionException(this.code, this._message);
  String get message {
    final key = 'session_$code';
    final translated = tr(key);
    return translated == key ? _message : translated;
  }

  @override
  String toString() => message;
}

class GuestSession {
  final String accessToken;
  final String ownerId;
  final DateTime expiresAt;
  const GuestSession(this.accessToken, this.ownerId, this.expiresAt);
}

/// REST and realtime share one identity. Credentials are never persisted.
class AuthSessionService extends ChangeNotifier {
  static final instance = AuthSessionService();
  final http.Client _client;
  final ApiEndpointConfig _config;
  final DateTime Function() _now;
  GuestSession? _session;
  Future<GuestSession>? _pending;
  Timer? _expiryTimer;
  int _generation = 0;
  bool _suspended = false;
  bool _disposed = false;

  AuthSessionService({
    http.Client? client,
    ApiEndpointConfig? config,
    DateTime Function()? now,
  }) : _client = client ?? http.Client(),
       _config = config ?? apiEndpointConfig,
       _now = now ?? DateTime.now;
  String? get currentToken => _session?.accessToken;
  bool get isSuspended => _suspended;

  Future<GuestSession> ensureSession() {
    if (_suspended || _disposed) {
      return Future.error(
        const SessionException('inactive', 'Phiên đã tạm dừng.'),
      );
    }
    final session = _session;
    if (session != null &&
        _now().isBefore(
          session.expiresAt.subtract(const Duration(seconds: 15)),
        )) {
      return Future.value(session);
    }
    if (_pending != null) return _pending!;
    if (session != null) invalidate(expectedToken: session.accessToken);
    final generation = _generation;
    return _pending = _createGuest(generation);
  }

  Future<http.Response> _send(
    String method,
    String path, {
    String? token,
    Object? body,
  }) async {
    final request = http.Request(method, _config.endpoint(path))
      ..followRedirects = false
      ..headers['Accept'] = 'application/json';
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    if (body != null) {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    try {
      final response = await _client
          .send(request)
          .timeout(const Duration(seconds: 15));
      return await http.Response.fromStream(
        response,
      ).timeout(const Duration(seconds: 15));
    } on TimeoutException {
      throw const SessionException(
        'timeout',
        'Máy chủ phản hồi quá chậm. Hãy thử lại.',
      );
    } on http.ClientException {
      throw const SessionException('network', 'Không thể kết nối máy chủ.');
    }
  }

  Future<GuestSession> _createGuest(int generation) async {
    try {
      final response = await _send('POST', '/api/session/guest');
      if (response.statusCode != 200 && response.statusCode != 201) {
        throw const SessionException(
          'guest_denied',
          'Không thể tạo phiên khách. Hãy thử lại sau.',
        );
      }
      final Object? decoded;
      try {
        decoded = jsonDecode(response.body);
      } on FormatException {
        throw const SessionException(
          'contract',
          'Phản hồi phiên không hợp lệ.',
        );
      }
      if (decoded is! Map<String, dynamic> ||
          decoded['access_token'] is! String ||
          (decoded['access_token'] as String).isEmpty ||
          (decoded['access_token'] as String).length > 8192 ||
          !RegExp(r'^[A-Za-z0-9._-]+$').hasMatch(decoded['access_token']) ||
          decoded['token_type'] != 'bearer' ||
          decoded['role'] != 'guest' ||
          decoded['owner_id'] is! String ||
          !RegExp(
            r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$',
          ).hasMatch(decoded['owner_id']) ||
          decoded['expires_in'] is! int ||
          decoded['expires_in'] <= 15 ||
          decoded['expires_in'] > 86400) {
        throw const SessionException(
          'contract',
          'Phản hồi phiên không hợp lệ.',
        );
      }
      final session = GuestSession(
        decoded['access_token'],
        decoded['owner_id'],
        _now().add(Duration(seconds: decoded['expires_in'])),
      );
      // A delayed handshake must not revive credentials after logout/backgrounding.
      if (_disposed || _suspended || generation != _generation) {
        await _revoke(session.accessToken);
        throw const SessionException('cancelled', 'Phiên đã kết thúc.');
      }
      _session = session;
      _expiryTimer?.cancel();
      _expiryTimer = Timer(
        Duration(seconds: decoded['expires_in'] - 15),
        () => invalidate(expectedToken: session.accessToken),
      );
      notifyListeners();
      return session;
    } finally {
      if (generation == _generation) _pending = null;
    }
  }

  Future<http.Response> request(
    String method,
    String path, {
    Object? body,
  }) async {
    final session = await ensureSession();
    final response = await _send(
      method,
      path,
      token: session.accessToken,
      body: body,
    );
    if (response.statusCode == 401) {
      invalidate(expectedToken: session.accessToken);
      throw const SessionException(
        'unauthorized',
        'Phiên đã hết hạn. Hãy thực hiện lại thao tác.',
      );
    }
    if (response.statusCode == 403) {
      throw const SessionException(
        'forbidden',
        'Phiên này không có quyền thực hiện thao tác.',
      );
    }
    if (_suspended || currentToken != session.accessToken) {
      throw const SessionException('cancelled', 'Phiên đã kết thúc.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw const SessionException(
        'request_failed',
        'Yêu cầu chưa thành công. Hãy thử lại.',
      );
    }
    return response;
  }

  void invalidate({String? expectedToken}) {
    if (expectedToken != null && expectedToken != _session?.accessToken) return;
    _generation++;
    _session = null;
    _pending = null;
    _expiryTimer?.cancel();
    if (!_disposed) notifyListeners();
  }

  Future<void> _revoke(String token) async {
    try {
      await _send('POST', '/api/session/logout', token: token);
    } catch (_) {
      /* Local logout remains effective offline; server expiry is the fallback. */
    }
  }

  Future<void> logout() async {
    final token = currentToken;
    invalidate();
    if (token != null) await _revoke(token);
  }

  Future<void> suspend() async {
    _suspended = true;
    await logout();
  }

  void resume() {
    if (!_disposed) {
      _suspended = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _expiryTimer?.cancel();
    _generation++;
    _session = null;
    _client.close();
    super.dispose();
  }
}
