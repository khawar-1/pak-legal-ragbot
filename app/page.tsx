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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from "@mui/material";
import { 
  Mic, 
  Send, 
  Cloud, 
  SmartToy, 
  Psychology, 
  Lightbulb,
  Person,
  AutoAwesome,
  Build,
  Chat,
  Assessment,
  SwitchLeft,
  SwitchRight,
  MenuOpen,
  Menu,
  Refresh,
  Delete
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

type ChatMode = "aws_chat" | "requirement_extraction";

// Generate UUID for session_id
const generateSessionId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Get or create session_id from localStorage
const getSessionId = (mode: ChatMode): string => {
  if (typeof window === 'undefined') return generateSessionId();
  
  const key = `${mode}_session_id`;
  let sessionId = localStorage.getItem(key);
  
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(key, sessionId);
  }
  
  return sessionId;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [awsChatHistory, setAwsChatHistory] = useState<ChatMessage[]>([]);
  const [requirementChatHistory, setRequirementChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMode, setLoadingMode] = useState<ChatMode | null>(null);
  const [currentMode, setCurrentMode] = useState<ChatMode>("aws_chat");
  const [requirementProgress, setRequirementProgress] = useState<{
    completed: number;
    total: number;
    missingFields: string[];
  }>({ completed: 0, total: 9, missingFields: [] });
  const [dashboardVisible, setDashboardVisible] = useState(true);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get current chat history based on mode
  const getCurrentChatHistory = () => {
    return currentMode === "aws_chat" ? awsChatHistory : requirementChatHistory;
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [awsChatHistory, requirementChatHistory]);

  // Load session data when switching to requirement extraction mode
  useEffect(() => {
    const loadSessionProgress = async () => {
      if (currentMode === "requirement_extraction") {
        const sessionId = getSessionId("requirement_extraction");
        try {
          const res = await fetch(`http://localhost:8000/api/session/${sessionId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.found && data.progress) {
              setRequirementProgress({
                completed: data.progress.completed,
                total: data.progress.total,
                missingFields: data.progress.missingFields || []
              });
            }
          }
        } catch (error) {
          console.error("Error loading session progress:", error);
        }
      }
    };

    loadSessionProgress();
  }, [currentMode]);

  const handleModeSwitch = (newMode: ChatMode) => {
    if (newMode !== currentMode) {
      setCurrentMode(newMode);
      // Progress will be loaded via useEffect when switching to requirement_extraction
    }
  };

  const toggleDashboard = () => {
    setDashboardVisible(!dashboardVisible);
  };

  const handleResetClick = () => {
    setResetDialogOpen(true);
  };

  const handleResetConfirm = async () => {
    setResetDialogOpen(false);
    
    try {
      const sessionId = getSessionId("requirement_extraction");
      
      // Delete session from MongoDB
      const res = await fetch(`http://localhost:8000/api/session/${sessionId}`, {
        method: "DELETE"
      });
      
      if (res.ok) {
        // Clear localStorage to generate new session_id
        localStorage.removeItem("requirement_extraction_session_id");
        
        // Clear chat history
        setRequirementChatHistory([]);
        
        // Reset progress
        setRequirementProgress({
          completed: 0,
          total: 9,
          missingFields: []
        });
        
        console.log("Session reset successfully");
      } else {
        console.error("Failed to reset session");
      }
    } catch (error) {
      console.error("Error resetting session:", error);
    }
  };

  const handleResetCancel = () => {
    setResetDialogOpen(false);
  };

  const fetchResponse = async (userMessage: string) => {
    setIsLoading(true);
    setLoadingMode(currentMode);
    try {
      // Get session_id for current mode
      const sessionId = getSessionId(currentMode);
      
      // Connect directly to FastAPI backend, bypassing Next.js proxy
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_input: userMessage,
          mode: currentMode,
          session_id: sessionId,
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
      } else if (data.response_type === "requirement_follow_up") {
        // Requirement Follow-up Response
        chatMessage.requirementFollowUp = data.requirement_follow_up;
        chatMessage.text = data.requirement_follow_up?.message || "";
        
        // Update progress tracking
        if (data.requirement_follow_up) {
          const completed = Object.keys(data.requirement_follow_up.current_requirements || {}).length;
          setRequirementProgress({
            completed,
            total: 9, // Updated to 9 fields
            missingFields: data.requirement_follow_up.missing_fields || []
          });
        }
      } else if (data.response_type === "complete_requirements") {
        // Complete Requirements Response
        chatMessage.completeRequirements = data.complete_requirements;
        chatMessage.text = data.complete_requirements?.message || "";
      }

      // Add the AI response to the correct chat history
      if (currentMode === "aws_chat") {
        setAwsChatHistory((prevChatHistory) => [
          ...prevChatHistory,
          chatMessage
        ]);
      } else {
        setRequirementChatHistory((prevChatHistory) => [
          ...prevChatHistory,
          chatMessage
        ]);
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      // Add error message to the correct chat history
      const errorMessage = { 
        sender: "AI", 
        text: `Connection error: ${
          error instanceof Error ? error.message : String(error)
        }. Make sure FastAPI backend is running on port 8000.`,
        timestamp: new Date()
      };
      
      if (currentMode === "aws_chat") {
        setAwsChatHistory((prevChatHistory) => [...prevChatHistory, errorMessage]);
      } else {
        setRequirementChatHistory((prevChatHistory) => [...prevChatHistory, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      setLoadingMode(null);
    }
  };

  const handleSend = () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();

    // Add the user's message to the correct chat history
    const userMessageObj = { 
      sender: "User", 
      text: userMessage,
      timestamp: new Date()
    };
    
    if (currentMode === "aws_chat") {
      setAwsChatHistory((prevChatHistory) => [...prevChatHistory, userMessageObj]);
    } else {
      setRequirementChatHistory((prevChatHistory) => [...prevChatHistory, userMessageObj]);
    }

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
          
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            {currentMode === "requirement_extraction" && requirementProgress.completed > 0 ? (
              <Chip
                icon={<Refresh sx={{ color: "#ff8a80 !important" }} />}
                label="Start New Project"
                onClick={handleResetClick}
                variant="outlined"
                sx={{
                  bgcolor: "rgba(255, 82, 82, 0.1)",
                  border: "1px solid #ff5252",
                  borderColor: "#ff5252",
                  color: "#ff5252",
                  cursor: "pointer",
                  "&:hover": {
                    bgcolor: "rgba(255, 82, 82, 0.2)",
                    borderColor: "#ff5252",
                    "& .MuiChip-icon": {
                      color: "#ffab91",
                    },
                  },
                  "& .MuiChip-icon": {
                    color: "#ff8a80",
                  },
                }}
              />
            ) : currentMode === "aws_chat" ? (
              <Chip
                icon={<Cloud />}
                label="RAG Enhanced"
                color="primary"
                variant="outlined"
                sx={{
                  bgcolor: "rgba(33, 150, 243, 0.1)",
                  borderColor: "#2196f3",
                  color: "#2196f3",
                }}
              />
            ) : (
              <Chip
                icon={<Assessment />}
                label="Requirement Extractor"
                color="primary"
                variant="outlined"
                sx={{
                  bgcolor: "rgba(76, 175, 80, 0.1)",
                  borderColor: "#4caf50",
                  color: "#4caf50",
                }}
              />
            )}
            <IconButton
              onClick={toggleDashboard}
              sx={{
                color: "white",
                bgcolor: "rgba(255, 255, 255, 0.1)",
                "&:hover": {
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                },
              }}
              title={dashboardVisible ? "Hide Dashboard" : "Show Dashboard"}
            >
              {dashboardVisible ? <MenuOpen /> : <Menu />}
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Side Dashboard */}
      {dashboardVisible && (
        <Box
          sx={{
            position: "fixed",
            left: 0,
            top: 64, // Below the header
            width: 280,
            height: "calc(100vh - 64px)",
            bgcolor: "rgba(0, 0, 0, 0.95)",
            backdropFilter: "blur(10px)",
            borderRight: "1px solid rgba(255, 255, 255, 0.1)",
            zIndex: 1000,
            display: "flex",
            flexDirection: "column",
            p: 2,
            transition: "transform 0.3s ease-in-out",
          }}
        >
        {/* Mode Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={600} color="white" sx={{ mb: 2 }}>
            Choose Mode
          </Typography>
          
          {/* AWS Chat Mode */}
          <Box
            onClick={() => handleModeSwitch("aws_chat")}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              p: 2,
              borderRadius: 2,
              cursor: "pointer",
              bgcolor: currentMode === "aws_chat" ? "rgba(33, 150, 243, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: currentMode === "aws_chat" ? "1px solid #2196f3" : "1px solid rgba(255, 255, 255, 0.1)",
              transition: "all 0.2s ease-in-out",
              "&:hover": {
                bgcolor: currentMode === "aws_chat" ? "rgba(33, 150, 243, 0.3)" : "rgba(255, 255, 255, 0.1)",
              },
              mb: 1,
            }}
          >
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: currentMode === "aws_chat" ? "#2196f3" : "rgba(255, 255, 255, 0.2)",
              }}
            >
              <Chat />
            </Avatar>
            <Box>
              <Typography variant="subtitle1" fontWeight={600} color="white">
                AWS Chatbot
              </Typography>
              <Typography variant="caption" color="rgba(255, 255, 255, 0.7)">
                Ask technical AWS questions
              </Typography>
            </Box>
            {currentMode === "aws_chat" && (
              <SwitchRight sx={{ ml: "auto", color: "#2196f3" }} />
            )}
          </Box>

          {/* Requirement Extraction Mode */}
          <Box
            onClick={() => handleModeSwitch("requirement_extraction")}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              p: 2,
              borderRadius: 2,
              cursor: "pointer",
              bgcolor: currentMode === "requirement_extraction" ? "rgba(76, 175, 80, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: currentMode === "requirement_extraction" ? "1px solid #4caf50" : "1px solid rgba(255, 255, 255, 0.1)",
              transition: "all 0.2s ease-in-out",
              "&:hover": {
                bgcolor: currentMode === "requirement_extraction" ? "rgba(76, 175, 80, 0.3)" : "rgba(255, 255, 255, 0.1)",
              },
            }}
          >
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: currentMode === "requirement_extraction" ? "#4caf50" : "rgba(255, 255, 255, 0.2)",
              }}
            >
              <Assessment />
            </Avatar>
            <Box>
              <Typography variant="subtitle1" fontWeight={600} color="white">
                Requirement Extraction
              </Typography>
              <Typography variant="caption" color="rgba(255, 255, 255, 0.7)">
                Extract project requirements
              </Typography>
            </Box>
            {currentMode === "requirement_extraction" && (
              <SwitchRight sx={{ ml: "auto", color: "#4caf50" }} />
            )}
          </Box>
        </Box>

        {/* Progress Tracking (only show in requirement extraction mode) */}
        {currentMode === "requirement_extraction" && (
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} color="white" sx={{ mb: 2 }}>
              Progress
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2" color="white">
                  Requirements
                </Typography>
                <Typography variant="body2" color="rgba(255, 255, 255, 0.7)">
                  {requirementProgress.completed}/{requirementProgress.total}
                </Typography>
              </Box>
              
              {/* Progress Bar */}
              <Box
                sx={{
                  width: "100%",
                  height: 8,
                  bgcolor: "rgba(255, 255, 255, 0.1)",
                  borderRadius: 4,
                  overflow: "hidden",
                }}
              >
                <Box
                  sx={{
                    width: `${(requirementProgress.completed / requirementProgress.total) * 100}%`,
                    height: "100%",
                    bgcolor: "#4caf50",
                    transition: "width 0.3s ease-in-out",
                  }}
                />
              </Box>
            </Box>

            {/* Missing Fields */}
            {requirementProgress.missingFields.length > 0 && (
              <Box>
                <Typography variant="body2" color="white" sx={{ mb: 1 }}>
                  Still need:
                </Typography>
                {requirementProgress.missingFields.slice(0, 5).map((field, index) => (
                  <Chip
                    key={index}
                    label={field.replace(/_/g, " ")}
                    size="small"
                    sx={{
                      bgcolor: "rgba(255, 152, 0, 0.2)",
                      color: "#ff9800",
                      mr: 0.5,
                      mb: 0.5,
                      fontSize: "0.7rem",
                    }}
                  />
                ))}
                {requirementProgress.missingFields.length > 5 && (
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.5)">
                    +{requirementProgress.missingFields.length - 5} more
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        )}
      </Box>
      )}

      {/* Chat Area */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          py: 2,
          px: 1,
          ml: dashboardVisible ? "280px" : "0px", // Dynamic margin based on dashboard visibility
          transition: "margin-left 0.3s ease-in-out",
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
        <Container 
          maxWidth="lg" 
          sx={{ 
            maxWidth: dashboardVisible ? "calc(100vw - 280px - 48px)" : "lg",
            transition: "max-width 0.3s ease-in-out"
          }}
        >
          {getCurrentChatHistory().length === 0 && (
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
                  {currentMode === "aws_chat" 
                    ? "Ask me anything about AWS services, architecture, and best practices"
                    : "Describe your project and I'll help extract the cloud requirements"
                  }
                </Typography>
                <Box sx={{ display: "flex", gap: 2, justifyContent: "center", flexWrap: "wrap" }}>
                  {currentMode === "aws_chat" ? (
                    <>
                      <Chip label="What is AWS Lambda?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                      <Chip label="How to set up a VPC?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                      <Chip label="S3 vs DynamoDB?" variant="outlined" sx={{ color: "#2196f3", borderColor: "#2196f3", bgcolor: "rgba(33, 150, 243, 0.1)" }} />
                    </>
                  ) : (
                    <>
                      <Chip label="E-commerce platform" variant="outlined" sx={{ color: "#4caf50", borderColor: "#4caf50", bgcolor: "rgba(76, 175, 80, 0.1)" }} />
                      <Chip label="Social media app" variant="outlined" sx={{ color: "#4caf50", borderColor: "#4caf50", bgcolor: "rgba(76, 175, 80, 0.1)" }} />
                      <Chip label="Mobile application" variant="outlined" sx={{ color: "#4caf50", borderColor: "#4caf50", bgcolor: "rgba(76, 175, 80, 0.1)" }} />
                    </>
                  )}
                </Box>
              </Box>
            </Fade>
          )}

          {getCurrentChatHistory().map((chatMessage, index) => (
            <ChatMessage
              key={index}
              sender={chatMessage.sender}
              text={chatMessage.text}
              answer={chatMessage.answer}
              timestamp={chatMessage.timestamp}
              responseType={chatMessage.responseType}
              intentClassification={chatMessage.intentClassification}
              requirementFollowUp={chatMessage.requirementFollowUp}
              completeRequirements={chatMessage.completeRequirements}
            />
          ))}

          {/* Loading Indicator - Only show when loading for current mode */}
          {isLoading && loadingMode === currentMode && (
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
                    bgcolor: currentMode === "aws_chat" 
                      ? "rgba(33, 150, 243, 0.15)" 
                      : "rgba(76, 175, 80, 0.15)",
                    px: 3,
                    py: 2,
                    borderRadius: "18px 18px 18px 4px",
                    boxShadow: currentMode === "aws_chat"
                      ? "0 4px 12px rgba(33, 150, 243, 0.2)"
                      : "0 4px 12px rgba(76, 175, 80, 0.2)",
                    border: currentMode === "aws_chat"
                      ? "1px solid rgba(33, 150, 243, 0.3)"
                      : "1px solid rgba(76, 175, 80, 0.3)",
                  }}
                >
                  <CircularProgress 
                    size={20} 
                    sx={{ 
                      color: currentMode === "aws_chat" ? "#2196f3" : "#4caf50" 
                    }} 
                  />
                  <Typography variant="body2" color="white">
                    {currentMode === "aws_chat" 
                      ? "AWS Assistant is thinking..." 
                      : "Extracting requirements..."}
                  </Typography>
                </Box>
                <Avatar
                  sx={{
                    width: 40,
                    height: 40,
                    bgcolor: currentMode === "aws_chat"
                      ? "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)"
                      : "linear-gradient(135deg, #4caf50 0%, #388e3c 100%)",
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
          ml: dashboardVisible ? "280px" : "0px", // Dynamic margin based on dashboard visibility
          transition: "margin-left 0.3s ease-in-out",
        }}
      >
        <Container 
          maxWidth="lg" 
          sx={{ 
            maxWidth: dashboardVisible ? "calc(100vw - 280px - 48px)" : "lg",
            transition: "max-width 0.3s ease-in-out"
          }}
        >
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
              placeholder={currentMode === "aws_chat" ? "Ask me anything about AWS..." : "Describe your project requirements..."}
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

      {/* Reset Confirmation Dialog */}
      <Dialog
        open={resetDialogOpen}
        onClose={handleResetCancel}
        PaperProps={{
          sx: {
            bgcolor: "rgba(0, 0, 0, 0.95)",
            border: "1px solid rgba(255, 82, 82, 0.3)",
            borderRadius: 2,
          }
        }}
      >
        <DialogTitle sx={{ color: "white", fontWeight: 600 }}>
          Reset Project?
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: "rgba(255, 255, 255, 0.8)" }}>
            Are you sure you want to discard this project and start fresh? 
            This will clear all your progress and chat history. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            onClick={handleResetCancel}
            sx={{
              color: "rgba(255, 255, 255, 0.7)",
              "&:hover": {
                bgcolor: "rgba(255, 255, 255, 0.1)",
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleResetConfirm}
            variant="contained"
            sx={{
              bgcolor: "#ff5252",
              color: "white",
              "&:hover": {
                bgcolor: "#d32f2f",
              }
            }}
          >
            Reset & Start New
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}