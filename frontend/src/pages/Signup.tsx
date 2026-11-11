import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Lock, Mail, User, ArrowRight } from 'lucide-react';

export const Signup: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('Agent Vikram Rathore');
  const [email, setEmail] = useState('agent.vikram@fiu.gov.in');
  const [role, setRole] = useState('INVESTIGATOR');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6 font-sans">
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <h2 className="text-xl font-bold font-mono tracking-wider">OFFICER ENROLLMENT</h2>
          <p className="text-xs text-slate-400 mt-1">Enroll investigator profile into PHANTOM RLS</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5">Officer Full Name</label>
            <div className="relative flex items-center">
              <User className="absolute left-3 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5">Official Agency Email</label>
            <div className="relative flex items-center">
              <Mail className="absolute left-3 w-4 h-4 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5">Clearance Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="INVESTIGATOR">INVESTIGATOR (Case Lead & Freeze Action)</option>
              <option value="ANALYST">ANALYST (Triage & Screening)</option>
              <option value="ADMIN">ADMIN (System Configuration)</option>
            </select>
          </div>

          <button
            type="submit"
            className="w-full mt-4 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition-all"
          >
            Create Officer Profile <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Already have credentials?{' '}
          <Link to="/login" className="text-cyan-400 hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

