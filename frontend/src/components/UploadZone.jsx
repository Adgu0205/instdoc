import React, { useState, useRef } from 'react';
import { Upload, FileText, ClipboardList } from 'lucide-react';

export default function UploadZone({ onFileSelected, onTextSubmitted }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'paste'
  const [dragActive, setDragActive] = useState(false);
  const [pastedText, setPastedText] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file) => {
    if (onFileSelected) {
      onFileSelected(file);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!pastedText.trim()) return;
    if (onTextSubmitted) {
      onTextSubmitted(pastedText);
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
    </div>
  );
}
