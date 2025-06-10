// client/src/pages/ConversationList.tsx

import React, { useEffect, useState, useContext } from "react";
import {
  Box,
  Typography,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Button,
} from "@mui/material";
import { AuthContext } from "../../store";
import { getConversationsList, type ConversationSummary } from "../../services/chatService";


interface ConversationListProps {
  selectedConvoId?: number;
  onSelectConvo: (id: number) => void;
  onNewChat: () => void;
}

export default function ConversationList({
  selectedConvoId,
  onSelectConvo,
  onNewChat,
}: ConversationListProps) {
  const { user, logout } = useContext(AuthContext);

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    fetchConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchConversations = async () => {
    setLoading(true);
    setErrorText(null);
    try {
      const data = await getConversationsList();
      setConversations(data);
    } catch (err: any) {
      console.error(err);
      setErrorText("Failed to load conversations.");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <Box
      sx={{
        width: 300,
        borderRight: "1px solid #ddd",
        pr: 2,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Conversations</Typography>
        <Button variant="outlined" color="error" size="small" onClick={logout}>
          Log Out
        </Button>
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" mt={2}>
          <CircularProgress size={24} />
        </Box>
      ) : errorText ? (
        <Alert severity="error">{errorText}</Alert>
      ) : (
        <Box sx={{ overflowY: "auto" }}>
          {conversations.map((c) => (
            <React.Fragment key={c.conversation_id}>
              <ListItemButton
                selected={c.conversation_id === selectedConvoId}
                onClick={() => onSelectConvo(c.conversation_id)}
              >
                <ListItemText
                  primary={`#${c.conversation_id}`}
                  secondary={c.summary || new Date(c.created_at).toLocaleString()}
                  sx={{
                    "& .MuiListItemText-secondary": {
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    },
                  }}
                />
              </ListItemButton>
              <Divider />
            </React.Fragment>
          ))}
        </Box>
      )}

      <Box mt={2}>
        <Button variant="contained" fullWidth onClick={onNewChat}>
          New Chat
        </Button>
      </Box>
    </Box>
  );
}
