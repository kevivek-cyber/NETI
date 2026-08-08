import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './layouts/Layout';
// import { Landing } from './pages/Landing';
import { Checkin } from './pages/Checkin';
import { Instructions } from './pages/Instructions';
import { Exam } from './pages/Exam';
import { Receipt } from './pages/Receipt';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* We'll add Landing later, defaulting to checkin for now */}
          <Route index element={<Navigate to="/checkin" replace />} />
          <Route path="checkin" element={<Checkin />} />
          <Route path="instructions" element={<Instructions />} />
          <Route path="receipt" element={<Receipt />} />
        </Route>
        {/* Exam page must bypass the Layout wrapper to be full screen edge-to-edge */}
        <Route path="/exam" element={<Exam />} />
      </Routes>
    </BrowserRouter>
  );
}
