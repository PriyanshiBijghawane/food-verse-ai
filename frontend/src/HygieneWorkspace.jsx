import React, { useState, useRef } from 'react'
import {
  Store,
  Upload,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Video,
  Download,
  Check,
  XCircle
} from 'lucide-react'

export default function HygieneWorkspace({ apiBaseUrl = 'http://127.0.0.1:8000' }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [mediaType, setMediaType] = useState('image') // 'image' or 'video'
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [apiError, setApiError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFile = (file) => {
    if (!file) return
    const isImg = file.type.startsWith('image/')
    const isVid = file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|avi|webm|mkv)$/i)

    if (!isImg && !isVid) {
      setValidationError('Please upload a valid image (JPEG, PNG, WEBP) or video (MP4, MOV, AVI, WEBM, MKV).')
      return
    }

    const maxImageBytes = 15 * 1024 * 1024 // 15MB
    const maxVideoBytes = 60 * 1024 * 1024 // 60MB

    if (isImg && file.size > maxImageBytes) {
      setValidationError('Image exceeds 15 MB limit.')
      return
    }
    if (isVid && file.size > maxVideoBytes) {
      setValidationError('Video exceeds 60 MB limit.')
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
    setMediaType(isVid ? 'video' : 'image')
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

      const response = await fetch(`${apiBaseUrl}/api/v1/hygiene/audit`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Hygiene audit failed.')
      }

      setResult(data)
    } catch (err) {
      setApiError(err.message || 'Unable to connect to the hygiene audit service.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleDownloadReport = (format = 'markdown') => {
    if (!result?.audit_id) return
    window.open(`${apiBaseUrl}/api/v1/hygiene/report/${result.audit_id}?format=${format}`, '_blank')
  }

  return (
    <div className="module-view">
      {/* Banner */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Commercial Kitchen Safety & Sanitation Audit</span>
          </div>
          <h1 className="welcome-title">Restaurant Hygiene Monitoring</h1>
          <p className="welcome-description">
            Automated visual inspection of kitchen prep counters, sanitation zones, food handling compliance, and cross-contamination hazards.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <Store size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {isAnalyzing ? 'Auditing...' : result ? `${result.compliance_score}/100` : selectedFile ? 'Ready' : 'Awaiting'}
              </span>
              <span className="metric-label">Compliance Score</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-orange">
              <ShieldCheck size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {result ? result.audit_status : 'Multi-Frame Inspection'}
              </span>
              <span className="metric-label">Audit Rating</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Section */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Kitchen Image or Video Footage Upload</h2>
            <p className="section-subtitle">
              Upload kitchen photos or recorded video clips for automated frame sampling and indicator auditing.
            </p>
          </div>
          <span className="card-badge badge-amber">Vision Inspection</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          {/* File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/mp4,video/quicktime,video/x-msvideo,video/webm,video/x-matroska"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            style={{ display: 'none' }}
          />

          {/* Upload Dropzone / Preview */}
          {!selectedFile ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false) }}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${isDragging ? '#f59e0b' : 'rgba(22, 62, 48, 0.2)'}`,
                background: isDragging ? 'rgba(245, 158, 11, 0.05)' : 'rgba(244, 237, 227, 0.35)',
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
                  background: 'rgba(245, 158, 11, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 14px',
                  color: '#d97706',
                }}
              >
                <Upload size={26} />
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                Drag and drop kitchen photo or video footage
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '10px' }}>
                Photos (JPEG, PNG, WEBP max 15MB) or Video (MP4, MOV, AVI, WEBM, MKV max 60MB)
              </p>
              <button
                type="button"
                className="card-action-btn"
                style={{ display: 'inline-flex', width: 'auto', padding: '8px 18px', fontSize: '0.84rem' }}
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}
              >
                Select Media File
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
                {mediaType === 'image' ? (
                  <img
                    src={previewUrl}
                    alt="Kitchen Footage Preview"
                    style={{
                      width: '140px',
                      height: '110px',
                      objectFit: 'cover',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid rgba(22, 62, 48, 0.1)',
                    }}
                  />
                ) : (
                  <video
                    src={previewUrl}
                    controls
                    style={{
                      width: '200px',
                      maxHeight: '120px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid rgba(22, 62, 48, 0.1)',
                    }}
                  />
                )}
                <div style={{ flex: 1, minWidth: '200px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <CheckCircle2 size={18} color="#10b981" />
                    <span style={{ fontWeight: 700, color: 'var(--color-primary-900)', fontSize: '0.95rem' }}>
                      {selectedFile.name}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                    Type: {mediaType.toUpperCase()} | Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
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
                          <span>Extracting & Auditing Frames...</span>
                        </>
                      ) : (
                        <>
                          <Store size={16} />
                          <span>Run Hygiene Audit</span>
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

          {/* Audit Results Presentation */}
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
                    Audit Reference: {result.audit_id}
                  </span>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary-900)' }}>
                    Commercial Kitchen Hygiene Audit
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Engine: <strong>{result.inspection_engine}</strong> | Analyzed Frames: <strong>{result.frames_analyzed}</strong>
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: result.compliance_score >= 80 ? '#059669' : result.compliance_score >= 60 ? '#d97706' : '#dc2626' }}>
                      {result.compliance_score}/100
                    </div>
                    <span
                      className={`card-badge ${
                        result.audit_status === 'Compliant'
                          ? 'badge-emerald'
                          : result.audit_status === 'Needs Improvement'
                          ? 'badge-amber'
                          : 'badge-orange'
                      }`}
                    >
                      {result.audit_status}
                    </span>
                  </div>

                  <button
                    onClick={() => handleDownloadReport('markdown')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: '#ffffff',
                      border: '1px solid rgba(22, 62, 48, 0.15)',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      color: 'var(--color-primary-900)',
                    }}
                  >
                    <Download size={15} />
                    <span>Download Report</span>
                  </button>
                </div>
              </div>

              {/* Executive Summary */}
              <div style={{ background: '#ffffff', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '6px' }}>
                  Auditor Executive Summary
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                  {result.ai_summary}
                </p>
              </div>

              {/* Observable Violations List */}
              <div>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
                  Observable Sanitation Violations ({result.violations?.length || 0})
                </h4>

                {!result.violations || result.violations.length === 0 ? (
                  <div style={{ background: '#f0fdf4', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid #bbf7d0', color: '#166534', fontSize: '0.84rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={18} />
                    <span>No observable violations or gross contamination detected in inspected frames.</span>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.violations.map((v, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#ffffff',
                          padding: '14px',
                          borderRadius: 'var(--radius-sm)',
                          borderLeft: `4px solid ${v.severity === 'high' ? '#dc2626' : v.severity === 'medium' ? '#f59e0b' : '#3b82f6'}`,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--color-primary-900)' }}>
                            {v.violation_type}
                          </span>
                          <span
                            className="card-badge"
                            style={{
                              background: v.severity === 'high' ? '#fee2e2' : '#fef3c7',
                              color: v.severity === 'high' ? '#991b1b' : '#92400e',
                              fontSize: '0.7rem',
                            }}
                          >
                            {v.severity.toUpperCase()} SEVERITY
                          </span>
                        </div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                          <strong>Evidence:</strong> {v.evidence}
                        </p>
                        <p style={{ fontSize: '0.8rem', color: '#047857' }}>
                          <strong>Action Plan:</strong> {v.recommendation}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Category Observations */}
              {result.observations && (
                <div>
                  <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
                    Visual Observations by Station
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
                    {Object.entries(result.observations).map(([cat, note], idx) => (
                      <div key={idx} style={{ background: '#ffffff', padding: '12px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                        <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--color-primary-800)', display: 'block', textTransform: 'capitalize', marginBottom: '4px' }}>
                          {cat.replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>
                          {note}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div
                style={{
                  fontSize: '0.71rem',
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.45,
                  background: 'rgba(255, 255, 255, 0.85)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  borderLeft: '3px solid var(--color-accent-amber)',
                }}
              >
                {result.disclaimer}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
