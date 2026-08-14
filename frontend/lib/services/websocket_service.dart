import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:web_socket_channel/web_socket_channel.dart';

class RealtimeWebSocketService {
  WebSocketChannel? _channel;
  final StreamController<dynamic> _controller =
      StreamController<dynamic>.broadcast();
  String? _url;
  Map<String, dynamic>? _configPayload;
  bool _configSent = false;
  bool _reconnecting = false;
  bool _closed = false;

  bool get isConnected => _channel != null;

  Stream<dynamic> get stream => _controller.stream;

  void connect(String url) {
    if (_channel != null) {
      return;
    }
    _url = url;
    _closed = false;
    _connectInternal();
  }

  void setConfigPayload(Map<String, dynamic> payload) {
    _configPayload = payload;
    if (_channel != null) {
      _sendConfig();
    }
  }

  void _connectInternal() {
    final url = _url;
    if (url == null) {
      return;
    }
    _channel = WebSocketChannel.connect(Uri.parse(url));
    _configSent = false;
    _sendConfig();
    _channel!.stream.listen(
      (event) {
        _controller.add(event);
      },
      onError: (error) {
        _controller.addError(error);
        _scheduleReconnect();
      },
      onDone: () {
        _scheduleReconnect();
      },
      cancelOnError: true,
    );
  }

  void _scheduleReconnect() {
    if (_closed || _reconnecting) {
      return;
    }
    _reconnecting = true;
    // FIX BUG: autoReconnect
    Future.delayed(const Duration(seconds: 3), () {
      _reconnecting = false;
      if (_closed) {
        return;
      }
      _channel = null;
      _configSent = false;
      _connectInternal();
    });
  }

  void _sendConfig() {
    final channel = _channel;
    final payload = _configPayload;
    if (channel == null || payload == null) {
      return;
    }
    channel.sink.add(jsonEncode(payload));
    _configSent = true;
  }

  void sendJson(Map<String, dynamic> payload) {
    final channel = _channel;
    if (channel == null) {
      return;
    }
    channel.sink.add(jsonEncode(payload));
  }

  void sendBytes(Uint8List bytes) {
    final channel = _channel;
    if (channel == null || !_configSent) {
      return;
    }
    channel.sink.add(bytes);
  }

  Future<void> close() async {
    final channel = _channel;
    _channel = null;
    _closed = true;
    _configSent = false;
    if (channel != null) {
      await channel.sink.close();
    }
    await _controller.close();
  }
}
