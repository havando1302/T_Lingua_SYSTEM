import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive/hive.dart';

import '../models/history.dart';

const secureHistoryBoxName = 'history_secure_v1';
const _legacyHistoryBoxName = 'history';
const _historyKeyName = 'tlingua_history_aes_key_v1';

class SecureHistoryBox {
  static const _keyStore = FlutterSecureStorage(
    aOptions: AndroidOptions(resetOnError: false, migrateWithBackup: true),
  );

  static Future<void> openAndMigrate() async {
    var encodedKey = await _keyStore.read(key: _historyKeyName);
    if (encodedKey == null) {
      encodedKey = base64UrlEncode(Hive.generateSecureKey());
      // Persist the key before creating the encrypted box. A crash can then be
      // resumed without ever replacing an existing encrypted box with a new key.
      await _keyStore.write(key: _historyKeyName, value: encodedKey);
    }
    final key = base64Url.decode(encodedKey);
    if (key.length != 32) {
      throw StateError('Invalid local history encryption key');
    }

    final secureBox = await Hive.openBox<HistoryModel>(
      secureHistoryBoxName,
      encryptionCipher: HiveAesCipher(key),
    );

    // One-time, resumable migration. Plaintext is removed only after every
    // record has been flushed to the authenticated encrypted box.
    if (await Hive.boxExists(_legacyHistoryBoxName)) {
      final legacy = await Hive.openBox<HistoryModel>(_legacyHistoryBoxName);
      final pending = <dynamic, HistoryModel>{};
      for (final legacyKey in legacy.keys) {
        final value = legacy.get(legacyKey);
        if (value != null && !secureBox.containsKey(legacyKey)) {
          pending[legacyKey] = value;
        }
      }
      if (pending.isNotEmpty) {
        await secureBox.putAll(pending);
        await secureBox.flush();
      }
      await legacy.clear();
      await legacy.close();
      await Hive.deleteBoxFromDisk(_legacyHistoryBoxName);
    }
  }
}
