import { AppLayout } from '@/components/layout/AppLayout';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | SecurityHub',
  description: 'Security dashboard for monitoring and managing security events',
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppLayout>{children}</AppLayout>;
}
