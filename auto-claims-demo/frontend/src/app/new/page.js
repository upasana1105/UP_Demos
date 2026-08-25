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
import { ArrowLeft, ArrowRight, Upload, X, Check, MapPin, Calendar, Car, Shield, AlertCircle, FileText } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_URL } from '../config';

const STEPS = [
  { id: 1, name: 'Incident Details' },
  { id: 2, name: 'Classification' },
  { id: 3, name: 'Upload Photos' },
  { id: 4, name: 'Review & Submit' }
];

export default function NewClaim() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [policyNumber, setPolicyNumber] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form State
  const [accidentDate, setAccidentDate] = useState('');
  const [description, setDescription] = useState('');
  const [incidentCity, setIncidentCity] = useState('');
  const [incidentState, setIncidentState] = useState('');
  const [incidentType, setIncidentType] = useState('Single Vehicle Collision');
  const [collisionType, setCollisionType] = useState('Front Collision');
  const [severity, setSeverity] = useState('Minor Damage');
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);

  useEffect(() => {
    const policy = localStorage.getItem('policy_number');
    const name = localStorage.getItem('customer_name');
    if (!policy) {
      router.replace('/login');
      return;
    }
    setPolicyNumber(policy);
    setCustomerName(name || '');
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    setAccidentDate(today);
  }, [router]);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles((prev) => [...prev, ...selectedFiles]);

    const newPreviews = selectedFiles.map((file) => URL.createObjectURL(file));
    setPreviews((prev) => [...prev, ...newPreviews]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => {
      // Revoke URL to prevent memory leaks
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  };

  const nextStep = () => {
    if (currentStep === 1 && (!accidentDate || !description.trim() || !incidentCity.trim())) {
      setError('Please fill in the accident date, description, and city.');
      return;
    }
    setError('');
    setCurrentStep((prev) => Math.min(prev + 1, STEPS.length));
  };

  const prevStep = () => {
    setError('');
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('policy_number', policyNumber);
    formData.append('customer_name', customerName);
    formData.append('description', description);
    formData.append('accident_date', accidentDate);
    formData.append('incident_city', incidentCity);
    formData.append('incident_state', incidentState);
    formData.append('incident_type', incidentType);
    formData.append('collision_type', collisionType);
    formData.append('severity', severity);

    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const res = await fetch(`${API_URL}/api/claims`, {
        method: 'POST',
        body: formData,
        // Content-Type header is automatically set to multipart/form-data by fetch when using FormData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const detail = errData.detail;
        if (detail && typeof detail === 'object') {
          const reason = detail.reasoning || detail.message || (detail.violations && detail.violations.join(', ')) || JSON.stringify(detail);
          throw new Error(`Security Firewall Policy: ${reason}`);
        }
        throw new Error(errData.detail || errData.error || 'Failed to submit claim');
      }

      const claim = await res.json();
      router.push(`/claims/${claim.id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const slideVariants = {
    enter: (direction) => ({
      x: direction > 0 ? 100 : -100,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (direction) => ({
      x: direction < 0 ? 100 : -100,
      opacity: 0
    })
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-3xl w-full mx-auto px-6 py-10">
        {/* Progress header */}
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-6">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-zinc-500 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <h1 className="text-xl font-bold">File a New Claim</h1>
          </div>

          <div className="flex justify-between items-center relative">
            <div className="absolute top-1/2 left-0 w-full h-[2px] bg-zinc-800 -translate-y-1/2 z-0" />
            <div 
              className="absolute top-1/2 left-0 h-[2px] bg-indigo-500 -translate-y-1/2 z-0 transition-all duration-300"
              style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
            />
            
            {STEPS.map((step) => {
              const active = step.id <= currentStep;
              const current = step.id === currentStep;
              return (
                <div key={step.id} className="flex flex-col items-center z-10">
                  <div 
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all border ${
                      current 
                        ? 'bg-indigo-600 text-white border-indigo-500 ring-4 ring-indigo-500/20' 
                        : active 
                          ? 'bg-indigo-950 text-indigo-400 border-indigo-500/50' 
                          : 'bg-zinc-900 text-zinc-500 border-zinc-800'
                    }`}
                  >
                    {active && step.id < currentStep ? <Check size={14} /> : step.id}
                  </div>
                  <span className={`text-[10px] font-semibold mt-2 ${active ? 'text-zinc-200' : 'text-zinc-500'}`}>
                    {step.name}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm mb-8">
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-3xl p-8 shadow-xl min-h-[380px] flex flex-col justify-between">
          <div className="flex-1">
            {currentStep === 1 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                      Accident Date
                    </label>
                    <input
                      type="date"
                      value={accidentDate}
                      onChange={(e) => setAccidentDate(e.target.value)}
                      className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                        City
                      </label>
                      <input
                        type="text"
                        value={incidentCity}
                        onChange={(e) => setIncidentCity(e.target.value)}
                        placeholder="e.g. Springfield"
                        className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                        State
                      </label>
                      <input
                        type="text"
                        value={incidentState}
                        onChange={(e) => setIncidentState(e.target.value)}
                        placeholder="e.g. IL"
                        className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm uppercase"
                        maxLength={2}
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                    Accident Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Briefly describe what happened (e.g., Rear-ended by another vehicle at an intersection)..."
                    rows={4}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm resize-none"
                  />
                </div>
              </motion.div>
            )}

            {currentStep === 2 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                      Incident Type
                    </label>
                    <select
                      value={incidentType}
                      onChange={(e) => setIncidentType(e.target.value)}
                      className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm cursor-pointer"
                    >
                      <option>Single Vehicle Collision</option>
                      <option>Multi-vehicle Collision</option>
                      <option>Parked Car</option>
                      <option>Vehicle Theft</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                      Collision Type
                    </label>
                    <select
                      value={collisionType}
                      onChange={(e) => setCollisionType(e.target.value)}
                      className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm cursor-pointer"
                    >
                      <option>Front Collision</option>
                      <option>Rear Collision</option>
                      <option>Side Collision</option>
                      <option>Unknown</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                    Initial Severity Guess
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full h-11 bg-zinc-950 border border-zinc-800 rounded-xl px-4 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm cursor-pointer"
                  >
                    <option>Minor Damage</option>
                    <option>Major Damage</option>
                    <option>Total Loss</option>
                  </select>
                </div>
              </motion.div>
            )}

            {currentStep === 3 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="border-2 border-dashed border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors relative">
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleFileChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="w-12 h-12 bg-zinc-950 rounded-xl flex items-center justify-center text-zinc-400 mb-3 border border-zinc-800">
                    <Upload size={20} />
                  </div>
                  <p className="text-sm font-semibold">Upload vehicle images</p>
                  <p className="text-[11px] text-zinc-500 mt-1">PNG, JPG, JPEG up to 10MB each</p>
                </div>

                {previews.length > 0 && (
                  <div className="grid grid-cols-4 gap-4 mt-6">
                    {previews.map((src, idx) => (
                      <div key={idx} className="relative aspect-square rounded-xl overflow-hidden border border-zinc-800 group">
                        <img src={src} alt="Upload preview" className="w-full h-full object-cover" />
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full flex items-center justify-center text-zinc-300 hover:text-white hover:bg-black/90 transition-all"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {currentStep === 4 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <h3 className="text-sm font-bold text-zinc-400 border-b border-zinc-800 pb-2 mb-4">Claim Summary</h3>
                
                <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-xs">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-zinc-500" />
                    <span className="text-zinc-400">Date:</span>
                    <span className="font-semibold">{accidentDate}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={14} className="text-zinc-500" />
                    <span className="text-zinc-400">Location:</span>
                    <span className="font-semibold">{incidentCity}, {incidentState || 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Car size={14} className="text-zinc-500" />
                    <span className="text-zinc-400">Incident type:</span>
                    <span className="font-semibold">{incidentType}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield size={14} className="text-zinc-500" />
                    <span className="text-zinc-400">Collision details:</span>
                    <span className="font-semibold">{collisionType} ({severity})</span>
                  </div>
                </div>

                <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800/80">
                  <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Description</span>
                  <p className="text-xs text-zinc-300 leading-5">{description}</p>
                </div>

                <div className="flex gap-2 mt-4">
                  {previews.map((src, idx) => (
                    <div key={idx} className="w-10 h-10 rounded-lg overflow-hidden border border-zinc-800 shrink-0">
                      <img src={src} alt="Upload preview" className="w-full h-full object-cover" />
                    </div>
                  ))}
                  <div className="flex items-center text-[10px] text-zinc-500 font-medium ml-2">
                    {files.length} Photo{files.length !== 1 && 's'} attached
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          <div className="flex items-center justify-between border-t border-zinc-800/60 pt-6 mt-8">
            <button
              onClick={prevStep}
              disabled={currentStep === 1 || loading}
              className="flex items-center gap-2 text-zinc-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors text-sm font-semibold"
            >
              <ArrowLeft size={16} />
              <span>Back</span>
            </button>

            {currentStep < STEPS.length ? (
              <button
                type="button"
                onClick={nextStep}
                className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white font-semibold px-4 py-2.5 rounded-xl border border-zinc-700 transition-all text-sm"
              >
                <span>Continue</span>
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-semibold px-5 py-2.5 rounded-xl transition-all text-sm disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white" />
                ) : (
                  <>
                    <span>Submit Claim</span>
                    <Check size={16} />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
