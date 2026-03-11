'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Dynamically import the ChatInterface component with no SSR
const ChatInterface = dynamic(
  () => import('@/components/ChatInterface'),
  { ssr: false }
);

export default function ChatPage() {
  const router = useRouter();

  // Check if we're in the browser before accessing localStorage
  useEffect(() => {
    const isAuthenticated = typeof window !== 'undefined' ? localStorage.getItem('isAuthenticated') : null;
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-6 text-blue-600">Network Security Assistant</h1>
        <div className="border rounded-lg overflow-hidden">
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}
