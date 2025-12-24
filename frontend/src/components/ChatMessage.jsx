import { Bot, User } from 'lucide-react';
import './ChatMessage.css';

function ChatMessage({ message, isAI = false, timestamp }) {
    return (
        <div className={`chat-message ${isAI ? 'chat-message--ai' : 'chat-message--user'}`}>
            <div className="chat-message-avatar">
                {isAI ? (
                    <Bot size={20} strokeWidth={1.5} />
                ) : (
                    <User size={20} strokeWidth={1.5} />
                )}
            </div>
            <div className="chat-message-content">
                <div className="chat-message-bubble">
                    <p>{message}</p>
                </div>
                {timestamp && (
                    <span className="chat-message-time">{timestamp}</span>
                )}
            </div>
        </div>
    );
}

export default ChatMessage;
