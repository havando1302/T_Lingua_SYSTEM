import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

import '../core/app_localizations.dart';

class SettingsController extends ChangeNotifier {
  static final SettingsController instance = SettingsController._internal();
  SettingsController._internal();

  late Box<String> _box;

  String _voiceSpeed = 'Normal';
  String _voiceGender = 'Female';
  String _language = 'vi';
  bool _historyEnabled = false;
  int _historyRetentionDays = 7;
  bool get historyEnabled => _historyEnabled;
  int get historyRetentionDays => _historyRetentionDays;

  String get voiceSpeed => _voiceSpeed;
  String get voiceGender => _voiceGender;
  String get language => _language;

  void init() {
    _box = Hive.box<String>('settings');
    loadSettings();
  }

  void loadSettings() {
    _voiceSpeed = _box.get('voice_speed', defaultValue: 'Normal')!;
    _voiceGender = _box.get('voice_gender', defaultValue: 'Female')!;
    _language = _box.get('app_language', defaultValue: 'vi')!;
    _historyEnabled = _box.get('history_opt_in') == 'true';
    _historyRetentionDays =
        (int.tryParse(_box.get('history_retention_days') ?? '') ?? 7).clamp(
          1,
          30,
        );

    // Sync to AppLocalizations
    AppLocalizations.instance.init(_language);
  }

  Future<void> setVoiceSpeed(String value, {bool persist = true}) async {
    final previous = _voiceSpeed;
    _voiceSpeed = value;
    notifyListeners();
    if (!persist) return;
    try {
      await _box.put('voice_speed', value);
    } catch (_) {
      _voiceSpeed = previous;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> setHistoryEnabled(bool value, {bool persist = true}) async {
    final previous = _historyEnabled;
    _historyEnabled = value;
    notifyListeners();
    if (!persist) return;
    try {
      await _box.put('history_opt_in', value.toString());
    } catch (_) {
      _historyEnabled = previous;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> setHistoryRetentionDays(int value, {bool persist = true}) async {
    if (value < 1 || value > 30) {
      throw ArgumentError('Retention must be between 1 and 30 days.');
    }
    final previous = _historyRetentionDays;
    _historyRetentionDays = value;
    notifyListeners();
    if (!persist) return;
    try {
      await _box.put('history_retention_days', value.toString());
    } catch (_) {
      _historyRetentionDays = previous;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> setVoiceGender(String value) async {
    _voiceGender = value;
    await _box.put('voice_gender', value);
    notifyListeners();
  }

  Future<void> setLanguage(String value, {bool persist = true}) async {
    if (value != 'vi' && value != 'en') return;
    final previous = _language;
    _language = value;
    AppLocalizations.instance.setLocale(value);
    notifyListeners();
    if (!persist) return;
    try {
      await _box.put('app_language', value);
    } catch (_) {
      _language = previous;
      AppLocalizations.instance.setLocale(previous);
      notifyListeners();
      rethrow;
    }
  }
}
