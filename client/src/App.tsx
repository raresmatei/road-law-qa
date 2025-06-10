// src/App.tsx
import AppRouter from './router';
import { AuthProvider } from './store/AuthContext';

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;
