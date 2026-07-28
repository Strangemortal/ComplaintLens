import React from 'react';
import { Bot, User, AlertCircle } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`message-wrapper ${isAssistant ? 'assistant' : 'user'}`}>
      <div className="message-bubble">
        <p style={{ whiteSpace: 'pre-line', fontSize: '0.95rem' }}>{message.content}</p>
        <div className="message-info">
          {isAssistant ? (
            <>
              <Bot size={12} />
              <span>Co-Pilot</span>
              {message.is_mock && <span className="mock-badge">Mock Mode</span>}
            </>
          ) : (
            <>
              <User size={12} />
              <span>You</span>
            </>
          )}
          <span style={{ fontSize: '0.7rem', opacity: 0.6 }}>• {message.timestamp}</span>
        </div>
      </div>
    </div>
  );
}
