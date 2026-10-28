import React from 'react';
import { Bot, User, Zap } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`message-wrapper ${isAssistant ? 'assistant' : 'user'}`}>
      <div className="message-bubble">
        <p style={{ whiteSpace: 'pre-line', fontSize: '0.93rem', lineHeight: '1.5' }}>{message.content}</p>
        <div className="message-info">
          {isAssistant ? (
            <>
              <Bot size={13} className="icon-blue" />
              <span style={{ fontWeight: '600' }}>AI Co-Pilot</span>
              {message.is_mock ? (
                <span className="mock-badge">Mock Rules</span>
              ) : (
                <span className="live-ai-badge">
                  <Zap size={10} /> Groq AI
                </span>
              )}
            </>
          ) : (
            <>
              <User size={13} />
              <span>You</span>
            </>
          )}
          <span style={{ fontSize: '0.7rem', opacity: 0.6 }}>• {message.timestamp}</span>
        </div>
      </div>
    </div>
  );
}
