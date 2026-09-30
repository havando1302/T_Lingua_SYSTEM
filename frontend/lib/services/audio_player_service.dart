import 'dart:async';
import 'dart:collection';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';

class _AudioChunk {
  final Uint8List bytes;
  final double rate;
  _AudioChunk(this.bytes, this.rate);
}

class AudioPlayerService {
  final AudioPlayer _player;
  final Queue<_AudioChunk> _audioQueue = Queue<_AudioChunk>();
  final List<Uint8List> _turnChunks = [];
  List<Uint8List> _lastCompleteTurnChunks = [];
  late final StreamSubscription<void> _completion;
  Future<void> _commands = Future.value();
  bool _isPlaying = false;
  bool _disposed = false;
  int _generation = 0;
  String? _activeTurnId;

  AudioPlayerService({AudioPlayer? player})
    : _player = player ?? AudioPlayer() {
    _completion = _player.onPlayerComplete.listen((_) {
      _isPlaying = false;
      _playNext();
    });
  }

  String? get activeTurnId => _activeTurnId;
  List<Uint8List> get lastCompleteTurnChunks =>
      List.unmodifiable(_lastCompleteTurnChunks);
  // Backward compatibility for single-file consumers. Multiple complete WAV
  // files must never be byte-concatenated into a supposedly valid WAV file.
  Uint8List? get lastCompleteTurnAudio => _lastCompleteTurnChunks.length == 1
      ? _lastCompleteTurnChunks.single
      : null;

  void _schedule(Future<void> Function() action) {
    _commands = _commands.then((_) => action()).catchError((Object _) {
      _isPlaying = false;
    });
  }

  void setActiveTurn(String turnId) {
    if (_activeTurnId == turnId) return;
    _generation++;
    _activeTurnId = turnId;
    _audioQueue.clear();
    _turnChunks.clear();
    _lastCompleteTurnChunks = [];
    _isPlaying = false;
    _schedule(_player.stop);
  }

  Future<void> playUrl(String url, {double rate = 1.0}) async {
    await clearQueue();
    if (_disposed) return;
    _schedule(() async {
      await _player.setPlaybackRate(rate);
      await _player.play(UrlSource(url));
    });
    await _commands;
  }

  void enqueueChunk(Uint8List wavBytes, {String? turnId, double rate = 1.0}) {
    if (_disposed || wavBytes.isEmpty) return;
    // A cancelled turn has no active ID; late chunks must not revive it.
    if (turnId != null && turnId != _activeTurnId) return;
    _audioQueue.add(_AudioChunk(wavBytes, rate));
    if (turnId != null) _turnChunks.add(wavBytes);
    _playNext();
  }

  void completeTurn(String? turnId) {
    if (_activeTurnId != null && turnId == _activeTurnId) {
      _lastCompleteTurnChunks = List.of(_turnChunks);
    }
  }

  Future<bool> replayLastTurn({double rate = 1.0}) async {
    if (_lastCompleteTurnChunks.isEmpty || _disposed) return false;
    final chunks = List<Uint8List>.of(_lastCompleteTurnChunks);
    await clearQueue();
    if (_disposed) return false;
    for (final bytes in chunks) {
      _audioQueue.add(_AudioChunk(bytes, rate));
    }
    _playNext();
    return true;
  }

  void _playNext() {
    if (_disposed || _isPlaying || _audioQueue.isEmpty) return;
    _isPlaying = true;
    final chunk = _audioQueue.removeFirst();
    final generation = _generation;
    _schedule(() async {
      if (_disposed || generation != _generation) return;
      await _player.setPlaybackRate(chunk.rate);
      if (_disposed || generation != _generation) return;
      await _player.play(BytesSource(chunk.bytes));
    });
  }

  Future<void> clearQueueForTurn(String turnId) async {
    if (_activeTurnId != turnId) return;
    _activeTurnId = null;
    _lastCompleteTurnChunks = [];
    await clearQueue();
  }

  Future<void> clearQueue() async {
    _generation++;
    _audioQueue.clear();
    _turnChunks.clear();
    _isPlaying = false;
    _schedule(_player.stop);
    await _commands;
  }

  Future<void> stop() => clearQueue();

  Future<void> dispose() async {
    _disposed = true;
    await _completion.cancel();
    await clearQueue();
    await _player.dispose();
  }
}
