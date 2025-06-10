// client/src/router/index.tsx

import { useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";

import Home from "../pages/Home/Home";
import Register from "../pages/Register/Register";
import Login from "../pages/Login/Login";
import NotFound from "../pages/NotFound/NotFound";

import { AuthContext } from "../store/AuthContext";

function ProtectedRoute() {
  const { user } = useContext(AuthContext);
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        {/* Protected */}
        <Route element={<ProtectedRoute />}>
          <Route path="/home" element={<Home />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
