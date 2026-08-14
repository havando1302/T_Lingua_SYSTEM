import 'dart:typed_data';

import 'package:record/record.dart';

class AudioStreamService {
  final AudioRecorder _record = AudioRecorder();

  Future<Stream<Uint8List>> startStream({
    required int sampleRate,
    required int channels,
  }) async {
    final hasPermission = await _record.hasPermission();
    if (!hasPermission) {
      throw Exception('Microphone permission denied');
    }

    const encoder = AudioEncoder.pcm16bits;
    final config = RecordConfig(
      encoder: encoder,
      sampleRate: sampleRate,
      numChannels: channels,
    );

    return _record.startStream(config);
  }

  Future<void> stop() async {
    await _record.stop();
  }

  Future<void> dispose() async {
    await _record.dispose();
  }
}
