import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Otp from "./pages/Otp";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import PensionSlip from "./pages/PensionSlip";
import DisbursementHistory from "./pages/DisbursementHistory";
import Tax from "./pages/Tax";
import BankRequests from "./pages/BankRequests";
import Grievances from "./pages/Grievances";
import ArrearsBenefits from "./pages/ArrearsBenefits";
import Announcements from "./pages/Announcements";
import LifeCertificate from "./pages/LifeCertificate";
import MyRequests from "./pages/MyRequests";
import Approver from "./pages/Approver";

function RequireAuth({ children }) {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

const protectedRoutes = [
  { path: "/dashboard", element: <Dashboard /> },
  { path: "/profile", element: <Profile /> },
  { path: "/pension-slip", element: <PensionSlip /> },
  { path: "/disbursements", element: <DisbursementHistory /> },
  { path: "/tax", element: <Tax /> },
  { path: "/bank-requests", element: <BankRequests /> },
  { path: "/grievances", element: <Grievances /> },
  { path: "/arrears-benefits", element: <ArrearsBenefits /> },
  { path: "/announcements", element: <Announcements /> },
  { path: "/life-certificate", element: <LifeCertificate /> },
  { path: "/my-requests", element: <MyRequests /> },
  { path: "/approver", element: <Approver /> },
];

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/otp" element={<Otp />} />
      <Route path="/register" element={<Register />} />
      {protectedRoutes.map(({ path, element }) => (
        <Route key={path} path={path} element={<RequireAuth>{element}</RequireAuth>} />
      ))}
    </Routes>
  );
}
