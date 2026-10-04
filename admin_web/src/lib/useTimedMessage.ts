import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Custom React hook for alert/notification messages.
 * Automatically clears the message after `duration` ms (default 4000ms = 4s, within the 3-5s range).
 * If a new message is triggered while one is already active, it resets the timer and displays the new message immediately.
 */
export function useTimedMessage(initialValue = '', duration = 4000): [string, (val: string) => void] {
  const [message, setMessage] = useState(initialValue);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setTimedMessage = useCallback(
    (newVal: string) => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      setMessage(newVal);
      if (newVal) {
        timerRef.current = setTimeout(() => {
          setMessage('');
          timerRef.current = null;
        }, duration);
      }
    },
    [duration]
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return [message, setTimedMessage];
}
