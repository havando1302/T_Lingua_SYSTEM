import 'package:flutter/material.dart';
import '../../../core/app_localizations.dart';
import 'translation_actions.dart';

class TranslateCard extends StatelessWidget {
  final String speechText;
  final String translatedText;
  final bool isListening;
  final VoidCallback? onPlay;
  final VoidCallback? onCopy;
  final VoidCallback? onSave;
  final VoidCallback? onFlag;

  const TranslateCard({
    super.key,
    required this.speechText,
    required this.translatedText,
    this.isListening = false,
    this.onPlay,
    this.onCopy,
    this.onSave,
    this.onFlag,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,

      children: [
        // ================= CARD =================
        Container(
          width: double.infinity,

          padding: const EdgeInsets.all(22),

          decoration: BoxDecoration(
            color: Colors.white,

            borderRadius: BorderRadius.circular(28),

            border: Border.all(color: Colors.black.withValues(alpha: 0.03)),

            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),

          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [
              // ===== YOU SAID =====
              Text(
                tr('you_said'),

                style: const TextStyle(
                  color: Color.fromARGB(255, 0, 0, 0),
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),

              const SizedBox(height: 10),

              Text(
                speechText.isEmpty ? "..." : speechText,

                style: const TextStyle(
                  color: Color(0xFF222222),
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                ),
              ),

              const Padding(
                padding: EdgeInsets.symmetric(vertical: 18),

                child: Divider(color: Color(0xFFEAEAEA), thickness: 1),
              ),

              // ===== TRANSLATION =====
              Text(
                tr('translation'),

                style: const TextStyle(
                  color: Color.fromARGB(255, 0, 0, 0),
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),

              const SizedBox(height: 10),

              Text(
                translatedText.isEmpty ? "..." : translatedText,

                style: const TextStyle(
                  color: Color(0xFF111111),
                  fontSize: 19,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),

        // ================= ACTION BUTTONS =================
        // FIX BUG: Action Buttons
        if (translatedText.isNotEmpty) const SizedBox(height: 18),

        if (translatedText.isNotEmpty)
          TranslationActions(
            onPlay: onPlay,
            onCopy: onCopy,
            onSave: onSave,
            onFlag: onFlag,
          ),
      ],
    );
  }
}
