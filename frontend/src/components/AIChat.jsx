import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage } from '../redux/complaintSlice';
import { clearChat } from '../redux/chatSlice';
import ChatMessage from './ChatMessage';
import DocumentUploader from './DocumentUploader';
import { Send, Bot, Minus, MessageSquare, RotateCcw } from 'lucide-react';


export default function AIChat() {
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const loading = useSelector((state) => state.complaints.loading);
  const [inputValue, setInputValue] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // Draggable State
  const [position, setPosition] = useState({ x: null, y: null });
  const [isDragging, setIsDragging] = useState(false);
  
  const chatRef = useRef(null);
  const dragStart = useRef({ offsetX: 0, offsetY: 0 });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!isCollapsed) {
      scrollToBottom();
    }
  }, [messages, isCollapsed]);

  // Handle Dragging
  const handleMouseDown = (e) => {
    // If clicking on buttons or inputs, do not drag
    if (e.target.closest('button') || e.target.closest('input')) return;
    
    if (chatRef.current) {
      const rect = chatRef.current.getBoundingClientRect();
      dragStart.current = {
        offsetX: e.clientX - rect.left,
        offsetY: e.clientY - rect.top
      };
      setIsDragging(true);
    }
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      let newX = e.clientX - dragStart.current.offsetX;
      let newY = e.clientY - dragStart.current.offsetY;

      // Restrict boundaries to viewport
      newX = Math.max(10, Math.min(newX, window.innerWidth - 410));
      newY = Math.max(10, Math.min(newY, window.innerHeight - 620));

      setPosition({ x: newX, y: newY });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleSend = () => {
    if (!inputValue.trim() || loading) return;

    dispatch(sendChatMessage(inputValue));
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  if (isCollapsed) {
    return (
      <button
        className="floating-chat-trigger"
        onClick={() => setIsCollapsed(false)}
        title="Open AI Co-Pilot"
        style={{
          // If custom position was set, place the trigger bubble near it!
          top: position.y !== null ? `${Math.min(position.y + 540, window.innerHeight - 80)}px` : 'auto',
          left: position.x !== null ? `${Math.min(position.x + 330, window.innerWidth - 80)}px` : 'auto',
          bottom: position.y !== null ? 'auto' : '2rem',
          right: position.x !== null ? 'auto' : '2rem',
        }}
      >
        <MessageSquare size={28} />
      </button>
    );
  }

  // Inline styling overrides when the window has been dragged
  const windowStyle = {
    top: position.y !== null ? `${position.y}px` : 'auto',
    left: position.x !== null ? `${position.x}px` : 'auto',
    bottom: position.y !== null ? 'auto' : '2rem',
    right: position.x !== null ? 'auto' : '2rem',
  };

  return (
    <div
      ref={chatRef}
      className="floating-chat-window glass"
      style={windowStyle}
    >
      {/* Draggable Card Header */}
      <div
        className="card-header"
        onMouseDown={handleMouseDown}
        style={{
          padding: '0.85rem 1.25rem',
          cursor: isDragging ? 'grabbing' : 'grab',
          userSelect: 'none',
          background: 'rgba(31, 41, 55, 0.4)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', pointerEvents: 'none' }}>
          <Bot size={20} className="icon-blue" />
          <h2 style={{ fontSize: '1.05rem', fontFamily: 'var(--font-title)' }}>
            AI QMS Co-Pilot
          </h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dark)', fontWeight: '600', pointerEvents: 'none' }}>
            ONLINE
          </span>
          <button
            className="chat-close-btn"
            onClick={() => dispatch(clearChat())}
            title="Reset Chat Session"
          >
            <RotateCcw size={14} />
          </button>
          <button
            className="chat-close-btn"
            onClick={() => setIsCollapsed(true)}
            title="Minimize Chat"
          >
            <Minus size={16} />
          </button>
        </div>
      </div>


      <div className="chat-messages" style={{ padding: '1rem' }}>
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompt Suggestions */}
      <div className="chat-quick-chips">
        <button
          className="quick-chip"
          disabled={loading}
          onClick={() => dispatch(sendChatMessage("A pharmacy reported that Paracetamol 500 mg tablets from batch PCM24015 are discolored. Around 300 strips are affected. Manufactured January 2026 and expires December 2028."))}
          title="Extract Discolored Paracetamol complaint"
        >
          💊 Paracetamol Discolored
        </button>
        <button
          className="quick-chip"
          disabled={loading}
          onClick={() => dispatch(sendChatMessage("Quality alert: Customer identified particulate contamination in Amoxicillin 250 mg bottles, batch AMX-9901, 150 units affected."))}
          title="Extract Critical particulate complaint"
        >
          ⚠️ Contamination (Critical)
        </button>
        <button
          className="quick-chip"
          disabled={loading}
          onClick={() => dispatch(sendChatMessage("Batch number is PCM24099 instead."))}
          title="Update batch number"
        >
          ✏️ Edit Batch
        </button>
        <button
          className="quick-chip"
          disabled={loading}
          onClick={() => dispatch(sendChatMessage("Quantity is actually 850 strips."))}
          title="Update quantity"
        >
          🔢 Edit Qty
        </button>
      </div>

      <div className="chat-input-bar" style={{ padding: '0.65rem 1rem' }}>
        <div className="chat-input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder={loading ? "Processing..." : "Type instruction or details..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            style={{ padding: '0.6rem 2.75rem 0.6rem 1rem', fontSize: '0.9rem' }}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || loading}
            style={{ width: '28px', height: '28px', right: '0.4rem' }}
          >
            <Send size={12} />
          </button>
        </div>
      </div>

      <DocumentUploader />
    </div>
  );
}

