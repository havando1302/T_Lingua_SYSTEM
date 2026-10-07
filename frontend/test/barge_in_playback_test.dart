import 'dart:async';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:t_lingua/controllers/translate_controller.dart';
import 'package:t_lingua/services/audio_player_service.dart';
import 'package:t_lingua/services/audio_stream_service.dart';
import 'package:t_lingua/services/websocket_service.dart';

class _FakePlayback implements AudioPlayback {
  final StreamController<void> completions = StreamController<void>.broadcast();
  Completer<void>? stopGate;
  int playCalls = 0;
  int stopCalls = 0;

  @override
  Stream<void> get onPlayerComplete => completions.stream;

  @override
  Future<void> setPlaybackRate(double rate) async {}

  @override
  Future<void> play(Source source) async {
    playCalls++;
  }

  @override
  Future<void> stop() async {
    stopCalls++;
    final gate = stopGate;
    if (gate != null) await gate.future;
  }

  @override
  Future<void> dispose() => completions.close();
}

class _FakeAudioStreamService implements AudioCapture {
  final StreamController<Uint8List> audio = StreamController<Uint8List>();
  int startCalls = 0;

  @override
  Future<Stream<Uint8List>> startStream({
    required int sampleRate,
    required int channels,
  }) async {
    startCalls++;
    return audio.stream;
  }

  @override
  Future<void> stop() async {}

  @override
  Future<void> dispose() => audio.close();
}

class _FakeWebSocketService extends RealtimeWebSocketService {
  final StreamController<dynamic> events =
      StreamController<dynamic>.broadcast();
  final List<String> startedTurns = [];
  final List<String> cancelledTurns = [];
  bool connected = true;

  @override
  bool get isConnected => connected;

  @override
  Stream<dynamic> get stream => events.stream;

  @override
  void setConfigPayload(Map<String, dynamic> payload) {}

  @override
  Future<void> connect(String url) async {
    connected = true;
  }

  @override
  void startTurn({
    required String turnId,
    required String speaker,
    required String sourceLang,
    required String targetLang,
  }) {
    startedTurns.add(turnId);
  }

  @override
  void cancelTurn({required String turnId}) {
    cancelledTurns.add(turnId);
  }

  @override
  void sendBytes(Uint8List bytes) {}

  @override
  void endTurn({required String turnId}) {}

  @override
  Future<void> close() async {
    connected = false;
    await events.close();
    await super.close();
  }
}

Future<void> _flushAsync() => Future<void>.delayed(Duration.zero);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('switching turns stops playback and rejects late old chunks', () async {
    final playback = _FakePlayback();
    final player = AudioPlayerService(playback: playback);

    await player.setActiveTurn('turn-1');
    player.enqueueChunk(Uint8List.fromList([1]), turnId: 'turn-1');
    await _flushAsync();
    expect(playback.playCalls, 1);

    final gate = Completer<void>();
    playback.stopGate = gate;
    var interruptionFinished = false;
    final interruption = player.setActiveTurn('turn-2').then((_) {
      interruptionFinished = true;
    });
    await _flushAsync();

    expect(playback.stopCalls, 2);
    expect(interruptionFinished, isFalse);
    player.enqueueChunk(Uint8List.fromList([2]), turnId: 'turn-1');
    gate.complete();
    await interruption;
    await _flushAsync();
    expect(
      playback.playCalls,
      1,
      reason: 'late audio from turn 1 must be discarded',
    );

    player.enqueueChunk(Uint8List.fromList([3]), turnId: 'turn-2');
    await _flushAsync();
    expect(playback.playCalls, 2);
    await player.dispose();
  });

  test('microphone waits for playback interruption before recording', () async {
    final playback = _FakePlayback();
    final gate = Completer<void>();
    playback.stopGate = gate;
    final player = AudioPlayerService(playback: playback);
    final audio = _FakeAudioStreamService();
    final websocket = _FakeWebSocketService();
    final logic = TranslationLogic(
      websocket: websocket,
      audio: audio,
      player: player,
    );

    final starting = logic.startRecording(
      sourceLang: 'vi',
      targetLang: 'eng_Latn',
      isMe: true,
    );
    await _flushAsync();

    expect(playback.stopCalls, 1);
    expect(
      audio.startCalls,
      0,
      reason: 'the mic must not capture outgoing TTS',
    );
    expect(websocket.startedTurns, isEmpty);

    gate.complete();
    await starting;
    expect(audio.startCalls, 1);
    expect(websocket.startedTurns, hasLength(1));
    expect(logic.isRecording, isTrue);

    playback.stopGate = null;
    await logic.cancelRecording();
    logic.dispose();
    await _flushAsync();
  });
}
