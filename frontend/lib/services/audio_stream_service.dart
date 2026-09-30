import 'dart:async';
import 'dart:typed_data';

import 'package:record/record.dart';

class MicrophonePermissionException implements Exception {}

class AudioStreamService {
  final AudioRecorder _record = AudioRecorder();
  Future<void> _operations = Future.value();
  int _generation = 0;

  Future<T> _serialize<T>(Future<T> Function() operation) {
    final next = _operations.then((_) => operation());
    _operations = next.then<void>((_) {}, onError: (Object _, StackTrace _) {});
    return next;
  }

  Future<Stream<Uint8List>> startStream({
    required int sampleRate,
    required int channels,
  }) {
    final generation = ++_generation;
    return _serialize(() async {
      final hasPermission = await _record.hasPermission();
      if (generation != _generation) {
        throw StateError('Microphone start cancelled');
      }
      if (!hasPermission) throw MicrophonePermissionException();

      const encoder = AudioEncoder.pcm16bits;
      final config = RecordConfig(
        encoder: encoder,
        sampleRate: sampleRate,
        numChannels: channels,
        noiseSuppress: true,
        echoCancel: true,
      );

      final stream = await _record.startStream(config);
      if (generation != _generation) {
        await _record.stop();
        throw StateError('Microphone start cancelled');
      }
      return stream;
    });
  }

  Future<void> stop() {
    _generation++;
    return _serialize(() async {
      await _record.stop();
    });
  }

  Future<void> dispose() {
    _generation++;
    return _serialize(_record.dispose);
  }
}
