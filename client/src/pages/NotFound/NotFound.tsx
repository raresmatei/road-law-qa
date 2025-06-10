// src/pages/NotFound/NotFound.tsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>404 - Page Not Found</h2>
      <Link to="/">Go back to Home</Link>
    </div>
  );
}
