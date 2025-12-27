import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Dumbbell, Apple, Moon, Loader2, Trash2 } from 'lucide-react';
import ChatMessage from '../components/ChatMessage';
import GlassCard from '../components/GlassCard';
import { getChatResponse, getChatHistory, clearChatHistory } from '../services/backendService';
import { useAuth } from '../context/AuthContext';
import './AICoach.css';

function AICoach() {
    const { isAuthenticated } = useAuth();
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(true);
    const messagesEndRef = useRef(null);

    const welcomeMessage = {
        id: 'welcome',
        text: 'Cześć! 👋 Jestem Twoim AI trenerem. Jak mogę Ci dzisiaj pomóc? Mogę zaplanować trening, doradzić w kwestii diety lub odpowiedzieć na pytania o ćwiczenia.',
        isAI: true,
        timestamp: new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })
    };

    const quickActions = [
        { icon: Dumbbell, label: 'Zaplanuj trening', prompt: 'Zaplanuj mi trening na dziś' },
        { icon: Apple, label: 'Porada dietetyczna', prompt: 'Daj mi poradę dietetyczną' },
        { icon: Moon, label: 'Tips na regenerację', prompt: 'Jakie są najlepsze sposoby na regenerację po treningu?' },
    ];

    // Load chat history on mount
    useEffect(() => {
        const loadHistory = async () => {
            if (!isAuthenticated) {
                setMessages([welcomeMessage]);
                setHistoryLoading(false);
                return;
            }

            try {
                const data = await getChatHistory();
                if (data.messages && data.messages.length > 0) {
                    // Convert backend messages to frontend format
                    const loadedMessages = data.messages.map(msg => ({
                        id: msg.id,
                        text: msg.content,
                        isAI: msg.role === 'assistant',
                        timestamp: new Date(msg.created_at).toLocaleTimeString('pl-PL', {
                            hour: '2-digit',
                            minute: '2-digit'
                        })
                    }));
                    setMessages(loadedMessages);
                } else {
                    setMessages([welcomeMessage]);
                }
            } catch (error) {
                console.error('Failed to load chat history:', error);
                setMessages([welcomeMessage]);
            } finally {
                setHistoryLoading(false);
            }
        };

        loadHistory();
    }, [isAuthenticated]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Convert messages to history format for API
    const getHistory = () => {
        return messages.filter(msg => msg.id !== 'welcome').map(msg => ({
            role: msg.isAI ? 'assistant' : 'user',
            content: msg.text
        }));
    };

    const handleSend = async (customMessage = null) => {
        const messageText = customMessage || inputValue.trim();
        if (!messageText || isLoading) return;

        const newMessage = {
            id: Date.now(),
            text: messageText,
            isAI: false,
            timestamp: new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, newMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const history = getHistory();
            const response = await getChatResponse(messageText, history);

            const aiResponse = {
                id: Date.now() + 1,
                text: response,
                isAI: true,
                timestamp: new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, aiResponse]);
        } catch (error) {
            const errorResponse = {
                id: Date.now() + 1,
                text: '❌ ' + error.message,
                isAI: true,
                timestamp: new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, errorResponse]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClearHistory = async () => {
        if (!window.confirm('Czy na pewno chcesz wyczyścić historię chatu?')) return;

        try {
            await clearChatHistory();
            setMessages([welcomeMessage]);
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    };

    const handleQuickAction = (prompt) => {
        handleSend(prompt);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (historyLoading) {
        return (
            <div className="page ai-coach">
                <div className="loading-container">
                    <Loader2 size={40} className="spinning" />
                    <p>Ładowanie historii...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page ai-coach">
            <header className="page-header">
                <div>
                    <h1 className="page-title">
                        <Sparkles size={24} className="title-icon" />
                        AI Coach
                    </h1>
                    <p className="page-subtitle">Twój osobisty trener 24/7</p>
                </div>
                <div className="coach-header-actions">
                    {isAuthenticated && messages.length > 1 && (
                        <button
                            className="clear-history-btn"
                            onClick={handleClearHistory}
                            title="Wyczyść historię"
                        >
                            <Trash2 size={18} />
                        </button>
                    )}
                    <div className="coach-status">
                        <span className={`status-dot ${isLoading ? 'status-dot--loading' : ''}`}></span>
                        {isLoading ? 'Myśli...' : 'Online'}
                    </div>
                </div>
            </header>

            {/* Quick Actions */}
            <div className="quick-actions">
                {quickActions.map(({ icon: Icon, label, prompt }) => (
                    <button
                        key={label}
                        className="quick-action-btn"
                        onClick={() => handleQuickAction(prompt)}
                        disabled={isLoading}
                    >
                        <Icon size={16} />
                        {label}
                    </button>
                ))}
            </div>

            {/* Chat Messages */}
            <div className="chat-container">
                <div className="chat-messages">
                    {messages.map(msg => (
                        <ChatMessage
                            key={msg.id}
                            message={msg.text}
                            isAI={msg.isAI}
                            timestamp={msg.timestamp}
                        />
                    ))}
                    {isLoading && (
                        <div className="typing-indicator">
                            <Loader2 size={20} className="spinning" />
                            <span>AI Coach pisze...</span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <GlassCard className="chat-input-container">
                <div className="chat-input-wrapper">
                    <textarea
                        className="chat-input"
                        placeholder="Napisz wiadomość..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        className={`send-btn ${inputValue.trim() && !isLoading ? 'send-btn--active' : ''}`}
                        onClick={() => handleSend()}
                        disabled={!inputValue.trim() || isLoading}
                    >
                        {isLoading ? <Loader2 size={20} className="spinning" /> : <Send size={20} />}
                    </button>
                </div>
            </GlassCard>
        </div>
    );
}

export default AICoach;
