import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { post } from "../api/apiService";
import AuthLayout from "./AuthLayout";

const emptyForm = {
  ppo_number: "",
  name: "",
  email: "",
  mobile: "",
  date_of_birth: "",
  retired_from_office: "",
  bank_account_number: "",
  bank_ifsc: "",
  bank_name: "",
  password: "",
  role: "pensioner",
};

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await post("/auth/register", form);
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "w-full border border-slate-300 rounded-md px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600";
  const labelClass = "block text-sm font-medium text-slate-700 mb-1.5";

  return (
    <AuthLayout title="Create account" subtitle="Register with your PPO particulars">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div>
            <label className={labelClass} htmlFor="ppo_number">PPO number</label>
            <input id="ppo_number" name="ppo_number" className={inputClass} value={form.ppo_number} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="name">Full name</label>
            <input id="name" name="name" className={inputClass} value={form.name} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className={inputClass} value={form.email} onChange={handleChange} />
          </div>
          <div>
            <label className={labelClass} htmlFor="mobile">Mobile</label>
            <input id="mobile" name="mobile" className={inputClass} value={form.mobile} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="date_of_birth">Date of birth</label>
            <input id="date_of_birth" name="date_of_birth" type="date" className={inputClass} value={form.date_of_birth} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="retired_from_office">Retired from office</label>
            <input id="retired_from_office" name="retired_from_office" className={inputClass} value={form.retired_from_office} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="bank_account_number">Bank account number</label>
            <input id="bank_account_number" name="bank_account_number" className={inputClass} value={form.bank_account_number} onChange={handleChange} required />
          </div>
          <div>
            <label className={labelClass} htmlFor="bank_ifsc">Bank IFSC</label>
            <input id="bank_ifsc" name="bank_ifsc" className={inputClass} value={form.bank_ifsc} onChange={handleChange} required />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="bank_name">Bank name</label>
            <input id="bank_name" name="bank_name" className={inputClass} value={form.bank_name} onChange={handleChange} required />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="password">Password</label>
            <input id="password" name="password" type="password" className={inputClass} value={form.password} onChange={handleChange} required minLength={6} />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="role">Role (for demo/testing an approver account)</label>
            <select id="role" name="role" className={inputClass} value={form.role} onChange={handleChange}>
              <option value="pensioner">Pensioner</option>
              <option value="pension_officer">Pension officer (approver)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-800 text-white rounded-md py-2.5 font-medium hover:bg-blue-900 transition-colors disabled:opacity-60"
        >
          {loading ? "Registering..." : "Register"}
        </button>

        <p className="text-sm text-slate-500 mt-6 text-center">
          Already registered?{" "}
          <Link to="/login" className="text-blue-800 font-medium hover:text-blue-900">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
