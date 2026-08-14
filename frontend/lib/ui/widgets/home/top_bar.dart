import 'package:flutter/material.dart';
import '../../../core/app_localizations.dart';

class TopBar extends StatelessWidget {
  final VoidCallback onHistoryPressed;
  final VoidCallback onSettingsPressed;

  const TopBar({
    super.key,
    required this.onHistoryPressed,
    required this.onSettingsPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),

      decoration: BoxDecoration(
        color: Colors.white,

        borderRadius: BorderRadius.circular(18),

        border: Border.all(color: Colors.black.withOpacity(0.03)),

        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),

      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,

        children: [
          // HISTORY BUTTON
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFFF5F5F7),
              borderRadius: BorderRadius.circular(12),
            ),

            child: IconButton(
              onPressed: onHistoryPressed,

              icon: const Icon(Icons.history_rounded, color: Color(0xFF222222)),
            ),
          ),

          // TITLE
          Text(
            tr('voice_translator'),

            style: const TextStyle(
              color: Color(0xFF222222),
              fontSize: 17,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.3,
            ),
          ),

          // SETTINGS BUTTON
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFFF5F5F7),
              borderRadius: BorderRadius.circular(12),
            ),

            child: IconButton(
              onPressed: onSettingsPressed,

              icon: const Icon(
                Icons.settings_outlined,
                color: Color(0xFF222222),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
