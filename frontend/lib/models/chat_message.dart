class ChatMessage {
  final String id;
  final String text;
  final String translation;
  final bool isMe;
  final bool isDraft;
  final String? turnId;
  final String? sourceLang;
  final String? targetLang;
  final String? qaAudioToken;

  ChatMessage({
    required this.id,
    required this.text,
    required this.translation,
    required this.isMe,
    this.isDraft = false,
    this.turnId,
    this.sourceLang,
    this.targetLang,
    this.qaAudioToken,
  });

  ChatMessage copyWith({
    String? id,
    String? text,
    String? translation,
    bool? isMe,
    bool? isDraft,
    String? turnId,
    String? sourceLang,
    String? targetLang,
    String? qaAudioToken,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      text: text ?? this.text,
      translation: translation ?? this.translation,
      isMe: isMe ?? this.isMe,
      isDraft: isDraft ?? this.isDraft,
      turnId: turnId ?? this.turnId,
      sourceLang: sourceLang ?? this.sourceLang,
      targetLang: targetLang ?? this.targetLang,
      qaAudioToken: qaAudioToken ?? this.qaAudioToken,
    );
  }
}
