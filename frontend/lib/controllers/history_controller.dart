// [NEW] Controller quản lý logic cho trang History — sử dụng Hive làm storage
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import '../models/history.dart';

class HistoryController extends ChangeNotifier {
  // [NEW] Hive Box chứa dữ liệu lịch sử
  late final Box<HistoryModel> _box;

  // [NEW] Lắng nghe thay đổi từ Hive Box (khi TranslationLogic ghi data mới)
  StreamSubscription? _boxSub;

  // [NEW] Danh sách đã sort sẵn — UI chỉ cần đọc getter này
  List<HistoryModel> _historyList = [];
  List<HistoryModel> get historyList => _historyList;

  HistoryController() {
    _box = Hive.box<HistoryModel>('history');
    loadHistory();

    // [NEW] Tự động reload khi Hive Box thay đổi (ví dụ: TranslationLogic thêm item mới)
    _boxSub = _box.watch().listen((_) {
      loadHistory();
    });
  }

  // ============================================================
  // [NEW] Load toàn bộ dữ liệu từ Hive Box và sort
  // ============================================================
  void loadHistory() {
    _historyList = _box.values.toList();
    _sortList();
    notifyListeners();
  }

  // ============================================================
  // [NEW] Toggle Favorite — cập nhật Hive và sort lại
  // ============================================================
  void toggleFavorite(String id) {
    try {
      final item = _historyList.firstWhere((e) => e.id == id);
      item.isFavorite = !item.isFavorite;
      item.save(); // Ghi trực tiếp vào Hive nhờ extend HiveObject
      _sortList();
      notifyListeners();
    } catch (e) {
      debugPrint('HistoryController.toggleFavorite error: $e');
    }
  }

  // ============================================================
  // [NEW] Xóa item khỏi Hive và cập nhật UI ngay lập tức
  // ============================================================
  void deleteItem(String id) {
    try {
      final item = _historyList.firstWhere((e) => e.id == id);
      item.delete(); // Xóa khỏi Hive nhờ extend HiveObject
      _historyList.removeWhere((e) => e.id == id);
      notifyListeners();
    } catch (e) {
      debugPrint('HistoryController.deleteItem error: $e');
    }
  }

  // ============================================================
  // [NEW] Thêm item mới vào Hive (gọi từ TranslationLogic khi dịch xong)
  // ============================================================
  void addHistory(HistoryModel item) {
    _box.add(item); // Lưu vào Hive
    _historyList.add(item);
    _sortList();
    notifyListeners();
  }

  // ============================================================
  // [NEW] Sort logic:
  //   1. Starred items luôn ở trên cùng
  //   2. Trong cùng nhóm → mới nhất (time lớn hơn) lên trước
  // ============================================================
  void _sortList() {
    _historyList.sort((a, b) {
      // Ưu tiên starred lên đầu
      if (a.isFavorite && !b.isFavorite) return -1;
      if (!a.isFavorite && b.isFavorite) return 1;
      // Trong cùng nhóm → so sánh id giảm dần (mới nhất trước)
      return b.id.compareTo(a.id);
    });
  }

  // [NEW] Giải phóng stream subscription khi controller bị huỷ
  @override
  void dispose() {
    _boxSub?.cancel();
    super.dispose();
  }
}
