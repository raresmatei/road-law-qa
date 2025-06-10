import React, { useEffect, useState, useContext } from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Alert,
  CircularProgress,
  TextField,
  Button,
} from "@mui/material";
import { AuthContext } from "../../store";
import { chatService, getConversationHistory, type ChatRequest, type ChatResponse, type MessageItem } from "../../services/chatService";


interface ChatAreaProps {
  conversationId?: number;
  onConversationCreated: (id: number) => void;
}

export default function ChatArea({ conversationId, onConversationCreated }: ChatAreaProps) {
  const navigate = useContext(AuthContext).logout; // just to get logout from context
  const { user, logout } = useContext(AuthContext);

  const [chatLog, setChatLog] = useState<MessageItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!user) return;
    if (conversationId !== undefined) {
      fetchHistory(conversationId);
    } else {
      setChatLog([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, user]);

  const fetchHistory = async (convoId: number) => {
    setLoadingHistory(true);
    setChatError(null);
    try {
      const data = await getConversationHistory(convoId);
      setChatLog(data.messages);
    } catch (err: any) {
      console.error(err);
      setChatError("Failed to load conversation history.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSend = async () => {
    if (!message.trim()) return;
    setChatError(null);

    const userEntry: MessageItem = {
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };
    setChatLog((prev) => [...prev, userEntry]);
    const userMessage = message;
    setMessage("");
    setSending(true);

    try {
      const payload: ChatRequest = conversationId
        ? { conversation_id: conversationId, message: userMessage }
        : { message: userMessage };

      const data: ChatResponse = await chatService(payload);

      const botEntry: MessageItem = {
        role: "assistant",
        content: data.reply,
        created_at: new Date().toISOString(),
      };
      setChatLog((prev) => [...prev, botEntry]);

      if (!conversationId) {
        onConversationCreated(data.conversation_id);
      }
    } catch (err: any) {
      console.error(err);
      setChatError("Server error – please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Box flex={1} pl={2} display="flex" flexDirection="column">
      <Typography variant="h5" mb={2}>
        {conversationId ? `Conversation #${conversationId}` : "New Chat"}
      </Typography>

      {loadingHistory ? (
        <Box display="flex" justifyContent="center" mt={2}>
          <CircularProgress />
        </Box>
      ) : chatError ? (
        <Alert severity="error">{chatError}</Alert>
      ) : (
        <Paper
          variant="outlined"
          sx={{
            flexGrow: 1,
            mb: 2,
            p: 2,
            overflowY: "auto",
            backgroundColor: "#fafafa",
          }}
        >
          {chatLog.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center">
              {conversationId
                ? "No messages in this conversation yet."
                : "Start a new conversation!"}
            </Typography>
          ) : (
            <List>
              {chatLog.map((entry, idx) => (
                <ListItem key={idx} disableGutters>
                  <ListItemText
                    primary={entry.content}
                    secondary={
                      entry.role === "user"
                        ? "You"
                        : "Bot • " + new Date(entry.created_at).toLocaleString()
                    }
                    sx={{
                      "& .MuiListItemText-primary": {
                        whiteSpace: "pre-wrap",
                      },
                    }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Paper>
      )}

      <Box display="flex" gap={1}>
        <TextField
          label="Type your question…"
          variant="outlined"
          fullWidth
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !sending) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={sending}
        />
        <Button
          variant="contained"
          onClick={handleSend}
          disabled={sending}
          sx={{ width: "120px" }}
        >
          {sending ? "Sending…" : "Send"}
        </Button>
      </Box>
    </Box>
  );
}
