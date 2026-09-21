import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Generate from "./pages/Generate";
import ReviewQueue from "./pages/ReviewQueue";
import ContentLibrary from "./pages/ContentLibrary";
import Leads from "./pages/Leads";
import Research from "./pages/Research";
import Publishing from "./pages/Publishing";
import Analytics from "./pages/Analytics";
import Users from "./pages/Users";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="generate" element={<Generate />} />
            <Route path="review" element={<ReviewQueue />} />
            <Route path="library" element={<ContentLibrary />} />
            <Route path="research" element={<Research />} />
            <Route path="leads" element={<Leads />} />
            <Route path="publishing" element={<Publishing />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
        </Route>

        <Route element={<ProtectedRoute adminOnly />}>
          <Route element={<Layout />}>
            <Route path="users" element={<Users />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}