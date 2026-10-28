import React, { useState, useRef } from 'react'
import {
  Leaf,
  Upload,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Info,
  Calendar,
  Thermometer,
  Eye,
  FileText
} from 'lucide-react'

export default function FreshnessWorkspace({ apiBaseUrl = 'http://127.0.0.1:8001' }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState(null)
  const [foodHint, setFoodHint] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [apiError, setApiError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFile = (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setValidationError('Please upload a valid image file (JPEG, PNG, or WEBP).')
      return
    }
    // Max 15MB
    if (file.size > 15 * 1024 * 1024) {
      setValidationError('Image size exceeds 15 MB limit. Please select a smaller photo.')
      return
    }

    setValidationError(null)
    setApiError(null)
    setResult(null)

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    const url = URL.createObjectURL(file)
    setSelectedFile(file)
    setPreviewUrl(url)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setSelectedFile(null)
    setPreviewUrl(null)
    setValidationError(null)
    setResult(null)
    setApiError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleAnalyze = async () => {
    if (!selectedFile) return
    setIsAnalyzing(true)
    setApiError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      let url = `${apiBaseUrl}/api/v1/food/freshness`
      if (foodHint.trim()) {
        url += `?food_hint=${encodeURIComponent(foodHint.trim())}`
      }

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Freshness evaluation failed.')
      }

      setResult(data)
    } catch (err) {
      setApiError(err.message || 'Unable to connect to the freshness detection backend.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const getScoreColor = (label) => {
    switch (label) {
      case 'Fresh':
        return '#10b981'
      case 'Moderate':
        return '#f59e0b'
      case 'Spoiled':
        return '#ef4444'
      default:
        return '#64748b'
    }
  }

  return (
    <div className="module-view">
      {/* Module Header Banner */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Quality Control & Spoilage Auditing</span>
          </div>
          <h1 className="welcome-title">Freshness & Spoilage Detection</h1>
          <p className="welcome-description">
            Evaluate produce surface degradation, oxidation browning, discoloration patterns, and fungal growth indicators.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <Leaf size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {isAnalyzing ? 'Scanning...' : result ? `${result.freshness_score}/100` : selectedFile ? 'Ready' : 'Awaiting'}
              </span>
              <span className="metric-label">Analysis State</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-orange">
              <ShieldCheck size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {result ? result.freshness_label : 'Visual Heuristics'}
              </span>
              <span className="metric-label">Quality Classification</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Section */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Produce & Food Specimen Analysis</h2>
            <p className="section-subtitle">
              A photo can reveal visible surface cues only. This heuristic screening cannot determine whether food is safe to eat.
            </p>
          </div>
          <span className="card-badge badge-emerald">Heuristic Vision Pipeline</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          {/* File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            style={{ display: 'none' }}
          />

          {/* Optional Food Label / Category Hint */}
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--color-primary-800)',
                marginBottom: '6px',
              }}
            >
              Food Item or Category Hint (Optional — e.g. "Apple", "Curry", "Spinach", "Bread")
            </label>
            <input
              type="text"
              placeholder="e.g. Banana, Chicken, Strawberry, Bread..."
              value={foodHint}
              onChange={(e) => setFoodHint(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid rgba(22, 62, 48, 0.15)',
                background: '#ffffff',
                fontSize: '0.88rem',
                color: 'var(--color-text-main)',
              }}
            />
          </div>

          {/* Upload Dropzone / Preview */}
          {!selectedFile ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false) }}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${isDragging ? '#10b981' : 'rgba(22, 62, 48, 0.2)'}`,
                background: isDragging ? 'rgba(16, 185, 129, 0.05)' : 'rgba(244, 237, 227, 0.35)',
                borderRadius: 'var(--radius-md)',
                padding: '44px 20px',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                marginBottom: '20px',
              }}
            >
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 14px',
                  color: '#059669',
                }}
              >
                <Upload size={26} />
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                Drag and drop food photo here
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '10px' }}>
                Supports PNG, JPG, JPEG, and WEBP (Max 15MB)
              </p>
              <button
                type="button"
                className="card-action-btn"
                style={{ display: 'inline-flex', width: 'auto', padding: '8px 18px', fontSize: '0.84rem' }}
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}
              >
                Browse Image
              </button>
            </div>
          ) : (
            <div style={{ marginBottom: '24px' }}>
              <div
                style={{
                  display: 'flex',
                  gap: '20px',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  padding: '16px',
                  background: '#ffffff',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(22, 62, 48, 0.1)',
                }}
              >
                <img
                  src={previewUrl}
                  alt="Food Specimen Preview"
                  style={{
                    width: '130px',
                    height: '130px',
                    objectFit: 'cover',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.1)',
                  }}
                />
                <div style={{ flex: 1, minWidth: '200px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <CheckCircle2 size={18} color="#10b981" />
                    <span style={{ fontWeight: 700, color: 'var(--color-primary-900)', fontSize: '0.95rem' }}>
                      {selectedFile.name}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                    Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
                      className="card-action-btn"
                      style={{
                        display: 'inline-flex',
                        width: 'auto',
                        padding: '8px 20px',
                        fontSize: '0.88rem',
                        opacity: isAnalyzing ? 0.7 : 1,
                      }}
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          <span>Auditing Visual Markers...</span>
                        </>
                      ) : (
                        <>
                          <Leaf size={16} />
                          <span>Detect Freshness</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleClear}
                      disabled={isAnalyzing}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 14px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid #fecaca',
                        background: '#fef2f2',
                        color: '#991b1b',
                        fontSize: '0.84rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <Trash2 size={15} />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Validation Error */}
          {validationError && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 16px',
                background: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: 'var(--radius-sm)',
                color: '#991b1b',
                fontSize: '0.84rem',
                marginBottom: '16px',
              }}
            >
              <AlertCircle size={17} />
              <span>{validationError}</span>
            </div>
          )}

          {/* API Error */}
          {apiError && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 16px',
                background: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: 'var(--radius-sm)',
                color: '#991b1b',
                fontSize: '0.84rem',
                marginBottom: '16px',
              }}
            >
              <AlertCircle size={17} />
              <span>{apiError}</span>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div
              style={{
                background: 'rgba(250, 247, 242, 0.85)',
                border: '1px solid rgba(22, 62, 48, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '24px',
                marginTop: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
              }}
            >
              {/* Header result row */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  borderBottom: '1px solid rgba(22, 62, 48, 0.08)',
                  paddingBottom: '16px',
                }}
              >
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Food Label (Best Effort)
                  </span>
                  <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--color-primary-900)' }}>
                    {result.detected_food}
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Category: <strong>{result.food_category.toUpperCase()}</strong> | Visual screening only
                  </span>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span
                    className={`card-badge ${
                      result.freshness_label === 'Fresh'
                        ? 'badge-emerald'
                        : result.freshness_label === 'Moderate'
                        ? 'badge-amber'
                        : 'badge-orange'
                    }`}
                    style={{ fontSize: '0.9rem', padding: '6px 14px' }}
                  >
                    {result.freshness_label} ({result.freshness_score}/100)
                  </span>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    Not a food-safety determination
                  </div>
                </div>
              </div>

              {result.pipeline_disclosure && (
                <div style={{
                  fontSize: '0.76rem',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.45,
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  padding: '10px 12px',
                }}>
                  <strong>Analysis method ({result.analysis_mode}):</strong> {result.pipeline_disclosure}
                  <br />
                  Visual appearance cannot establish microbial safety or detect hidden contamination. Do not use this score to decide whether food is safe to consume.
                </div>
              )}

              {/* Freshness Score Bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px', fontWeight: 600 }}>
                  <span>Freshness Index</span>
                  <span style={{ color: getScoreColor(result.freshness_label) }}>{result.freshness_score}%</span>
                </div>
                <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${result.freshness_score}%`,
                      height: '100%',
                      background: getScoreColor(result.freshness_label),
                      borderRadius: '4px',
                      transition: 'width 0.6s ease',
                    }}
                  />
                </div>
              </div>

              {/* Reasoning & Visual Cues */}
              <div style={{ background: '#ffffff', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '8px' }}>
                  Visual Diagnostic Analysis
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '12px' }}>
                  {result.reasoning}
                </p>

                <div style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--color-primary-800)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Detected Visual Signs:
                </div>
                <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {result.detected_signs.map((sign, idx) => (
                    <li key={idx} style={{ fontSize: '0.82rem', color: 'var(--color-text-main)' }}>
                      {sign}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Extracted Computer Vision Features Grid */}
              {result.extracted_features && (
                <div>
                  <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
                    Extracted Surface Metrics
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)', textAlign: 'center' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Vivid Fresh Color</span>
                      <strong style={{ fontSize: '1rem', color: '#059669' }}>{result.extracted_features.fresh_vivid_colour_pct}%</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)', textAlign: 'center' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Discoloration / Browning</span>
                      <strong style={{ fontSize: '1rem', color: '#b45309' }}>{result.extracted_features.brown_discolouration_pct}%</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)', textAlign: 'center' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Mould Teal/Blue</span>
                      <strong style={{ fontSize: '1rem', color: '#dc2626' }}>{result.extracted_features.mould_teal_pct}%</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)', textAlign: 'center' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Texture Variance</span>
                      <strong style={{ fontSize: '1rem', color: 'var(--color-primary-800)' }}>{result.extracted_features.texture_variance}</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Handling & Storage Guidance */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div style={{ background: 'rgba(240, 248, 245, 0.8)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Thermometer size={16} color="#059669" />
                    Recommended Storage & Preservation
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Disclaimer Notice */}
              <div
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.45,
                  background: 'rgba(255, 255, 255, 0.9)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  borderLeft: '3px solid var(--color-accent-amber)',
                }}
              >
                <strong>Food Safety Notice:</strong> {result.disclaimer}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
