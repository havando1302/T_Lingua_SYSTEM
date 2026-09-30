import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'auth_session_service.dart';

class RealtimeWebSocketService {
  final AuthSessionService _auth;
  final WebSocketChannel Function(Uri) _openChannel;
  final StreamController<dynamic> _controller =
      StreamController<dynamic>.broadcast();
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Map<String, dynamic>? _configPayload;
  Future<void>? _connecting;
  Completer<void>? _ack;
  String? _activeToken;
  bool _authenticated = false;
  bool _disposed = false;
  int _generation = 0;

  RealtimeWebSocketService({
    AuthSessionService? auth,
    WebSocketChannel Function(Uri)? openChannel,
  }) : _auth = auth ?? AuthSessionService.instance,
       _openChannel = openChannel ?? WebSocketChannel.connect {
    _auth.addListener(_onAuthChanged);
  }

  bool get isConnected => _authenticated && _channel != null;
  Stream<dynamic> get stream => _controller.stream;

  void setConfigPayload(Map<String, dynamic> payload) {
    _configPayload = Map.of(payload)
      ..remove('client_id')
      ..remove('access_token');
    if (isConnected) _sendDynamicConfig();
  }

  Future<void> connect(String url) async {
    if (_disposed) throw const SessionException('closed', 'Kết nối đã đóng.');
    if (isConnected) return;
    if (_connecting != null) return _connecting!;
    final generation = _generation;
    final pending = _connectSession(Uri.parse(url), generation);
    _connecting = pending;
    try {
      await pending;
    } finally {
      if (identical(_connecting, pending)) _connecting = null;
    }
  }

  Future<void> _connectSession(Uri uri, int generation) async {
    for (var attempt = 0; attempt < 2; attempt++) {
      final session = await _auth.ensureSession();
      if (_disposed || generation != _generation) {
        throw const SessionException('cancelled', 'Kết nối đã hủy.');
      }
      final channel = _openChannel(uri);
      _channel = channel;
      _activeToken = session.accessToken;
      final ack = Completer<void>();
      _ack = ack;
      // Attach the error handler before the transport can close during handshake.
      final acknowledged = ack.future.timeout(const Duration(seconds: 10));
      _subscription = channel.stream.listen(
        (event) {
          if (_channel != channel || _disposed) return;
          if (event is String) {
            try {
              final data = jsonDecode(event);
              if (data is Map &&
                  data['type'] == 'status' &&
                  data['status'] == 'authenticated') {
                if (data['owner_id'] != session.ownerId) {
                  if (!ack.isCompleted) {
                    ack.completeError(
                      const SessionException(
                        'forbidden',
                        'Danh tính phiên không khớp.',
                      ),
                    );
                  }
                  return;
                }
                _authenticated = true;
                if (!ack.isCompleted) ack.complete();
              }
            } on FormatException {
              /* Ignore malformed messages without exposing payloads. */
            }
          }
          if (_authenticated) _controller.add(event);
        },
        onError: (_) {
          _authenticated = false;
          const error = SessionException(
            'network',
            'Kết nối bị gián đoạn. Hãy bật mic lại.',
          );
          if (!ack.isCompleted) {
            ack.completeError(error);
          } else {
            _controller.addError(error);
          }
        },
        onDone: () {
          if (_channel != channel || _disposed) return;
          _authenticated = false;
          final code = channel.closeCode;
          final error = SessionException(
            code == 4401
                ? 'unauthorized'
                : code == 4403
                ? 'forbidden'
                : 'closed',
            code == 4403
                ? 'Phiên không được phép kết nối.'
                : 'Kết nối đã kết thúc. Hãy bật mic lại.',
          );
          if (!ack.isCompleted) {
            ack.completeError(error);
          } else {
            _channel = null;
            _controller.addError(error);
            if (code == 4401) {
              _auth.invalidate(expectedToken: session.accessToken);
            }
          }
        },
      );
      try {
        // Credentials are sent only after transport readiness, never in the URL.
        await Future.wait<void>([
          channel.ready.timeout(const Duration(seconds: 10)).then((_) {
            if (_channel != channel || generation != _generation) {
              throw const SessionException('cancelled', 'Kết nối đã hủy.');
            }
            _sendHandshakeConfig();
          }),
          acknowledged,
        ], eagerError: true);
        return;
      } catch (error) {
        await _subscription?.cancel();
        _subscription = null;
        if (_channel == channel) _channel = null;
        _authenticated = false;
        _activeToken = null;
        unawaited(channel.sink.close());
        if (error is SessionException &&
            error.code == 'unauthorized' &&
            attempt == 0) {
          _auth.invalidate(expectedToken: session.accessToken);
          continue;
        }
        if (error is SessionException) rethrow;
        throw const SessionException(
          'handshake',
          'Không thể xác thực kết nối. Hãy thử lại.',
        );
      }
    }
  }

  void _sendHandshakeConfig() {
    final config = _configPayload;
    if (_channel == null || config == null || _activeToken == null) return;
    _channel!.sink.add(
      jsonEncode({...config, 'type': 'config', 'access_token': _activeToken}),
    );
  }

  void _sendDynamicConfig() {
    final config = _configPayload;
    if (_channel == null || config == null || !_authenticated) return;
    final dynamicConfig = <String, dynamic>{'type': 'config'};
    if (config.containsKey('source_lang')) dynamicConfig['source_lang'] = config['source_lang'];
    if (config.containsKey('target_lang')) dynamicConfig['target_lang'] = config['target_lang'];
    if (config.containsKey('speaker')) dynamicConfig['speaker'] = config['speaker'];
    _channel!.sink.add(jsonEncode(dynamicConfig));
  }

  void sendBytes(Uint8List bytes) {
    if (isConnected) _channel!.sink.add(bytes);
  }

  void sendJson(Map<String, dynamic> payload) {
    if (isConnected) _channel!.sink.add(jsonEncode(payload));
  }

  void startTurn({
    required String turnId,
    required String speaker,
    required String sourceLang,
    required String targetLang,
  }) {
    sendJson({
      'type': 'start_turn',
      'turn_id': turnId,
      'speaker': speaker,
      'source_lang': sourceLang,
      'target_lang': targetLang,
    });
  }

  void endTurn({required String turnId}) {
    sendJson({
      'type': 'end_turn',
      'turn_id': turnId,
    });
  }

  void cancelTurn({required String turnId}) {
    sendJson({
      'type': 'cancel_turn',
      'turn_id': turnId,
    });
  }

  void _onAuthChanged() {
    if (_activeToken != null && _activeToken != _auth.currentToken) {
      final wasConnected = isConnected;
      unawaited(disconnect());
      if (!_disposed && wasConnected) {
        _controller.addError(
          const SessionException(
            'expired',
            'Phiên đã kết thúc. Hãy bật mic lại.',
          ),
        );
      }
    }
  }

  Future<void> disconnect() async {
    _generation++;
    _authenticated = false;
    _activeToken = null;
    final channel = _channel;
    _channel = null;
    final ack = _ack;
    if (ack != null && !ack.isCompleted) {
      ack.completeError(const SessionException('cancelled', 'Kết nối đã hủy.'));
    }
    await _subscription?.cancel();
    _subscription = null;
    if (channel != null) unawaited(channel.sink.close());
  }

  Future<void> close() async {
    _disposed = true;
    _auth.removeListener(_onAuthChanged);
    await disconnect();
    await _controller.close();
  }
}
