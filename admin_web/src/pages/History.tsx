import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';
import { formatApiDate } from '../lib/date';
import { Card, CardContent, CardHeader, CardTitle} from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';

const History = () => {
  const list = usePaginatedList<any>('/quality/logs');
  const logs = list.items;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Lịch sử dịch thuật</h1>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle>Dữ liệu Audit</CardTitle>
            </div>
            <ListSearch list={list} />
          </div>
        </CardHeader>
        <CardContent>
          <ListStatus list={list} />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Khách hàng (Client)</TableHead>
                <TableHead className="w-1/3">Văn bản gốc</TableHead>
                <TableHead className="w-1/3">Bản dịch (AI)</TableHead>
                <TableHead>Độ trễ</TableHead>
                <TableHead>Thời gian</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-text-muted">
                    {list.fetching ? "Đang tải danh sách..." : list.error ? "Chưa tải được lịch sử." : "Không tìm thấy lịch sử nào."}
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">#{log.id}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-background text-text-muted border border-border">
                        {log.client_id || 'Không xác định'}
                      </span>
                    </TableCell>
                    <TableCell className="min-w-40 max-w-sm whitespace-pre-wrap break-words" title={log.source_text}>
                      {log.source_text}
                    </TableCell>
                    <TableCell className="min-w-40 max-w-sm whitespace-pre-wrap break-words" title={log.translated_text}>
                      {log.translated_text}
                    </TableCell>
                    <TableCell>{typeof log.latency === 'number' ? `${log.latency.toFixed(3)}s` : '-'}</TableCell>
                    <TableCell className="text-text-muted">
                      {formatApiDate(log.created_at)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <ListPagination list={list} />
        </CardContent>
      </Card>
    </div>
  );
};

export default History;
