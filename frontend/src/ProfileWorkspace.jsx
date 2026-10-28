import React, { useState, useEffect } from 'react'
import {
  User,
  Mail,
  Scale,
  Sparkles,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Shield,
  Activity,
  HeartPulse
} from 'lucide-react'

export default function ProfileWorkspace({
  apiBaseUrl = 'http://127.0.0.1:8001',
  currentProfile = null,
  userSettings = null,
  onProfileUpdated = null,
  onNotification = null
}) {
  const isImperial = userSettings?.units === 'imperial'

  const [name, setName] = useState(currentProfile?.name || '')
  const [email, setEmail] = useState(currentProfile?.email || '')
  const [age, setAge] = useState(currentProfile?.age || 28)
  const [gender, setGender] = useState(currentProfile?.gender || 'female')
  const [height, setHeight] = useState(
    isImperial
      ? Math.round((currentProfile?.height_cm || 168) / 2.54)
      : Math.round(currentProfile?.height_cm || 168)
  )
  const [weight, setWeight] = useState(
    isImperial
      ? Math.round((currentProfile?.weight_kg || 65) * 2.20462)
      : Math.round(currentProfile?.weight_kg || 65)
  )
  const [activityLevel, setActivityLevel] = useState(currentProfile?.activity_level || 'moderately_active')
  const [primaryGoal, setPrimaryGoal] = useState(currentProfile?.primary_goal || 'weight_loss')
  const [dietType, setDietType] = useState(currentProfile?.diet_type || 'balanced')
  const [allergiesText, setAllergiesText] = useState(currentProfile?.allergies?.join(', ') || '')
  const [foodRestrictionsText, setFoodRestrictionsText] = useState(currentProfile?.food_restrictions?.join(', ') || '')

  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)

  useEffect(() => {
    if (currentProfile) {
      setName(currentProfile.name || '')
      setEmail(currentProfile.email || '')
      setAge(currentProfile.age || 28)
      setGender(currentProfile.gender || 'female')
      setHeight(
        isImperial
          ? Math.round((currentProfile.height_cm || 168) / 2.54)
          : Math.round(currentProfile.height_cm || 168)
      )
      setWeight(
        isImperial
          ? Math.round((currentProfile.weight_kg || 65) * 2.20462)
          : Math.round(currentProfile.weight_kg || 65)
      )
      setActivityLevel(currentProfile.activity_level || 'moderately_active')
      setPrimaryGoal(currentProfile.primary_goal || 'weight_loss')
      setDietType(currentProfile.diet_type || 'balanced')
      setAllergiesText(currentProfile.allergies?.join(', ') || '')
      setFoodRestrictionsText(currentProfile.food_restrictions?.join(', ') || '')
    }
  }, [currentProfile, isImperial])

  const getInitials = (n) => {
    if (!n || !n.trim()) return 'FV'
    const parts = n.trim().split(' ')
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  const handleResetDefaults = () => {
    setName('Jane Doe')
    setEmail('jane.doe@example.com')
    setAge(28)
    setGender('female')
    setHeight(isImperial ? 66 : 168)
    setWeight(isImperial ? 143 : 65)
    setActivityLevel('moderately_active')
    setPrimaryGoal('weight_loss')
    setDietType('balanced')
    setAllergiesText('')
    setFoodRestrictionsText('')
    setSaveSuccess(false)
    setErrorMessage(null)
  }

  const handleSave = async (e) => {
    e?.preventDefault()
    setSaveSuccess(false)
    setErrorMessage(null)

    const numAge = Number(age)
    const effectiveHeightCm = isImperial ? Math.round(Number(height) * 2.54) : Number(height)
    const effectiveWeightKg = isImperial ? Math.round(Number(weight) * 0.453592 * 10) / 10 : Number(weight)

    if (isNaN(numAge) || numAge < 1 || numAge > 120) {
      setErrorMessage('Age must be a valid number between 1 and 120.')
      return
    }

    if (isNaN(effectiveHeightCm) || effectiveHeightCm < 50 || effectiveHeightCm > 250) {
      setErrorMessage(`Height must be between 50 and 250 cm${isImperial ? ' (20 - 98 inches)' : ''}.`)
      return
    }

    if (isNaN(effectiveWeightKg) || effectiveWeightKg < 20 || effectiveWeightKg > 300) {
      setErrorMessage(`Weight must be between 20 and 300 kg${isImperial ? ' (44 - 660 lbs)' : ''}.`)
      return
    }

    const allergies = allergiesText
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)

    const foodRestrictions = foodRestrictionsText
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)

    const updatedProfile = {
      name: name.trim() || 'Guest User',
      email: email.trim(),
      age: numAge,
      gender,
      height_cm: effectiveHeightCm,
      weight_kg: effectiveWeightKg,
      activity_level: activityLevel,
      primary_goal: primaryGoal,
      diet_type: dietType,
      allergies,
      food_restrictions: foodRestrictions,
      cuisine_preferences: currentProfile?.cuisine_preferences || ['Mediterranean', 'Balanced']
    }

    setIsSaving(true)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/user/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : 'Failed to save profile.')
      }

      // Persist in localStorage as well
      localStorage.setItem('foodverse_profile', JSON.stringify(updatedProfile))

      if (onProfileUpdated) {
        onProfileUpdated(updatedProfile)
      }

      setSaveSuccess(true)

      if (onNotification) {
        onNotification({
          id: `profile-${Date.now()}`,
          title: 'Profile Updated',
          message: `Saved biometric & dietary preferences for ${updatedProfile.name}.`,
          type: 'success',
          module: 'profile'
        })
      }
    } catch (err) {
      // If backend fails, still save to localStorage so changes persist across page refresh
      localStorage.setItem('foodverse_profile', JSON.stringify(updatedProfile))
      if (onProfileUpdated) {
        onProfileUpdated(updatedProfile)
      }
      setSaveSuccess(true)
      setErrorMessage(`Note: Saved locally. Backend notice: ${err.message}`)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="module-view">
      {/* Header Section */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Biometric Identity Hub</span>
          </div>
          <h1 className="welcome-title">User Profile & Biometrics</h1>
          <p className="welcome-description">
            Manage your physiological statistics, daily activity cadence, primary fitness goals, and dietary restrictions to power accurate meal and recipe synthesis.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <User size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">{name.trim() || 'Guest User'}</span>
              <span className="metric-label">Profile Name</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-purple">
              <HeartPulse size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">{dietType.toUpperCase()}</span>
              <span className="metric-label">Active Diet Rule</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Form Section */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Edit Personal & Biometric Attributes</h2>
            <p className="section-subtitle">
              Changes saved here persist locally and automatically feed into your Personalized Meal Planner.
            </p>
          </div>
          <span className="card-badge badge-emerald">Persistent Storage</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          {/* Identity Preview Card */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '18px',
              padding: '16px 20px',
              background: 'rgba(244, 237, 227, 0.45)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid rgba(22, 62, 48, 0.1)',
              marginBottom: '26px',
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary-700), var(--color-primary-500))',
                color: '#ffffff',
                fontWeight: 800,
                fontSize: '1.2rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              {getInitials(name)}
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--color-primary-900)' }}>
                {name.trim() || 'Guest User'}
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                {email.trim() || 'No email specified'} • {age} yrs • {gender}
              </p>
            </div>
          </div>

          <form onSubmit={handleSave}>
            {/* Account Info */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '14px',
                marginBottom: '20px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Email Address (Optional)
                </label>
                <input
                  type="email"
                  placeholder="e.g. jane@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                />
              </div>
            </div>

            {/* Biometrics */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '14px',
                marginBottom: '20px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Age (Years)
                </label>
                <input
                  type="number"
                  min={1}
                  max={120}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Gender
                </label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other / Non-Binary</option>
                  <option value="prefer_not_to_say">Prefer Not To Say</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Height ({isImperial ? 'Inches' : 'cm'})
                </label>
                <input
                  type="number"
                  min={isImperial ? 20 : 50}
                  max={isImperial ? 98 : 250}
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Weight ({isImperial ? 'lbs' : 'kg'})
                </label>
                <input
                  type="number"
                  min={isImperial ? 44 : 20}
                  max={isImperial ? 660 : 300}
                  step={0.5}
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  required
                />
              </div>
            </div>

            {/* Lifestyle & Targets */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '14px',
                marginBottom: '20px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Physical Activity Level
                </label>
                <select
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="sedentary">Sedentary (Desk Job)</option>
                  <option value="lightly_active">Lightly Active (1-3 days/wk)</option>
                  <option value="moderately_active">Moderately Active (3-5 days/wk)</option>
                  <option value="very_active">Very Active (6-7 days/wk)</option>
                  <option value="extra_active">Extra Active (Athletic/Physical)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Primary Biometric Goal
                </label>
                <select
                  value={primaryGoal}
                  onChange={(e) => setPrimaryGoal(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="weight_loss">Weight Loss (Caloric Deficit)</option>
                  <option value="maintenance">Maintenance (Energy Balance)</option>
                  <option value="muscle_gain">Muscle Gain (High Protein Surplus)</option>
                  <option value="energy_boost">Sustained Daily Energy</option>
                  <option value="heart_health">Cardiovascular & Heart Health</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Diet Type
                </label>
                <select
                  value={dietType}
                  onChange={(e) => setDietType(e.target.value)}
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
                  <option value="vegetarian">Vegetarian (Plant + Dairy/Egg)</option>
                  <option value="vegan">100% Plant-Based Vegan</option>
                  <option value="keto">Keto (High Fat, Low Carb)</option>
                  <option value="mediterranean">Mediterranean Heart-Healthy</option>
                  <option value="high_protein">High Protein Athletic</option>
                </select>
              </div>
            </div>

            {/* Allergies & Restrictions */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '14px',
                marginBottom: '24px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Allergies (Comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. peanuts, tree nuts, shellfish..."
                  value={allergiesText}
                  onChange={(e) => setAllergiesText(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Disliked / Excluded Foods (Comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. cilantro, mushrooms, pork..."
                  value={foodRestrictionsText}
                  onChange={(e) => setFoodRestrictionsText(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                />
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
                  marginBottom: '16px',
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
                  marginBottom: '16px',
                }}
              >
                <CheckCircle2 size={16} />
                <span>Profile parameters updated and saved successfully.</span>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
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
                    <span>Saving Profile...</span>
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    <span>Save Profile Changes</span>
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

          {/* Privacy Note */}
          <div
            style={{
              fontSize: '0.74rem',
              color: 'var(--color-text-muted)',
              marginTop: '24px',
              paddingTop: '16px',
              borderTop: '1px solid rgba(22, 62, 48, 0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Shield size={14} color="#059669" />
            <span>
              <strong>Local Privacy Notice:</strong> Profile data is stored in your local browser and local backend instance to personalize meal and recipe calculations. No remote user tracking or external authentication services are involved.
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}
