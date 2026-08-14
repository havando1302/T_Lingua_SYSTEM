import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:hive/hive.dart'; // [NEW] Hive
import '../models/history.dart'; // [NEW] HistoryModel

import '../core/constants.dart';
import '../services/audio_player_service.dart';
import '../services/audio_stream_service.dart';
import '../services/websocket_service.dart';
import '../repositories/translate_repository.dart';
import '../models/chat_message.dart';
import 'settings_controller.dart';

class TranslationLogic extends ChangeNotifier {
  final RealtimeWebSocketService _ws = RealtimeWebSocketService();
  final AudioStreamService _audio = AudioStreamService();
  final AudioPlayerService _player = AudioPlayerService();

  bool isRecording = false;
  
  // State for Chat Messages
  List<ChatMessage> messages = [];
  
  // Unique Client ID for backend session memory
  final String clientId = 'client_${DateTime.now().millisecondsSinceEpoch}';

  // Language Config
  String currentSourceLang = 'vi';
  String currentTargetLang = 'eng_Latn';
  bool isMeSpeaking = true;

  String? _lastAudioUrl;

  StreamSubscription<dynamic>? _wsSub;
  StreamSubscription<Uint8List>? _audioSub;
  bool _connecting = false;

  TranslationLogic() {
    _initLanguagesFromSettings();
    SettingsController.instance.addListener(_onSettingsChanged);
  }

  void _initLanguagesFromSettings() {
    final defaultLang = SettingsController.instance.language;
    if (defaultLang == 'en') {
      currentSourceLang = 'en';
      currentTargetLang = 'vie_Latn';
      isMeSpeaking = false;
    } else {
      currentSourceLang = 'vi';
      currentTargetLang = 'eng_Latn';
      isMeSpeaking = true;
    }
  }

  void _onSettingsChanged() {
    _initLanguagesFromSettings();
    notifyListeners();
  }

  void swapLanguages() {
    if (currentSourceLang == 'vi') {
      currentSourceLang = 'en';
      currentTargetLang = 'vie_Latn';
      isMeSpeaking = false;
    } else {
      currentSourceLang = 'vi';
      currentTargetLang = 'eng_Latn';
      isMeSpeaking = true;
    }
    notifyListeners();
  }

  Future<void> toggleRecording() async {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording(
        sourceLang: currentSourceLang,
        targetLang: currentTargetLang,
        isMe: isMeSpeaking,
      );
    }
  }

  Future<void> startRecording({
    String? sourceLang,
    String? targetLang,
    bool? isMe,
  }) async {
    if (isRecording) {
      return;
    }

    if (sourceLang != null) currentSourceLang = sourceLang;
    if (targetLang != null) currentTargetLang = targetLang;
    if (isMe != null) isMeSpeaking = isMe;

    await _connectIfNeeded();

    final stream = await _audio.startStream(
      sampleRate: audioSampleRate,
      channels: audioChannels,
    );

    isRecording = true;
    notifyListeners();

    _audioSub = stream.listen(
      (chunk) {
        if (!isRecording) {
          return;
        }
        _ws.sendBytes(chunk);
      },
      onError: (error) {
        stopRecording();
      },
    );
  }

  Future<void> stopRecording() async {
    if (!isRecording) {
      return;
    }

    isRecording = false;
    notifyListeners();

    await _audioSub?.cancel();
    _audioSub = null;
    await _audio.stop();

    await _sendSilence(durationMs: 1500);
  }

  Future<void> _connectIfNeeded() async {
    final payload = {
      'type': 'config',
      'client_id': clientId,
      'sample_rate': audioSampleRate,
      'channels': audioChannels,
      'sample_width': audioSampleWidth,
      'source_lang': currentSourceLang,
      'target_lang': currentTargetLang,
    };

    if (_ws.isConnected || _connecting) {
      _ws.setConfigPayload(payload);
      return;
    }
    _connecting = true;

    _ws.setConfigPayload(payload);
    _ws.connect(wsBaseUrl);

    _wsSub?.cancel();
    _wsSub = _ws.stream.listen(
      _handleMessage,
      onError: (_) {
        _connecting = false;
      },
      onDone: () {
        _connecting = false;
      },
    );

    _connecting = false;
  }

  void _handleMessage(dynamic message) {
    if (message is! String) {
      return;
    }

    Map<String, dynamic> data;
    try {
      data = jsonDecode(message) as Map<String, dynamic>;
    } catch (e) {
      // FIX BUG: Crash JSON
      debugPrint('WS JSON parse error: $e');
      return;
    }
    final type = data['type'];

    if (type == 'status') {
      return;
    }

    if (type == 'stt') {
      final text = (data['data']?['text'] ?? '') as String;
      final msgId = (data['message_id'] ?? '') as String;
      
      if (text.trim().isEmpty) return;

      final existingIdx = messages.indexWhere((m) => m.id == msgId);
      if (existingIdx >= 0) {
        messages[existingIdx] = messages[existingIdx].copyWith(text: text);
      } else {
        messages.add(ChatMessage(
          id: msgId,
          text: text,
          translation: '',
          isMe: isMeSpeaking,
          isDraft: true,
        ));
      }
      notifyListeners();
      return;
    }

    if (type == 'translation') {
      final translated = (data['data']?['translated_text'] ?? '') as String;
      final msgId = (data['message_id'] ?? '') as String;
      
      final existingIdx = messages.indexWhere((m) => m.id == msgId);
      if (existingIdx >= 0) {
        messages[existingIdx] = messages[existingIdx].copyWith(
          translation: translated,
          isDraft: false,
        );

        // [NEW] Tự động lưu vào Hive ngay khi dịch xong — không cần bấm Save
        _autoSaveToHistory(
          originalText: messages[existingIdx].text,
          translatedText: translated,
        );
      }
      notifyListeners();
      return;
    }

    if (type == 'audio') {
      final audioPath = data['audio_url'] as String?;
      if (audioPath != null) {
        _lastAudioUrl = '$httpBaseUrl$audioPath';
        final speedStr = SettingsController.instance.voiceSpeed;
        double rate = 1.0;
        if (speedStr == 'Slow') {
          rate = 0.8;
        } else if (speedStr == 'Fast') {
          rate = 1.25;
        }
        _player.playUrl(_lastAudioUrl!, rate: rate);
      }
    }
  }

  Future<void> _sendSilence({required int durationMs}) async {
    final bytesPerSecond = audioSampleRate * audioChannels * audioSampleWidth;
    final totalBytes = (bytesPerSecond * durationMs / 1000).round();
    final chunkSize = (bytesPerSecond * 0.2).round();

    int sent = 0;
    while (sent < totalBytes) {
      final size = (totalBytes - sent) < chunkSize
          ? (totalBytes - sent)
          : chunkSize;
      _ws.sendBytes(Uint8List(size));
      sent += size;
      await Future.delayed(const Duration(milliseconds: 20));
    }
  }

  Future<void> playLastAudio() async {
    final url = _lastAudioUrl;
    if (url == null) {
      return;
    }
    final speedStr = SettingsController.instance.voiceSpeed;
    double rate = 1.0;
    if (speedStr == 'Slow') {
      rate = 0.8;
    } else if (speedStr == 'Fast') {
      rate = 1.25;
    }
    await _player.playUrl(url, rate: rate);
  }

  Future<void> copyTranslation() async {
    if (messages.isEmpty || messages.last.translation.isEmpty) {
      return;
    }
    await Clipboard.setData(ClipboardData(text: messages.last.translation));
  }

  void saveTranslation() {
    // Placeholder: hook into history storage when available.
  }

  Future<void> flagMessage(String messageId) async {
    try {
      final msg = messages.firstWhere((m) => m.id == messageId);
      if (msg.translation.isEmpty) return;
      
      final repo = TranslateRepository();
      await repo.flagTranslation(
        sourceText: msg.text,
        translatedText: msg.translation,
        clientId: clientId,
      );
    } catch (e) {
      debugPrint('Error flagging message: $e');
      rethrow;
    }
  }

  // [NEW] Tự động lưu bản dịch vào Hive khi nhận kết quả từ WebSocket
  void _autoSaveToHistory({
    required String originalText,
    required String translatedText,
  }) {
    try {
      final box = Hive.box<HistoryModel>('history');
      final now = DateTime.now();
      final timeStr =
          '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';

      final item = HistoryModel(
        id: now.millisecondsSinceEpoch.toString(),
        originalText: originalText,
        translatedText: translatedText,
        time: timeStr,
        fromFlag: currentSourceLang == 'vi' ? '🇻🇳' : '🇺🇸',
        toFlag: currentTargetLang == 'eng_Latn' ? '🇺🇸' : '🇻🇳',
      );
      box.add(item);
      debugPrint('[NEW] Auto-saved to history: $originalText → $translatedText');
    } catch (e) {
      debugPrint('[NEW] Auto-save history error: $e');
    }
  }

  @override
  void dispose() {
    SettingsController.instance.removeListener(_onSettingsChanged);
    _audioSub?.cancel();
    _wsSub?.cancel();
    _audio.dispose();
    _player.dispose();
    _ws.close();
    super.dispose();
  }
}

class TextTranslateController extends ChangeNotifier {
  final TranslateRepository _repository;

  TextTranslateController({TranslateRepository? repository})
    : _repository = repository ?? TranslateRepository();

  bool isLoading = false;
  String translatedText = '';
  String? errorMessage;

  Future<void> translateText({
    required String text,
    required String sourceLang,
    required String targetLang,
  }) async {
    if (text.trim().isEmpty) {
      translatedText = '';
      errorMessage = 'Text is required.';
      notifyListeners();
      return;
    }

    isLoading = true;
    errorMessage = null;
    notifyListeners();

    try {
      translatedText = await _repository.translateText(
        text: text,
        sourceLang: sourceLang,
        targetLang: targetLang,
      );
    } catch (error) {
      errorMessage = error.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> flagTranslation(String sourceText, String translatedText) async {
    try {
      await _repository.flagTranslation(
        sourceText: sourceText,
        translatedText: translatedText,
        clientId: 'text_client',
      );
    } catch (e) {
      debugPrint('Error flagging translation: $e');
      rethrow;
    }
  }
}
