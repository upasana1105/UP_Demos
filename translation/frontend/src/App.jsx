import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  ChevronRight,
  FileText,
  Languages,
  FileCheck,
  Download,
  AlertCircle,
  Cloud,
  Cpu,
  Network,
  Eye,
  Plus,
  X,
  Target,
  Sparkles,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Helper for tailwind class merging
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE = window.location.hostname === "localhost" ? "http://localhost:8000" : "";

const Dashboard = () => {
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [glossaryFile, setGlossaryFile] = useState(null);
  const [glossaryPath, setGlossaryPath] = useState('');
  const [targetLang, setTargetLang] = useState('de');
  const [glossaryId, setGlossaryId] = useState('');
  const [status, setStatus] = useState('idle'); // idle, processing, complete, error
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);
  const [agentReasoning, setAgentReasoning] = useState('');
  const [auditReport, setAuditReport] = useState(null);
  const [activeTab, setActiveTab] = useState('audit'); // 'pdf' or 'audit'
  const logContainerRef = useRef(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message }]);
  };

  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile && uploadedFile.type === "application/pdf") {
      setFile(uploadedFile);
      setFileUrl(URL.createObjectURL(uploadedFile));
      addLog(`Selected document: ${uploadedFile.name}`);
    }
  };

  const handleGlossaryUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile && (uploadedFile.name.endsWith('.csv'))) {
      setGlossaryFile(uploadedFile);
      addLog(`Selected glossary: ${uploadedFile.name}`);
      const formData = new FormData();
      formData.append('file', uploadedFile);
      try {
        const response = await axios.post(`${API_BASE}/api/upload-glossary`, formData);
        if (response.data.status === 'success') {
          setGlossaryPath(response.data.file_path);
          addLog(`Glossary staged successfully.`);
        }
      } catch (err) {
        addLog(`Error staging glossary: ${err.message}`);
      }
    }
  };

  const startTranslation = async () => {
    if (!file) return;
    setStatus('processing');
    setLogs([]);
    setResult(null);
    addLog("🚀 Initializing high-precision orchestration...");
    addLog(`🌐 Target: ${targetLang.toUpperCase()}`);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', targetLang);
    if (glossaryId) formData.append('glossary_id', glossaryId);
    if (glossaryPath) formData.append('custom_glossary_path', glossaryPath);

    try {
      const response = await axios.post(`${API_BASE}/api/translate`, formData);
      if (response.data.status === 'success') {
        setStatus('complete');
        setResult(response.data.output_file);
        setAgentReasoning(response.data.agent_reasoning);
        setAuditReport(response.data.audit_report);
        setActiveTab('audit');
        addLog("✅ Workflow and Audit completed successfully.");
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      setStatus('error');
      addLog(`❌ Fatal Error: ${error.message}`);
    }
  };

  const handleDownload = () => window.open(`${API_BASE}/api/download?file_path=${result}`, '_blank');

  return (
    <div className="h-screen w-screen bg-kpmg-light text-slate-900 font-sans selection:bg-kpmg-blue/30 overflow-hidden flex flex-col">
      {/* Subtle Corporate Background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-slate-200/50 to-transparent" />
      </div>

      <div className="relative z-10 flex flex-col h-full w-full">
        {/* Top Control Bar */}
        <header className="px-6 py-4 border-b border-slate-200 bg-[#002b7a] flex items-center justify-between shadow-sm z-20 shrink-0">
          <div className="flex items-center gap-6">
            <div className="flex items-center pr-6 border-r border-white/20">
              <img src="/kpmg_logo.png" alt="KPMG Logo" className="h-16 object-contain" />
            </div>
            <h1 className="text-lg font-light tracking-wide text-white">Translation Assistant</h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Target Language */}
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-[11px] font-bold uppercase tracking-widest focus:outline-none focus:ring-1 focus:ring-white text-white shadow-inner"
            >
              <option value="de" className="text-slate-800">German (HGB)</option>
              <option value="ja" className="text-slate-800">Japanese (GAAP)</option>
              <option value="fr" className="text-slate-800">French (IFRS)</option>
              <option value="es" className="text-slate-800">Spanish (IASB)</option>
              <option value="en" className="text-slate-800">English (Global)</option>
            </select>

            {/* Glossary */}
            <label className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all cursor-pointer shadow-inner",
              glossaryFile ? "bg-white/20 border-white text-white" : "bg-white/5 border-white/20 text-white/80 hover:bg-white/10"
            )}>
              {glossaryFile ? <FileCheck className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
              <span className="text-[10px] font-bold uppercase tracking-widest">
                {glossaryFile ? glossaryFile.name : 'Add Glossary'}
              </span>
              <input id="glossary-upload" type="file" className="hidden" onChange={handleGlossaryUpload} accept=".csv" />
            </label>

            {/* Execution */}
            <button
              onClick={startTranslation}
              disabled={!file || status === 'processing'}
              className={cn(
                "flex items-center gap-2 px-6 py-2.5 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] transition-all shadow-md",
                !file || status === 'processing'
                  ? "bg-slate-400 border border-transparent opacity-50 cursor-not-allowed text-white"
                  : "bg-kpmg-blue text-white hover:bg-blue-700 hover:-translate-y-0.5"
              )}
            >
              {status === 'processing' ? <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {status === 'processing' ? 'Processing...' : 'Run Pipeline'}
            </button>
          </div>
        </header>


        {/* Main Side-by-Side Split */}
        <main className="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 min-h-0">

          {/* LEFT: SOURCE DOCUMENT */}
          <div className="bg-white border border-slate-200 rounded-3xl flex flex-col shadow-xl relative overflow-hidden group h-full">
            <div className="px-6 py-3 border-b border-slate-200 bg-slate-50 flex justify-between items-center z-10 shrink-0">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-600" />
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-700">Original Document</span>
              </div>
              <div className="px-2 py-0.5 bg-slate-200 rounded text-[9px] font-bold uppercase tracking-widest text-slate-600">Source</div>
            </div>

            <div className="flex-grow relative bg-slate-50/50 flex flex-col justify-center items-center overflow-hidden">
              {!file ? (
                <label className="w-3/4 max-w-sm h-64 border-2 border-dashed border-slate-300 rounded-3xl flex flex-col items-center justify-center cursor-pointer hover:border-kpmg-blue hover:bg-blue-50/50 transition-colors group/drop shadow-sm bg-white">
                  <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf" />
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4 group-hover/drop:scale-110 transition-transform shadow-sm">
                    <Upload className="w-6 h-6 text-kpmg-dark" />
                  </div>
                  <span className="text-sm font-bold text-slate-800">Upload PDF Report</span>
                  <span className="text-[10px] text-slate-500 mt-2 uppercase tracking-[0.2em]">Ready for Validation</span>
                </label>
              ) : (
                <div className="absolute inset-0 p-4">
                  <iframe src={fileUrl} className="w-full h-full rounded-2xl border border-slate-200 shadow-sm bg-white" title="Original Document" />
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: TARGET DOCUMENT / CONSOLE */}
          <div className={cn(
            "bg-white border rounded-3xl flex flex-col shadow-xl relative overflow-hidden transition-colors duration-700 h-full",
            status === 'complete' ? "border-kpmg-blue/30 shadow-[0_0_50px_rgba(0,94,184,0.08)]" : "border-slate-200"
          )}>
            <div className="px-6 py-3 border-b border-slate-200 bg-slate-50 flex justify-between items-center z-10 shrink-0">
              <div className="flex items-center gap-4">
                <div onClick={() => setActiveTab('pdf')} className={cn(
                  "flex items-center gap-2 cursor-pointer py-1 border-b-2 transition-all",
                  activeTab === 'pdf' ? "border-kpmg-blue text-kpmg-blue" : "border-transparent text-slate-500 hover:text-slate-700"
                )}>
                  {status === 'complete' ? <FileCheck className="w-4 h-4" /> : <Target className="w-4 h-4" />}
                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">Localized Output</span>
                </div>
                {status === 'complete' && auditReport && (
                  <div onClick={() => setActiveTab('audit')} className={cn(
                    "flex items-center gap-2 cursor-pointer py-1 border-b-2 transition-all",
                    activeTab === 'audit' ? "border-kpmg-blue text-kpmg-blue" : "border-transparent text-slate-500 hover:text-slate-700"
                  )}>
                    <Zap className="w-4 h-4" />
                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">Quality Audit</span>
                    <div className="px-1.5 py-0.5 bg-blue-100 rounded-full text-[8px] font-bold text-kpmg-blue">NEW</div>
                  </div>
                )}
              </div>
              {status === 'complete' && activeTab === 'pdf' && (
                <button onClick={handleDownload} className="flex items-center gap-2 px-3 py-1 bg-kpmg-blue hover:bg-blue-700 rounded font-bold uppercase text-[9px] tracking-widest text-white transition-colors">
                  <Download className="w-3 h-3" /> Download PDF
                </button>
              )}
            </div>

            <div className="flex-grow relative bg-slate-50/50 flex flex-col overflow-hidden">
              {status === 'complete' ? (
                <div className="absolute inset-0 p-4">
                  {activeTab === 'pdf' ? (
                    <iframe src={`${API_BASE}/api/view-file?file_path=${result}`} className="w-full h-full rounded-2xl border border-slate-200 shadow-sm bg-white" title="Translated Document" />
                  ) : (
                    <div className="h-full w-full flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2">
                      {/* Audit KPI Grid */}
                      <div className="grid grid-cols-4 gap-3 shrink-0">
                        {[
                          { label: 'Overall', score: auditReport.overall_score, color: 'bg-kpmg-blue' },
                          { label: 'Accuracy', score: auditReport.accuracy_score, color: 'bg-emerald-500' },
                          { label: 'Fluency', score: auditReport.fluency_score, color: 'bg-amber-500' },
                          { label: 'Tone', score: auditReport.tone_score, color: 'bg-indigo-500' }
                        ].map((stat, i) => (
                          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.1 }} key={stat.label} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center relative overflow-hidden group">
                            <div className={cn("absolute bottom-0 left-0 h-1 transition-all group-hover:h-full group-hover:opacity-5", stat.color)} style={{ width: `${stat.score}%` }} />
                            <div className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-1">{stat.label}</div>
                            <div className="text-2xl font-black text-slate-800">{stat.score}%</div>
                          </motion.div>
                        ))}
                      </div>

                      {/* Executive Summary */}
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm shrink-0">
                        <div className="flex items-center gap-2 mb-3">
                          <Eye className="w-4 h-4 text-kpmg-blue" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-slate-700">Auditor's Executive Summary</span>
                        </div>
                        <p className="text-[12px] leading-relaxed text-slate-600 italic">"{auditReport.executive_summary}"</p>
                      </motion.div>

                      {/* Issue Timeline */}
                      <div className="flex-grow flex flex-col min-h-0">
                        <div className="flex items-center gap-2 mb-3">
                          <AlertCircle className="w-4 h-4 text-amber-500" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-slate-700">Audit Findings ({auditReport.audit_findings?.length || 0})</span>
                        </div>
                        <div className="space-y-3">
                          {auditReport.audit_findings?.map((finding, idx) => (
                            <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.5 + idx * 0.1 }} key={idx} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-amber-500 hover:shadow-md transition-shadow">
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="text-[11px] font-bold text-slate-800 uppercase tracking-wide">{finding.issue}</h4>
                                <span className={cn(
                                  "px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest",
                                  finding.impact === 'High' ? "bg-rose-100 text-rose-600" : "bg-amber-100 text-amber-600"
                                )}>{finding.impact}</span>
                              </div>
                              <div className="grid grid-cols-2 gap-4 mb-3">
                                <div className="space-y-1">
                                  <div className="text-[8px] font-black uppercase text-slate-400">Original</div>
                                  <div className="text-[10px] p-2 bg-slate-50 rounded-lg text-slate-600 line-clamp-2">{finding.original_text}</div>
                                </div>
                                <div className="space-y-1">
                                  <div className="text-[8px] font-black uppercase text-slate-400">Translated</div>
                                  <div className="text-[10px] p-2 bg-blue-50 rounded-lg text-kpmg-blue line-clamp-2">{finding.translated_text}</div>
                                </div>
                              </div>
                              <div className="flex items-start gap-2 bg-emerald-50/50 p-2 rounded-lg border border-emerald-100/50">
                                <ChevronRight className="w-3 h-3 text-emerald-500 mt-1 shrink-0" />
                                <div className="text-[10px] text-emerald-700 leading-relaxed font-medium">
                                  <span className="font-black uppercase text-[8px] tracking-widest block mb-0.5 text-emerald-800">Recommendation</span>
                                  {finding.recommendation}
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-grow flex flex-col overflow-hidden">
                  <div ref={logContainerRef} className="flex-grow p-6 font-mono text-[11px] overflow-y-auto custom-scrollbar space-y-3">
                    <AnimatePresence>
                      {logs.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-300 select-none">
                          <Network className="w-16 h-16 mb-4" />
                          <p className="text-[10px] uppercase tracking-[0.4em] font-black text-center max-w-xs text-slate-400">Awaiting Source Document<br />and Execution Trigger</p>
                        </div>
                      )}
                      {logs.map((log, i) => (
                        <motion.div key={i} initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }} className="flex gap-4">
                          <span className="text-slate-400 font-bold shrink-0">[{log.timestamp}]</span>
                          <span className={cn("leading-relaxed", log.message.includes("✅") ? "text-emerald-600 font-bold" : log.message.includes("❌") ? "text-rose-600 font-bold" : log.message.includes("🚀") ? "text-kpmg-blue font-bold" : "text-slate-700")}>
                            {log.message}
                          </span>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                  {status === 'processing' && (
                    <div className="p-4 border-t border-slate-200 bg-slate-100 shrink-0">
                      <div className="h-1 bg-slate-200 rounded-full overflow-hidden w-full">
                        <motion.div initial={{ x: "-100%" }} animate={{ x: "0%" }} transition={{ duration: 40, ease: "linear" }} className="h-full w-full bg-gradient-to-r from-kpmg-blue to-blue-400" />
                      </div>
                      <p className="text-[9px] font-black uppercase text-center text-kpmg-blue mt-2 tracking-[0.3em] animate-pulse">Neural Translation & Audit Active</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.1); border-radius: 10px; }
      `}</style>
    </div>
  );
};

export default Dashboard;
