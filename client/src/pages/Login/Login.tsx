import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Paper,
} from '@mui/material';
import { AuthContext } from '../../store';
import type { LoginPayload } from '../../services/authService';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]     = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const isAdmin = await login({ username, password } as LoginPayload);
      if (isAdmin) {
        navigate('/admin');
      } else {
        navigate('/home');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box display='flex' justifyContent='center' mt={8}>
      <Paper sx={{ p: 4, width: 360 }}>
        <Typography variant='h5' mb={2} align='center'>
          Log In
        </Typography>

        {error && (
          <Alert severity='error' sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box
          component='form'
          onSubmit={handleSubmit}
          display='flex'
          flexDirection='column'
          gap={2}
        >
          <TextField
            label='Username'
            variant='outlined'
            fullWidth
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
          <TextField
            label='Password'
            type='password'
            variant='outlined'
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          <Button
            variant='contained'
            type='submit'
            disabled={loading}
            sx={{ mt: 1 }}
          >
            {loading ? 'Logging in…' : 'Log In'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
