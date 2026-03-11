import Link from 'next/link';
import { useRouter } from 'next/router';
import { User } from '@/context/AuthContext';
import { 
  LayoutDashboard, 
  Shield, 
  Activity, 
  BarChart2, 
  Settings, 
  LogOut,
  AlertTriangle,
  Network,
  Server,
  Users
} from 'lucide-react';

interface SidebarProps {
  user: User;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Threats', href: '/threats', icon: AlertTriangle },
  { name: 'Network', href: '/network', icon: Network },
  { name: 'Devices', href: '/devices', icon: Server },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Analytics', href: '/analytics', icon: BarChart2 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar = ({ user }: SidebarProps) => {
  const router = useRouter();

  return (
    <div className="hidden md:flex md:flex-shrink-0">
      <div className="flex flex-col w-64 border-r border-gray-200 bg-white">
        <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <Shield className="w-8 h-8 text-indigo-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">SecurityHub</span>
          </div>
          <div className="mt-5 flex-1 flex flex-col">
            <nav className="flex-1 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = router.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <item.icon
                      className={`mr-3 flex-shrink-0 h-6 w-6 ${
                        isActive ? 'text-indigo-500' : 'text-gray-400 group-hover:text-gray-500'
                      }`}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-indigo-100">
                  <span className="text-indigo-600 font-medium">
                    {user.name
                      .split(' ')
                      .map((n) => n[0])
                      .join('')}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700">{user.name}</p>
                <p className="text-xs text-gray-500">{user.role}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
