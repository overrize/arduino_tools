import React from 'react';
import { Message } from '../App';
import './Chat.css';

interface ChatProps {
  messages: Message[];
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const Chat: React.FC<ChatProps> = ({ messages, messagesEndRef }) => {
  return (
    <div className="chat-container">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role} ${message.isLoading ? 'loading' : ''}`}
        >
          <div className="message-header">
            <span className="message-role">
              {message.role === 'user' ? '你' : message.role === 'system' ? '系统' : 'Arduino Desktop'}
            </span>
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <div className="message-content">
            {message.isLoading ? (
              <div className="loading-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            ) : (
              <pre>{message.content}</pre>
            )}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default Chat;
