import { Navigate } from "react-router-dom";

interface PrivateRouteProps {
  children: React.ReactNode;
}

export const PrivateRoute = ({ children }: PrivateRouteProps) => {
  const token = localStorage.getItem("token");
  if (!token || token === "undefined" || token === "null") {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};
