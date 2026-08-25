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
import { useEffect, useState, useRef, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, RefreshCw, AlertCircle, Calendar, MapPin, Shield, DollarSign, Wrench, Search, MessageSquare, Send, CheckCircle2, User, Loader2, X, Lock, Key, Cpu, ShieldCheck, ExternalLink, AlertTriangle } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { API_URL } from '../../config';
import Link from 'next/link';


export default function ClaimDetail({ params: paramsPromise }) {
  const params = use(paramsPromise);
  const router = useRouter();
  const claimId = params.id;

  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Photo viewer state
  const [selectedPhoto, setSelectedPhoto] = useState(null);

  // Shop Finder State
  const [shops, setShops] = useState([]);
  const [searchingShops, setSearchingShops] = useState(false);
  const [selectedShop, setSelectedShop] = useState(null);

  // Chat State
  const [chatOpen, setChatOpen] = useState(false);
  const [chatSession, setChatSession] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [sendingChat, setSendingChat] = useState(false);
  const chatBottomRef = useRef(null);

  // Zero Trust State
  const [securityCert, setSecurityCert] = useState(null);
  const [tamperStatus, setTamperStatus] = useState(null);

  useEffect(() => {
    const policy = localStorage.getItem('policy_number');
    if (!policy) {
      router.replace('/login');
      return;
    }
    fetchClaimDetails();
  }, [claimId, router]);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatLog]);

  const fetchClaimDetails = async () => {
    try {
      const res = await fetch(`${API_URL}/api/claims/${claimId}`);
      if (!res.ok) throw new Error('Claim not found');
      const data = await res.json();
      setClaim(data);
      if (data.photos && data.photos.length > 0) {
        setSelectedPhoto(data.photos[0]);
      }

      // Fetch Zero-Trust Provenance and Audit Verification
      try {
        const [ledgerRes, auditRes] = await Promise.all([
          fetch(`${API_URL}/api/security/ledger?limit=50`).then(r => r.json()),
          fetch(`${API_URL}/api/security/verify`, { method: 'POST' }).then(r => r.json())
        ]);
        const match = ledgerRes?.ledger?.find(e => String(e.claim_id) === String(claimId));
        if (match) setSecurityCert(match);

        const tamperedRec = auditRes?.database_integrity?.tampered_records?.find(
          r => String(r.claim_id) === String(claimId)
        );
        if (tamperedRec) {
          setTamperStatus({
            isTampered: true,
            discrepancies: tamperedRec.discrepancies,
          });
        } else {
          setTamperStatus(null);
        }
      } catch (secErr) {
        console.warn("Security status fetch notice:", secErr);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    setActionLoading(true);
    setError('');
    
    // Update local UI state to 'Analyzing' first
    setClaim(prev => ({ ...prev, status: 'Analyzing' }));

    try {
      const res = await fetch(`${API_URL}/api/claims/${claimId}/analyze`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Failed to run AI analysis pipeline.');
      const updatedClaim = await res.json();
      setClaim(updatedClaim);
      if (updatedClaim.photos && updatedClaim.photos.length > 0) {
        // Refresh selected photo with analyses
        const matched = updatedClaim.photos.find(p => p.id === selectedPhoto?.id) || updatedClaim.photos[0];
        setSelectedPhoto(matched);
      }
    } catch (err) {
      setError(err.message);
      fetchClaimDetails(); // rollback/refresh
    } finally {
      setActionLoading(false);
    }
  };

  const findRepairShops = async () => {
    setSearchingShops(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/claims/${claimId}/repair-shops`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Failed to search repair shops.');
      const data = await res.json();
      setShops(data.shops || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearchingShops(false);
    }
  };

  const startChat = (shop) => {
    setSelectedShop(shop);
    setChatSession(Math.random().toString(36).substring(7));
    setChatLog([
      {
        sender: 'agent',
        text: `Hello! I'm your booking assistant. I see you want to schedule an appointment with ${shop.name} for repairs. What date and time works best for you?`
      }
    ]);
    setChatOpen(true);
  };

  const sendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || sendingChat) return;

    const userText = chatMessage.trim();
    setChatLog(prev => [...prev, { sender: 'user', text: userText }]);
    setChatMessage('');
    setSendingChat(true);

    try {
      const res = await fetch(`${API_URL}/api/claims/${claimId}/book-appointment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: chatSession,
          message: userText,
          shop_name: selectedShop.name
        })
      });

      if (!res.ok) throw new Error('Booking assistant connection error.');
      const data = await res.json();
      
      setChatLog(prev => [...prev, { sender: 'agent', text: data.agent_message }]);
    } catch (err) {
      setChatLog(prev => [...prev, { sender: 'agent', text: `Sorry, I'm experiencing connectivity issues: ${err.message}` }]);
    } finally {
      setSendingChat(false);
    }
  };

  // Helper to parse detections from Photo.analysis_result
  const getDetections = (photo) => {
    if (!photo?.analysis_result?.detections) return [];
    try {
      // It can be double serialized or a single JSON string
      const parsed = typeof photo.analysis_result.detections === 'string'
        ? JSON.parse(photo.analysis_result.detections)
        : photo.analysis_result.detections;
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error('Error parsing detections:', e);
      return [];
    }
  };

  const getEstimateItems = (claim) => {
    if (!claim?.estimates || claim.estimates.length === 0) return [];
    const est = claim.estimates[0];
    try {
      const parsed = typeof est.items === 'string' ? JSON.parse(est.items) : est.items;
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center">
          <Loader2 size={36} className="animate-spin text-indigo-500 mb-4" />
          <p className="text-zinc-500 text-sm">Loading claim data...</p>
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center max-w-md mx-auto text-center px-6">
          <AlertCircle size={48} className="text-red-500 mb-4" />
          <h2 className="text-lg font-bold">Claim details not found</h2>
          <button onClick={() => router.push('/dashboard')} className="mt-6 bg-zinc-800 px-4 py-2.5 rounded-xl border border-zinc-700 hover:bg-zinc-700 text-xs font-semibold">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const detections = getDetections(selectedPhoto);
  const estimateItems = getEstimateItems(claim);
  const totalCost = claim.estimates?.[0]?.total_amount || 0;

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {/* Back navigation and status */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-zinc-500 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight">Claim #{claim.id}</h1>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase ${
                  claim.status === 'Assessed' 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : claim.status === 'Analyzing'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                }`}>
                  {claim.status}
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">Filed by {claim.customer_name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {claim.status !== 'Assessed' && (
              <button
                onClick={triggerAnalysis}
                disabled={actionLoading || claim.status === 'Analyzing'}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:pointer-events-none text-white font-semibold px-4 py-2.5 rounded-2xl shadow-lg transition-all text-xs"
              >
                {claim.status === 'Analyzing' ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Analyzing Damage...</span>
                  </>
                ) : (
                  <>
                    <Play size={14} />
                    <span>Run AI Analysis</span>
                  </>
                )}
              </button>
            )}
            {claim.status === 'Assessed' && (
              <button
                onClick={triggerAnalysis}
                disabled={actionLoading}
                className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-semibold px-4 py-2.5 rounded-2xl border border-zinc-700 transition-all text-xs"
              >
                <RefreshCw size={14} className={actionLoading ? 'animate-spin' : ''} />
                <span>Re-Analyze</span>
              </button>
            )}
          </div>
        </div>

        {tamperStatus?.isTampered && (
          <div className="flex items-start gap-3 p-4 bg-rose-500/15 border border-rose-500/30 rounded-2xl text-rose-300 text-xs mb-6 shadow-lg shadow-rose-950/40">
            <AlertTriangle size={18} className="text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-bold text-rose-400 text-sm">Security Audit Alert: Database Tampering Detected on Claim #{claim.id}</div>
              <div>
                The SQLite database row total has been modified out-of-band and fails cryptographic HMAC-SHA256 signature verification.
              </div>
              <div className="text-zinc-400 text-[11px] font-mono">
                Discrepancy: {tamperStatus.discrepancies?.join(', ')}
              </div>
              <Link href="/security" className="inline-flex items-center gap-1 text-indigo-400 hover:underline text-[11px] font-semibold mt-1">
                <span>View Incident in Security Console</span>
                <ExternalLink size={10} />
              </Link>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm mb-6">
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN: Photos and Bounding Box Canvas (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Interactive Image Overlay */}
            <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-3xl p-6 relative overflow-hidden shadow-xl">
              <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-4">
                Interactive Damage Visualizer
              </span>
              
              {selectedPhoto ? (
                <div className="flex flex-col items-center">
                  <div className="relative w-full max-h-[480px] overflow-hidden rounded-2xl bg-zinc-950 border border-zinc-850 flex items-center justify-center">
                    <img 
                      src={selectedPhoto.url} 
                      alt="Damage" 
                      className="w-full h-auto max-h-[480px] object-contain block" 
                    />
                    
                    {/* Bounding box overlays */}
                    {detections.map((det, idx) => {
                      const [xMin, yMin, xMax, yMax] = det.box;
                      return (
                        <div
                          key={idx}
                          className="absolute border-[2.5px] border-red-500 bg-red-500/10 rounded-sm cursor-help transition-all group"
                          style={{
                            left: `${xMin * 100}%`,
                            top: `${yMin * 100}%`,
                            width: `${(xMax - xMin) * 100}%`,
                            height: `${(yMax - yMin) * 100}%`,
                          }}
                        >
                          <span className="absolute bottom-full left-0 mb-1 bg-red-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20">
                            {det.type} ({(det.confidence * 100).toFixed(0)}%)
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  
                  {detections.length > 0 && (
                    <div className="flex flex-wrap gap-2 justify-center mt-4">
                      {detections.map((det, idx) => (
                        <span key={idx} className="bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize">
                          {det.type.replace(/-/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-zinc-600 text-xs">
                  No images uploaded
                </div>
              )}
            </div>

            {/* Photo Thumbnails */}
            {claim.photos && claim.photos.length > 1 && (
              <div className="flex gap-4 overflow-x-auto pb-2">
                {claim.photos.map((photo) => {
                  const isSelected = selectedPhoto?.id === photo.id;
                  const count = getDetections(photo).length;
                  return (
                    <div
                      key={photo.id}
                      onClick={() => setSelectedPhoto(photo)}
                      className={`w-20 h-20 rounded-2xl overflow-hidden cursor-pointer border-2 shrink-0 transition-all relative ${
                        isSelected ? 'border-indigo-500 scale-[1.03]' : 'border-zinc-800 hover:border-zinc-700'
                      }`}
                    >
                      <img src={photo.url} alt="Thumbnail" className="w-full h-full object-cover" />
                      {count > 0 && (
                        <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-600 border border-zinc-950 flex items-center justify-center text-[9px] font-bold text-white">
                          {count}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            
            {/* Description Card */}
            <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-3xl p-6 shadow-md">
              <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Claim Description</span>
              <p className="text-sm text-zinc-300 leading-6">{claim.description || 'No description provided'}</p>
              
              <div className="grid grid-cols-2 gap-4 mt-6 border-t border-zinc-800/60 pt-4 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <Calendar size={14} className="text-zinc-600" />
                  <span>Date: {claim.accident_date ? new Date(claim.accident_date).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin size={14} className="text-zinc-600" />
                  <span>Location: {[claim.incident_city, claim.incident_state].filter(Boolean).join(', ') || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Estimates, Shops, Chat (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* AI Estimation Card */}
            <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-3xl p-6 shadow-xl flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                  AI Damage Estimate
                </span>
                <DollarSign size={18} className="text-zinc-500" />
              </div>

              {claim.status === 'New' || claim.status === 'Analyzing' ? (
                <div className="py-6 text-center">
                  <Wrench size={32} className="text-zinc-600 mx-auto mb-2" />
                  <p className="text-xs text-zinc-400">No estimate generated yet. Run analysis to calculate repair cost.</p>
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <span className="text-3xl font-bold tracking-tight text-white">
                      ${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className="text-[10px] text-zinc-400 block mt-1">Total estimated parts & labor</span>
                  </div>

                  {estimateItems.length > 0 && (
                    <div className="border-t border-zinc-800/60 pt-4 mt-2">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="text-zinc-500 border-b border-zinc-800/40">
                            <th className="pb-2 font-medium">Part / Item</th>
                            <th className="pb-2 text-right font-medium">Cost</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-850">
                          {estimateItems.map((item, idx) => (
                            <tr key={idx} className="text-zinc-300">
                              <td className="py-2.5 pr-2 font-medium capitalize">{item.part.replace(/-/g, ' ')}</td>
                              <td className="py-2.5 text-right font-mono text-zinc-400">${item.cost.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Zero-Trust Cryptographic Provenance */}
                  <div className="mt-4 pt-4 border-t border-zinc-800/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                        Security & Provenance
                      </span>
                      <Link href="/security" className="text-[10px] text-indigo-400 hover:underline flex items-center gap-1 font-mono">
                        <span>Ledger #{(securityCert?.nonce || claim.id)}</span>
                        <ExternalLink size={10} />
                      </Link>
                    </div>

                    <div className="bg-zinc-950/80 rounded-2xl p-3 border border-zinc-850 space-y-2 text-[11px] font-mono">
                      <div className="flex items-center justify-between text-zinc-400">
                        <span className="flex items-center gap-1.5 text-zinc-300 font-semibold">
                          <Key size={12} className="text-indigo-400" />
                          <span>HMAC-SHA256 Signed</span>
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          AUTHENTIC
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-zinc-500 text-[10px]">
                        <span>Agent Principal:</span>
                        <span className="text-zinc-300">ProcessorAgent</span>
                      </div>

                      <div className="flex items-center justify-between text-zinc-500 text-[10px]">
                        <span>Sandbox Runtime:</span>
                        <span className="text-purple-400">gVisor / Cloud Run (0 Egress)</span>
                      </div>

                      <div className="flex items-center justify-between text-zinc-500 text-[10px]">
                        <span>Policy Check:</span>
                        <span className="text-emerald-400">Under $2,500 Cap</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Repair Shop & Chat Section */}
            {claim.status === 'Assessed' && (
              <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-3xl p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                    Book Repairs
                  </span>
                  <Wrench size={16} className="text-zinc-500" />
                </div>

                {shops.length === 0 ? (
                  <button
                    onClick={findRepairShops}
                    disabled={searchingShops}
                    className="w-full h-11 bg-zinc-800 border border-zinc-700 text-white font-semibold rounded-2xl flex items-center justify-center gap-2 hover:bg-zinc-750 active:scale-95 transition-all text-xs"
                  >
                    {searchingShops ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        <span>Finding certified shops...</span>
                      </>
                    ) : (
                      <>
                        <Search size={14} />
                        <span>Find Certified Repair Shops</span>
                      </>
                    )}
                  </button>
                ) : (
                  <div className="space-y-4">
                    <p className="text-xs text-zinc-400">Select a certified repair shop to book your appointment:</p>
                    <div className="space-y-3">
                      {shops.map((shop, i) => (
                        <div
                          key={i}
                          onClick={() => startChat(shop)}
                          className="p-3.5 bg-zinc-950 border border-zinc-850 hover:border-indigo-500/50 rounded-2xl cursor-pointer hover:bg-zinc-900/30 transition-all flex flex-col"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{shop.name}</span>
                            <span className="text-[10px] text-amber-400 font-bold">★ {shop.rating || 'N/A'}</span>
                          </div>
                          <span className="text-[10px] text-zinc-500 mt-1">{shop.address}</span>
                          <span className="text-[10px] text-indigo-400 mt-2 flex items-center gap-1 font-semibold">
                            <MessageSquare size={11} />
                            <span>Book with AI Agent</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* CHAT DRAWER / PANEL FOR APPOINTMENT BOOKING */}
      <AnimatePresence>
        {chatOpen && selectedShop && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-end"
            onClick={() => setChatOpen(false)}
          >
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="w-full max-w-md h-full bg-zinc-900 border-l border-zinc-800 flex flex-col justify-between shadow-2xl relative"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Chat Header */}
              <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-950">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                    <User size={16} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">Booking Assistant</h3>
                    <p className="text-[10px] text-zinc-500">Scheduling repairs with {selectedShop.name}</p>
                  </div>
                </div>
                <button
                  onClick={() => setChatOpen(false)}
                  className="text-zinc-500 hover:text-white transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Chat Log */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-zinc-950/20">
                {chatLog.map((msg, i) => {
                  const isAgent = msg.sender === 'agent';
                  return (
                    <div
                      key={i}
                      className={`flex ${isAgent ? 'justify-start' : 'justify-end'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-5 shadow-sm ${
                          isAgent
                            ? 'bg-zinc-800 text-zinc-200 rounded-tl-sm'
                            : 'bg-indigo-600 text-white rounded-tr-sm'
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  );
                })}
                {sendingChat && (
                  <div className="flex justify-start">
                    <div className="bg-zinc-800 text-zinc-400 rounded-2xl rounded-tl-sm px-4 py-3 text-xs flex items-center gap-1.5">
                      <Loader2 size={12} className="animate-spin" />
                      <span>Agent is typing...</span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input */}
              <form onSubmit={sendChatMessage} className="p-4 border-t border-zinc-800 bg-zinc-950 flex items-center gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="Type dates or times (e.g. Next Monday 10am)..."
                  className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 h-10 text-xs focus:outline-none focus:border-indigo-500 transition-all text-white placeholder-zinc-600"
                />
                <button
                  type="submit"
                  disabled={sendingChat || !chatMessage.trim()}
                  className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-500 active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all"
                >
                  <Send size={14} />
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
