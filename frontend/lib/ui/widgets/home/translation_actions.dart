import 'package:flutter/material.dart';
import '../../../core/app_localizations.dart';

class TranslationActions extends StatelessWidget {
  final VoidCallback? onPlay;
  final VoidCallback? onCopy;
  final VoidCallback? onSave;
  final VoidCallback? onFlag;

  const TranslationActions({
    super.key,
    this.onPlay,
    this.onCopy,
    this.onSave,
    this.onFlag,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _buildActionButton(
            icon: Icons.volume_up_rounded,
            label: tr('play'),
            iconColor: Colors.blue,
            onTap: onPlay,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildActionButton(
            icon: Icons.copy_rounded,
            label: tr('copy'),
            iconColor: Colors.indigo,
            onTap: onCopy,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildActionButton(
            icon: Icons.star_rounded,
            label: tr('save'),
            iconColor: Colors.amber,
            onTap: onSave,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildActionButton(
            icon: Icons.flag_rounded,
            label: tr('flag'),
            iconColor: Colors.redAccent,
            onTap: onFlag,
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required Color iconColor,
    required VoidCallback? onTap,
  }) {
    return Tooltip(
      message: label,
      child: Semantics(
        button: true,
        enabled: onTap != null,
        label: label,
        child: Material(
          color: Colors.white, // Nền trắng
          borderRadius: BorderRadius.circular(16),
          elevation: 2, // Tạo độ nổi nhẹ
          shadowColor: Colors.black26,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(16),
            splashColor: iconColor.withValues(
              alpha: 0.1,
            ), // Màu gợn sóng khi nhấn
            highlightColor: iconColor.withValues(
              alpha: 0.05,
            ), // Màu khi giữ tay vào
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(icon, color: iconColor, size: 20),
                  const SizedBox(width: 4),
                  Flexible(
                    child: Text(
                      label,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF334155),
                        fontWeight: FontWeight.w700,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
