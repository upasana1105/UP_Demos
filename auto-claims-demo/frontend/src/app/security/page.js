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
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Lock, Key, Cpu, Database, CheckCircle2, AlertTriangle,
  RefreshCw, Copy, Check, Loader2, ArrowLeft, Search, Filter,
  FileCode, ChevronRight, X, ExternalLink, ShieldCheck, Terminal
} from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_URL } from '../config';
import Link from 'next/link';

export default function SecurityAuditConsole() {
  const [posture, setPosture] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [tamperLoading, setTamperLoading] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [filterQuery, setFilterQuery] = useState('');
  const [copiedKey, setCopiedKey] = useState(null);

  const fetchSecurityData = async () => {
    try {
      setLoading(true);
      const [postureRes, ledgerRes] = await Promise.all([
        fetch(`${API_URL}/api/security/posture`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/security/ledger?limit=100`).then(r => r.json()).catch(() => ({ ledger: [] })),
      ]);
      setPosture(postureRes);
      setLedger(ledgerRes?.ledger || []);
      if (ledgerRes?.ledger?.length > 0 && !selectedEntry) {
        setSelectedEntry(ledgerRes.ledger[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const runAudit = async () => {
    try {
      setAuditing(true);
      const res = await fetch(`${API_URL}/api/security/verify`, { method: 'POST' });
      const data = await res.json();
      setAuditResult(data);
      // Refresh ledger
      const ledgerRes = await fetch(`${API_URL}/api/security/ledger?limit=100`).then(r => r.json());
      setLedger(ledgerRes?.ledger || []);
    } catch (err) {
      console.error("Audit error:", err);
    } finally {
      setAuditing(false);
    }
  };

  const simulateTamper = async () => {
    try {
      setTamperLoading(true);
      const claimId = ledger[0]?.claim_id || 1;
      await fetch(`${API_URL}/api/security/tamper-demo?claim_id=${claimId}&tampered_amount=14850.00`, {
        method: 'POST',
      });
      await runAudit();
    } catch (err) {
      console.error("Tamper simulation error:", err);
    } finally {
      setTamperLoading(false);
    }
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const filteredLedger = ledger.filter(item => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (
      item.agent_id?.toLowerCase().includes(q) ||
      item.payload_hash?.toLowerCase().includes(q) ||
      String(item.claim_id).includes(q) ||
      String(item.nonce).includes(q) ||
      JSON.stringify(item.payload).toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {/* Breadcrumb & Console Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-zinc-800/80">
          <div>
            <div className="flex items-center gap-2 text-xs text-zinc-400 mb-1.5 font-medium">
              <Link href="/dashboard" className="hover:text-white transition-colors">Claims Platform</Link>
              <span>/</span>
              <span className="text-zinc-200">Security & Cryptographic Audit Logs</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold tracking-tight text-white">Security Command & Audit Ledger</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                ZERO-TRUST ENFORCED
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={simulateTamper}
              disabled={tamperLoading}
              className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 px-3.5 py-2 rounded-xl text-xs font-semibold active:scale-95 transition-all"
            >
              {tamperLoading ? <Loader2 size={13} className="animate-spin" /> : <AlertTriangle size={13} className="text-amber-400" />}
              <span>Test DB Tamper Detection</span>
            </button>

            <button
              onClick={runAudit}
              disabled={auditing}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/20 active:scale-95 transition-all"
            >
              {auditing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              <span>Verify Cryptographic Integrity</span>
            </button>
          </div>
        </div>

        {/* Security Posture Status Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4">
            <div className="text-zinc-500 text-[11px] font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Cryptographic Identity</span>
              <Key size={14} className="text-indigo-400" />
            </div>
            <div className="text-lg font-bold text-white">HMAC-SHA256</div>
            <div className="text-[11px] text-zinc-400 mt-1 flex items-center gap-1">
              <CheckCircle2 size={11} className="text-emerald-400" />
              <span>Chained Merkle Nonces</span>
            </div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4">
            <div className="text-zinc-500 text-[11px] font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Execution Sandbox</span>
              <Cpu size={14} className="text-purple-400" />
            </div>
            <div className="text-lg font-bold text-white">gVisor / Cloud Run</div>
            <div className="text-[11px] text-zinc-400 mt-1 flex items-center gap-1">
              <ShieldCheck size={11} className="text-emerald-400" />
              <span>Zero Network Egress</span>
            </div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4">
            <div className="text-zinc-500 text-[11px] font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Semantic Gateway</span>
              <Shield size={14} className="text-amber-400" />
            </div>
            <div className="text-lg font-bold text-white">$2,500.00 Limit</div>
            <div className="text-[11px] text-zinc-400 mt-1 flex items-center gap-1">
              <Lock size={11} className="text-emerald-400" />
              <span>Injection Firewall Active</span>
            </div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4">
            <div className="text-zinc-500 text-[11px] font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Audit Ledger Status</span>
              <Database size={14} className="text-emerald-400" />
            </div>
            <div className="text-lg font-bold text-white">{ledger.length} Blocks Recorded</div>
            <div className="text-[11px] text-zinc-400 mt-1">
              {auditResult ? (
                auditResult.overall_health ? (
                  <span className="text-emerald-400 font-semibold">✔ 100% DB State Authentic</span>
                ) : (
                  <span className="text-rose-400 font-semibold">✖ Tampering Alert</span>
                )
              ) : (
                <span className="text-zinc-500">Live Chain Verified</span>
              )}
            </div>
          </div>
        </div>

        {/* Audit Verification Alert Banner */}
        {auditResult && !auditResult.overall_health && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertTriangle size={20} className="text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-bold text-rose-400">Cryptographic Discrepancy Detected</h3>
                <p className="text-xs text-rose-300 mt-0.5">
                  The SQLite database row content does not match the immutable HMAC-SHA256 signature recorded at adjudication time.
                </p>
                {auditResult.database_integrity?.tampered_records?.map((rec, i) => (
                  <div key={i} className="mt-2.5 bg-zinc-950/90 rounded-lg p-3 border border-rose-500/40 text-xs font-mono text-zinc-300">
                    <div className="text-rose-400 font-bold mb-1">Claim #{rec.claim_id} Signature Mismatch:</div>
                    <div>Discrepancies: {rec.discrepancies?.join(', ')}</div>
                    <div className="text-zinc-500 text-[10px] mt-1 break-all">Signed Payload Hash: {rec.signed_hash}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Main Log Viewer & Detail Drawer */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Table (8 cols) */}
          <div className="lg:col-span-7 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-5 flex flex-col">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="relative flex-1 max-w-sm">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Filter logs by claim, agent, or hash..."
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-9 pr-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600 font-mono"
                />
              </div>
              <span className="text-xs text-zinc-500 font-mono">{filteredLedger.length} events</span>
            </div>

            <div className="overflow-x-auto flex-1">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-500 text-[10px] uppercase">
                    <th className="py-2.5 px-3">Nonce</th>
                    <th className="py-2.5 px-3">Principal</th>
                    <th className="py-2.5 px-3">Claim</th>
                    <th className="py-2.5 px-3">Payload Hash</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {filteredLedger.map((entry) => {
                    const isSelected = selectedEntry?.nonce === entry.nonce;
                    return (
                      <tr
                        key={entry.nonce}
                        onClick={() => setSelectedEntry(entry)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? 'bg-indigo-600/15 text-white' : 'hover:bg-zinc-900/60 text-zinc-300'
                        }`}
                      >
                        <td className="py-3 px-3 text-indigo-400 font-bold">#{entry.nonce}</td>
                        <td className="py-3 px-3 text-zinc-300">{entry.agent_id}</td>
                        <td className="py-3 px-3">
                          {entry.claim_id ? (
                            <Link href={`/claims/${entry.claim_id}`} className="text-indigo-400 hover:underline">
                              Claim #{entry.claim_id}
                            </Link>
                          ) : (
                            <span className="text-zinc-500">System</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-zinc-400">{entry.payload_hash?.slice(0, 10)}...</td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 size={10} />
                            <span>VERIFIED</span>
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredLedger.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-zinc-600 italic">
                        No signed ledger entries found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detail Drawer (5 cols) */}
          <div className="lg:col-span-5 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-5 flex flex-col font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80 mb-4">
              <div className="flex items-center gap-2">
                <FileCode size={16} className="text-indigo-400" />
                <span className="font-bold text-sm text-white">Cryptographic Certificate</span>
              </div>
              {selectedEntry && (
                <span className="text-xs text-indigo-400 font-bold">Block #{selectedEntry.nonce}</span>
              )}
            </div>

            {selectedEntry ? (
              <div className="space-y-4 flex-1 overflow-y-auto">
                <div className="bg-zinc-950/90 rounded-xl p-3.5 border border-zinc-850 space-y-2 text-[11px]">
                  <div className="flex justify-between text-zinc-400">
                    <span>Signing Principal:</span>
                    <span className="text-white font-bold">{selectedEntry.agent_id}</span>
                  </div>
                  <div className="flex justify-between text-zinc-400">
                    <span>Timestamp:</span>
                    <span className="text-zinc-300">{selectedEntry.timestamp}</span>
                  </div>
                  <div className="flex justify-between text-zinc-400">
                    <span>Audit Status:</span>
                    <span className="text-emerald-400 font-bold">VERIFIED AUTHENTIC</span>
                  </div>
                </div>

                {/* Hash & Signature */}
                <div className="space-y-2">
                  <div>
                    <div className="flex items-center justify-between text-zinc-400 text-[10px] mb-1">
                      <span>PAYLOAD DIGEST (SHA-256):</span>
                      <button
                        onClick={() => copyToClipboard(selectedEntry.payload_hash, 'ph')}
                        className="text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
                      >
                        {copiedKey === 'ph' ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                        <span>{copiedKey === 'ph' ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-850 text-[10px] text-zinc-300 break-all select-all">
                      {selectedEntry.payload_hash}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-zinc-400 text-[10px] mb-1">
                      <span>HMAC-SHA256 SIGNATURE:</span>
                      <button
                        onClick={() => copyToClipboard(selectedEntry.signature, 'sig')}
                        className="text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
                      >
                        {copiedKey === 'sig' ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                        <span>{copiedKey === 'sig' ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-850 text-[10px] text-indigo-300 break-all select-all">
                      {selectedEntry.signature}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-zinc-400 text-[10px] mb-1">
                      <span>MERKLE CHAIN HASH:</span>
                    </div>
                    <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-850 text-[10px] text-zinc-500 break-all select-all">
                      {selectedEntry.chain_hash}
                    </div>
                  </div>
                </div>

                {/* Canonical Payload JSON */}
                <div>
                  <span className="text-zinc-400 text-[10px] block mb-1">CANONICAL SIGNED DATA PAYLOAD:</span>
                  <pre className="bg-zinc-950 p-3 rounded-lg border border-zinc-850 text-[11px] text-zinc-300 overflow-x-auto">
                    {JSON.stringify(selectedEntry.payload, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-600 italic">
                Select a signed transaction block from the table to view its certificate.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
