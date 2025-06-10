// src/pages/Dashboard/Dashboard.tsx
import React, { useContext } from 'react';
import { AuthContext } from '../../store/AuthContext';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const { user, logout } = useContext(AuthContext);

  return (
    <div className={styles.container}>
      <h2>Dashboard</h2>
      <p>Welcome, {user?.name || 'User'}!</p>
      <button onClick={logout}>Log Out</button>
    </div>
  );
}
