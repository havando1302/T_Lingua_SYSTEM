import 'package:flutter/material.dart';
import '../widgets/history/history_card.dart';
import '../../models/history.dart';
import '../../controllers/history_controller.dart'; // [NEW] Import controller
import '../../controllers/settings_controller.dart';
import '../../core/app_localizations.dart';

class HistoryScreen extends StatefulWidget {
  // 1. Thêm callback nhận lệnh từ màn hình điều hướng cha
  final VoidCallback? onBackToHome;

  const HistoryScreen({super.key, this.onBackToHome});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  // [NEW] Thay thế mock data bằng HistoryController kết nối Hive
  late final HistoryController _controller;

  @override
  void initState() {
    super.initState();
    // [NEW] Khởi tạo controller — tự động load dữ liệu từ Hive trong constructor
    _controller = HistoryController();
  }

  @override
  void dispose() {
    // [NEW] Giải phóng controller khi widget bị huỷ
    _controller.dispose();
    super.dispose();
  }

  // [NEW] Gọi controller thay vì setState trực tiếp
  Future<void> _toggleFavorite(String id) async {
    try {
      await _controller.toggleFavorite(id);
    } catch (_) {
      _showError();
    }
  }

  // [NEW] Gọi controller thay vì setState trực tiếp
  Future<void> _deleteItem(String id) async {
    try {
      await _controller.deleteItem(id);
    } catch (_) {
      _showError();
    }
  }

  void _showError() {
    if (mounted) {
      ScaffoldMessenger.of(context)
        ..clearSnackBars()
        ..showSnackBar(
          SnackBar(
            content: Text(tr('update_failed')),
            duration: const Duration(seconds: 4),
          ),
        );
    }
  }

  void _showDetailDialog(BuildContext context, HistoryModel item) {
    showDialog(
      context: context,
      builder: (context) => AnimatedBuilder(
        animation: _controller,
        builder: (context, _) => !_controller.contains(item.id)
            ? AlertDialog(
                content: Text(tr('history_removed')),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text(tr('close')),
                  ),
                ],
              )
            : AlertDialog(
                backgroundColor: const Color(0xFFF1F5F9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                titlePadding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
                contentPadding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                actionsPadding: const EdgeInsets.fromLTRB(24, 12, 24, 16),
                title: Row(
                  children: [
                    Text(item.fromFlag, style: const TextStyle(fontSize: 22)),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 8),
                      child: Icon(
                        Icons.arrow_forward,
                        size: 18,
                        color: Color(0xFF64748B),
                      ),
                    ),
                    Text(item.toFlag, style: const TextStyle(fontSize: 22)),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE2E8F0),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        item.time,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF475569),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
                content: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(height: 8),
                      // Label "Bản gốc"
                      Text(
                        tr('original'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF475569),
                          fontSize: 14,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Nội dung bản gốc
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Text(
                          item.originalText,
                          style: const TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF0F172A),
                            height: 1.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Label "Bản dịch"
                      Text(
                        tr('translated'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF475569),
                          fontSize: 14,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Nội dung bản dịch
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Text(
                          item.translatedText,
                          style: const TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF0F172A),
                            height: 1.5,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                actions: [
                  SizedBox(
                    width: double.infinity,
                    child: TextButton(
                      style: TextButton.styleFrom(
                        backgroundColor: const Color(0xFF6366F1),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      onPressed: () => Navigator.pop(context),
                      child: Text(
                        tr('close'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // [NEW] Wrap bằng AnimatedBuilder để lắng nghe HistoryController (đúng pattern project)
    return AnimatedBuilder(
      animation: Listenable.merge([
        _controller,
        AppLocalizations.instance,
        SettingsController.instance,
      ]),
      builder: (context, _) {
        // [NEW] Lấy danh sách đã sort sẵn từ controller (không cần sort ở UI nữa)
        final sortedList = _controller.historyList;

        return Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                decoration: const BoxDecoration(
                  color: Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: sortedList.isEmpty
                    ? Center(
                        child: Text(
                          tr('history_empty'),
                          style: const TextStyle(color: Colors.grey),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.only(top: 25, bottom: 100),
                        itemCount:
                            sortedList.length + (_controller.hasMore ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == sortedList.length) {
                            return TextButton(
                              onPressed: _controller.loadMore,
                              child: Text(
                                '${tr('load_more')} (${sortedList.length}/${_controller.total})',
                              ),
                            );
                          }
                          final item = sortedList[index];
                          return HistoryCard(
                            originalText: item.originalText,
                            translatedText: item.translatedText,
                            time: item.time,
                            fromFlag: item.fromFlag,
                            toFlag: item.toFlag,
                            isFavorite: item.isFavorite,
                            onFavoriteToggle: () => _toggleFavorite(item.id),
                            onDelete: () => _deleteItem(item.id),
                            onTap: () => _showDetailDialog(context, item),
                          );
                        },
                      ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          IconButton(
            tooltip: tr('back'),
            icon: const Icon(
              Icons.arrow_back_ios_new,
              color: Color.fromARGB(255, 0, 0, 0),
              size: 20,
            ),
            onPressed: () {
              // 2. Không dùng Navigator.pop() nữa mà gọi hàm callback truyền từ ngoài vào
              if (widget.onBackToHome != null) {
                widget.onBackToHome!();
              }
            },
          ),
          Text(
            tr('history'),
            style: const TextStyle(
              color: Color.fromARGB(255, 0, 0, 0),
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
