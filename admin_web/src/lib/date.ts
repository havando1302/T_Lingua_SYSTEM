export function parseApiDate(value: string): Date {
  // Older server responses contain UTC without an offset. Explicit offsets stay intact.
  const normalized = value.trim();
  const hasOffset = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized);
  return new Date(hasOffset ? normalized : `${normalized}Z`);
}

export function formatApiDate(value: string | null | undefined): string {
  if (!value) return 'Không xác định';
  const date = parseApiDate(value);
  return Number.isNaN(date.getTime()) ? 'Thời gian không hợp lệ' : date.toLocaleString('vi-VN');
}
