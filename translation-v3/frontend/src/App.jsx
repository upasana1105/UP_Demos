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
  Zap,
  Sliders,
  HelpCircle,
  Minimize2,
  Maximize2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Smartphone,
  Monitor,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Helper for tailwind class merging
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE = window.location.hostname === "localhost" ? "http://localhost:8002" : "";

// Simulator Preset Phrases & Calculations
const PRESETS = {
  short: {
    label: "Short String (Button / Label)",
    en: "Search Patients",
    de: "Patientendatenbank durchsuchen",
    fr: "Rechercher des patients",
    fi: "Etsi potilaita",
    custom: "Search Patients EXTRA LONG STRESS TEST PHRASE FOR EXPANSION"
  },
  medium: {
    label: "Medium Title (Card Header)",
    en: "Therapy Stages & Recommendations",
    de: "Therapiestufen und Empfehlungen",
    fr: "Étapes de traitement et recommandations",
    fi: "Hoidon vaiheet ja suositukset",
    custom: "Therapy Stages & Recommendations MAXIMUM EXPANSION STRESS TEST STRING"
  },
  paragraph: {
    label: "Paragraph (Description Block)",
    en: "The oncology board reviewed the pathology report and authorized the high-priority systemic chemotherapy plan.",
    de: "Der Onkologie-Ausschuss hat den Pathologiebericht überprüft und den hochprioritären systemischen Chemotherapieplan genehmigt.",
    fr: "Le comité d'oncologie a examiné le rapport de pathologie et a autorisé le protocole de chimiothérapie systémique hautement prioritaire.",
    fi: "Onkologinen työryhmä tarkisti patologian raportin ja valtuutti korkean prioriteetin systeemisen solunsalpaajahoidon.",
    custom: "The oncology board reviewed the pathology report and authorized the high-priority systemic chemotherapy plan EXTRA LONG STRESS PHRASE TO OBSERVE DRASTIC WRAPPING."
  }
};

const getSimulatedText = (presetKey, lang, sliderVal, customVal = '') => {
  if (presetKey === 'custom') {
    const baseText = customVal || "Enter custom text";
    if (sliderVal === 0) return baseText;
    const targetLen = Math.round(baseText.length * (1 + sliderVal / 100));
    let text = baseText;
    const padding = " [EXPANDED]";
    while (text.length < targetLen) {
      text += padding;
    }
    return text.substring(0, targetLen);
  }

  const preset = PRESETS[presetKey];
  const src = preset.en;
  const tr = preset[lang] || src;
  
  if (sliderVal === 0) return src;
  
  const targetLen = Math.round(src.length * (1 + sliderVal / 100));
  
  if (targetLen <= tr.length) {
    return tr.substring(0, targetLen);
  } else {
    let text = tr;
    const words = tr.split(' ');
    const lastWord = words[words.length - 1] || "extra";
    const padding = " " + lastWord;
    while (text.length < targetLen) {
      text += padding;
    }
    return text.substring(0, targetLen);
  }
};

const Dashboard = () => {
  const [viewMode, setViewMode] = useState('assistant'); // 'assistant' or 'simulator'
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
    if (uploadedFile && (uploadedFile.type === "application/pdf" || uploadedFile.name.endsWith(".pdf") || uploadedFile.name.endsWith(".docx") || uploadedFile.name.endsWith(".pptx"))) {
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
            <div className="flex flex-col">
              <h1 className="text-md font-black tracking-wider text-white uppercase">KPMG Translation Suite</h1>
              <span className="text-[9px] text-slate-300 tracking-widest uppercase font-bold">Intelligent Localization</span>
            </div>

            {/* View Mode Switcher */}
            <div className="flex bg-white/10 p-1 rounded-xl border border-white/10 shadow-inner ml-4">
              <button
                onClick={() => setViewMode('assistant')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5",
                  viewMode === 'assistant' ? "bg-white text-[#002b7a] shadow-md font-bold" : "text-white/70 hover:text-white hover:bg-white/5"
                )}
              >
                <Languages className="w-3.5 h-3.5" /> Assistant Mode
              </button>
              <button
                onClick={() => setViewMode('simulator')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5",
                  viewMode === 'simulator' ? "bg-white text-[#002b7a] shadow-md font-bold" : "text-white/70 hover:text-white hover:bg-white/5"
                )}
              >
                <Sliders className="w-3.5 h-3.5" /> Layout Simulator
              </button>
            </div>
          </div>

          {viewMode === 'assistant' ? (
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
                    : "bg-[#005EB8] text-white hover:bg-blue-700 hover:-translate-y-0.5"
                )}
              >
                {status === 'processing' ? <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {status === 'processing' ? 'Processing...' : 'Run Pipeline'}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="text-white/80 font-mono text-[10px] uppercase tracking-wider bg-white/5 border border-white/10 px-3 py-1.5 rounded-xl flex items-center gap-1.5">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                Interactive Lab Active
              </div>
            </div>
          )}
        </header>

        {viewMode === 'assistant' ? (
          /* Main Side-by-Side Split */
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
                    <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.docx,.pptx" />
                    <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4 group-hover/drop:scale-110 transition-transform shadow-sm">
                      <Upload className="w-6 h-6 text-[#002b7a]" />
                    </div>
                    <span className="text-sm font-bold text-slate-800">Upload Report (PDF, DOCX, PPTX)</span>
                    <span className="text-[10px] text-slate-500 mt-2 uppercase tracking-[0.2em]">Ready for Validation</span>
                  </label>
                ) : (
                  <div className="absolute inset-0 p-4 flex flex-col items-center justify-center bg-white rounded-2xl border border-slate-200 shadow-sm">
                    {file.name.endsWith('.pdf') ? (
                      <iframe src={fileUrl} className="w-full h-full rounded-xl" title="Original Document" />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-400 p-8 text-center">
                        <FileText className="w-16 h-16 mb-4 text-[#005EB8]" />
                        <span className="text-sm font-bold text-slate-700">{file.name}</span>
                        <span className="text-[10px] text-slate-500 mt-1 uppercase tracking-widest">Office Document Loaded</span>
                      </div>
                    )}
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
                    <Download className="w-3 h-3" /> Download File
                  </button>
                )}
              </div>

              <div className="flex-grow relative bg-slate-50/50 flex flex-col overflow-hidden">
                {status === 'complete' ? (
                  <div className="absolute inset-0 p-4">
                    {activeTab === 'pdf' ? (
                      result && result.endsWith('.pdf') ? (
                        <iframe src={`${API_BASE}/api/view-file?file_path=${result}`} className="w-full h-full rounded-2xl border border-slate-200 shadow-sm bg-white" title="Translated Document" />
                      ) : (
                        <div className="absolute inset-0 p-4 flex flex-col items-center justify-center bg-white rounded-2xl border border-slate-200 shadow-sm text-center">
                          <FileCheck className="w-16 h-16 mb-4 text-emerald-600" />
                          <span className="text-sm font-bold text-slate-700">{result ? result.split('/').pop() : 'Translated Document'}</span>
                          <span className="text-[10px] text-slate-500 mt-2 uppercase tracking-widest">Translation Complete</span>
                          <button onClick={handleDownload} className="mt-4 flex items-center gap-2 px-4 py-2 bg-kpmg-blue hover:bg-blue-700 rounded-xl font-bold uppercase text-[10px] tracking-widest text-white transition-colors shadow-md">
                            <Download className="w-4 h-4" /> Download File
                          </button>
                        </div>
                      )
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
        ) : (
          <Simulator />
        )}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.1); border-radius: 10px; }
      `}</style>
    </div>
  );
};

// Visual Layout Simulator Component
const Simulator = () => {
  const [presetKey, setPresetKey] = useState('short');
  const [selectedLang, setSelectedLang] = useState('de');
  const [sliderVal, setSliderVal] = useState(30);
  const [customText, setCustomText] = useState('');
  
  // Visual overlays
  const [helperBounds, setHelperBounds] = useState(true);
  const [helperOverflow, setHelperOverflow] = useState(true);
  const [helperBuffer, setHelperBuffer] = useState(true);
  const [helperReadability, setHelperReadability] = useState(true);
  
  // Viewport modes
  const [viewportMode, setViewportMode] = useState('desktop');
  
  // Tooltip hover status
  const [hoveredStrategy4, setHoveredStrategy4] = useState(false);
  
  // Simulated Telemetry Stream
  const [telemetry, setTelemetry] = useState([
    { timestamp: new Date().toLocaleTimeString(), message: "Simulator engine initialized in high-fidelity sandbox.", type: "system" },
    { timestamp: new Date().toLocaleTimeString(), message: "Active benchmark loaded: English Source to German Preset (+30% expansion rate default).", type: "info" }
  ]);
  
  const telemetryEndRef = useRef(null);
  
  useEffect(() => {
    if (telemetryEndRef.current) {
      telemetryEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [telemetry]);

  const addTelemetry = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setTelemetry(prev => [...prev, { timestamp, message, type }]);
  };

  const handleLangChange = (lang) => {
    setSelectedLang(lang);
    let defaultExp = 30;
    let langName = "German";
    let explanation = "";
    
    if (lang === 'de') {
      defaultExp = 30;
      langName = "German";
      explanation = "German compounding yields extremely long uninterrupted nouns (like 'Patientendatenbank') that break horizontal boundaries.";
    } else if (lang === 'fr') {
      defaultExp = 25;
      langName = "French";
      explanation = "French requires extra prepositions and descriptive layout elements (e.g. 'de traitement'), expanding character footprint.";
    } else if (lang === 'fi') {
      defaultExp = 35;
      langName = "Finnish";
      explanation = "Finnish utilizes severe morphological agglutination (word suffix stacking), rendering strings highly expansive.";
    } else if (lang === 'custom') {
      defaultExp = 80;
      langName = "Stress Test";
      explanation = "Forced stress mode (+80% length multiplier) to audit extreme wrapping thresholds and structural failure points.";
    }
    
    setSliderVal(defaultExp);
    addTelemetry(`🌐 Switched translation target preset to: ${langName} (+${defaultExp}% default expansion rate).`, 'info');
    if (explanation) {
      addTelemetry(`ℹ️ Linguistic constraint details: ${explanation}`, 'info');
    }
  };

  const handleSliderChange = (val) => {
    setSliderVal(val);
    if (val > 100) {
      addTelemetry(`🚨 Stress level WARNING: Text length increased by +${val}%. Unresponsive boxes will suffer complete collapse.`, 'alert');
    } else if (val > 50) {
      addTelemetry(`⚠️ High density warning: Text expansion set to +${val}%. Expect wrap thresholds to trigger.`, 'warning');
    } else if (val === 0) {
      addTelemetry(`✨ Standard English baseline (0% expansion) restored. All elements return to designed ideal layout size.`, 'optimal');
    } else {
      addTelemetry(`🔄 Slider adjusted: expansion stress is +${val}%.`, 'info');
    }
  };

  const handleCustomTextChange = (e) => {
    const txt = e.target.value;
    setCustomText(txt);
    if (presetKey !== 'custom') {
      setPresetKey('custom');
      addTelemetry(`✏️ Custom sandbox text loaded: "${txt.substring(0, 24)}..."`, 'info');
    }
  };

  const resetSimulator = () => {
    setPresetKey('short');
    setSelectedLang('de');
    setSliderVal(30);
    setCustomText('');
    setHelperBounds(true);
    setHelperOverflow(true);
    setHelperBuffer(true);
    setHelperReadability(true);
    setViewportMode('desktop');
    setTelemetry([
      { timestamp: new Date().toLocaleTimeString(), message: "Sandbox reset to default simulation parameters.", type: "system" },
      { timestamp: new Date().toLocaleTimeString(), message: "German preset active at baseline English staging.", type: "info" }
    ]);
  };

  const srcText = presetKey === 'custom' ? (customText || "Enter custom text") : PRESETS[presetKey].en;
  const simulatedText = getSimulatedText(presetKey, selectedLang, sliderVal, customText);

  return (
    <div className="flex-grow flex overflow-hidden bg-slate-900 text-slate-100 relative">
      {/* LEFT Panel: Control Panel */}
      <div className="w-full lg:w-[360px] bg-slate-950 border-r border-slate-800 p-5 flex flex-col gap-5 overflow-y-auto custom-scrollbar shrink-0 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#005EB8]" />
            <h2 className="text-[11px] font-black uppercase tracking-wider text-white">Sandbox Controls</h2>
          </div>
          <button onClick={resetSimulator} className="text-[8px] font-black uppercase tracking-widest px-2 py-1 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded border border-slate-800 flex items-center gap-1 transition-colors">
            <RefreshCw className="w-2.5 h-2.5" /> Reset
          </button>
        </div>

        {/* Preset Selectors */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[9px] font-black uppercase tracking-wider text-slate-500">Target Language Profile</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: 'de', label: 'German', exp: '+30%' },
              { id: 'fr', label: 'French', exp: '+25%' },
              { id: 'fi', label: 'Finnish', exp: '+35%' },
              { id: 'custom', label: 'Stress Test', exp: '+80%' }
            ].map((lang) => (
              <button
                key={lang.id}
                onClick={() => handleLangChange(lang.id)}
                className={cn(
                  "p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between",
                  selectedLang === lang.id
                    ? "bg-[#005EB8]/10 border-[#005EB8] text-white shadow-md"
                    : "bg-slate-900/50 border-slate-800 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200"
                )}
              >
                <span className="text-[10px] font-black uppercase tracking-wider">{lang.label}</span>
                <div className="flex items-center justify-between mt-1.5 w-full">
                  <span className="text-[7px] font-black text-slate-500 uppercase">Linguistic</span>
                  <span className={cn(
                    "text-[8px] font-mono font-black px-1 py-0.5 rounded",
                    selectedLang === lang.id ? "bg-[#005EB8] text-white" : "bg-slate-800 text-slate-400"
                  )}>{lang.exp}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Phrase Size Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[9px] font-black uppercase tracking-wider text-slate-500">Staged UI Component</label>
          <div className="flex flex-col gap-1">
            {[
              { id: 'short', label: 'Action Button (Short text)' },
              { id: 'medium', label: 'Card Header (Medium text)' },
              { id: 'paragraph', label: 'Description Block (Long text)' }
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setPresetKey(p.id);
                  addTelemetry(`📋 Component Preset Staged: ${p.label}.`, 'info');
                }}
                className={cn(
                  "px-3.5 py-2.5 rounded-xl border text-left text-[10px] font-bold transition-all flex items-center justify-between",
                  presetKey === p.id
                    ? "bg-slate-800/80 border-slate-700 text-white font-bold"
                    : "bg-slate-900/30 border-slate-850/50 text-slate-500 hover:bg-slate-900/50 hover:text-slate-300"
                )}
              >
                <span>{p.label}</span>
                {presetKey === p.id && <div className="w-1.5 h-1.5 bg-[#005EB8] rounded-full shadow-lg" />}
              </button>
            ))}
            
            {/* Custom input switch */}
            <button
              onClick={() => {
                setPresetKey('custom');
                addTelemetry(`✏️ Custom text string input staging enabled.`, 'info');
              }}
              className={cn(
                "px-3.5 py-2.5 rounded-xl border text-left text-[10px] font-bold transition-all flex items-center justify-between",
                presetKey === 'custom'
                  ? "bg-slate-800/80 border-slate-700 text-white font-bold"
                  : "bg-slate-900/30 border-slate-850/50 text-slate-500 hover:bg-slate-900/50 hover:text-slate-300"
              )}
            >
              <span>Custom Input String...</span>
              {presetKey === 'custom' && <div className="w-1.5 h-1.5 bg-[#005EB8] rounded-full shadow-lg" />}
            </button>
          </div>
        </div>

        {/* Custom text block */}
        {presetKey === 'custom' && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="flex flex-col gap-1">
            <textarea
              value={customText}
              onChange={handleCustomTextChange}
              placeholder="Type your custom text phrase here..."
              className="w-full h-16 bg-slate-900 border border-slate-850 rounded-xl p-2 text-[10px] font-medium focus:outline-none focus:ring-1 focus:ring-[#005EB8] text-slate-200 placeholder-slate-750 animate-fade-in"
            />
          </motion.div>
        )}

        {/* Dynamic expansion multiplier slider */}
        <div className="flex flex-col gap-1.5 bg-slate-900/30 p-3.5 rounded-xl border border-slate-850">
          <div className="flex justify-between items-center">
            <span className="text-[9px] font-black uppercase tracking-wider text-slate-500">Length Stressor</span>
            <span className={cn(
              "text-[8px] font-black px-1.5 py-0.5 rounded font-mono",
              sliderVal > 100 ? "bg-rose-950 text-rose-400" : sliderVal > 50 ? "bg-amber-950 text-amber-400" : "bg-[#005EB8]/20 text-blue-400"
            )}>+{sliderVal}% EXPANDED</span>
          </div>
          <input
            type="range"
            min="0"
            max="150"
            value={sliderVal}
            onChange={(e) => handleSliderChange(parseInt(e.target.value))}
            className="w-full accent-[#005EB8] cursor-pointer my-1"
          />
          <div className="flex justify-between text-[8px] font-bold text-slate-600">
            <span>0% (English Baseline)</span>
            <span>150% (Extreme)</span>
          </div>
        </div>

        {/* Visual HUD Overlays */}
        <div className="flex flex-col gap-2">
          <label className="text-[9px] font-black uppercase tracking-wider text-slate-500">Diagnostic Helper Toggles</label>
          <div className="flex flex-col gap-2">
            {[
              { id: 'bounds', state: helperBounds, setState: setHelperBounds, label: 'Outline Layout Bounds', desc: 'Highlights rigid/fluid container boundaries' },
              { id: 'overflow', state: helperOverflow, setState: setHelperOverflow, label: 'Identify Text Clipping', desc: 'Highlights overflows and truncation points in red' },
              { id: 'buffer', state: helperBuffer, setState: setHelperBuffer, label: 'Show Expansion Guidelines', desc: 'Draws a 30% designed safe margin limit guide' },
              { id: 'readability', state: helperReadability, setState: setHelperReadability, label: 'Readability Legibility HUD', desc: 'Calculates live visual legibility score' }
            ].map((opt) => (
              <label key={opt.id} className="flex items-start gap-2.5 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={opt.state}
                  onChange={(e) => {
                    opt.setState(e.target.checked);
                    addTelemetry(`🔧 Overlay '${opt.label}' ${e.target.checked ? 'activated' : 'deactivated'}.`, 'info');
                  }}
                  className="rounded border-slate-800 bg-slate-900 text-[#005EB8] focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5 mt-0.5 cursor-pointer"
                />
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-300 group-hover:text-white transition-colors">{opt.label}</span>
                  <span className="text-[8px] text-slate-600 leading-none mt-0.5">{opt.desc}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT Panel: Sandbox Arena */}
      <div className="flex-grow flex flex-col gap-4 p-4 overflow-hidden bg-slate-900">
        {/* Dashboard Title */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl px-5 py-3 flex justify-between items-center shrink-0 shadow-xl">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#005EB8]" />
            <span className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400">Layout sandbox engine</span>
          </div>
          
          {/* Viewport Mode Selector */}
          <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-800 shadow-inner">
            <button
              onClick={() => {
                setViewportMode('desktop');
                addTelemetry("🖥️ Viewport width set to Desktop mode.", "info");
              }}
              className={cn(
                "px-2.5 py-1 rounded text-[8px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5",
                viewportMode === 'desktop' ? "bg-slate-800 text-white shadow-md" : "text-slate-500 hover:text-slate-300"
              )}
            >
              <Monitor className="w-3.5 h-3.5" /> Desktop View
            </button>
            <button
              onClick={() => {
                setViewportMode('mobile');
                addTelemetry("📱 Viewport width set to Mobile device width. Layout container compacted.", "warning");
              }}
              className={cn(
                "px-2.5 py-1 rounded text-[8px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5",
                viewportMode === 'mobile' ? "bg-slate-800 text-white shadow-md" : "text-slate-500 hover:text-slate-300"
              )}
            >
              <Smartphone className="w-3.5 h-3.5" /> Mobile View
            </button>
          </div>
        </div>

        {/* Main Grid Arena */}
        <div className="flex-grow overflow-y-auto custom-scrollbar pr-1">
          <div className={cn(
            "transition-all duration-500",
            viewportMode === 'mobile' ? "max-w-[460px] mx-auto border-x border-dashed border-slate-700 px-4 py-2 bg-slate-950/20 rounded-3xl shadow-inner" : "w-full"
          )}>
            <div className={cn(
              "grid gap-4",
              viewportMode === 'mobile' ? "grid-cols-1" : "grid-cols-1 xl:grid-cols-2"
            )}>
              
              {/* STRATEGY 1 CARD */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-lg relative overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-[10px] font-black uppercase tracking-wider text-white">Strategy 1: CSS clamp() Typographic Floor</h3>
                    <p className="text-[8.5px] text-slate-500 leading-normal mt-0.5">
                      Sets a strict, un-shrinkable floor size under text, ensuring it remains legible while allowing wrappers to grow.
                    </p>
                  </div>
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[7px] font-black uppercase tracking-widest text-[#005EB8]">TYPOGRAPHY</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-1">
                  {/* Trap Box */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-rose-500 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-ping" /> Rigid Auto-Shrink
                      </span>
                      <span className="text-[7px] font-mono text-slate-600 font-bold uppercase">TRAP</span>
                    </div>

                    <div className={cn(
                      "w-full h-14 border bg-slate-900/40 flex items-center justify-center p-2.5 rounded-lg relative overflow-hidden transition-colors",
                      helperBounds ? "border-dashed border-rose-500/30" : "border-slate-850"
                    )}>
                      {(() => {
                        const calculatedSize = Math.max(4.5, Math.min(13.5, 13.5 * (srcText.length / simulatedText.length)));
                        const isIllegible = calculatedSize < 9.5;
                        return (
                          <div className="flex flex-col items-center w-full text-center">
                            <span
                              style={{ fontSize: `${calculatedSize}px`, lineHeight: '1.2' }}
                              className={cn(
                                "font-medium text-slate-300 break-all transition-all duration-150",
                                isIllegible && "text-rose-400 font-semibold"
                              )}
                            >
                              {simulatedText}
                            </span>
                            {helperReadability && (
                              <div className="absolute bottom-1 right-2">
                                <span className={cn(
                                  "text-[6.5px] font-black uppercase px-1.5 py-0.2 rounded-full font-mono tracking-wide",
                                  isIllegible ? "bg-rose-950 text-rose-400 animate-pulse font-bold" : "bg-slate-800 text-slate-500"
                                )}>
                                  {calculatedSize.toFixed(1)}px {isIllegible ? 'UNREADABLE' : 'LEGIBLE'}
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })()}
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none">
                      Shrinks font size indefinitely to squeeze into single row.
                    </div>
                  </div>

                  {/* Clamp Box */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between min-h-[130px] h-auto">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-emerald-500 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" /> CSS clamp() Floor
                      </span>
                      <span className="text-[7px] font-mono text-emerald-500/80 font-bold uppercase">OPTIMAL</span>
                    </div>

                    <div className={cn(
                      "w-full min-h-14 h-auto py-2 px-2.5 border bg-slate-900/40 flex items-center justify-center rounded-lg relative transition-all duration-300",
                      helperBounds ? "border-dashed border-emerald-500/30" : "border-slate-850"
                    )}>
                      <span
                        style={{ fontSize: 'clamp(11.5px, 1.3vw, 13.5px)', lineHeight: '1.3' }}
                        className="font-medium text-slate-300 text-center break-words w-full"
                      >
                        {simulatedText}
                      </span>
                      {helperReadability && (
                        <div className="absolute bottom-1 right-2">
                          <span className="text-[6.5px] font-black uppercase px-1.5 py-0.2 bg-emerald-950 text-emerald-400 rounded-full font-mono tracking-wide">
                            Clamp 11.5px Floor
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none mt-1.5">
                      Maintains legibility minimum, wraps characters vertically.
                    </div>
                  </div>
                </div>
              </div>

              {/* STRATEGY 2 CARD */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-lg relative overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-[10px] font-black uppercase tracking-wider text-white">Strategy 2: Flowing wrap vs Rigid Width Bounds</h3>
                    <p className="text-[8.5px] text-slate-500 leading-normal mt-0.5">
                      Replaces fixed boundaries and `whitespace-nowrap` structures with dynamic padding layouts that wrap text cleanly.
                    </p>
                  </div>
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[7px] font-black uppercase tracking-widest text-[#005EB8]">CONTAINERS</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-1">
                  {/* Trap Container */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-rose-500 flex items-center gap-1">
                        🔴 Fixed No-Wrap
                      </span>
                      <span className="text-[7px] font-mono text-slate-600 font-bold uppercase">TRAP</span>
                    </div>

                    <div className={cn(
                      "w-full h-12 border bg-slate-900/40 flex items-center px-3 rounded-lg relative overflow-hidden transition-colors",
                      helperBounds ? "border-dashed border-rose-500/30" : "border-slate-850"
                    )}>
                      <span className="text-[11px] text-slate-300 whitespace-nowrap">
                        {simulatedText}
                      </span>
                      {helperOverflow && simulatedText.length > srcText.length && (
                        <div className="absolute right-0 inset-y-0 w-8 bg-gradient-to-l from-rose-950 to-transparent flex items-center justify-end pr-1.5 pointer-events-none">
                          <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
                        </div>
                      )}
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none flex justify-between items-center">
                      <span>Clips expanded string tail</span>
                      {helperOverflow && simulatedText.length > srcText.length && (
                        <span className="text-[7.5px] font-black text-rose-400 uppercase tracking-wide animate-pulse">CLIPPED BOUNDS</span>
                      )}
                    </div>
                  </div>

                  {/* Fluid Wrap Container */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between min-h-[130px] h-auto">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-emerald-500 flex items-center gap-1">
                        🟢 flex flex-wrap
                      </span>
                      <span className="text-[7px] font-mono text-emerald-500/80 font-bold uppercase">OPTIMAL</span>
                    </div>

                    <div className={cn(
                      "w-full min-h-12 h-auto py-2 px-3 border bg-slate-900/40 flex items-center rounded-lg relative transition-all duration-300",
                      helperBounds ? "border-dashed border-emerald-500/30" : "border-slate-850"
                    )}>
                      <span className="text-[11px] text-slate-300 break-words leading-relaxed w-full">
                        {simulatedText}
                      </span>
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none mt-1.5">
                      Auto-wraps rows seamlessly and extends height parameters.
                    </div>
                  </div>
                </div>
              </div>

              {/* STRATEGY 3 CARD */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-lg relative overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-[10px] font-black uppercase tracking-wider text-white">Strategy 3: Design with 30% Expansion Buffers</h3>
                    <p className="text-[8.5px] text-slate-500 leading-normal mt-0.5">
                      Creates comfortable breathing space around English labels, accommodating natural text growth safely.
                    </p>
                  </div>
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[7px] font-black uppercase tracking-widest text-[#005EB8]">SPACING</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-1">
                  {/* Tight English Button */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-rose-500 flex items-center gap-1">
                        🔴 0% Spacing Margin
                      </span>
                      <span className="text-[7px] font-mono text-slate-600 font-bold uppercase">TRAP</span>
                    </div>

                    <div className="flex items-center justify-center w-full h-12">
                      <div className={cn(
                        "w-[105px] h-8 border rounded-lg flex items-center justify-center overflow-hidden whitespace-nowrap px-1 transition-all duration-300",
                        simulatedText.length > 14 ? "border-rose-950 bg-rose-950/10" : "border-slate-800 bg-slate-900"
                      )}>
                        <span className={cn(
                          "text-[10px] transition-colors font-medium",
                          simulatedText.length > 14 ? "text-rose-400 font-bold" : "text-slate-400"
                        )}>
                          {simulatedText}
                        </span>
                      </div>
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none">
                      Button labels collide/break because design is tight-fitted.
                    </div>
                  </div>

                  {/* Buffered Button */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-emerald-500 flex items-center gap-1">
                        🟢 30% Protective Margin
                      </span>
                      <span className="text-[7px] font-mono text-emerald-500/80 font-bold uppercase">OPTIMAL</span>
                    </div>

                    <div className="flex items-center justify-center w-full h-12">
                      <div className={cn(
                        "min-w-[105px] max-w-[190px] w-auto h-8 border bg-slate-900 rounded-lg flex items-center justify-center px-4 relative transition-all duration-300",
                        helperBounds ? "border-dashed border-emerald-500/30" : "border-slate-850"
                      )}>
                        <span className="text-[10px] text-slate-300 whitespace-nowrap font-medium">
                          {simulatedText}
                        </span>
                        {helperBuffer && (
                          <div className="absolute inset-0 border border-dashed border-blue-500/30 rounded-lg m-[2px] pointer-events-none flex items-center justify-center">
                            <span className="text-[6.5px] font-mono text-blue-400/40 uppercase tracking-wider absolute bottom-[-9px]">Safe Buffer Zone</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none">
                      Absorbs standard 30% text expansions cleanly inside cushion.
                    </div>
                  </div>
                </div>
              </div>

              {/* STRATEGY 4 CARD */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-lg relative overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-[10px] font-black uppercase tracking-wider text-white">Strategy 4: Truncated Ellipses + Hover Tooltips</h3>
                    <p className="text-[8.5px] text-slate-500 leading-normal mt-0.5">
                      Uses CSS text-overflow ellipsis inside highly restricted, locked tabular cells combined with rich hover tooltip blocks.
                    </p>
                  </div>
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[7px] font-black uppercase tracking-widest text-[#005EB8]">HUD DESIGN</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-1">
                  {/* Ugly Wrap */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-rose-500 flex items-center gap-1">
                        🔴 Letter-Break Wrap
                      </span>
                      <span className="text-[7px] font-mono text-slate-600 font-bold uppercase">TRAP</span>
                    </div>

                    <div className={cn(
                      "w-full h-14 border bg-slate-900/40 p-2 rounded-lg flex items-center justify-center overflow-hidden",
                      helperBounds ? "border-dashed border-rose-500/30" : "border-slate-850"
                    )}>
                      <span className="text-[9.5px] text-slate-400 text-center break-all font-medium leading-tight">
                        {simulatedText}
                      </span>
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none">
                      Distorts structural page alignments by vertical blowing.
                    </div>
                  </div>

                  {/* Truncate Box */}
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between h-[130px]">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-black uppercase text-emerald-500 flex items-center gap-1">
                        🟢 Truncation + Tooltip HUD
                      </span>
                      <span className="text-[7px] font-mono text-emerald-500/80 font-bold uppercase">OPTIMAL</span>
                    </div>

                    <div className="flex items-center justify-center w-full h-14 relative">
                      <div
                        onMouseEnter={() => {
                          setHoveredStrategy4(true);
                          addTelemetry("👁️ Hover detected: Rendering micro-animated premium high-contrast Tooltip HUD overlay.", "system");
                        }}
                        onMouseLeave={() => setHoveredStrategy4(false)}
                        className={cn(
                          "w-[140px] border bg-slate-900 flex items-center px-2.5 py-1.5 rounded-lg relative cursor-pointer transition-colors hover:bg-slate-850",
                          helperBounds ? "border-dashed border-emerald-500/30" : "border-slate-850"
                        )}
                      >
                        <span className="text-[10px] text-slate-300 truncate w-full block font-medium">
                          {simulatedText}
                        </span>

                        <AnimatePresence>
                          {hoveredStrategy4 && (
                            <motion.div
                              initial={{ opacity: 0, y: 6, scale: 0.95 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              exit={{ opacity: 0, y: 6, scale: 0.95 }}
                              className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-slate-950 text-white text-[9.5px] p-2.5 rounded-xl shadow-2xl border border-slate-800 z-30 w-[190px] pointer-events-none leading-relaxed text-center animate-fade-in"
                            >
                              <div className="font-black uppercase text-[7.5px] tracking-widest text-[#005EB8] mb-1 border-b border-slate-800 pb-0.5">
                                Full Localization String
                              </div>
                              <span className="text-slate-300 font-medium">{simulatedText}</span>
                              <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-950 border-r border-b border-slate-800 rotate-45 -translate-y-1" />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>

                    <div className="text-[8px] text-slate-500 leading-none">
                      Maintains layout stability, reveals complete strings on hover.
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Telemetry Console Box */}
        <div className="h-36 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl shrink-0">
          <div className="px-4 py-2 border-b border-slate-800 bg-slate-900 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-[#005EB8]" />
              <span className="text-[8.5px] font-black uppercase tracking-widest text-slate-400">Layout Telemetry Console</span>
            </div>
            <div className="flex items-center gap-1.5 font-mono text-[7.5px] text-slate-500">
              <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
              TELEMETRY ACTIVE
            </div>
          </div>
          <div className="flex-grow overflow-y-auto p-3 font-mono text-[9.5px] space-y-2 custom-scrollbar bg-slate-950/70">
            {telemetry.map((t, idx) => (
              <div key={idx} className="flex gap-3.5 leading-normal">
                <span className="text-slate-600 font-medium shrink-0 select-none">[{t.timestamp}]</span>
                <span className={cn(
                  t.type === 'system' ? "text-slate-500" :
                  t.type === 'warning' ? "text-amber-400 font-bold" :
                  t.type === 'alert' ? "text-rose-400 font-bold" :
                  t.type === 'optimal' ? "text-emerald-400 font-bold" : "text-slate-300"
                )}>
                  {t.message}
                </span>
              </div>
            ))}
            <div ref={telemetryEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
