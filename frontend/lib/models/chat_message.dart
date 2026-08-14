class ChatMessage {
  final String id; // [NEW] ID to link STT with Translation
  final String text; // Nội dung câu gốc (ví dụ: "Xin chào")
  final String translation; // Nội dung đã dịch (ví dụ: "Hello")
  final bool isMe; // Để phân biệt bên trái hay bên phải
  final bool isDraft; // Đánh dấu tin nhắn đang là dự thảo (partial STT)

  ChatMessage({
    required this.id,
    required this.text,
    required this.translation,
    required this.isMe,
    this.isDraft = false,
  });

  ChatMessage copyWith({
    String? id,
    String? text,
    String? translation,
    bool? isMe,
    bool? isDraft,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      text: text ?? this.text,
      translation: translation ?? this.translation,
      isMe: isMe ?? this.isMe,
      isDraft: isDraft ?? this.isDraft,
    );
  }
}
