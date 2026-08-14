import 'package:flutter/material.dart';
import '../../../controllers/translate_controller.dart';
import '../../../core/app_localizations.dart';

class LanguageSelector extends StatelessWidget {
  final TranslationLogic logic;

  const LanguageSelector({super.key, required this.logic});

  @override
  Widget build(BuildContext context) {
    bool isVietnameseFirst = logic.currentSourceLang == 'vi';

    final leftLang = isVietnameseFirst ? tr('vietnamese') : tr('english');
    final leftFlag = isVietnameseFirst ? '🇻🇳' : '🇬🇧';

    final rightLang = isVietnameseFirst ? tr('english') : tr('vietnamese');
    final rightFlag = isVietnameseFirst ? '🇬🇧' : '🇻🇳';

    return Row(
      children: [
        Expanded(child: _buildLanguageCard(leftFlag, leftLang)),

        const SizedBox(width: 12),

        // BUTTON SWAP
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: logic.swapLanguages,
            borderRadius: BorderRadius.circular(14),

            child: Container(
              padding: const EdgeInsets.all(14),

              decoration: BoxDecoration(
                color: Colors.blueAccent,

                borderRadius: BorderRadius.circular(14),

                boxShadow: [
                  BoxShadow(
                    color: Colors.blueAccent.withOpacity(0.25),
                    blurRadius: 12,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),

              child: const Icon(
                Icons.swap_horiz,
                color: Colors.white,
                size: 24,
              ),
            ),
          ),
        ),

        const SizedBox(width: 12),

        Expanded(child: _buildLanguageCard(rightFlag, rightLang)),
      ],
    );
  }

  // ================= LANGUAGE CARD =================

  Widget _buildLanguageCard(String flag, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),

      decoration: BoxDecoration(
        color: Colors.white,

        borderRadius: BorderRadius.circular(20),

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
        mainAxisAlignment: MainAxisAlignment.center,

        children: [
          Text(flag, style: const TextStyle(fontSize: 20)),

          const SizedBox(width: 8),

          Text(
            label,

            style: const TextStyle(
              color: Color(0xFF222222),
              fontSize: 15,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
