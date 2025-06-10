// src/pages/Register/Register.tsx
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { registerService } from '../../services/authService';
import type { RegisterPayload } from '../../services/authService';

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorText, setErrorText] = useState<string | null>(null);
  const [successText, setSuccessText] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorText(null);
    setSuccessText(null);

    try {
      const payload: RegisterPayload = { username, password };
      const res = await registerService(payload);
      // res is { id: number; username: string }
      setSuccessText(`User ${res.username} (id=${res.id}) created!`);
      setTimeout(() => {
        navigate('/login');
      }, 1000);
    } catch (err: any) {
      console.error(err);
      if (err.response && err.response.data) {
        setErrorText(err.response.data.detail || 'Registration failed.');
      } else {
        setErrorText('Registration failed.');
      }
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Register
      </Typography>

      {errorText && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorText}
        </Alert>
      )}
      {successText && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successText}
        </Alert>
      )}

      <Box
        component="form"
        onSubmit={handleRegister}
        display="flex"
        flexDirection="column"
        gap={2}
      >
        <TextField
          required
          label="Username"
          variant="outlined"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <TextField
          required
          label="Password"
          type="password"
          variant="outlined"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <Button type="submit" variant="contained" size="large">
          Register
        </Button>
      </Box>

      <Box textAlign="center" sx={{ mt: 2 }}>
        <Typography variant="body2">
          Already have an account?{' '}
          <Button
            onClick={() => navigate('/login')}
            size="small"
            sx={{ textTransform: 'none' }}
          >
            Log in
          </Button>
        </Typography>
      </Box>
    </Container>
  );
}
