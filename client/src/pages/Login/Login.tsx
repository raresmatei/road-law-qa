// src/pages/Login/Login.tsx
import React, { useState, useContext } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../store/AuthContext';
import type { LoginPayload } from '../../services/authService';

export default function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorText, setErrorText] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorText(null);

    try {
      const payload: LoginPayload = { username, password };
      await login(payload);
      navigate('/home');
    } catch (err: any) {
      console.error(err);
      if (err.response && err.response.data) {
        setErrorText(err.response.data.detail || 'Login failed.');
      } else {
        setErrorText('Login failed.');
      }
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Log In
      </Typography>

      {errorText && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorText}
        </Alert>
      )}

      <Box
        component="form"
        onSubmit={handleLogin}
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
          Log In
        </Button>
      </Box>

      <Box textAlign="center" sx={{ mt: 2 }}>
        <Typography variant="body2">
          Don’t have an account?{' '}
          <Button
            onClick={() => navigate('/register')}
            size="small"
            sx={{ textTransform: 'none' }}
          >
            Register
          </Button>
        </Typography>
      </Box>
    </Container>
  );
}
