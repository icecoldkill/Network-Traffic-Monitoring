'use client';

import { useState } from 'react';
import { MessageSquare } from 'lucide-react';
import ChatInterface from '../ChatInterface';

export function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen ? (
        <div className="w-80 h-[500px] bg-white rounded-lg shadow-xl flex flex-col border border-gray-200">
          <ChatInterface onClose={() => setIsOpen(false)} />
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-indigo-600 text-white p-4 rounded-full shadow-lg hover:bg-indigo-700 transition-colors"
          aria-label="Open chat"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}
    </div>
  );
}
