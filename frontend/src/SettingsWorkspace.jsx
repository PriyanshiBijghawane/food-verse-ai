import React, { useState, useEffect } from 'react'
import {
  Settings,
  Scale,
  Sparkles,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Server,
  Bell,
  Sliders,
  Palette,
  ChefHat,
  Eye
} from 'lucide-react'

export default function SettingsWorkspace({
  apiBaseUrl = 'http://127.0.0.1:8001',
  currentSettings = null,
  onSettingsUpdated = null,
  onNotification = null
}) {
  const [units, setUnits] = useState(currentSettings?.units || 'metric')
  const [defaultDiet, setDefaultDiet] = useState(currentSettings?.default_diet || 'balanced')
  const [defaultCuisine, setDefaultCuisine] = useState(currentSettings?.default_cuisine || 'Any')
  const [defaultCookingTime, setDefaultCookingTime] = useState(currentSettings?.default_cooking_time || 30)
  const [visionConfidence, setVisionConfidence] = useState(
    Math.round((currentSettings?.vision_confidence_threshold || 0.20) * 100)
  )
  const [inAppNotifications, setInAppNotifications] = useState(
    currentSettings?.in_app_notifications !== undefined ? currentSettings.in_app_notifications : true
  )

  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)

  // Connection test state
  const [isTestingApi, setIsTestingApi] = useState(false)
  const [apiStatus, setApiStatus] = useState(null)

  useEffect(() => {
    if (currentSettings) {
      if (currentSettings.units) setUnits(currentSettings.units)
      if (currentSettings.default_diet) setDefaultDiet(currentSettings.default_diet)
      if (currentSettings.default_cuisine) setDefaultCuisine(currentSettings.default_cuisine)
      if (currentSettings.default_cooking_time) setDefaultCookingTime(currentSettings.default_cooking_time)
      if (currentSettings.vision_confidence_threshold !== undefined) {
        setVisionConfidence(Math.round(currentSettings.vision_confidence_threshold * 100))
      }
      if (currentSettings.in_app_notifications !== undefined) {
        setInAppNotifications(currentSettings.in_app_notifications)
      }
    }
  }, [currentSettings])

  const handleTestConnection = async () => {
    setIsTestingApi(true)
    setApiStatus(null)
    const start = performance.now()
    try {
      const res = await fetch(`${apiBaseUrl}/health`)
      const duration = Math.round(performance.now() - start)
      if (res.ok) {
        const data = await res.json()
        setApiStatus({
          ok: true,
          message: `Connected (${duration}ms) — Model: ${data.model_id || 'Active'}`,
        })
      } else {
        setApiStatus({ ok: false, message: `Server responded with HTTP ${res.status}` })
      }
    } catch (err) {
      setApiStatus({ ok: false, message: `Connection failed: ${err.message}` })
    } finally {
      setIsTestingApi(false)
    }
  }

  const handleResetDefaults = () => {
    setUnits('metric')
    setDefaultDiet('balanced')
    setDefaultCuisine('Any')
    setDefaultCookingTime(30)
    setVisionConfidence(20)
    setInAppNotifications(true)
    setSaveSuccess(false)
    setErrorMessage(null)
  }

  const handleSave = async (e) => {
    e?.preventDefault()
    setSaveSuccess(false)
    setErrorMessage(null)

    const updatedSettings = {
      units,
      default_diet: defaultDiet,
      default_cuisine: defaultCuisine,
      default_cooking_time: Number(defaultCookingTime),
      vision_confidence_threshold: Number(visionConfidence) / 100,
      in_app_notifications: inAppNotifications,
    }

    setIsSaving(true)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/user/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedSettings),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : 'Failed to save settings.')
      }

      localStorage.setItem('foodverse_settings', JSON.stringify(updatedSettings))

      if (onSettingsUpdated) {
        onSettingsUpdated(updatedSettings)
      }

      setSaveSuccess(true)

      if (onNotification) {
        onNotification({
          id: `settings-${Date.now()}`,
          title: 'Settings Updated',
          message: `Preferences saved: ${units} units, ${defaultDiet} diet.`,
          type: 'success',
          module: 'settings',
        })
      }
    } catch (err) {
      // Still persist locally
      localStorage.setItem('foodverse_settings', JSON.stringify(updatedSettings))
      if (onSettingsUpdated) {
        onSettingsUpdated(updatedSettings)
      }
      setSaveSuccess(true)
      setErrorMessage(`Saved locally. Backend notice: ${err.message}`)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="module-view">
      {/* Header Banner */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Preferences & System Control</span>
          </div>
          <h1 className="welcome-title">Application Settings</h1>
          <p className="welcome-description">
            Customize measurement units, default dietary rules, cooking defaults, computer vision thresholds, and backend connectivity across all Food Verse modules.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-purple">
              <Scale size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">{units === 'metric' ? 'Metric' : 'Imperial'}</span>
              <span className="metric-label">Measurement Unit</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-orange">
              <Sliders size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">{visionConfidence}%</span>
              <span className="metric-label">Vision Sensitivity</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Settings Form */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Global User & Studio Configuration</h2>
            <p className="section-subtitle">
              Adjust settings below. Changes persist across sessions and propagate to all interactive modules.
            </p>
          </div>
          <span className="card-badge badge-blue">Active Configuration</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          <form onSubmit={handleSave}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Measurement Units */}
              <div style={{ paddingBottom: '20px', borderBottom: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                  Measurement System
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '10px' }}>
                  Used for biometric height, weight, and ingredient metrics across the Meal Planner and Cooking Assistant.
                </p>
                <div style={{ display: 'flex', gap: '14px' }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 16px',
                      borderRadius: 'var(--radius-sm)',
                      border: units === 'metric' ? '2px solid var(--color-primary-600)' : '1px solid rgba(22, 62, 48, 0.15)',
                      background: units === 'metric' ? 'var(--color-primary-50)' : '#ffffff',
                      cursor: 'pointer',
                      fontSize: '0.86rem',
                      fontWeight: 600,
                    }}
                  >
                    <input
                      type="radio"
                      name="units"
                      value="metric"
                      checked={units === 'metric'}
                      onChange={() => setUnits('metric')}
                    />
                    <span>Metric (kg, cm, °C)</span>
                  </label>

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 16px',
                      borderRadius: 'var(--radius-sm)',
                      border: units === 'imperial' ? '2px solid var(--color-primary-600)' : '1px solid rgba(22, 62, 48, 0.15)',
                      background: units === 'imperial' ? 'var(--color-primary-50)' : '#ffffff',
                      cursor: 'pointer',
                      fontSize: '0.86rem',
                      fontWeight: 600,
                    }}
                  >
                    <input
                      type="radio"
                      name="units"
                      value="imperial"
                      checked={units === 'imperial'}
                      onChange={() => setUnits('imperial')}
                    />
                    <span>Imperial (lbs, in, °F)</span>
                  </label>
                </div>
              </div>

              {/* Default Dietary & Cuisine Preferences */}
              <div style={{ paddingBottom: '20px', borderBottom: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                  Default Culinary Assumptions
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                  Pre-fills selectors in Meal Planner and Cooking Assistant for faster workflows.
                </p>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '14px',
                  }}
                >
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                      Default Diet Mode
                    </label>
                    <select
                      value={defaultDiet}
                      onChange={(e) => setDefaultDiet(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '9px 12px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid rgba(22, 62, 48, 0.15)',
                        background: '#ffffff',
                        fontSize: '0.85rem',
                      }}
                    >
                      <option value="balanced">Balanced Macro</option>
                      <option value="vegetarian">Vegetarian</option>
                      <option value="vegan">100% Plant-Based Vegan</option>
                      <option value="keto">Keto / Low-Carb</option>
                      <option value="mediterranean">Mediterranean</option>
                      <option value="high_protein">High Protein Athletic</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                      Default Cuisine Inspiration
                    </label>
                    <select
                      value={defaultCuisine}
                      onChange={(e) => setDefaultCuisine(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '9px 12px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid rgba(22, 62, 48, 0.15)',
                        background: '#ffffff',
                        fontSize: '0.85rem',
                      }}
                    >
                      <option value="Any">Chef's Choice (Best Fit)</option>
                      <option value="Italian">Italian Bistro</option>
                      <option value="Indian">Indian Spiced</option>
                      <option value="Mediterranean">Mediterranean Fresh</option>
                      <option value="Mexican">Mexican Fiesta</option>
                      <option value="Asian">Asian Stir-Fry</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                      Default Max Cooking Time ({defaultCookingTime} mins)
                    </label>
                    <input
                      type="range"
                      min={15}
                      max={90}
                      step={5}
                      value={defaultCookingTime}
                      onChange={(e) => setDefaultCookingTime(Number(e.target.value))}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>
                </div>
              </div>

              {/* Vision Sensitivity Slider */}
              <div style={{ paddingBottom: '20px', borderBottom: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '2px' }}>
                      Vision Detection Sensitivity
                    </label>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                      Minimum confidence score required for food and produce recognition (Current: {visionConfidence}%).
                    </p>
                  </div>
                  <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-primary-700)' }}>
                    {visionConfidence}%
                  </span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={60}
                  step={5}
                  value={visionConfidence}
                  onChange={(e) => setVisionConfidence(Number(e.target.value))}
                  style={{ width: '100%', marginTop: '10px' }}
                />
              </div>

              {/* Notification Preferences */}
              <div style={{ paddingBottom: '20px', borderBottom: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '2px' }}>
                      In-App Activity Notifications
                    </label>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                      Record meal generation, recipe synthesis, and scan events in the top notification bell drawer.
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                    <input
                      type="checkbox"
                      checked={inAppNotifications}
                      onChange={(e) => setInAppNotifications(e.target.checked)}
                      style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary-600)' }}
                    />
                    <span style={{ fontSize: '0.84rem', fontWeight: 600 }}>Enabled</span>
                  </label>
                </div>
              </div>

              {/* Theme Indicator (Design Aesthetic) */}
              <div style={{ paddingBottom: '20px', borderBottom: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                  Visual Theme
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                  Application appearance is configured to the signature high-contrast culinary theme.
                </p>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-primary-50)',
                    border: '1px solid var(--color-primary-100)',
                    color: 'var(--color-primary-800)',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  <Palette size={16} color="var(--color-primary-600)" />
                  <span>Signature Green & Warm Cream (Active Default)</span>
                </div>
              </div>

              {/* Backend API Connection & Diagnostics */}
              <div>
                <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '4px' }}>
                  Backend API Service
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                  Active API Gateway endpoint: <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>{apiBaseUrl}</code>
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={handleTestConnection}
                    disabled={isTestingApi}
                    className="card-action-btn"
                    style={{
                      display: 'inline-flex',
                      width: 'auto',
                      padding: '8px 16px',
                      fontSize: '0.84rem',
                      background: '#ffffff',
                      color: 'var(--color-primary-800)',
                      border: '1px solid rgba(22, 62, 48, 0.2)',
                    }}
                  >
                    {isTestingApi ? (
                      <>
                        <Loader2 size={15} className="animate-spin" />
                        <span>Pinging /health...</span>
                      </>
                    ) : (
                      <>
                        <Server size={15} />
                        <span>Test API Connection</span>
                      </>
                    )}
                  </button>

                  {apiStatus && (
                    <span
                      style={{
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        color: apiStatus.ok ? '#059669' : '#dc2626',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      {apiStatus.ok ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                      {apiStatus.message}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: 'var(--radius-sm)',
                  color: '#991b1b',
                  fontSize: '0.84rem',
                  marginTop: '20px',
                }}
              >
                <AlertCircle size={16} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Message */}
            {saveSuccess && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  borderRadius: 'var(--radius-sm)',
                  color: '#166534',
                  fontSize: '0.84rem',
                  marginTop: '20px',
                }}
              >
                <CheckCircle2 size={16} />
                <span>Application settings saved successfully.</span>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginTop: '24px' }}>
              <button
                type="submit"
                disabled={isSaving}
                className="card-action-btn"
                style={{
                  display: 'inline-flex',
                  width: 'auto',
                  padding: '10px 24px',
                  fontSize: '0.92rem',
                  opacity: isSaving ? 0.7 : 1,
                }}
              >
                {isSaving ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Saving Settings...</span>
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    <span>Save Preferences</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleResetDefaults}
                className="card-action-btn"
                style={{
                  display: 'inline-flex',
                  width: 'auto',
                  padding: '10px 18px',
                  fontSize: '0.88rem',
                  background: '#f3f4f6',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                }}
              >
                <RotateCcw size={16} />
                <span>Reset to Defaults</span>
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}
