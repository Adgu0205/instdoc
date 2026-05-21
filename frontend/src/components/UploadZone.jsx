import React, { useState, useRef } from 'react';
import { Upload, FileText, ClipboardList, AlertCircle, RefreshCw } from 'lucide-react';
import { analyzeFile, analyzeText } from '../services/api';

export default function UploadZone({ onAnalysisComplete, onError }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'paste'
  const [dragActive, setDragActive] = useState(false);
  const [pastedText, setPastedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const fileInputRef = useRef(null);

  const loadingStages = [
    'Initializing secure document sandbox...',
    'Extracting semantic text layout...',
    'Running deterministic keyword scoring...',
    'Invoking Gemini 2.5 Flash analysis...',
    'Structuring risk profiles and simulations...',
    'Validating final legal safety audit...'
  ];

  const cycleLoadingStages = () => {
    let index = 0;
    setLoadingStage(loadingStages[0]);
    const interval = setInterval(() => {
      index = (index + 1) % loadingStages.length;
      setLoadingStage(loadingStages[index]);
    }, 2800);
    return interval;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    setIsLoading(true);
    const stageInterval = cycleLoadingStages();
    try {
      const data = await analyzeFile(file);
      onAnalysisComplete(data);
    } catch (err) {
      onError(err.message || 'An error occurred while uploading and parsing your file.');
    } finally {
      clearInterval(stageInterval);
      setIsLoading(false);
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!pastedText.trim()) return;

    setIsLoading(true);
    const stageInterval = cycleLoadingStages();
    try {
      const data = await analyzeText(pastedText);
      onAnalysisComplete(data);
    } catch (err) {
      onError(err.message || 'An error occurred while analyzing the contract text.');
    } finally {
      clearInterval(stageInterval);
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mt-6 bg-paper border border-editorial-border shadow-sm p-6 relative">
      {/* Privacy Notice Header */}
      <div className="bg-stone-100 text-xs text-stone-600 px-4 py-2 text-center uppercase tracking-wide border-b border-editorial-border mb-6">
        🔒 Confidential Process: Your contracts are parsed temporarily in-memory and never permanently stored.
      </div>

      {/* Tabs */}
      <div className="flex border-b border-editorial-border mb-6">
        <button
          onClick={() => setActiveTab('upload')}
          className={`flex-1 py-3 text-sm font-serif font-semibold tracking-wider uppercase flex items-center justify-center gap-2 border-b-2 transition-all ${
            activeTab === 'upload'
              ? 'border-charcoal text-ink bg-stone-50/50'
              : 'border-transparent text-stone-500 hover:text-stone-700'
          }`}
        >
          <Upload className="w-4 h-4" />
          Upload Document (.pdf, .docx, .txt)
        </button>
        <button
          onClick={() => setActiveTab('paste')}
          className={`flex-1 py-3 text-sm font-serif font-semibold tracking-wider uppercase flex items-center justify-center gap-2 border-b-2 transition-all ${
            activeTab === 'paste'
              ? 'border-charcoal text-ink bg-stone-50/50'
              : 'border-transparent text-stone-500 hover:text-stone-700'
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          Paste Plain Text
        </button>
      </div>

      {/* Upload Panel */}
      {activeTab === 'upload' && (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          className={`border border-dashed p-10 text-center cursor-pointer transition-colors duration-200 ${
            dragActive
              ? 'border-editorial-gold bg-stone-50'
              : 'border-editorial-border hover:bg-stone-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
          />
          <div className="max-w-md mx-auto flex flex-col items-center">
            <div className="w-12 h-12 rounded-full border border-editorial-border flex items-center justify-center mb-4 bg-cream">
              <FileText className="w-6 h-6 text-editorial-gold" />
            </div>
            <h3 className="font-serif text-lg font-bold text-ink mb-1">
              Drag & Drop your contract file here
            </h3>
            <p className="text-xs text-stone-500 uppercase tracking-widest mb-3">
              or click to browse local files
            </p>
            <span className="text-xs text-stone-400">
              Supported Formats: PDF, DOCX, TXT (Maximum file size: 5.00MB)
            </span>
          </div>
        </div>
      )}

      {/* Paste Panel */}
      {activeTab === 'paste' && (
        <form onSubmit={handleTextSubmit} className="space-y-4">
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            rows={10}
            placeholder="Paste your legal clauses or the entire agreement text here..."
            className="w-full p-4 border border-editorial-border bg-cream-light font-sans text-sm focus:outline-none focus:border-charcoal resize-y placeholder:text-stone-400"
          ></textarea>
          <div className="flex justify-between items-center">
            <span className="text-xs text-stone-500 font-medium">
              Characters: {pastedText.length.toLocaleString()} | Words: {pastedText.split(/\s+/).filter(Boolean).length.toLocaleString()}
            </span>
            <button
              type="submit"
              disabled={!pastedText.trim()}
              className={`px-6 py-2.5 text-xs font-serif font-bold uppercase tracking-wider border border-charcoal bg-charcoal text-cream hover:bg-white hover:text-charcoal transition-colors duration-200 ${
                !pastedText.trim() ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              Analyze Contract Risk
            </button>
          </div>
        </form>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-cream/95 z-50 flex flex-col items-center justify-center p-8 transition-opacity duration-300">
          <div className="relative mb-6">
            <RefreshCw className="w-10 h-10 text-editorial-gold animate-spin" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-xs font-serif italic text-charcoal">
              ⚖️
            </div>
          </div>
          <h2 className="font-serif text-xl font-black text-ink mb-1 uppercase tracking-wider">
            Auditing Ledger Clauses
          </h2>
          <p className="text-xs font-mono uppercase tracking-widest text-stone-500 animate-pulse">
            {loadingStage}
          </p>
          <div className="w-48 h-0.5 bg-stone-200 overflow-hidden mt-4 relative">
            <div className="w-1/2 h-full bg-editorial-gold absolute left-0 top-0 animate-[shimmer_1.5s_infinite]"></div>
          </div>
          <p className="mt-8 text-[11px] text-stone-400 max-w-xs text-center">
            Parsing document structure, looking up commercial precedents, and generating risk heatmaps.
          </p>
        </div>
      )}
    </div>
  );
}
