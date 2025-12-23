import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import { Message } from '../types';
import { getChatResponse } from '../backendService';

interface ChatInterfaceProps {
  onSaveWorkout: (title: string, content: string) => void;
}

interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

const STORAGE_KEY = 'fitcoach_chat_history';
const INITIAL_MESSAGE: Message = {
  id: '1',
  role: 'model',
  content: '# SYSTEM GOTOWY\nWprowadź zapytanie dotyczące planu treningowego lub analizy danych.',
  timestamp: Date.now()
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSaveWorkout }) => {
  // Load messages from localStorage or use the initial message
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : [INITIAL_MESSAGE];
  });

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    scrollToBottom();
  }, [isLoading]);

  useEffect(() => {
    const SpeechRecognition = (window as IWindow).SpeechRecognition || (window as IWindow).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.lang = 'pl-PL';
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };
      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
    
    // Configure marked options
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const history = messages.slice(-10).map(m => ({
      role: m.role,
      parts: [{ text: m.content }]
    }));

    const responseText = await getChatResponse(input, history);
    
    setMessages(prev => [...prev, {
      id: (Date.now() + 1).toString(),
      role: 'model',
      content: responseText,
      timestamp: Date.now()
    }]);
    setIsLoading(false);
  };

  const handleReset = () => {
    if (confirm('Czy na pewno chcesz wyczyścić historię czatu?')) {
      setMessages([INITIAL_MESSAGE]);
    }
  };

  // Helper to safely render markdown as HTML
  const getMarkdownHtml = (content: string) => {
    return { __html: marked.parse(content) as string };
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#020617] view-enter">
      {/* Tool Header - Condensed for mobile */}
      <header className="px-4 md:px-8 py-4 md:py-5 border-b border-white/5 bg-[#020617]/90 backdrop-blur-xl sticky top-0 z-10 flex items-center justify-between shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
          </div>
          <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Terminal AI</h2>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleReset}
            className="text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-all bg-white/5 px-3 py-1.5 rounded-lg border border-white/5 flex items-center gap-2"
          >
            <i className="fas fa-trash-can text-[8px]"></i> Wyczyść
          </button>
        </div>
      </header>

      {/* Workspace - Improved padding and font sizing for mobile */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scrollbar-hide">
        <div className="max-w-4xl mx-auto space-y-8">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
            >
              <div className={`relative w-full sm:w-auto sm:max-w-[85%] rounded-[1.5rem] md:rounded-[2rem] shadow-xl ${
                msg.role === 'user' 
                  ? 'bg-blue-600/10 border border-blue-500/20 text-blue-50 p-5 md:p-6 ml-10 sm:ml-0' 
                  : 'bg-slate-900/60 border border-white/5 text-slate-100 p-6 md:p-10 mr-4 sm:mr-0'
              }`}>
                {msg.role === 'model' && (
                  <div className="absolute -top-2.5 left-6 bg-blue-600 text-white text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full shadow-lg">
                    System
                  </div>
                )}
                
                <div 
                  className={`prose prose-invert max-w-none text-sm md:text-base
                    prose-headings:font-black prose-headings:tracking-tight
                    prose-h1:text-xl md:h1:text-2xl prose-h1:mb-4
                    prose-h2:text-lg prose-h2:mt-6 prose-h2:text-blue-400
                    prose-p:leading-relaxed prose-p:text-slate-300
                    prose-strong:text-white prose-strong:font-black
                    prose-ul:my-4 prose-li:my-1
                  `}
                  dangerouslySetInnerHTML={getMarkdownHtml(msg.content)}
                />
                
                {msg.role === 'model' && msg.id !== '1' && (
                  <div className="mt-8 pt-6 border-t border-white/5 flex flex-wrap gap-2">
                    <button 
                      onClick={() => onSaveWorkout(msg.content.split('\n')[0].replace('# ', '') || `Plan ${new Date().toLocaleDateString()}`, msg.content)}
                      className="text-[9px] font-black uppercase tracking-widest bg-blue-600 hover:bg-blue-500 px-4 py-2.5 rounded-xl text-white transition-all shadow-lg flex items-center gap-2"
                    >
                      <i className="fas fa-save"></i> Zapisz
                    </button>
                    <button 
                      onClick={() => navigator.clipboard.writeText(msg.content)}
                      className="text-[9px] font-black uppercase tracking-widest bg-white/5 px-4 py-2.5 rounded-xl text-slate-300 border border-white/5"
                    >
                      Kopiuj
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-3 px-6 py-3 rounded-full bg-slate-900/40 border border-white/5">
                <div className="flex gap-1.5">
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Analiza...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Command Input - Compact and touch-friendly */}
      <div className="p-4 md:p-10 bg-[#020617] border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex items-center gap-2 md:gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Napisz do asystenta..."
                className="w-full bg-slate-900/80 border border-white/10 text-white rounded-2xl py-4 px-5 focus:outline-none focus:border-blue-500/50 text-sm placeholder:text-slate-700"
              />
            </div>
            <button
              type="button"
              onClick={toggleListening}
              className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all border ${
                isListening ? 'bg-red-500/20 text-red-500 border-red-500/30 animate-pulse' : 'bg-white/5 text-slate-500 border-white/5'
              }`}
            >
              <i className={`fas ${isListening ? 'fa-microphone' : 'fa-microphone-slash'}`}></i>
            </button>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-20 text-white w-12 h-12 rounded-xl flex items-center justify-center transition-all shadow-xl shadow-blue-900/40"
            >
              <i className={`fas ${isLoading ? 'fa-circle-notch fa-spin' : 'fa-arrow-up'}`}></i>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;