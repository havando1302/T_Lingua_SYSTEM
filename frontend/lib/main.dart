import 'package:flutter/material.dart';

import 'dart:async';

import 'core/constants.dart';
import 'services/auth_session_service.dart';
import 'services/history_storage_service.dart';
import 'services/secure_history_box.dart';

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
  await SecureHistoryBox.openAndMigrate();
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
          builder: (context, child) {
            final media = MediaQuery.of(context);
            final screenWidth = media.size.width;
            final screenHeight = media.size.height;

            // 1. Mobile screen (width <= 600px): Native full screen
            if (screenWidth <= 600) {
              return child ?? const SizedBox.shrink();
            }

            // 2. Responsive Laptop / Tablet / Desktop
            // Dynamically scale width according to laptop screen size
            double targetWidth;
            if (screenWidth <= 960) {
              targetWidth = (screenWidth * 0.90).clamp(520.0, 680.0);
            } else if (screenWidth <= 1440) {
              targetWidth = (screenWidth * 0.58).clamp(660.0, 780.0);
            } else {
              targetWidth = 820.0;
            }

            // Adapt height & padding to prevent overflow on standard laptop screens (e.g. 768p/900p)
            final isCompactHeight = screenHeight <= 780;
            final verticalPadding = isCompactHeight ? 0.0 : (screenHeight <= 900 ? 12.0 : 24.0);
            final targetMaxHeight = isCompactHeight
                ? screenHeight
                : (screenHeight - (verticalPadding * 2)).clamp(580.0, 1020.0);
            final borderRadiusValue = isCompactHeight ? 0.0 : 24.0;

            return Scaffold(
              backgroundColor: const Color(0xFF0F172A),
              body: Container(
                width: double.infinity,
                height: double.infinity,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF0B0F17),
                      Color(0xFF0F172A),
                      Color(0xFF1E293B),
                    ],
                  ),
                ),
                child: Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(
                      vertical: verticalPadding,
                      horizontal: isCompactHeight ? 0 : 16,
                    ),
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        maxWidth: targetWidth,
                        maxHeight: targetMaxHeight,
                      ),
                      child: Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFFF5F5F7),
                          borderRadius: BorderRadius.circular(borderRadiusValue),
                          border: isCompactHeight
                              ? null
                              : Border.all(
                                  color: const Color(0xFF334155).withOpacity(0.35),
                                  width: 1.5,
                                ),
                          boxShadow: isCompactHeight
                              ? []
                              : [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.35),
                                    blurRadius: 32,
                                    spreadRadius: 2,
                                    offset: const Offset(0, 8),
                                  ),
                                ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(
                            isCompactHeight ? 0.0 : 22.0,
                          ),
                          child: child ?? const SizedBox.shrink(),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }
}
