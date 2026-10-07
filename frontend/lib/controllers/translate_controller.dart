import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../services/auth_session_service.dart';
import '../services/history_storage_service.dart';
import '../models/history.dart';

import '../core/constants.dart';
import '../core/app_localizations.dart';
import '../services/audio_player_service.dart';
import '../services/audio_stream_service.dart';
import '../services/mic_state_machine.dart';
import '../services/websocket_service.dart';
import '../repositories/translate_repository.dart';
import '../models/chat_message.dart';
import 'settings_controller.dart';

class TranslationLogic extends ChangeNotifier {
  final RealtimeWebSocketService _ws;
  final AudioCapture _audio;
  final AudioPlayerService _player;
  static TranslationLogic? _microphoneOwner;
  static Future<void> _microphoneQueue = Future.value();
  final Set<String> _cancelledTurns = {};
  final Set<String> _flaggingMessages = {};
  final String _historyNamespace = DateTime.now().microsecondsSinceEpoch
      .toString();
  final MicStateMachine mic = MicStateMachine();

  bool isRecording = false;

  // State for Chat Messages
  List<ChatMessage> messages = [];

  bool _starting = false;
  bool _disposed = false;
  int _recordingGeneration = 0;
  String? _errorMessage;
  Timer? _errorTimer;
  String? activeTurnId;

  String? get errorMessage => _errorMessage;
  set errorMessage(String? value) {
    _errorTimer?.cancel();
    _errorTimer = null;
    _errorMessage = value;
    if (value != null && !_disposed) {
      _errorTimer = Timer(const Duration(seconds: 4), () {
        if (!_disposed && _errorMessage == value) {
          _errorMessage = null;
          notifyListeners();
        }
      });
    }
  }

  // Language Config
  String currentSourceLang = 'vi';
  String currentTargetLang = 'eng_Latn';
  bool isMeSpeaking = true;

  StreamSubscription<dynamic>? _wsSub;
  StreamSubscription<Uint8List>? _audioSub;

  TranslationLogic({
    RealtimeWebSocketService? websocket,
    AudioCapture? audio,
    AudioPlayerService? player,
  }) : _ws = websocket ?? RealtimeWebSocketService(),
       _audio = audio ?? AudioStreamService(),
       _player = player ?? AudioPlayerService() {
    mic.addListener(_onMicChanged);
    _initLanguagesFromSettings();
    SettingsController.instance.addListener(_onSettingsChanged);
    AuthSessionService.instance.addListener(_onAuthChanged);
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
    // UI preferences and playback speed never overwrite the selected direction.
    if (!_disposed) notifyListeners();
  }

  void _onMicChanged() {
    if (!_disposed) notifyListeners();
  }

  bool get isMicBusy => mic.isStarting || mic.isStopping;
  bool get isFlagging => _flaggingMessages.isNotEmpty;

  Future<void> _claimMicrophone(int generation) {
    final claim = _microphoneQueue.then((_) async {
      if (_disposed || generation != _recordingGeneration) return;
      final previous = _microphoneOwner;
      if (previous != null && previous != this) {
        await previous.cancelRecording();
      }
      if (!_disposed && generation == _recordingGeneration) {
        _microphoneOwner = this;
      }
    });
    _microphoneQueue = claim.catchError((Object _) {});
    return claim;
  }

  void _rememberCancelledTurn(String turnId) {
    _cancelledTurns.add(turnId);
    // A long-running app must not retain every historical turn forever.
    while (_cancelledTurns.length > 128) {
      _cancelledTurns.remove(_cancelledTurns.first);
    }
  }

  void swapLanguages() {
    if (mic.isActive || activeTurnId != null) {
      unawaited(cancelRecording());
    }
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
    if (mic.isStarting) {
      await cancelRecording();
    } else if (isRecording || mic.isRecording) {
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
    if (_disposed ||
        mic.isActive ||
        mic.isStopping ||
        AuthSessionService.instance.isSuspended) {
      return;
    }

    if (sourceLang != null) currentSourceLang = sourceLang;
    if (targetLang != null) currentTargetLang = targetLang;
    if (isMe != null) isMeSpeaking = isMe;

    errorMessage = null;
    notifyListeners();

    await mic.start(() async {
      _starting = true;
      final generation = ++_recordingGeneration;
      final turnId =
          '${DateTime.now().millisecondsSinceEpoch}-$_recordingGeneration';

      try {
        // Barge-in is latest-turn-wins: invalidate and stop previous playback
        // before opening the microphone so TTS cannot leak into the next STT.
        final supersededTurnId = activeTurnId;
        if (supersededTurnId != null && supersededTurnId != turnId) {
          _rememberCancelledTurn(supersededTurnId);
          if (_ws.isConnected) {
            _ws.cancelTurn(turnId: supersededTurnId);
          }
        }
        activeTurnId = turnId;
        await _player.setActiveTurn(turnId);
        if (_disposed || generation != _recordingGeneration) return;

        await _claimMicrophone(generation);
        if (_disposed ||
            generation != _recordingGeneration ||
            _microphoneOwner != this) {
          return;
        }
        await _connectIfNeeded();
        if (_disposed ||
            generation != _recordingGeneration ||
            !_ws.isConnected) {
          throw Exception('Connection not established');
        }

        final stream = await _audio.startStream(
          sampleRate: audioSampleRate,
          channels: audioChannels,
        );

        if (_disposed ||
            generation != _recordingGeneration ||
            !_ws.isConnected) {
          await _audio.stop();
          throw Exception('Connection aborted after stream start');
        }

        isRecording = true;
        notifyListeners();

        // Protocol v2: signal start of turn with immutable turn metadata
        _ws.startTurn(
          turnId: turnId,
          speaker: isMeSpeaking ? 'me' : 'partner',
          sourceLang: currentSourceLang,
          targetLang: currentTargetLang,
        );

        _audioSub = stream.listen(
          (chunk) {
            if (!isRecording) {
              return;
            }
            _ws.sendBytes(chunk);
          },
          onError: (error) {
            unawaited(stopRecording());
          },
        );
      } catch (error) {
        if (_disposed || generation != _recordingGeneration) return;
        await _audio.stop();
        if (activeTurnId == turnId) activeTurnId = null;
        await _player.clearQueueForTurn(turnId);
        if (_microphoneOwner == this) _microphoneOwner = null;
        errorMessage = error is SessionException
            ? error.message
            : error is MicrophonePermissionException
            ? tr('microphone_denied')
            : tr('microphone_connection_error');
        rethrow;
      } finally {
        _starting = false;
        if (!_disposed) notifyListeners();
      }
    });
  }

  Future<void> stopRecording({bool sendSilence = false}) async {
    final endingTurnId = activeTurnId;
    _recordingGeneration++;

    await mic.stop(() async {
      // Keep the subscription alive until the recorder has flushed its final
      // PCM chunk. Short commands often carry their last consonant there.
      await _audio.stop();
      await _audioSub?.cancel();
      _audioSub = null;

      isRecording = false;
      if (!_disposed) notifyListeners();

      if (_ws.isConnected && endingTurnId != null) {
        // Protocol v2: explicitly end turn without artificial silence
        _ws.endTurn(turnId: endingTurnId);
      }
    });
  }

  Future<void> cancelRecording() async {
    final cancellingTurnId = activeTurnId;
    if (cancellingTurnId != null) _rememberCancelledTurn(cancellingTurnId);
    activeTurnId = null;
    _recordingGeneration++;

    await mic.stop(() async {
      isRecording = false;
      if (!_disposed) notifyListeners();

      await _audioSub?.cancel();
      _audioSub = null;
      await _audio.stop();
    });
    // Cancellation also applies after mic stop while STT/TTS is still running.
    if (_ws.isConnected && cancellingTurnId != null) {
      _ws.cancelTurn(turnId: cancellingTurnId);
    }
    if (cancellingTurnId != null) {
      await _player.clearQueueForTurn(cancellingTurnId);
    } else {
      await _player.stop();
    }
    if (_microphoneOwner == this) _microphoneOwner = null;
  }

  void _onAuthChanged() {
    if (AuthSessionService.instance.isSuspended ||
        AuthSessionService.instance.currentToken == null) {
      unawaited(cancelRecording());
    }
  }

  Future<void> _connectIfNeeded() async {
    final payload = {
      'type': 'config',
      'sample_rate': audioSampleRate,
      'channels': audioChannels,
      'sample_width': audioSampleWidth,
      'source_lang': currentSourceLang,
      'target_lang': currentTargetLang,
      'protocol_version': 2,
    };

    _ws.setConfigPayload(payload);
    _wsSub ??= _ws.stream.listen(
      _handleMessage,
      onError: (Object error) {
        if (isRecording || _starting) {
          errorMessage = error is SessionException
              ? error.message
              : tr('connection_interrupted');
          unawaited(cancelRecording());
          if (!_disposed) notifyListeners();
        }
      },
      onDone: () {
        if (isRecording || _starting) {
          unawaited(cancelRecording());
        }
      },
    );
    await _ws.connect(wsBaseUrl);
  }

  void _handleMessage(dynamic message) {
    if (_disposed || message is! String) {
      return;
    }

    Map<String, dynamic> data;
    try {
      data = jsonDecode(message) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Invalid realtime message.');
      return;
    }
    final type = data['type'];
    if (_cancelledTurns.contains(data['turn_id'])) return;

    if (type == 'status') {
      if (data['status'] == 'busy') {
        errorMessage = tr('server_busy');
        // Finish accepted sentences; the last rejected sentence can be retried.
        if (mic.isActive) unawaited(stopRecording());
        notifyListeners();
      }
      return;
    }

    if (type == 'error') {
      final turnId = data['turn_id'] as String?;
      final code = data['code'];
      // A turn may contain several utterances. Silence in a later one must
      // not discard an earlier successful translation or its audio.
      if (code == 'no_speech_detected' &&
          turnId != null &&
          messages.any((message) => message.turnId == turnId)) {
        return;
      }
      errorMessage = switch (data['code']) {
        'no_speech_detected' => tr('no_speech_detected'),
        'stt_unavailable' => tr('stt_unavailable'),
        'translation_unavailable' => tr('translation_unavailable'),
        'tts_unavailable' => tr('tts_unavailable'),
        _ => tr('session_request_failed'),
      };
      for (var i = 0; i < messages.length; i++) {
        if (turnId == null || messages[i].turnId == turnId) {
          messages[i] = messages[i].copyWith(isDraft: false);
        }
      }
      if (code != 'no_speech_detected' &&
          mic.isActive &&
          (turnId == null || turnId == activeTurnId)) {
        unawaited(cancelRecording());
      }
      notifyListeners();
      return;
    }

    if (type == 'stt') {
      final text = (data['data']?['text'] ?? '') as String;
      final msgId = (data['message_id'] ?? '') as String;
      final turnId = (data['turn_id'] ?? '') as String;
      final speaker = (data['speaker'] ?? '') as String;
      final srcLang = (data['source_lang'] ?? currentSourceLang) as String;
      final tgtLang = (data['target_lang'] ?? currentTargetLang) as String;

      if (text.trim().isEmpty) return;

      // Speaker and language bound to immutable turn metadata
      final msgIsMe = speaker.isNotEmpty ? (speaker == 'me') : isMeSpeaking;

      final existingIdx = messages.indexWhere((m) => m.id == msgId);
      if (existingIdx >= 0) {
        messages[existingIdx] = messages[existingIdx].copyWith(text: text);
      } else {
        messages.add(
          ChatMessage(
            id: msgId,
            text: text,
            translation: '',
            isMe: msgIsMe,
            isDraft: true,
            turnId: turnId.isNotEmpty ? turnId : null,
            sourceLang: srcLang,
            targetLang: tgtLang,
          ),
        );
      }
      notifyListeners();
      return;
    }

    if (type == 'translation') {
      final translated = (data['data']?['translated_text'] ?? '') as String;
      final msgId = (data['message_id'] ?? '') as String;

      final existingIdx = messages.indexWhere((m) => m.id == msgId);
      if (existingIdx >= 0) {
        final originalMsg = messages[existingIdx];
        messages[existingIdx] = originalMsg.copyWith(
          translation: translated,
          isDraft: false,
          qaAudioToken: data['data']?['qa_audio_token'] as String?,
        );

        unawaited(_autoSaveToHistory(messages[existingIdx]));
      }
      notifyListeners();
      return;
    }

    if (type == 'audio_chunk') {
      final b64 = data['audio_data'] as String?;
      final turnId = data['turn_id'] as String?;
      if (b64 != null && b64.isNotEmpty) {
        final Uint8List wavBytes;
        try {
          wavBytes = base64Decode(b64);
        } on FormatException {
          debugPrint('Invalid audio response.');
          return;
        }

        final speedStr = SettingsController.instance.voiceSpeed;
        double rate = 1.0;
        if (speedStr == 'Slow') {
          rate = 0.8;
        } else if (speedStr == 'Fast') {
          rate = 1.25;
        }

        // Isolated playback queue: chunks from cancelled turns are rejected
        _player.enqueueChunk(wavBytes, turnId: turnId, rate: rate);
      }
      return;
    }

    if (type == 'turn_complete') {
      final turnId = data['turn_id'] as String?;
      _player.completeTurn(turnId);
      if (turnId == activeTurnId) activeTurnId = null;
      notifyListeners();
    }
  }

  Future<bool> playLastAudio() => _player.replayLastTurn(
    rate: switch (SettingsController.instance.voiceSpeed) {
      'Slow' => 0.8,
      'Fast' => 1.25,
      _ => 1.0,
    },
  );

  Future<void> copyTranslation() async {
    if (messages.isEmpty || messages.last.translation.isEmpty) {
      return;
    }
    await Clipboard.setData(ClipboardData(text: messages.last.translation));
  }

  Future<HistorySaveResult> saveTranslation({ChatMessage? message}) async {
    final candidate = message ?? messages.lastOrNull;
    if (candidate == null || candidate.isDraft) {
      return HistorySaveResult.empty;
    }
    return _saveMessage(candidate);
  }

  Future<void> flagMessage(String messageId) async {
    if (!_flaggingMessages.add(messageId)) return;
    notifyListeners();
    try {
      final msg = messages.firstWhere((m) => m.id == messageId);
      if (msg.translation.isEmpty) return;

      final repo = TranslateRepository();
      await repo.flagTranslation(
        sourceText: msg.text,
        translatedText: msg.translation,
        sourceLang: msg.sourceLang ?? currentSourceLang,
        targetLang: msg.targetLang ?? currentTargetLang,
        inputMode: 'voice',
        qaAudioToken: msg.qaAudioToken,
      );
    } catch (e) {
      debugPrint('Flag request failed.');
      rethrow;
    } finally {
      _flaggingMessages.remove(messageId);
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> _autoSaveToHistory(ChatMessage message) async {
    try {
      await _saveMessage(message);
    } catch (_) {
      errorMessage = tr('history_save_failed');
      if (!_disposed) notifyListeners();
    }
  }

  Future<HistorySaveResult> _saveMessage(ChatMessage message) {
    final now = DateTime.now();
    final src = message.sourceLang ?? currentSourceLang;
    final tgt = message.targetLang ?? currentTargetLang;
    return HistoryStorageService.instance.save(
      HistoryModel(
        id: '$_historyNamespace:${message.turnId ?? ""}:${message.id}',
        savedAtEpochMs: now.millisecondsSinceEpoch,
        originalText: message.text,
        translatedText: message.translation,
        time:
            '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}',
        fromFlag: src == 'vi' || src == 'vie_Latn' ? '🇻🇳' : '🇺🇸',
        toFlag: tgt == 'en' || tgt == 'eng_Latn' ? '🇺🇸' : '🇻🇳',
      ),
    );
  }

  @override
  void dispose() {
    _disposed = true;
    _errorTimer?.cancel();
    _recordingGeneration++;
    if (_microphoneOwner == this) _microphoneOwner = null;
    mic.removeListener(_onMicChanged);
    mic.reset();
    mic.dispose();
    AuthSessionService.instance.removeListener(_onAuthChanged);
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
  String? _errorMessage;
  Timer? _errorTimer;

  String? get errorMessage => _errorMessage;
  set errorMessage(String? value) {
    _errorTimer?.cancel();
    _errorTimer = null;
    _errorMessage = value;
    if (value != null) {
      _errorTimer = Timer(const Duration(seconds: 4), () {
        if (_errorMessage == value) {
          _errorMessage = null;
          notifyListeners();
        }
      });
    }
  }

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
        inputMode: 'text',
      );
    } catch (e) {
      debugPrint('Flag request failed.');
      rethrow;
    }
  }

  @override
  void dispose() {
    _errorTimer?.cancel();
    super.dispose();
  }
}
