import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:t_lingua/controllers/settings_controller.dart';
import 'package:t_lingua/controllers/translate_controller.dart';
import 'package:t_lingua/core/app_localizations.dart';
import 'package:t_lingua/core/constants.dart';
import 'package:t_lingua/models/history.dart';
import 'package:t_lingua/services/audio_player_service.dart';
import 'package:t_lingua/services/audio_stream_service.dart';
import 'package:t_lingua/services/auth_session_service.dart';
import 'package:t_lingua/services/history_storage_service.dart';
import 'package:t_lingua/services/secure_history_box.dart';
import 'package:t_lingua/services/websocket_service.dart';
import 'package:t_lingua/ui/pages/setting_screen.dart';

class _FakePlayback implements AudioPlayback {
  final completions = StreamController<void>.broadcast();
  final rates = <double>[];

  @override
  Stream<void> get onPlayerComplete => completions.stream;

  @override
  Future<void> setPlaybackRate(double rate) async => rates.add(rate);

  @override
  Future<void> play(Source source) async {}

  @override
  Future<void> stop() async {}

  @override
  Future<void> dispose() => completions.close();
}

class _FakeAudioCapture implements AudioCapture {
  final audio = StreamController<Uint8List>();

  @override
  Future<Stream<Uint8List>> startStream({
    required int sampleRate,
    required int channels,
  }) async => audio.stream;

  @override
  Future<void> stop() async {}

  @override
  Future<void> dispose() => audio.close();
}

class _FakeWebSocket extends RealtimeWebSocketService {
  final events = StreamController<dynamic>.broadcast();
  bool connected = true;

  @override
  bool get isConnected => connected;

  @override
  Stream<dynamic> get stream => events.stream;

  @override
  void setConfigPayload(Map<String, dynamic> payload) {}

  @override
  Future<void> connect(String url) async => connected = true;

  @override
  void startTurn({
    required String turnId,
    required String speaker,
    required String sourceLang,
    required String targetLang,
  }) {}

  @override
  void cancelTurn({required String turnId}) {}

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

HistoryModel _history(String id, {int? savedAtEpochMs}) => HistoryModel(
  id: id,
  originalText: 'nguồn $id',
  translatedText: 'target $id',
  time: 'now',
  fromFlag: 'vi',
  toFlag: 'en',
  savedAtEpochMs: savedAtEpochMs,
);

Future<void> _flushAsync() => Future<void>.delayed(Duration.zero);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory hiveDirectory;
  late Box<String> settingsBox;
  late Box<HistoryModel> historyBox;

  setUpAll(() async {
    hiveDirectory = await Directory.systemTemp.createTemp('tlingua-settings-');
    Hive.init(hiveDirectory.path);
    if (!Hive.isAdapterRegistered(0)) {
      Hive.registerAdapter(HistoryModelAdapter());
    }
    settingsBox = await Hive.openBox<String>('settings');
    historyBox = await Hive.openBox<HistoryModel>(secureHistoryBoxName);
  });

  setUp(() async {
    await settingsBox.clear();
    await historyBox.clear();
    AppLocalizations.instance.init('vi');
    SettingsController.instance.init();
  });

  tearDownAll(() async {
    await Hive.close();
    await hiveDirectory.delete(recursive: true);
  });

  test(
    'settings persist and reload with validated retention and locale',
    () async {
      final settings = SettingsController.instance;
      await settings.setVoiceSpeed('Fast');
      await settings.setVoiceGender('Male');
      await settings.setLanguage('en');
      await settings.setHistoryEnabled(true);
      await settings.setHistoryRetentionDays(14);

      await settingsBox.close();
      settingsBox = await Hive.openBox<String>('settings');
      settings.init();

      expect(settings.voiceSpeed, 'Fast');
      expect(settings.voiceGender, 'Male');
      expect(settings.language, 'en');
      expect(settings.historyEnabled, isTrue);
      expect(settings.historyRetentionDays, 14);
      expect(AppLocalizations.instance.locale, 'en');
      expect(AppLocalizations.instance.tr('settings'), 'Settings');
      expect(
        () => settings.setHistoryRetentionDays(0),
        throwsA(isA<ArgumentError>()),
      );
      await settings.setLanguage('unsupported');
      expect(settings.language, 'en');
    },
  );

  test('voice speed changes live and replay playback rates', () async {
    final playback = _FakePlayback();
    final player = AudioPlayerService(playback: playback);
    final audio = _FakeAudioCapture();
    final websocket = _FakeWebSocket();
    final logic = TranslationLogic(
      websocket: websocket,
      audio: audio,
      player: player,
    );

    await SettingsController.instance.setVoiceSpeed('Fast');
    await logic.startRecording();
    final turnId = logic.activeTurnId!;
    websocket.events.add(
      jsonEncode({
        'type': 'audio_chunk',
        'turn_id': turnId,
        'audio_data': base64Encode(<int>[1, 2, 3]),
      }),
    );
    await _flushAsync();
    expect(playback.rates.last, 1.25);

    websocket.events.add(
      jsonEncode({'type': 'turn_complete', 'turn_id': turnId}),
    );
    playback.completions.add(null);
    await _flushAsync();
    await SettingsController.instance.setVoiceSpeed('Slow');
    expect(await logic.playLastAudio(), isTrue);
    await _flushAsync();
    expect(playback.rates.last, 0.8);

    await logic.cancelRecording();
    logic.dispose();
    await _flushAsync();
  });

  test(
    'history opt-in, retention, legacy preservation and clear all work',
    () async {
      final service = HistoryStorageService.instance;
      final now = DateTime.now();

      expect(
        await service.save(_history('disabled')),
        HistorySaveResult.disabled,
      );
      await SettingsController.instance.setHistoryEnabled(true);
      expect(await service.save(_history('saved')), HistorySaveResult.saved);
      expect(
        await service.save(_history('saved')),
        HistorySaveResult.alreadySaved,
      );

      await SettingsController.instance.setHistoryRetentionDays(7);
      await historyBox.put(
        'expired',
        _history(
          'expired',
          savedAtEpochMs: now
              .subtract(const Duration(days: 8))
              .millisecondsSinceEpoch,
        ),
      );
      await historyBox.put(
        'recent',
        _history(
          'recent',
          savedAtEpochMs: now
              .subtract(const Duration(days: 6))
              .millisecondsSinceEpoch,
        ),
      );
      await historyBox.put('legacy', _history('legacy'));

      await service.prune();
      expect(historyBox.containsKey('expired'), isFalse);
      expect(historyBox.containsKey('recent'), isTrue);
      expect(historyBox.containsKey('legacy'), isTrue);

      await service.clearAllByUser();
      expect(historyBox, isEmpty);
    },
  );

  testWidgets(
    'settings screen controls, confirmations and disabled rows behave',
    (tester) async {
      var clearHistoryCalls = 0;
      await tester.pumpWidget(
        MaterialApp(
          home: SettingsScreen(
            clearHistory: () async => clearHistoryCalls++,
            persistSettings: false,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Tốc độ giọng nói'), findsOneWidget);
      expect(find.text('Giới tính giọng nói'), findsOneWidget);
      expect(find.text('Chế độ AI'), findsOneWidget);

      await tester.tap(find.text('Giới tính giọng nói'));
      await tester.pumpAndSettle();
      expect(find.byType(BottomSheet), findsNothing);
      await tester.tap(find.text('Chế độ AI'));
      await tester.pumpAndSettle();
      expect(find.byType(BottomSheet), findsNothing);

      await tester.tap(find.text('Tốc độ giọng nói'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Nhanh').last);
      await tester.pumpAndSettle();
      expect(SettingsController.instance.voiceSpeed, 'Fast');

      await tester.tap(find.text('Ngôn ngữ ứng dụng'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Tiếng Anh').last);
      await tester.pumpAndSettle();
      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('App Language'), findsOneWidget);

      final historySwitch = find.byType(Switch);
      await tester.ensureVisible(historySwitch);
      await tester.tap(historySwitch);
      await tester.pumpAndSettle();
      expect(find.text('Enable history saving?'), findsOneWidget);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(SettingsController.instance.historyEnabled, isFalse);

      await tester.tap(historySwitch);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Agree'));
      await tester.pumpAndSettle();
      expect(SettingsController.instance.historyEnabled, isTrue);

      await tester.scrollUntilVisible(
        find.text('Retention period'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.text('Retention period'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('14 days').last);
      await tester.pumpAndSettle();
      expect(SettingsController.instance.historyRetentionDays, 14);
      ScaffoldMessenger.of(
        tester.element(find.byType(Scaffold)),
      ).clearSnackBars();
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(
        find.text('Delete all history'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.text('Delete all history'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(clearHistoryCalls, 0);
      await tester.tap(find.text('Delete all history'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Agree'));
      await tester.pumpAndSettle();
      expect(clearHistoryCalls, 1);
      expect(find.text('Deleted successfully'), findsOneWidget);

      await tester.scrollUntilVisible(
        find.text('Version 1.0.0'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('Version 1.0.0'), findsOneWidget);
    },
  );

  test(
    'logout invalidates locally and revokes the active guest token',
    () async {
      final requests = <http.Request>[];
      final client = MockClient((request) async {
        requests.add(request);
        if (request.url.path == '/api/session/guest') {
          return http.Response(
            jsonEncode({
              'access_token': 'header.payload.signature',
              'token_type': 'bearer',
              'role': 'guest',
              'owner_id': '12345678-1234-4234-8234-123456789abc',
              'expires_in': 300,
            }),
            201,
          );
        }
        if (request.url.path == '/api/session/logout') {
          return http.Response('', 204);
        }
        return http.Response('', 404);
      });
      final service = AuthSessionService(
        client: client,
        config: ApiEndpointConfig('https://example.test', release: false),
      );

      await service.ensureSession();
      expect(service.currentToken, isNotNull);
      await service.logout();
      expect(service.currentToken, isNull);
      expect(
        requests.where((request) => request.url.path == '/api/session/logout'),
        hasLength(1),
      );
      expect(
        requests.last.headers['Authorization'],
        'Bearer header.payload.signature',
      );
      service.dispose();
    },
  );
}
