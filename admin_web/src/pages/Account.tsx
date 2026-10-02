import {
  BarChart3,
  BookOpen,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  IdCard,
  KeyRound,
  Settings,
  ShieldCheck,
  UserRound,
  Users,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { roleLabels, useAuthUser, type Role } from '../lib/auth';
import { formatApiDate } from '../lib/date';

const roleDescriptions: Record<Role, string> = {
  employee: 'Theo dõi hoạt động, tra cứu thuật ngữ và duyệt chất lượng bản dịch.',
  admin: 'Giám sát nghiệp vụ, lịch sử vận hành và quy trình huấn luyện AI.',
  superadmin: 'Quản trị toàn bộ hệ thống, tài khoản, cấu hình và khóa tích hợp.',
};

const commonPermissions = [
  { icon: BarChart3, label: 'Xem bảng điều khiển và thống kê tổng hợp' },
  { icon: BookOpen, label: 'Tra cứu và xuất từ điển' },
  { icon: ClipboardCheck, label: 'Duyệt, hiệu chỉnh và phân loại dữ liệu QA' },
];

const permissionsByRole: Record<Role, typeof commonPermissions> = {
  employee: commonPermissions,
  admin: [
    ...commonPermissions,
    { icon: BrainCircuit, label: 'Theo dõi và vận hành trung tâm huấn luyện AI' },
  ],
  superadmin: [
    ...commonPermissions,
    { icon: BrainCircuit, label: 'Điều hành và phát hành mô hình AI' },
    { icon: Users, label: 'Quản lý nhân sự và phân quyền' },
    { icon: KeyRound, label: 'Quản lý mã kết nối API' },
    { icon: Settings, label: 'Thay đổi cấu hình hệ thống và từ điển' },
  ],
};

export default function Account() {
  const user = useAuthUser();
  if (!user) return null;

  const initials = user.username.slice(0, 2).toUpperCase();
  const createdAt = user.created_at ? formatApiDate(user.created_at) : 'Chưa có thông tin';

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Hồ sơ cá nhân</h1>
        <p className="mt-2 text-text-muted">Thông tin tài khoản và phạm vi quyền đang được cấp.</p>
      </div>

      <Card className="overflow-hidden">
        <div className="h-24 bg-gradient-to-r from-primary/80 to-blue-500/60" />
        <CardContent className="relative px-6 pb-6 pt-0">
          <div className="-mt-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex items-end gap-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl border-4 border-surface bg-primary text-2xl font-bold text-white shadow-lg">
                {initials}
              </div>
              <div className="pb-1">
                <h2 className="text-2xl font-bold">{user.username}</h2>
                <p className="text-sm font-medium text-primary">{roleLabels[user.role]}</p>
              </div>
            </div>
            <span className="inline-flex w-fit items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1.5 text-sm font-medium text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 size={16} /> Tài khoản đang hoạt động
            </span>
          </div>
          <p className="mt-5 max-w-2xl text-sm text-text-muted">{roleDescriptions[user.role]}</p>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Thông tin tài khoản</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ProfileRow icon={UserRound} label="Tên đăng nhập" value={user.username} />
            <ProfileRow icon={ShieldCheck} label="Vai trò" value={roleLabels[user.role]} />
            <ProfileRow icon={IdCard} label="Mã tài khoản" value={user.public_id || `#${user.id}`} mono />
            <ProfileRow icon={CalendarDays} label="Ngày tạo" value={createdAt} />
            <ProfileRow icon={KeyRound} label="Xác thực MFA" value={user.mfa_enabled ? 'Đã bật' : user.role === 'employee' ? 'Không bắt buộc' : 'Chưa bật'} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Quyền được cấp</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {permissionsByRole[user.role].map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-start gap-3 rounded-lg border border-border bg-background/40 p-3">
                <span className="rounded-md bg-primary/10 p-2 text-primary"><Icon size={16} /></span>
                <span className="pt-1 text-sm font-medium">{label}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ProfileRow({ icon: Icon, label, value, mono = false }: {
  icon: typeof UserRound;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-3 border-b border-border/60 pb-4 last:border-0 last:pb-0">
      <span className="rounded-lg bg-primary/10 p-2 text-primary"><Icon size={18} /></span>
      <div className="min-w-0">
        <p className="text-xs text-text-muted">{label}</p>
        <p className={`mt-1 break-all text-sm font-medium ${mono ? 'font-mono' : ''}`}>{value}</p>
      </div>
    </div>
  );
}
