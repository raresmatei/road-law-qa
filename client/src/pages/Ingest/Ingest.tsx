// src/components/Ingest.tsx
import { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from "@mui/material";
import { ingestLegislation, type IngestResponse } from "../../services/ingestService";

export default function Ingest() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IngestResponse | null>(null);

  const handleIngest = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await ingestLegislation({ url });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box flex={1} pl={2} display="flex" flexDirection="column">
      <Typography variant="h5" mb={2}>
        Ingest Legislation
      </Typography>

      <Paper
        variant="outlined"
        sx={{
          p: 2,
          mb: 2,
          display: "flex",
          flexDirection: "column",
          gap: 2,
          backgroundColor: "#fafafa",
        }}
      >
        <Box display="flex" gap={1}>
          <TextField
            label="Legislation URL"
            variant="outlined"
            fullWidth
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
          <Button
            variant="contained"
            onClick={handleIngest}
            disabled={loading}
            sx={{ width: "120px" }}
          >
            {loading ? <CircularProgress size={24} /> : "Ingest"}
          </Button>
        </Box>

        {error && (
          <Alert severity="error">
            {error}
          </Alert>
        )}

        {result && (
          <Alert severity="success">
            ✅ Inserted {result.inserted_chunks} chunks
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
