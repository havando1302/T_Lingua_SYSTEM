import 'package:hive/hive.dart'; // [NEW] Import Hive

// [NEW] Hive TypeAdapter viết tay — không cần build_runner
class HistoryModelAdapter extends TypeAdapter<HistoryModel> {
  @override
  final int typeId = 0;

  @override
  HistoryModel read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{};
    for (int i = 0; i < numOfFields; i++) {
      final key = reader.readByte();
      final value = reader.read();
      fields[key] = value;
    }
    return HistoryModel(
      id: fields[0] as String,
      originalText: fields[1] as String,
      translatedText: fields[2] as String,
      time: fields[3] as String,
      fromFlag: fields[4] as String,
      toFlag: fields[5] as String,
      isFavorite: fields[6] as bool,
      savedAtEpochMs: fields[7] as int?,
    );
  }

  @override
  void write(BinaryWriter writer, HistoryModel obj) {
    writer.writeByte(8);
    writer.writeByte(0);
    writer.write(obj.id);
    writer.writeByte(1);
    writer.write(obj.originalText);
    writer.writeByte(2);
    writer.write(obj.translatedText);
    writer.writeByte(3);
    writer.write(obj.time);
    writer.writeByte(4);
    writer.write(obj.fromFlag);
    writer.writeByte(5);
    writer.write(obj.toFlag);
    writer.writeByte(6);
    writer.write(obj.isFavorite);
    writer.writeByte(7);
    writer.write(obj.savedAtEpochMs);
  }
}

// [NEW] Extend HiveObject để có thể gọi .save() / .delete() trực tiếp trên instance
// dữ liệu lịch sử
class HistoryModel extends HiveObject {
  final String id;
  final String originalText;
  final String translatedText;
  final String time;
  final String fromFlag;
  final String toFlag;
  // Null marks legacy records, which are never silently removed by retention.
  final int? savedAtEpochMs;
  bool isFavorite; // Không để final vì thuộc tính này có thể thay đổi trạng thái thay vì tạo mới object

  HistoryModel({
    required this.id,
    required this.originalText,
    required this.translatedText,
    required this.time,
    required this.fromFlag,
    required this.toFlag,
    this.isFavorite = false,
    this.savedAtEpochMs,
  });

  // Bản lề kết nối Backend: Chuyển dữ liệu từ JSON (Backend Python) thành Object Dart
  factory HistoryModel.fromJson(Map<String, dynamic> json) {
    return HistoryModel(
      id: json['id']?.toString() ?? '',
      originalText:
          json['original_text'] ??
          '', // Backend Python thường đặt dạng snake_case
      translatedText: json['translated_text'] ?? '',
      time: json['time'] ?? '',
      fromFlag: json['from_flag'] ?? '',
      toFlag: json['to_flag'] ?? '',
      isFavorite: json['is_favorite'] ?? false,
    );
  }

  // Gửi ngược dữ liệu lên Backend (ví dụ khi cập nhật trạng thái Favorite)
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'original_text': originalText,
      'translated_text': translatedText,
      'time': time,
      'from_flag': fromFlag,
      'to_flag': toFlag,
      'is_favorite': isFavorite,
    };
  }
}
