import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

import '../controllers/settings_controller.dart';
import '../models/history.dart';
import 'secure_history_box.dart';

enum HistorySaveResult { saved, alreadySaved, disabled, empty }

class HistoryStorageService {
  static final instance = HistoryStorageService();
  Timer? _timer;
  bool _pruning = false;
  Box<HistoryModel> get _box => Hive.box<HistoryModel>(secureHistoryBoxName);

  void start() {
    SettingsController.instance.addListener(_settingsChanged);
    _timer ??= Timer.periodic(
      const Duration(minutes: 30),
      (_) => unawaited(prune()),
    );
    unawaited(prune());
  }

  void _settingsChanged() => unawaited(prune());

  static bool isExpired(HistoryModel item, DateTime now, int days) {
    final saved = item.savedAtEpochMs;
    return saved != null &&
        saved < now.subtract(Duration(days: days)).millisecondsSinceEpoch;
  }

  Future<HistorySaveResult> save(HistoryModel item) async {
    if (!SettingsController.instance.historyEnabled) {
      return HistorySaveResult.disabled;
    }
    if (item.originalText.trim().isEmpty ||
        item.translatedText.trim().isEmpty) {
      return HistorySaveResult.empty;
    }
    if (_box.values.any((existing) => existing.id == item.id)) {
      return HistorySaveResult.alreadySaved;
    }
    // Stable message IDs make auto-save and repeated manual saves idempotent.
    await _box.put(item.id, item);
    await prune();
    return HistorySaveResult.saved;
  }

  Future<void> prune() async {
    if (_pruning) return;
    _pruning = true;
    try {
      final now = DateTime.now();
      final days = SettingsController.instance.historyRetentionDays;
      final keys = _box.keys.where((key) {
        final item = _box.get(key);
        return item != null && isExpired(item, now, days);
      }).toList();
      await _box.deleteAll(keys);
    } catch (_) {
      debugPrint('Local history retention could not run.');
    } finally {
      _pruning = false;
    }
  }

  Future<void> clearAllByUser() async {
    await _box.clear();
  }
}
