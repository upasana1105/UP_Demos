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
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Plus, AlertCircle, FileText, Calendar, MapPin, Eye, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_URL } from '../config';

export default function Dashboard() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const policy = localStorage.getItem('policy_number');
    if (!policy) {
      router.replace('/login');
      return;
    }

    const fetchClaims = async () => {
      try {
        const res = await fetch(`${API_URL}/api/claims?policy_number=${policy}`);
        if (!res.ok) throw new Error('Failed to load claims');
        const data = await res.json();
        setClaims(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchClaims();
  }, [router]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'New':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <CheckCircle2 size={12} />
            <span>New</span>
          </span>
        );
      case 'Analyzing':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Loader2 size={12} className="animate-spin" />
            <span>Analyzing</span>
          </span>
        );
      case 'Assessed':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 size={12} />
            <span>Assessed</span>
          </span>
        );
      case 'Review Required':
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle size={12} />
            <span>Review Required</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Your Claims</h1>
            <p className="text-sm text-zinc-400 mt-1">Submit and track accident claims</p>
          </div>
          
          <button
            onClick={() => router.push('/new')}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-semibold px-4 py-2.5 rounded-2xl shadow-lg transition-all text-sm"
          >
            <Plus size={16} />
            <span>File a Claim</span>
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm mb-6">
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-zinc-900/40 border border-zinc-800 animate-pulse rounded-3xl" />
            ))}
          </div>
        ) : claims.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/10">
            <FileText size={48} className="text-zinc-600 mb-4" />
            <h3 className="text-base font-semibold text-zinc-300">No claims filed yet</h3>
            <p className="text-xs text-zinc-500 mt-1">Have you recently been in an accident? File a claim to begin.</p>
            <button
              onClick={() => router.push('/new')}
              className="mt-6 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl border border-zinc-700 transition-all"
            >
              Start Claim Wizard
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {claims.map((claim) => (
              <motion.div
                key={claim.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                onClick={() => router.push(`/claims/${claim.id}`)}
                className="bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-800/80 rounded-3xl p-6 cursor-pointer flex flex-col justify-between h-56 transition-all shadow-md hover:shadow-xl"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-[10px] font-bold text-zinc-500 font-mono uppercase tracking-wider">
                      Claim #{claim.id}
                    </span>
                    {getStatusBadge(claim.status)}
                  </div>

                  <h3 className="text-base font-semibold text-zinc-100 line-clamp-1 mb-2">
                    {claim.description || 'No description provided'}
                  </h3>

                  <div className="space-y-1.5 text-zinc-400 text-xs">
                    <div className="flex items-center gap-1.5">
                      <Calendar size={13} className="text-zinc-600" />
                      <span>{claim.accident_date ? new Date(claim.accident_date).toLocaleDateString() : 'Unknown date'}</span>
                    </div>
                    {(claim.incident_city || claim.incident_state) && (
                      <div className="flex items-center gap-1.5">
                        <MapPin size={13} className="text-zinc-600" />
                        <span>{[claim.incident_city, claim.incident_state].filter(Boolean).join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-zinc-800/60 pt-4 mt-4">
                  <div className="flex gap-1 overflow-hidden max-w-[120px]">
                    {claim.photos && claim.photos.length > 0 ? (
                      claim.photos.slice(0, 3).map((photo, i) => (
                        <div key={i} className="w-8 h-8 rounded-lg overflow-hidden border border-zinc-800 shrink-0">
                          <img src={photo.url} alt="Damage" className="w-full h-full object-cover" />
                        </div>
                      ))
                    ) : (
                      <span className="text-[10px] text-zinc-500 font-medium">No photos</span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-1 text-indigo-400 text-xs font-semibold">
                    <span>View Details</span>
                    <Eye size={14} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
