// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, ArrowRight, Car, AlertCircle } from 'lucide-react';
import { API_URL } from '../config';

export default function Login() {
  const [policyNumber, setPolicyNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Redirect if already logged in
    if (localStorage.getItem('policy_number')) {
      router.replace('/dashboard');
    }
  }, [router]);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!policyNumber.trim()) {
      setError('Please enter your policy number.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API_URL}/api/policies/${policyNumber.trim()}`);
      if (!res.ok) {
        if (res.status === 404) {
          throw new Error('Policy not found. Try numbers like 521585, 342868, or 227811.');
        } else {
          throw new Error('Failed to connect to the authentication server.');
        }
      }
      
      const policyData = await res.json();
      localStorage.setItem('policy_number', policyData.policy_number);
      localStorage.setItem('customer_name', `${policyData.first_name} ${policyData.last_name}`);
      localStorage.setItem('vehicle_info', `${policyData.auto_year} ${policyData.auto_make} ${policyData.auto_model}`);
      
      router.replace('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-zinc-950 overflow-hidden font-sans">
      {/* Decorative background glows */}
      <div className="absolute top-0 -left-4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 -right-4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md p-8 bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/80 rounded-3xl shadow-2xl relative z-10 mx-4"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-4 text-indigo-400">
            <Shield size={32} />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Auto Claims Assistant</h2>
          <p className="text-sm text-zinc-400 mt-1">Access your policyholder portal</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label htmlFor="policyNumber" className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
              Policy Number
            </label>
            <div className="relative">
              <input
                id="policyNumber"
                type="text"
                value={policyNumber}
                onChange={(e) => setPolicyNumber(e.target.value)}
                placeholder="e.g. 521585"
                className="w-full h-12 bg-zinc-950 border border-zinc-800 rounded-2xl px-4 text-white text-base placeholder-zinc-600 focus:outline-none focus:border-indigo-500/80 transition-all font-mono"
              />
            </div>
            <p className="text-[11px] text-zinc-500 mt-2">
              Tip: Use seed policy numbers like <span className="font-mono text-indigo-400">521585</span> or <span className="font-mono text-indigo-400">342868</span>.
            </p>
          </div>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-start gap-2.5 p-3.5 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-xs leading-5"
              >
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 bg-indigo-600 text-white font-semibold rounded-2xl flex items-center justify-center gap-2 hover:bg-indigo-500 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none"
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white" />
            ) : (
              <>
                <span>Access Dashboard</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
