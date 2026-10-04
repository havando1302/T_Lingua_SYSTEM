import 'package:flutter/material.dart';

import 'dart:async';

import 'core/constants.dart';
import 'services/auth_session_service.dart';
import 'services/history_storage_service.dart';

import 'package:hive_flutter/hive_flutter.dart'; // [NEW] Hive Flutter init

import 'models/history.dart'; // [NEW] Để register adapter
import 'ui/pages/home_page.dart'; // Đảm bảo đường dẫn này đúng với thư mục của bạn
import 'controllers/settings_controller.dart';
import 'core/app_localizations.dart';

// [NEW] Khởi tạo Hive trước khi chạy app
void main() async {
  WidgetsFlutterBinding.ensureInitialized(); // [NEW] Cần cho async main
  try {
    apiEndpointConfig.baseUri;
  } on FormatException {
    runApp(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text(
              'Cấu hình API_BASE_URL không hợp lệ. Bản phát hành yêu cầu HTTPS.',
            ),
          ),
        ),
      ),
    );
    return;
  }
  await Hive.initFlutter(); // [NEW] Khởi tạo Hive với đường dẫn mặc định
  Hive.registerAdapter(HistoryModelAdapter()); // [NEW] Đăng ký adapter
  await Hive.openBox<HistoryModel>(
    'history',
  ); // [NEW] Mở box sẵn để dùng toàn app
  await Hive.openBox<String>('settings'); // [NEW] Mở box settings cho config

  // Khởi tạo SettingsController (sẽ load settings & sync locale)
  SettingsController.instance.init();
  HistoryStorageService.instance.start();

  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      AuthSessionService.instance.resume();
      unawaited(HistoryStorageService.instance.prune());
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.hidden ||
        state == AppLifecycleState.detached) {
      unawaited(AuthSessionService.instance.suspend());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(AuthSessionService.instance.suspend());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppLocalizations.instance,
      builder: (context, child) {
        return MaterialApp(
          // Tắt chữ DEBUG ở góc phải
          debugShowCheckedModeBanner: false,

          title: 'T-Lingua',

          // Cấu hình Theme (Màu sắc chủ đạo)
          theme: ThemeData(
            useMaterial3: true,
            // Chế độ tối cho phù hợp với nền xanh đen 0xFF0F172A của bạn
            brightness: Brightness.light,
            primarySwatch: Colors.blue,
            scaffoldBackgroundColor: const Color.fromARGB(
              255,
              18,
              18,
              18,
            ), // Màu nền mặc định toàn app
            snackBarTheme: const SnackBarThemeData(
              behavior: SnackBarBehavior.floating,
            ),
          ),

          // Trang đầu tiên app hiện ra khi mở
          home: const HomePage(),
        );
      },
    );
  }
}
