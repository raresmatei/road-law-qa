import { useContext, useState } from "react";
import { Container, Box } from "@mui/material";
import { AuthContext } from "../../store/AuthContext";
import ConversationList from "../Conversations/ConversationsList";
import ChatArea from "../ChatArea/ChatArea";

export default function Home() {
  const { user } = useContext(AuthContext);
  const [selectedConvoId, setSelectedConvoId] = useState<number | undefined>(undefined);

  if (!user) {
    // If not logged in, show nothing (or a simple message/redirect)
    return null;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, height: "calc(100vh - 32px)" }}>
      <Box display="flex" height="100%">
        <ConversationList
          selectedConvoId={selectedConvoId}
          onSelectConvo={(id) => setSelectedConvoId(id)}
          onNewChat={() => setSelectedConvoId(undefined)}
        />

        <ChatArea
          conversationId={selectedConvoId}
          onConversationCreated={(newId) => setSelectedConvoId(newId)}
        />
      </Box>
    </Container>
  );
}
