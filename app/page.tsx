"use client";
import Image from "next/image";
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
  Chip,
  CircularProgress,
  Fade,
  Slide,
  Card,
  CardContent,
  Divider,
  IconButton,
} from "@mui/material";
import { 
  Mic, 
  Send, 
  Cloud, 
  SmartToy, 
  Psychology, 
  Lightbulb,
  Person,
  AutoAwesome
} from "@mui/icons-material";
import { useState, useRef, useEffect } from "react";

// Function to format text with bullet points, bold text, and line breaks
const formatText = (text: string) => {
  if (!text) return "";
  
  // Split by double line breaks first to preserve paragraphs
  const paragraphs = text.split('\n\n').map(p => p.trim()).filter(p => p.length > 0);
  
  return paragraphs.map((paragraph, pIndex) => {
    // Split each paragraph by single line breaks
    const lines = paragraph.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    
    return (
      <Box key={pIndex} sx={{ mb: 2 }}>
        {lines.map((line, lIndex) => {
          // Check if line starts with common bullet indicators
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
          
          // Regular line with potential bold text
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

// Function to format bold text
const formatBoldText = (text: string) => {
  const parts = text.split(/(\*\*.*?\*\*)/);
  
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Box key={index} component="span" sx={{ fontWeight: 600, color: 'white' }}>
          {part.slice(2, -2)}
        </Box>
      );
    }
    return part;
  });
};

interface ChatMessage {
  sender: string;
  text: string;
  answer?: string;
  tips?: string;
  timestamp?: Date;
  responseType?: string;
  intentClassification?: {
    intent: string;
    confidence: number;
    reasoning: string;
  };
  requirementFollowUp?: {
    type: string;
    status: string;
    current_requirements: any;
    missing_fields: string[];
    follow_up_questions: Array<{
      field: string;
      question: string;
      context: string;
    }>;
    progress: string;
    message: string;
  };
  completeRequirements?: {
    type: string;
    status: string;
    requirements: any;
    message: string;
  };
}

function ChatMessage({ 
  sender, 
  text, 
  tips, 
  answer, 
  timestamp, 
  responseType,
  intentClassification,
  requirementFollowUp,
  completeRequirements 
}: ChatMessage) {
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
          {/* Avatar */}
          <Avatar
            sx={{
              width: 40,
              height: 40,
              bgcolor: isAI 
                ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" 
                : "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            }}
          >
            {isAI ? <SmartToy /> : <Person />}
          </Avatar>

          {/* Message Content */}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 1,
              width: "100%",
            }}
          >
            {/* Sender Name */}
            <Typography
              variant="caption"
              sx={{
                color: "text.secondary",
                fontWeight: 600,
                px: 1,
              }}
            >
              {isAI ? "AWS Assistant" : "You"}
            </Typography>

            {/* User Message */}
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

            {/* AI Response */}
            {isAI && (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {/* Intent Classification Info */}
                {intentClassification && (
                  <Box sx={{ mb: 1 }}>
                    <Chip
                      label={`${intentClassification.intent.replace('_', ' ')} (${(intentClassification.confidence * 100).toFixed(0)}%)`}
                      size="small"
                      sx={{
                        bgcolor: intentClassification.intent === "aws_query" ? "rgba(33, 150, 243, 0.2)" : "rgba(76, 175, 80, 0.2)",
                        color: "white",
                        fontSize: "0.7rem"
                      }}
                    />
                  </Box>
                )}

                {/* AWS Query Response (Existing) */}
                {responseType === "aws_query_response" && (
                  <>
                    {/* Question Analysis */}
                    {text && (
                      <Card
                        elevation={2}
                        sx={{
                          borderRadius: "18px 18px 18px 4px",
                          bgcolor: "rgba(33, 150, 243, 0.15)",
                          color: "white",
                          boxShadow: "0 4px 12px rgba(33, 150, 243, 0.2)",
                          border: "1px solid rgba(33, 150, 243, 0.3)",
                        }}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                            <Psychology sx={{ fontSize: 20, color: "#2196f3" }} />
                            <Typography variant="subtitle2" fontWeight={600} color="white">
                              Question Analysis
                            </Typography>
                          </Box>
                          <Box>{formatText(text)}</Box>
                        </CardContent>
                      </Card>
                    )}

                    {/* Main Answer */}
                    {answer && (
                      <Card
                        elevation={2}
                        sx={{
                          borderRadius: "18px 18px 18px 4px",
                          bgcolor: "rgba(33, 150, 243, 0.2)",
                          color: "white",
                          boxShadow: "0 4px 12px rgba(33, 150, 243, 0.3)",
                          border: "1px solid rgba(33, 150, 243, 0.4)",
                        }}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                            <Cloud sx={{ fontSize: 20, color: "#2196f3" }} />
                            <Typography variant="subtitle2" fontWeight={600} color="white">
                              AWS Answer
                            </Typography>
                          </Box>
                          <Box>{formatText(answer)}</Box>
                        </CardContent>
                      </Card>
                    )}

                    {/* Tips */}
                    {tips && (
                      <Card
                        elevation={2}
                        sx={{
                          borderRadius: "18px 18px 18px 4px",
                          bgcolor: "rgba(33, 150, 243, 0.1)",
                          color: "white",
                          boxShadow: "0 4px 12px rgba(33, 150, 243, 0.2)",
                          border: "1px solid rgba(33, 150, 243, 0.3)",
                        }}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                            <Lightbulb sx={{ fontSize: 20, color: "#2196f3" }} />
                            <Typography variant="subtitle2" fontWeight={600} color="white">
                              Pro Tips
                            </Typography>
                          </Box>
                          <Box>{formatText(tips)}</Box>
                        </CardContent>
                      </Card>
                    )}
                  </>
                )}

                {/* Requirement Follow-up Response */}
                {responseType === "requirement_follow_up" && requirementFollowUp && (
                  <Card
                    elevation={2}
                    sx={{
                      borderRadius: "18px 18px 18px 4px",
                      bgcolor: "rgba(76, 175, 80, 0.15)",
                      color: "white",
                      boxShadow: "0 4px 12px rgba(76, 175, 80, 0.2)",
                      border: "1px solid rgba(76, 175, 80, 0.3)",
                    }}
                  >
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                        <Psychology sx={{ fontSize: 20, color: "#4caf50" }} />
                        <Typography variant="subtitle2" fontWeight={600} color="white">
                          Project Requirements Gathering
                        </Typography>
                        <Chip
                          label={requirementFollowUp.progress}
                          size="small"
                          sx={{ ml: "auto", bgcolor: "rgba(76, 175, 80, 0.3)", color: "white" }}
                        />
                      </Box>
                      
                      <Typography variant="body2" color="white" sx={{ mb: 2 }}>
                        {requirementFollowUp.message}
                      </Typography>

                      {requirementFollowUp.follow_up_questions.map((q, index) => (
                        <Box key={index} sx={{ mb: 2, p: 2, bgcolor: "rgba(76, 175, 80, 0.1)", borderRadius: 2 }}>
                          <Typography variant="body2" fontWeight={600} color="white" sx={{ mb: 1 }}>
                            {q.question}
                          </Typography>
                          <Typography variant="caption" color="rgba(255, 255, 255, 0.8)">
                            {q.context}
                          </Typography>
                        </Box>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Complete Requirements Response */}
                {responseType === "complete_requirements" && completeRequirements && (
                  <Card
                    elevation={2}
                    sx={{
                      borderRadius: "18px 18px 18px 4px",
                      bgcolor: "rgba(76, 175, 80, 0.2)",
                      color: "white",
                      boxShadow: "0 4px 12px rgba(76, 175, 80, 0.3)",
                      border: "1px solid rgba(76, 175, 80, 0.4)",
                    }}
                  >
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                        <AutoAwesome sx={{ fontSize: 20, color: "#4caf50" }} />
                        <Typography variant="subtitle2" fontWeight={600} color="white">
                          Requirements Extracted Successfully!
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="white" sx={{ mb: 2 }}>
                        {completeRequirements.message}
                      </Typography>

                      <Box sx={{ p: 2, bgcolor: "rgba(76, 175, 80, 0.1)", borderRadius: 2 }}>
                        <Typography variant="body2" fontWeight={600} color="white" sx={{ mb: 1 }}>
                          📋 Extracted Requirements:
                        </Typography>
                        <pre style={{ 
                          color: "white", 
                          fontSize: "0.8rem", 
                          whiteSpace: "pre-wrap",
                          fontFamily: "inherit"
                        }}>
                          {JSON.stringify(completeRequirements.requirements, null, 2)}
                        </pre>
                      </Box>
                    </CardContent>
                  </Card>
                )}
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </Fade>
  );
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const fetchResponse = async (userMessage: string) => {
    setIsLoading(true);
    try {
      // Connect directly to FastAPI backend, bypassing Next.js proxy
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_input: userMessage,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      
      console.log("Response data:", data);

      // Handle different response types
      let chatMessage: ChatMessage = {
        sender: "AI",
        text: "",
        timestamp: new Date(),
        responseType: data.response_type,
        intentClassification: data.intent_classification
      };

      if (data.response_type === "aws_query_response") {
        // AWS Query Response
        chatMessage.text = data.question_analysis || "";
        chatMessage.answer = data.answer || "";
        chatMessage.tips = data.tips || "";
      } else if (data.response_type === "requirement_follow_up") {
        // Requirement Follow-up Response
        chatMessage.requirementFollowUp = data.requirement_follow_up;
        chatMessage.text = data.requirement_follow_up?.message || "";
      } else if (data.response_type === "complete_requirements") {
        // Complete Requirements Response
        chatMessage.completeRequirements = data.complete_requirements;
        chatMessage.text = data.complete_requirements?.message || "";
      }

      // Add the AI response to chat history
      setChatHistory((prevChatHistory) => [
        ...prevChatHistory,
        chatMessage
      ]);
    } catch (error) {
      console.error("Error fetching response:", error);
      // Add error message to chat with more details
      setChatHistory((prevChatHistory) => [
        ...prevChatHistory,
        { 
          sender: "AI", 
          text: `Connection error: ${
            error instanceof Error ? error.message : String(error)
          }. Make sure FastAPI backend is running on port 8000.`,
          timestamp: new Date()
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();

    // Add the user's message to chat history
    setChatHistory((prevChatHistory) => [
      ...prevChatHistory,
      { 
        sender: "User", 
        text: userMessage,
        timestamp: new Date()
      },
    ]);

    // Clear the message input
    setMessage("");

    // Fetch AI response
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
        position="sticky" 
        sx={{ 
          bgcolor: "rgba(0, 0, 0, 0.95)",
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Avatar
              sx={{
                width: 50,
                height: 50,
                bgcolor: "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)",
              }}
            >
              <Cloud />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={700} color="white">
                AWS Cloud Assistant
              </Typography>
              
            </Box>
          </Box>
          
          <Chip
            icon={<AutoAwesome />}
            label="AI Powered"
            color="primary"
            variant="outlined"
            sx={{
              bgcolor: "rgba(33, 150, 243, 0.1)",
              borderColor: "#2196f3",
              color: "#2196f3",
            }}
          />
        </Toolbar>
      </AppBar>

      {/* Chat Area */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          py: 2,
          px: 1,
          "&::-webkit-scrollbar": {
            width: "6px",
          },
          "&::-webkit-scrollbar-track": {
            background: "rgba(255, 255, 255, 0.05)",
            borderRadius: "3px",
          },
          "&::-webkit-scrollbar-thumb": {
            background: "rgba(33, 150, 243, 0.5)",
            borderRadius: "3px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            background: "rgba(33, 150, 243, 0.7)",
          },
        }}
      >
        <Container maxWidth="lg">
          {chatHistory.length === 0 && (
            <Fade in timeout={1000}>
              <Box
                sx={{
                  textAlign: "center",
                  py: 8,
                  color: "white",
                }}
              >
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    mx: "auto",
                    mb: 3,
                    bgcolor: "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)",
                    boxShadow: "0 8px 32px rgba(33, 150, 243, 0.3)",
                  }}
                >
                  <SmartToy sx={{ fontSize: 40 }} />
                </Avatar>
                <Typography variant="h4" fontWeight={700} gutterBottom>
                  Welcome to AWS Cloud Assistant
                </Typography>
                <Typography variant="h6" sx={{ opacity: 0.8, mb: 4 }}>
                  Ask me anything about AWS services, architecture, and best practices
                </Typography>
                <Box sx={{ display: "flex", gap: 2, justifyContent: "center", flexWrap: "wrap" }}>
                  <Chip label="What is AWS Lambda?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                  <Chip label="How to set up a VPC?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                  <Chip label="S3 vs DynamoDB?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                </Box>
              </Box>
            </Fade>
          )}

          {chatHistory.map((chatMessage, index) => (
            <ChatMessage
              key={index}
              sender={chatMessage.sender}
              text={chatMessage.text}
              tips={chatMessage.tips}
              answer={chatMessage.answer}
              timestamp={chatMessage.timestamp}
              responseType={chatMessage.responseType}
              intentClassification={chatMessage.intentClassification}
              requirementFollowUp={chatMessage.requirementFollowUp}
              completeRequirements={chatMessage.completeRequirements}
            />
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <Fade in>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-end",
                  alignItems: "center",
                  gap: 2,
                  mb: 3,
                  px: 2,
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    bgcolor: "rgba(33, 150, 243, 0.15)",
                    px: 3,
                    py: 2,
                    borderRadius: "18px 18px 18px 4px",
                    boxShadow: "0 4px 12px rgba(33, 150, 243, 0.2)",
                    border: "1px solid rgba(33, 150, 243, 0.3)",
                  }}
                >
                  <CircularProgress size={20} sx={{ color: "#2196f3" }} />
                  <Typography variant="body2" color="white">
                    AWS Assistant is thinking...
                  </Typography>
                </Box>
                <Avatar
                  sx={{
                    width: 40,
                    height: 40,
                    bgcolor: "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)",
                  }}
                >
                  <SmartToy />
                </Avatar>
              </Box>
            </Fade>
          )}
          
          <div ref={messagesEndRef} />
        </Container>
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          bgcolor: "rgba(0, 0, 0, 0.3)",
          backdropFilter: "blur(15px)",
          borderTop: "1px solid rgba(33, 150, 243, 0.2)",
          p: 2,
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: "flex",
              gap: 2,
              alignItems: "flex-end",
            }}
          >
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Ask me anything about AWS..."
              variant="outlined"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              sx={{
                "& .MuiOutlinedInput-root": {
                  borderRadius: "25px",
                  bgcolor: "rgba(255, 255, 255, 0.05)",
                  backdropFilter: "blur(10px)",
                  color: "white",
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
                  "& fieldset": {
                    border: "1px solid rgba(33, 150, 243, 0.3)",
                  },
                  "&:hover fieldset": {
                    border: "1px solid rgba(33, 150, 243, 0.5)",
                  },
                  "&.Mui-focused fieldset": {
                    border: "2px solid #2196f3",
                  },
                },
                "& .MuiInputBase-input": {
                  color: "white",
                  "&::placeholder": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                },
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Mic sx={{ color: "rgba(255, 255, 255, 0.7)" }} />
                  </InputAdornment>
                ),
              }}
            />
            <IconButton
              onClick={handleSend}
              disabled={!message.trim() || isLoading}
              sx={{
                bgcolor: "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)",
                color: "white",
                width: 50,
                height: 50,
                boxShadow: "0 4px 12px rgba(33, 150, 243, 0.3)",
                "&:hover": {
                  bgcolor: "linear-gradient(135deg, #1976d2 0%, #1565c0 100%)",
                  transform: "translateY(-2px)",
                  boxShadow: "0 6px 16px rgba(33, 150, 243, 0.4)",
                },
                "&:disabled": {
                  bgcolor: "rgba(255,255,255,0.12)",
                  color: "rgba(255,255,255,0.26)",
                },
                transition: "all 0.2s ease-in-out",
              }}
            >
              <Send />
            </IconButton>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}