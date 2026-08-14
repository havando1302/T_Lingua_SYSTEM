import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart'; // [NEW] Hive Flutter init
import 'models/history.dart'; // [NEW] Để register adapter
import 'ui/pages/home_page.dart'; // Đảm bảo đường dẫn này đúng với thư mục của bạn
import 'controllers/settings_controller.dart';
import 'core/app_localizations.dart';

// [NEW] Khởi tạo Hive trước khi chạy app
void main() async {
  WidgetsFlutterBinding.ensureInitialized(); // [NEW] Cần cho async main
  await Hive.initFlutter(); // [NEW] Khởi tạo Hive với đường dẫn mặc định
  Hive.registerAdapter(HistoryModelAdapter()); // [NEW] Đăng ký adapter
  await Hive.openBox<HistoryModel>('history'); // [NEW] Mở box sẵn để dùng toàn app
  await Hive.openBox<String>('settings'); // [NEW] Mở box settings cho config
  
  // Khởi tạo SettingsController (sẽ load settings & sync locale)
  SettingsController.instance.init();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppLocalizations.instance,
      builder: (context, child) {
        return MaterialApp(
          // Tắt chữ DEBUG ở góc phải
          debugShowCheckedModeBanner: false,

          title: 'Voice Translator App',

          // Cấu hình Theme (Màu sắc chủ đạo)
          theme: ThemeData(
            useMaterial3: true,
            // Chế độ tối cho phù hợp với nền xanh đen 0xFF0F172A của bạn
            brightness: Brightness.dark,
            primarySwatch: Colors.blue,
            scaffoldBackgroundColor: const Color.fromARGB(
              255,
              18,
              18,
              18,
            ), // Màu nền mặc định toàn app
          ),

          // Trang đầu tiên app hiện ra khi mở
          home: const HomePage(),
        );
      },
    );
  }
}
