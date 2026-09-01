import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { post } from "../api/apiService";
import AuthLayout from "./AuthLayout";

export default function Login() {
  const navigate = useNavigate();
  const [ppoNumber, setPpoNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await post("/auth/login", {
        ppo_number: ppoNumber,
        password: password,
      });
      // Login is step 1 of 2. Carry the pending_token to the OTP page.
      sessionStorage.setItem("pending_token", data.pending_token);
      navigate("/otp");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Sign in" subtitle="Enter your PPO number and password to continue">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="ppo_number">
            PPO number
          </label>
          <input
            id="ppo_number"
            placeholder="e.g. PPO/2020/004821"
            className="w-full border border-slate-300 rounded-md px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
            value={ppoNumber}
            onChange={(e) => setPpoNumber(e.target.value)}
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            className="w-full border border-slate-300 rounded-md px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-800 text-white rounded-md py-2.5 font-medium hover:bg-blue-900 transition-colors disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-sm text-slate-500 mt-6 text-center">
          New user?{" "}
          <Link to="/register" className="text-blue-800 font-medium hover:text-blue-900">
            Register here
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
