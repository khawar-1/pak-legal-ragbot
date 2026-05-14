"use client";
import {
  AppBar,
  Avatar,
  Box,
  Container,
  Toolbar,
  InputAdornment,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Fade,
  Card,
  CardContent,
  IconButton,
} from "@mui/material";
import {
  Send,
  SmartToy,
  Lightbulb,
  Person,
  Gavel,
  Delete
} from "@mui/icons-material";
import { useState, useRef, useEffect } from "react";

// Function to format text with bullet points, bold text, and line breaks
const formatText = (text: string) => {
  if (!text) return "";

  const paragraphs = text.split('\n\n').map(p => p.trim()).filter(p => p.length > 0);

  return paragraphs.map((paragraph, pIndex) => {
    const lines = paragraph.split('\n').map(line => line.trim()).filter(line => line.length > 0);

    return (
      <Box key={pIndex} sx={{ mb: 2 }}>
        {lines.map((line, lIndex) => {
          const isBullet = line.match(/^[-•]\s/) || line.match(/^\d+\.\s/) || line.match(/^\*\s/);

          if (isBullet) {
            return (
              <Box key={lIndex} sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                <Typography variant="body2" sx={{ mr: 1.5, color: 'primary.main', fontWeight: 600, mt: 0.2 }}>
                  •
                </Typography>
                <Typography variant="body2" color="white">
                  {formatBoldText(line.replace(/^[-•*]\s/, '').replace(/^\d+\.\s/, ''))}
                </Typography>
              </Box>
            );
          }

          return (
            <Typography key={lIndex} variant="body2" color="white" sx={{ mb: 1, lineHeight: 1.6 }}>
              {formatBoldText(line)}
            </Typography>
          );
        })}
      </Box>
    );
  });
};

const formatBoldText = (text: string) => {
  const parts = text.split(/(\*\*.*?\*\*)/);

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Box key={`bold-${index}`} component="span" sx={{ fontWeight: 600, color: 'white' }}>
          {part.slice(2, -2)}
        </Box>
      );
    }
    return <span key={`text-${index}`}>{part}</span>;
  });
};

interface ChatMessage {
  sender: string;
  text: string;
  answer?: string;
  timestamp?: Date;
}

function ChatMessageComponent({ sender, text, answer, timestamp }: ChatMessage) {
  const isAI = sender === "AI";

  return (
    <Fade in timeout={500}>
      <Box
        sx={{
          display: "flex",
          justifyContent: isAI ? "flex-end" : "flex-start",
          alignItems: "flex-start",
          width: "100%",
          mb: 3,
          px: 2,
          pl: isAI ? 4 : 2,
          pr: isAI ? 2 : 4,
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: isAI ? "row-reverse" : "row",
            alignItems: "flex-start",
            gap: 2,
            maxWidth: "90%",
            width: "100%",
          }}
        >
          <Avatar
            sx={{
              width: 40,
              height: 40,
              bgcolor: isAI
                ? "linear-gradient(135deg, #1a472a 0%, #2d5016 100%)"
                : "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            }}
          >
            {isAI ? <Gavel /> : <Person />}
          </Avatar>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 1, width: "100%" }}>
            <Typography
              variant="caption"
              sx={{ color: "text.secondary", fontWeight: 600, px: 1 }}
            >
              {isAI ? "Legal Assistant" : "You"}
            </Typography>

            {!isAI && (
              <Paper
                elevation={2}
                sx={{
                  p: 2,
                  bgcolor: "rgba(33, 150, 243, 0.1)",
                  color: "white",
                  borderRadius: "18px 18px 4px 18px",
                  boxShadow: "0 4px 12px rgba(33, 150, 243, 0.2)",
                  border: "1px solid rgba(33, 150, 243, 0.3)",
                }}
              >
                <Typography variant="body1" color="white">{text}</Typography>
              </Paper>
            )}

            {isAI && answer && (
              <Card
                elevation={2}
                sx={{
                  borderRadius: "18px 18px 18px 4px",
                  bgcolor: "rgba(26, 71, 42, 0.2)",
                  color: "white",
                  boxShadow: "0 4px 12px rgba(26, 71, 42, 0.3)",
                  border: "1px solid rgba(26, 71, 42, 0.4)",
                }}
              >
                <CardContent sx={{ p: 2 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Gavel sx={{ fontSize: 20, color: "#4caf50" }} />
                    <Typography variant="subtitle2" fontWeight={600} color="white">
                      Legal Assistant
                    </Typography>
                  </Box>
                  <Box>{formatText(answer)}</Box>
                </CardContent>
              </Card>
            )}
          </Box>
        </Box>
      </Box>
    </Fade>
  );
}

const generateSessionId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const getSessionId = (): string => {
  if (typeof window === 'undefined') return generateSessionId();

  const key = 'legal_chat_session_id';
  let sessionId = localStorage.getItem(key);

  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(key, sessionId);
  }

  return sessionId;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleResetSession = async () => {
    try {
      const sessionId = getSessionId();
      await fetch(`/api/session/${sessionId}`, {
        method: "DELETE"
      });
      localStorage.removeItem("legal_chat_session_id");
      setChatHistory([]);
    } catch (error) {
      console.error("Error resetting session:", error);
    }
  };

  const fetchResponse = async (userMessage: string) => {
    setIsLoading(true);
    try {
      const sessionId = getSessionId();

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_input: userMessage,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();

      const chatMessage: ChatMessage = {
        sender: "AI",
        text: "",
        answer: data.answer || "",
        timestamp: new Date(),
      };

      setChatHistory((prev) => [...prev, chatMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorMessage: ChatMessage = {
        sender: "AI",
        text: `Connection error: ${error instanceof Error ? error.message : String(error)}. Make sure FastAPI backend is running on port 8000.`,
        timestamp: new Date()
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    if (!message.trim() || isLoading) return;
    const userMessage = message.trim();
    const userMessageObj: ChatMessage = {
      sender: "User",
      text: userMessage,
      timestamp: new Date(),
    };
    setChatHistory((prev) => [...prev, userMessageObj]);
    setMessage("");
    fetchResponse(userMessage);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#000000",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <AppBar
        position="static"
        sx={{
          bgcolor: "rgba(26, 71, 42, 0.95)",
          backdropFilter: "blur(10px)",
          boxShadow: "0 2px 20px rgba(0,0,0,0.3)"
        }}
      >
        <Toolbar>
          <Gavel sx={{ mr: 2, fontSize: 28 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Legal Case Assistant
          </Typography>
          <Typography variant="caption" sx={{ mr: 2, opacity: 0.8 }}>
            Pakistan Law RAG Chatbot
          </Typography>
          <IconButton color="inherit" onClick={handleResetSession} title="Reset Session">
            <Delete />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Chat Area */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          py: 3,
          "&::-webkit-scrollbar": { width: "8px" },
          "&::-webkit-scrollbar-track": { background: "transparent" },
          "&::-webkit-scrollbar-thumb": {
            background: "rgba(255,255,255,0.2)",
            borderRadius: "4px"
          },
        }}
      >
        <Container maxWidth="lg">
          {chatHistory.length === 0 && (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "60vh",
                textAlign: "center",
              }}
            >
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: "rgba(26, 71, 42, 0.3)",
                  mb: 3,
                }}
              >
                <Gavel sx={{ fontSize: 40 }} />
              </Avatar>
              <Typography variant="h4" color="white" gutterBottom fontWeight={600}>
                Legal Case Assistant
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500, mb: 4 }}>
                Ask me about Pakistan legal cases, court judgments, case law references,
                statutes, and legal principles. I can help you understand case citations
                and legal precedents.
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, justifyContent: "center" }}>
                {[
                  "What is pre-emption in property law?",
                  "Tell me about case 2008 CLC 332",
                  "What is the doctrine of sinker?",
                  "Explain AJK Prior Purchase Act"
                ].map((suggestion) => (
                  <Paper
                    key={suggestion}
                    onClick={() => {
                      setMessage(suggestion);
                    }}
                    sx={{
                      p: 1.5,
                      px: 2,
                      bgcolor: "rgba(26, 71, 42, 0.2)",
                      border: "1px solid rgba(26, 71, 42, 0.4)",
                      borderRadius: 2,
                      cursor: "pointer",
                      transition: "all 0.2s",
                      "&:hover": {
                        bgcolor: "rgba(26, 71, 42, 0.3)",
                        transform: "translateY(-2px)",
                      },
                    }}
                  >
                    <Typography variant="body2" color="white">
                      {suggestion}
                    </Typography>
                  </Paper>
                ))}
              </Box>
            </Box>
          )}

          {chatHistory.map((msg, index) => (
            <ChatMessageComponent key={index} {...msg} />
          ))}

          {isLoading && (
            <Box sx={{ display: "flex", justifyContent: "flex-end", px: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <CircularProgress size={24} sx={{ color: "#4caf50" }} />
                <Typography variant="body2" color="text.secondary">
                  Analyzing legal query...
                </Typography>
              </Box>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Container>
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          p: 2,
          bgcolor: "rgba(26, 71, 42, 0.1)",
          borderTop: "1px solid rgba(255,255,255,0.1)",
        }}
      >
        <Container maxWidth="lg">
          <TextField
            fullWidth
            placeholder="Ask about legal cases, statutes, or court judgments..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            sx={{
              "& .MuiOutlinedInput-root": {
                color: "white",
                bgcolor: "rgba(255,255,255,0.05)",
                borderRadius: 3,
                "& fieldset": { borderColor: "rgba(255,255,255,0.2)" },
                "&:hover fieldset": { borderColor: "rgba(76, 175, 80, 0.5)" },
                "&.Mui-focused fieldset": { borderColor: "#4caf50" },
              },
              "& .MuiInputBase-input::placeholder": {
                color: "rgba(255,255,255,0.5)",
              },
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSend}
                    disabled={isLoading || !message.trim()}
                    sx={{
                      bgcolor: message.trim() ? "#4caf50" : "transparent",
                      color: "white",
                      "&:hover": { bgcolor: "#45a049" },
                      "&.Mui-disabled": { color: "rgba(255,255,255,0.3)" },
                    }}
                  >
                    <Send />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Container>
      </Box>
    </Box>
  );
}