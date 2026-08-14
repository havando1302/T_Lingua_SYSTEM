import 'package:audioplayers/audioplayers.dart';

class AudioPlayerService {
  final AudioPlayer _player = AudioPlayer();

  Future<void> playUrl(String url, {double rate = 1.0}) async {
    await _player.stop();
    await _player.setPlaybackRate(rate);
    await _player.play(UrlSource(url));
  }

  Future<void> stop() async {
    await _player.stop();
  }

  Future<void> dispose() async {
    await _player.dispose();
  }
}
