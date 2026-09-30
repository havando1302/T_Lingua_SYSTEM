import 'dart:async';
import 'package:flutter/foundation.dart';

enum MicState {
  uninitialized,
  idle,
  starting,
  recording,
  stopping,
  error,
}

class MicStateMachine extends ChangeNotifier {
  MicState _state = MicState.idle;
  String? _errorMessage;
  int _operationId = 0;

  MicState get state => _state;
  String? get errorMessage => _errorMessage;

  bool get isIdle => _state == MicState.idle;
  bool get isStarting => _state == MicState.starting;
  bool get isRecording => _state == MicState.recording;
  bool get isStopping => _state == MicState.stopping;
  bool get hasError => _state == MicState.error;
  bool get isActive => isStarting || isRecording;

  /// Starts recording with strict state transitions and mutual exclusion.
  Future<bool> start(Future<void> Function() onStart) async {
    if (_state != MicState.idle && _state != MicState.error) {
      return false;
    }

    final currentOp = ++_operationId;
    _state = MicState.starting;
    _errorMessage = null;
    notifyListeners();

    try {
      await onStart();
      if (_operationId != currentOp) {
        return false;
      }
      _state = MicState.recording;
      notifyListeners();
      return true;
    } catch (e) {
      if (_operationId == currentOp) {
        _state = MicState.error;
        _errorMessage = e.toString();
        notifyListeners();
      }
      return false;
    }
  }

  /// Stops recording cleanly, ensuring completion of in-flight transitions.
  Future<bool> stop(Future<void> Function() onStop) async {
    if (_state != MicState.recording && _state != MicState.starting) {
      return false;
    }

    final currentOp = ++_operationId;
    _state = MicState.stopping;
    notifyListeners();

    try {
      await onStop();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      if (_operationId == currentOp) {
        _state = MicState.idle;
        notifyListeners();
      }
    }
    return true;
  }

  /// Reset to idle state unconditionally (e.g. on screen exit or connection reset).
  void reset() {
    _operationId++;
    _state = MicState.idle;
    _errorMessage = null;
    notifyListeners();
  }
}
