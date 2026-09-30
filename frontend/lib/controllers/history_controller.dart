import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

import '../models/history.dart';
import '../services/history_storage_service.dart';

class HistoryController extends ChangeNotifier {
  static const int pageSize = 50;
  final Box<HistoryModel> _box = Hive.box<HistoryModel>('history');
  StreamSubscription<BoxEvent>? _boxSub;
  List<HistoryModel> _historyList = [];
  int _visibleLimit = pageSize;
  int _total = 0;
  bool _reloadScheduled = false;
  bool _disposed = false;

  List<HistoryModel> get historyList => List.unmodifiable(_historyList);
  bool get hasMore => _historyList.length < _total;
  int get total => _total;

  HistoryController() {
    loadHistory();
    // Legacy Hive integer keys do not equal model IDs. Reload the authoritative
    // box and coalesce delete batches so clear/retention cannot leave stale UI.
    _boxSub = _box.watch().listen((_) {
      if (_reloadScheduled) return;
      _reloadScheduled = true;
      scheduleMicrotask(() {
        _reloadScheduled = false;
        if (!_disposed) loadHistory();
      });
    });
  }

  bool contains(String id) => _box.values.any((item) => item.id == id);

  void loadHistory() {
    final values = _box.values.toList()..sort(_compareHistory);
    _total = values.length;
    _historyList = values.take(_visibleLimit).toList();
    notifyListeners();
  }

  void loadMore() {
    _visibleLimit += pageSize;
    loadHistory();
  }

  Future<void> toggleFavorite(String id) async {
    final item = _historyList.where((item) => item.id == id).firstOrNull;
    if (item == null || !item.isInBox) return;
    item.isFavorite = !item.isFavorite;
    try {
      await item.save();
    } catch (_) {
      item.isFavorite = !item.isFavorite;
      rethrow;
    }
  }

  Future<void> deleteItem(String id) async {
    final item = _historyList.where((item) => item.id == id).firstOrNull;
    if (item != null && item.isInBox) await item.delete();
  }

  Future<HistorySaveResult> addHistory(HistoryModel item) =>
      HistoryStorageService.instance.save(item);

  static int _compareHistory(HistoryModel a, HistoryModel b) {
    if (a.isFavorite != b.isFavorite) return a.isFavorite ? -1 : 1;
    final aTime = a.savedAtEpochMs ?? int.tryParse(a.id) ?? 0;
    final bTime = b.savedAtEpochMs ?? int.tryParse(b.id) ?? 0;
    final byTime = bTime.compareTo(aTime);
    return byTime == 0 ? b.id.compareTo(a.id) : byTime;
  }

  @override
  void dispose() {
    _disposed = true;
    _boxSub?.cancel();
    super.dispose();
  }
}
