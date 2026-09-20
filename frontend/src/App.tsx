import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Generate from "./pages/Generate";
import ReviewQueue from "./pages/ReviewQueue";
import ContentLibrary from "./pages/ContentLibrary";
import Leads from "./pages/Leads";
import Research from "./pages/Research";
import Publishing from "./pages/Publishing";
import Analytics from "./pages/Analytics";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="generate" element={<Generate />} />
        <Route path="review" element={<ReviewQueue />} />
        <Route path="library" element={<ContentLibrary />} />
        <Route path="research" element={<Research />} />
        <Route path="leads" element={<Leads />} />
        <Route path="publishing" element={<Publishing />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}