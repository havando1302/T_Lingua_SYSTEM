import 'package:flutter/material.dart';
import '../../../core/app_localizations.dart';

class HistoryCard extends StatelessWidget {
  final String originalText;
  final String translatedText;
  final String time;
  final bool isFavorite;
  final String fromFlag;
  final String toFlag;

  final VoidCallback onFavoriteToggle;
  final VoidCallback onDelete;
  final VoidCallback onTap;

  const HistoryCard({
    super.key,
    required this.originalText,
    required this.translatedText,
    required this.time,
    required this.fromFlag,
    required this.toFlag,
    required this.onFavoriteToggle,
    required this.onDelete,
    required this.onTap,
    this.isFavorite = false,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Card(
          margin: const EdgeInsets.only(bottom: 16),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(20),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.03),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(fromFlag, style: const TextStyle(fontSize: 18)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          originalText,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF1E293B),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            tooltip: tr(
                              isFavorite ? 'remove_favorite' : 'add_favorite',
                            ),
                            constraints: const BoxConstraints(),
                            padding: EdgeInsets.zero,
                            icon: Icon(
                              isFavorite
                                  ? Icons.star_rounded
                                  : Icons.star_outline_rounded,
                              color: isFavorite
                                  ? const Color(0xFF6366F1)
                                  : Colors.grey.shade400,
                            ),
                            onPressed: onFavoriteToggle,
                          ),
                          const SizedBox(width: 12),
                          IconButton(
                            tooltip: tr('delete'),
                            constraints: const BoxConstraints(),
                            padding: EdgeInsets.zero,
                            icon: const Icon(
                              Icons.delete_outline_rounded,
                              color: Colors.redAccent,
                            ),
                            onPressed: onDelete,
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(toFlag, style: const TextStyle(fontSize: 18)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          translatedText,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 15,
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    time,
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (isFavorite)
          Positioned(
            left: -4,
            top: -4,
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: const BoxDecoration(
                color: Color(0xFF6366F1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.star, color: Colors.white, size: 10),
            ),
          ),
      ],
    );
  }
}
