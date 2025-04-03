import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, X, ChevronDown, ChevronUp } from 'lucide-react';

interface Message {
  id: number;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const ChatComponent: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      content: "Hello! I'm your SmartSea fishing assistant. Ask me about fishing zones, weather conditions, or border warnings.",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (inputMessage.trim() === '') return;
    
    // Add user message to chat
    const userMessage: Message = {
      id: messages.length,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      // Send message to backend
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: inputMessage,
          history: messages.map(m => ({
            role: m.sender === 'user' ? 'user' : 'model',
            content: m.content
          }))
        }),
      });
      
      const data = await response.json();
      
      // Add bot response to chat
      const botMessage: Message = {
        id: messages.length + 1,
        content: data.response,
        sender: 'bot',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: messages.length + 1,
        content: "Sorry, I'm having trouble connecting right now. Please try again later.",
        sender: 'bot',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Chat Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 shadow-lg flex items-center justify-center"
      >
        {isOpen ? <X size={24} /> : <Bot size={24} />}
      </button>
      
      {/* Chat Window */}
      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 sm:w-96 bg-white rounded-lg shadow-xl flex flex-col overflow-hidden border border-gray-200">
          {/* Chat Header */}
          <div className="bg-blue-600 text-white p-3 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Bot size={20} />
              <h3 className="font-medium">SmartSea Assistant</h3>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-white">
              <ChevronDown size={20} />
            </button>
          </div>
          
          {/* Messages Container */}
          <div className="flex-1 p-3 overflow-y-auto max-h-96 min-h-64">
            {messages.map(message => (
              <div 
                key={message.id}
                className={`mb-3 ${
                  message.sender === 'user' 
                    ? 'ml-auto max-w-[80%]' 
                    : 'mr-auto max-w-[80%]'
                }`}
              >
                <div className={`p-3 rounded-lg ${
                  message.sender === 'user'
                    ? 'bg-blue-100 text-blue-900'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {message.content}
                </div>
                <div className={`text-xs mt-1 text-gray-500 ${
                  message.sender === 'user' ? 'text-right' : 'text-left'
                }`}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="mr-auto max-w-[80%] mb-3">
                <div className="bg-gray-100 text-gray-800 p-3 rounded-lg flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="border-t border-gray-200 p-3">
            <div className="flex gap-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message here..."
                className="flex-1 p-2 border rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={1}
              />
              <button 
                onClick={sendMessage}
                disabled={inputMessage.trim() === '' || isLoading}
                className={`p-2 rounded ${
                  inputMessage.trim() === '' || isLoading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatComponent;