import React, { useState, useEffect } from 'react'
import {
  CalendarDays,
  Sparkles,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Droplet,
  Heart,
  Scale,
  Flame,
  Activity,
  Layers,
  ChevronDown,
  ChevronUp,
  Apple,
  RotateCcw,
  Utensils
} from 'lucide-react'

export default function MealPlannerWorkspace({
  apiBaseUrl = 'http://127.0.0.1:8001',
  userProfile = null,
  userSettings = null,
  onNotification = null
}) {
  const isImperial = userSettings?.units === 'imperial'

  // Biometrics & Goals
  const [age, setAge] = useState(userProfile?.age || 28)
  const [gender, setGender] = useState(userProfile?.gender || 'female')
  const [height, setHeight] = useState(
    isImperial
      ? Math.round((userProfile?.height_cm || 168) / 2.54)
      : Math.round(userProfile?.height_cm || 168)
  )
  const [weight, setWeight] = useState(
    isImperial
      ? Math.round((userProfile?.weight_kg || 65) * 2.20462)
      : Math.round(userProfile?.weight_kg || 65)
  )
  const [activityLevel, setActivityLevel] = useState(userProfile?.activity_level || 'moderately_active')
  const [primaryGoal, setPrimaryGoal] = useState(userProfile?.primary_goal || 'weight_loss')
  const [dietType, setDietType] = useState(
    userProfile?.diet_type || userSettings?.default_diet || 'balanced'
  )

  // Allergies & Preferences
  const [allergiesText, setAllergiesText] = useState(
    userProfile?.allergies?.join(', ') || ''
  )
  const [foodRestrictionsText, setFoodRestrictionsText] = useState(
    userProfile?.food_restrictions?.join(', ') || ''
  )
  const [cuisinePreferences, setCuisinePreferences] = useState(
    userProfile?.cuisine_preferences || ['Mediterranean', 'Balanced']
  )

  // API State
  const [isGenerating, setIsGenerating] = useState(false)
  const [planResult, setPlanResult] = useState(null)
  const [isOutdated, setIsOutdated] = useState(false)
  const [apiError, setApiError] = useState(null)
  const [validationError, setValidationError] = useState(null)

  // Update when userProfile or units change
  useEffect(() => {
    if (userProfile) {
      if (userProfile.age) setAge(userProfile.age)
      if (userProfile.gender) setGender(userProfile.gender)
      if (userProfile.height_cm) {
        setHeight(isImperial ? Math.round(userProfile.height_cm / 2.54) : Math.round(userProfile.height_cm))
      }
      if (userProfile.weight_kg) {
        setWeight(isImperial ? Math.round(userProfile.weight_kg * 2.20462) : Math.round(userProfile.weight_kg))
      }
      if (userProfile.activity_level) setActivityLevel(userProfile.activity_level)
      if (userProfile.primary_goal) setPrimaryGoal(userProfile.primary_goal)
      if (userProfile.diet_type) setDietType(userProfile.diet_type)
      if (userProfile.allergies) setAllergiesText(userProfile.allergies.join(', '))
      if (userProfile.food_restrictions) setFoodRestrictionsText(userProfile.food_restrictions.join(', '))
    }
  }, [userProfile, isImperial])

  // Invalidate previous plan when inputs change
  const handleInputChange = (setter) => (e) => {
    setter(e.target.value)
    if (planResult) {
      setIsOutdated(true)
    }
  }

  const handleReset = () => {
    setPlanResult(null)
    setIsOutdated(false)
    setValidationError(null)
    setApiError(null)
  }

  const handleGenerate = async (e) => {
    e?.preventDefault()
    setValidationError(null)
    setApiError(null)

    // Compute metric height and weight for backend
    const numAge = Number(age)
    const effectiveHeightCm = isImperial ? Math.round(Number(height) * 2.54) : Number(height)
    const effectiveWeightKg = isImperial ? Math.round(Number(weight) * 0.453592 * 10) / 10 : Number(weight)

    if (isNaN(numAge) || numAge < 1 || numAge > 120) {
      setValidationError('Please enter a valid age between 1 and 120.')
      return
    }

    if (isNaN(effectiveHeightCm) || effectiveHeightCm < 50 || effectiveHeightCm > 250) {
      setValidationError(
        `Height must be between 50 and 250 cm${isImperial ? ' (approx 20 - 98 inches)' : ''}.`
      )
      return
    }

    if (isNaN(effectiveWeightKg) || effectiveWeightKg < 20 || effectiveWeightKg > 300) {
      setValidationError(
        `Weight must be between 20 and 300 kg${isImperial ? ' (approx 44 - 660 lbs)' : ''}.`
      )
      return
    }

    // Parse allergies & restrictions
    const allergies = allergiesText
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)

    const foodRestrictions = foodRestrictionsText
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)

    const payload = {
      age: numAge,
      gender,
      height_cm: effectiveHeightCm,
      weight_kg: effectiveWeightKg,
      activity_level: activityLevel,
      primary_goal: primaryGoal,
      diet_type: dietType,
      cuisine_preferences: cuisinePreferences,
      allergies,
      food_restrictions: foodRestrictions,
      days: 7,
      meals_per_day: 5,
      servings: 1,
      medical_conditions: [],
    }

    setIsGenerating(true)
    setPlanResult(null)
    setIsOutdated(false)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/meal-plan/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : 'Failed to generate meal plan.')
      }

      setPlanResult(data)
      setIsOutdated(false)

      if (onNotification) {
        onNotification({
          id: `plan-${Date.now()}`,
          title: 'Meal Plan Synthesized',
          message: `Generated 5-meal daily plan targeting ${data.biometric_calculations?.target_calories_kcal || 'recommended'} kcal.`,
          type: 'success',
          module: 'meal-planner',
        })
      }
    } catch (err) {
      const errorMsg = err.message || 'Unable to connect to the meal planner service.'
      setApiError(errorMsg)
      if (onNotification) {
        onNotification({
          id: `plan-err-${Date.now()}`,
          title: 'Meal Plan Generation Failed',
          message: errorMsg,
          type: 'error',
          module: 'meal-planner',
        })
      }
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="module-view">
      {/* Header Banner */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Biometric Dietary Optimization</span>
          </div>
          <h1 className="welcome-title">Personalized Meal Planner</h1>
          <p className="welcome-description">
            Scientifically computed caloric distribution, macronutrient targets, 5-meal daily plans, and 7-day schedule forecasts tailored to your exact metabolic requirements.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-purple">
              <CalendarDays size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {planResult
                  ? `${planResult.daily_nutrition_totals?.total_calories_kcal} kcal`
                  : '—'}
              </span>
              <span className="metric-label">
                {planResult ? 'Target Energy' : 'Awaiting Synthesis'}
              </span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <Activity size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {planResult ? `${planResult.meals?.length || 5} Meals` : '5 Meals / Day'}
              </span>
              <span className="metric-label">Plan Cadence</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Section */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Biometric Profile & Dietary Parameters</h2>
            <p className="section-subtitle">
              Set biometric stats, fitness targets, and strict allergen blacklists for precision synthesis.
            </p>
          </div>
          <span className="card-badge badge-purple">Metabolic Engine</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          <form onSubmit={handleGenerate}>
            {/* Biometric Row */}
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
                  onChange={handleInputChange(setAge)}
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
                  onChange={handleInputChange(setGender)}
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
                  onChange={handleInputChange(setHeight)}
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
                  onChange={handleInputChange(setWeight)}
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

            {/* Activity & Goals Row */}
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
                  onChange={handleInputChange(setActivityLevel)}
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
                  onChange={handleInputChange(setPrimaryGoal)}
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
                  onChange={handleInputChange(setDietType)}
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

            {/* Allergies & Restrictions Inputs */}
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
                  Allergies (Comma separated — e.g. peanuts, dairy, gluten, shellfish)
                </label>
                <input
                  type="text"
                  placeholder="e.g. peanuts, tree nuts, shrimp..."
                  value={allergiesText}
                  onChange={handleInputChange(setAllergiesText)}
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
                  placeholder="e.g. cilantro, mushrooms, pork, spicy food..."
                  value={foodRestrictionsText}
                  onChange={handleInputChange(setFoodRestrictionsText)}
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

            {/* Errors */}
            {validationError && (
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
                <span>{validationError}</span>
              </div>
            )}

            {apiError && (
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
                <span>{apiError}</span>
              </div>
            )}

            {/* Submit & Reset Button Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="submit"
                disabled={isGenerating}
                className="card-action-btn"
                style={{
                  display: 'inline-flex',
                  width: 'auto',
                  padding: '10px 24px',
                  fontSize: '0.92rem',
                  opacity: isGenerating ? 0.7 : 1,
                }}
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Computing Metabolic Targets & Schedule...</span>
                  </>
                ) : (
                  <>
                    <CalendarDays size={18} />
                    <span>Synthesize Personalized Meal Plan</span>
                  </>
                )}
              </button>

              {planResult && (
                <button
                  type="button"
                  onClick={handleReset}
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
                  <span>Clear Plan</span>
                </button>
              )}
            </div>
          </form>

          {/* Outdated Parameters Banner */}
          {planResult && isOutdated && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 18px',
                background: '#fffbeb',
                border: '1px solid #fcd34d',
                borderRadius: 'var(--radius-sm)',
                color: '#92400e',
                marginTop: '22px',
                gap: '12px',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertCircle size={18} color="#d97706" />
                <span style={{ fontSize: '0.86rem', fontWeight: 600 }}>
                  Biometric or dietary parameters were modified. This displayed plan reflects previous values.
                </span>
              </div>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="card-action-btn"
                style={{
                  padding: '6px 14px',
                  fontSize: '0.8rem',
                  width: 'auto',
                  background: '#d97706',
                  color: '#ffffff',
                }}
              >
                Regenerate Plan
              </button>
            </div>
          )}

          {/* Generated Plan Presentation */}
          {planResult && (
            <div
              style={{
                background: 'rgba(250, 247, 242, 0.95)',
                border: '1px solid rgba(22, 62, 48, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '28px',
                marginTop: '28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '24px',
                opacity: isOutdated ? 0.85 : 1,
              }}
            >
              <div style={{
                padding: '10px 12px',
                background: '#eff6ff',
                border: '1px solid #bfdbfe',
                borderRadius: '6px',
                color: '#1e3a8a',
                fontSize: '0.78rem',
                lineHeight: 1.45,
              }}>
                This seven-day schedule is assembled by the backend's deterministic nutrition and meal-planning rules; it is not generated by a generative AI model. Nutrition values are estimates.
              </div>

              {/* Biometrics Summary & Hydration */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                }}
              >
                <div style={{ background: '#ffffff', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                    Metabolic Calculations
                  </span>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-primary-900)', marginTop: '4px' }}>
                    {planResult.biometric_calculations?.target_calories_kcal} kcal / day
                  </div>
                  <span style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)' }}>
                    BMR: {planResult.biometric_calculations?.bmr_kcal} kcal | TDEE: {planResult.biometric_calculations?.tdee_kcal} kcal
                  </span>
                </div>

                <div style={{ background: '#ffffff', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                    Target Macronutrient Split
                  </span>
                  <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--color-primary-900)', marginTop: '6px' }}>
                    P: {planResult.daily_nutrition_totals?.total_protein_g}g | C: {planResult.daily_nutrition_totals?.total_carbs_g}g | F: {planResult.daily_nutrition_totals?.total_fat_g}g
                  </div>
                  <span style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)' }}>
                    Fiber: {planResult.daily_nutrition_totals?.total_fiber_g}g | Total: {planResult.daily_nutrition_totals?.total_calories_kcal} kcal
                  </span>
                </div>

                <div style={{ background: '#ffffff', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Droplet size={14} color="#0284c7" />
                    Hydration Target
                  </span>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0369a1', marginTop: '4px' }}>
                    {planResult.hydration_guidance?.recommended_liters_per_day} Liters
                  </div>
                  <span style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)' }}>
                    ≈ {planResult.hydration_guidance?.recommended_glasses} glasses / day
                  </span>
                </div>
              </div>

              {/* 5 Daily Eating Occasions */}
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-primary-900)', marginBottom: '14px' }}>
                  Daily 5-Meal Schedule
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {planResult.meals?.map((meal, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: '#ffffff',
                        padding: '16px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid rgba(22, 62, 48, 0.08)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        flexWrap: 'wrap',
                        gap: '12px',
                      }}
                    >
                      <div style={{ flex: 1, minWidth: '220px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                          <span
                            className="card-badge badge-purple"
                            style={{ fontSize: '0.68rem', padding: '2px 8px' }}
                          >
                            {meal.meal_type}
                          </span>
                          {meal.preparation_time && (
                            <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                              Prep: {meal.preparation_time}
                            </span>
                          )}
                          {meal.portion_size && (
                            <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                              Portion: {meal.portion_size}
                            </span>
                          )}
                        </div>
                        <h5 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-primary-900)' }}>
                          {meal.dish_name}
                        </h5>
                        {meal.description && (
                          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                            {meal.description}
                          </p>
                        )}
                        <div style={{ marginTop: '8px' }}>
                          <strong style={{ fontSize: '0.78rem', color: 'var(--color-primary-900)' }}>Ingredients:</strong>{' '}
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                            {Array.isArray(meal.ingredients) ? meal.ingredients.join(', ') : meal.ingredients}
                          </span>
                        </div>
                        {meal.explanation && (
                          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginTop: '6px' }}>
                            {meal.explanation}
                          </p>
                        )}
                      </div>

                      <div style={{ textAlign: 'right', minWidth: '120px' }}>
                        <strong style={{ fontSize: '1.1rem', color: 'var(--color-primary-900)', display: 'block' }}>
                          {meal.calories} kcal
                        </strong>
                        <span style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)' }}>
                          P: {meal.macronutrients?.protein_g ?? 0}g | C: {meal.macronutrients?.carbs_g ?? 0}g | F: {meal.macronutrients?.fat_g ?? 0}g
                        </span>
                        {meal.macronutrients?.fiber_g !== undefined && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>
                            Fiber: {meal.macronutrients.fiber_g}g
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Safe Alternative Meals */}
              {planResult.alternative_meals && planResult.alternative_meals.length > 0 && (
                <div style={{ background: '#ffffff', padding: '18px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '10px' }}>
                    Allergen-Safe Dish Alternatives
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                    {planResult.alternative_meals.map((alt, idx) => (
                      <div key={idx} style={{ padding: '12px', background: 'rgba(240, 248, 245, 0.6)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>
                          Replaces {alt.replaces_meal}
                        </span>
                        <strong style={{ display: 'block', fontSize: '0.88rem', color: 'var(--color-primary-900)', marginTop: '2px' }}>
                          {alt.dish_name}
                        </strong>
                        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                          {alt.description}
                        </p>
                        <span style={{ fontSize: '0.76rem', color: 'var(--color-primary-800)', fontWeight: 600, display: 'block', marginTop: '4px' }}>
                          {alt.calories} kcal | P: {alt.macronutrients?.protein_g ?? 0}g | C: {alt.macronutrients?.carbs_g ?? 0}g | F: {alt.macronutrients?.fat_g ?? 0}g
                        </span>
                        {alt.allergen_safe_notes && (
                          <span style={{ fontSize: '0.72rem', color: '#059669', display: 'block', marginTop: '2px' }}>
                            ✓ {alt.allergen_safe_notes}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 7-Day Weekly Schedule Forecast */}
              {planResult.weekly_overview && planResult.weekly_overview.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '10px' }}>
                    7-Day Schedule Overview
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
                    {planResult.weekly_overview.map((day, idx) => (
                      <div key={idx} style={{ background: '#ffffff', padding: '12px 10px', borderRadius: '6px', border: '1px solid rgba(22, 62, 48, 0.08)', textAlign: 'center' }}>
                        <strong style={{ fontSize: '0.84rem', color: 'var(--color-primary-900)', display: 'block' }}>
                          {day.day}
                        </strong>
                        <span style={{ fontSize: '0.76rem', color: '#059669', fontWeight: 700 }}>
                          {day.target_calories} kcal
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--color-primary-800)', display: 'block', marginTop: '4px', fontWeight: 600 }}>
                          {day.focus}
                        </span>
                        {day.meals_preview && (
                          <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', display: 'block', marginTop: '2px' }}>
                            {day.meals_preview}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Adherence & Disclaimer */}
              <div
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.45,
                  background: 'rgba(255, 255, 255, 0.85)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  borderLeft: '3px solid var(--color-accent-amber)',
                }}
              >
                <strong>Nutritional Disclaimer:</strong> Daily caloric targets and macronutrient values are calculated approximations using the Mifflin-St Jeor equation. These do not constitute medical advice. Consult a licensed dietitian or physician for clinical dietary treatment.
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
