import React, { useState, useRef, useEffect } from 'react'
import {
  ChefHat,
  Upload,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  Clock,
  Flame,
  Utensils,
  BookOpen,
  Timer,
  Lightbulb,
  Repeat,
  RotateCcw
} from 'lucide-react'

export default function CookingAssistantWorkspace({
  apiBaseUrl = 'http://127.0.0.1:8001',
  userSettings = null,
  onNotification = null
}) {
  const [ingredientsText, setIngredientsText] = useState('')
  const [dietary, setDietary] = useState(userSettings?.default_diet || 'none')
  const [cuisine, setCuisine] = useState(userSettings?.default_cuisine || 'Any')
  const [maxTime, setMaxTime] = useState(userSettings?.default_cooking_time || 30)
  const [skillLevel, setSkillLevel] = useState('Intermediate')

  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [validationError, setValidationError] = useState(null)

  const [isGenerating, setIsGenerating] = useState(false)
  const [recipe, setRecipe] = useState(null)
  const [apiError, setApiError] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (userSettings) {
      if (userSettings.default_diet) setDietary(userSettings.default_diet)
      if (userSettings.default_cuisine) setCuisine(userSettings.default_cuisine)
      if (userSettings.default_cooking_time) setMaxTime(userSettings.default_cooking_time)
    }
  }, [userSettings])

  const handleFile = (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setValidationError('Please upload a valid image file (JPEG, PNG, or WEBP).')
      return
    }
    if (file.size > 15 * 1024 * 1024) {
      setValidationError('Image size exceeds 15 MB limit.')
      return
    }

    setValidationError(null)
    setApiError(null)

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    const url = URL.createObjectURL(file)
    setSelectedFile(file)
    setPreviewUrl(url)
  }

  const handleClearImage = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setSelectedFile(null)
    setPreviewUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleReset = () => {
    handleClearImage()
    setIngredientsText('')
    setRecipe(null)
    setValidationError(null)
    setApiError(null)
  }

  const handleGenerate = async (e) => {
    e?.preventDefault()
    if (!ingredientsText.trim() && !selectedFile) {
      setValidationError('Please enter at least one ingredient or upload a pantry/fridge photo.')
      return
    }

    setValidationError(null)
    setApiError(null)
    setIsGenerating(true)
    setRecipe(null)

    try {
      const formData = new FormData()
      if (ingredientsText.trim()) {
        formData.append('ingredients', ingredientsText.trim())
      }
      formData.append('dietary_preference', dietary)
      formData.append('cuisine', cuisine)
      formData.append('max_time_minutes', maxTime.toString())
      formData.append('skill_level', skillLevel)

      if (selectedFile) {
        formData.append('image', selectedFile)
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/cooking/assistant`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Recipe generation failed.')
      }

      setRecipe(data)

      if (onNotification) {
        const dishTitle = data.dish_name || data.recipe_title || 'Chef Special'
        onNotification({
          id: `recipe-${Date.now()}`,
          title: 'Recipe Synthesized',
          message: `Created "${dishTitle}" (${data.total_time || data.cook_time || maxTime + ' mins'}).`,
          type: 'success',
          module: 'smart-cooking',
        })
      }
    } catch (err) {
      const errorMsg = err.message || 'Unable to connect to the smart cooking assistant service.'
      setApiError(errorMsg)
      if (onNotification) {
        onNotification({
          id: `recipe-err-${Date.now()}`,
          title: 'Recipe Synthesis Failed',
          message: errorMsg,
          type: 'error',
          module: 'smart-cooking',
        })
      }
    } finally {
      setIsGenerating(false)
    }
  }

  // Normalized values for presentation
  const recipeDishName = recipe?.dish_name || recipe?.recipe_title
  const recipeSummary = recipe?.summary || recipe?.description
  const recipePrepTime = recipe?.prep_time || (recipe?.prep_time_minutes ? `${recipe.prep_time_minutes} min` : '10 mins')
  const recipeCookTime = recipe?.cook_time || (recipe?.cook_time_minutes ? `${recipe.cook_time_minutes} min` : '15 mins')
  const recipeTotalTime = recipe?.total_time || (recipe?.total_time_minutes ? `${recipe.total_time_minutes} min` : `${recipeCookTime}`)
  const recipeNutrition = recipe?.nutrition_estimates || recipe?.nutrition_estimate
  const recipeDietaryTags = recipe?.dietary_tags
    ? Array.isArray(recipe.dietary_tags)
      ? recipe.dietary_tags.join(' • ')
      : recipe.dietary_tags
    : recipe?.dietary_compatibility || (dietary === 'none' ? 'Standard' : dietary.toUpperCase())
  const normalizeIngredient = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const enteredIngredients = ingredientsText.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean)
  const recipeInputIngredients = (recipe?.input_ingredients_used || []).map(normalizeIngredient)
  const recipeSubstitutions = recipe?.substitutions || []

  return (
    <div className="module-view">
      {/* Module Header */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Interactive Culinary Intelligence</span>
          </div>
          <h1 className="welcome-title">Smart Cooking Assistant</h1>
          <p className="welcome-description">
            Synthesize chef-crafted recipes with exact measurements, step-by-step guidance, timers, and nutritional breakdowns from pantry items or photos.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-orange">
              <ChefHat size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {isGenerating
                  ? 'Cooking...'
                  : recipe
                  ? recipeTotalTime
                  : '—'}
              </span>
              <span className="metric-label">
                {recipe ? 'Cook Time' : `Target: ${maxTime} min`}
              </span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <Flame size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">
                {recipe
                  ? `${recipeNutrition?.calories || 450} kcal`
                  : dietary === 'none'
                  ? 'Standard'
                  : dietary.toUpperCase()}
              </span>
              <span className="metric-label">Dietary Profile</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Section */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">Recipe Synthesis Studio</h2>
            <p className="section-subtitle">
              Input available ingredients, specify dietary preferences, or upload your pantry photo.
            </p>
          </div>
          <span className="card-badge badge-orange">Culinary Engine</span>
        </div>

        <div className="module-card" style={{ padding: '32px 28px' }}>
          <form onSubmit={handleGenerate}>
            {/* Ingredients Text Input */}
            <div style={{ marginBottom: '20px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  color: 'var(--color-primary-900)',
                  marginBottom: '6px',
                }}
              >
                Available Ingredients (Comma or line-separated)
              </label>
              <textarea
                rows={3}
                placeholder="e.g. eggs, spinach, cherry tomatoes, feta cheese, garlic, olive oil..."
                value={ingredientsText}
                onChange={(e) => setIngredientsText(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(22, 62, 48, 0.15)',
                  background: '#ffffff',
                  fontSize: '0.88rem',
                  color: 'var(--color-text-main)',
                  lineHeight: 1.45,
                  resize: 'vertical',
                }}
              />
            </div>

            {/* Optional Pantry / Fridge Photo Upload */}
            <div style={{ marginBottom: '22px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  color: 'var(--color-primary-900)',
                  marginBottom: '6px',
                }}
              >
                Upload Pantry or Fridge Photo (Optional Reference Only)
              </label>
              <p style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', margin: '0 0 8px', lineHeight: 1.4 }}>
                Food-101 recognizes prepared dishes, not pantry ingredients. This photo is not used to infer ingredients; enter the ingredients in the text field above.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                style={{ display: 'none' }}
              />

              {!selectedFile ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: '1px dashed rgba(22, 62, 48, 0.25)',
                    background: 'rgba(244, 237, 227, 0.3)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '16px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    color: 'var(--color-text-secondary)',
                    fontSize: '0.84rem',
                  }}
                >
                  <Upload size={18} color="var(--color-primary-600)" />
                  <span>Click to attach a reference photo (Food-101 does not detect pantry ingredients)</span>
                </div>
              ) : (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    padding: '10px 14px',
                    background: '#ffffff',
                    border: '1px solid rgba(22, 62, 48, 0.1)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <img
                    src={previewUrl}
                    alt="Pantry Upload"
                    style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px' }}
                  />
                  <div style={{ flex: 1, fontSize: '0.82rem' }}>
                    <strong>{selectedFile.name}</strong> ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </div>
                  <button
                    type="button"
                    onClick={handleClearImage}
                    style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            </div>

            {/* Customization Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '14px',
                marginBottom: '22px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Dietary Preference
                </label>
                <select
                  value={dietary}
                  onChange={(e) => setDietary(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="none">No Restrictions</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="keto">Keto / Low-Carb</option>
                  <option value="gluten-free">Gluten-Free</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Cuisine Inspiration
                </label>
                <select
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
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
                  Max Cooking Time ({maxTime} mins)
                </label>
                <input
                  type="range"
                  min={10}
                  max={90}
                  step={5}
                  value={maxTime}
                  onChange={(e) => setMaxTime(Number(e.target.value))}
                  style={{ width: '100%', marginTop: '6px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-primary-800)', marginBottom: '4px' }}>
                  Chef Skill Level
                </label>
                <select
                  value={skillLevel}
                  onChange={(e) => setSkillLevel(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.15)',
                    background: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="Beginner">Beginner (Quick & Simple)</option>
                  <option value="Intermediate">Intermediate (Balanced)</option>
                  <option value="Advanced">Advanced (Artisan / Gourmet)</option>
                </select>
              </div>
            </div>

            {/* Validation Error */}
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

            {/* API Error */}
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

            {/* Action Buttons */}
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
                    <span>Synthesizing Culinary Plan...</span>
                  </>
                ) : (
                  <>
                    <ChefHat size={18} />
                    <span>Generate Custom Recipe</span>
                  </>
                )}
              </button>

              {(recipe || ingredientsText || selectedFile) && (
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
                  <span>Reset / Clear</span>
                </button>
              )}
            </div>
          </form>

          {/* Structured Recipe Output */}
          {recipe && (
            <div
              style={{
                background: 'rgba(250, 247, 242, 0.95)',
                border: '1px solid rgba(22, 62, 48, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '28px',
                marginTop: '28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
              }}
            >
              {/* Recipe Title & Meta */}
              <div style={{ borderBottom: '1px solid rgba(22, 62, 48, 0.1)', paddingBottom: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <span className="card-badge badge-orange" style={{ fontSize: '0.74rem', marginBottom: '8px', display: 'inline-block' }}>
                      {recipe.cuisine || cuisine} • {recipeDietaryTags}
                    </span>
                    <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-primary-900)', lineHeight: 1.2 }}>
                      {recipeDishName}
                    </h3>
                    {recipeSummary && (
                      <p style={{ fontSize: '0.88rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                        {recipeSummary}
                      </p>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', textAlign: 'center', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                      <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', display: 'block' }}>Prep</span>
                      <strong>{recipePrepTime}</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', textAlign: 'center', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                      <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', display: 'block' }}>Cook</span>
                      <strong>{recipeCookTime}</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', textAlign: 'center', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                      <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', display: 'block' }}>Servings</span>
                      <strong>{recipe.servings || 2}</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Nutrition Estimates Strip */}
              {recipeNutrition && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                    gap: '8px',
                    background: '#ffffff',
                    padding: '14px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(22, 62, 48, 0.08)',
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Calories</span>
                    <strong style={{ fontSize: '1.15rem', color: 'var(--color-primary-900)' }}>{recipeNutrition.calories} kcal</strong>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Protein</span>
                    <strong style={{ fontSize: '1.15rem', color: '#059669' }}>{recipeNutrition.protein_g}g</strong>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Carbohydrates</span>
                    <strong style={{ fontSize: '1.15rem', color: '#d97706' }}>{recipeNutrition.carbs_g}g</strong>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', display: 'block' }}>Total Fat</span>
                    <strong style={{ fontSize: '1.15rem', color: '#dc2626' }}>{recipeNutrition.fat_g}g</strong>
                  </div>
                </div>
              )}

              {/* Ingredients & Substitutions Two-Column */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                <div style={{ background: '#ffffff', padding: '18px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Utensils size={16} color="#059669" />
                    Recipe Ingredients
                  </h4>
                  {enteredIngredients.length > 0 && (
                    <div style={{ marginBottom: '14px', padding: '10px 12px', borderRadius: 'var(--radius-sm)', background: '#f8fafc', fontSize: '0.78rem', lineHeight: 1.5 }}>
                      <strong>Your entered ingredients:</strong>
                      <ul style={{ margin: '6px 0 0', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {enteredIngredients.map((ingredient, idx) => {
                          const normalizedInput = normalizeIngredient(ingredient)
                          const included = recipeInputIngredients.includes(normalizedInput)
                          const substitution = recipeSubstitutions.find(
                            (item) => normalizeIngredient(item.original || '') === normalizedInput
                          )
                          return (
                            <li key={`${ingredient}-${idx}`} style={{ color: included || substitution ? '#166534' : '#92400e' }}>
                              {ingredient}: {included
                                ? 'listed in the recipe'
                                : substitution
                                  ? `substituted with ${substitution.substitute || substitution.replacement}`
                                  : 'not explicitly listed in the recipe'}
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}
                  {recipe.ingredients && recipe.ingredients.length > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {recipe.ingredients.map((item, idx) => (
                        <li key={idx} style={{ fontSize: '0.84rem', color: 'var(--color-text-main)' }}>
                          {typeof item === 'string' ? (
                            <span>{item}</span>
                          ) : (
                            <>
                              <strong>{item.quantity}</strong> {item.name}{' '}
                              {item.notes && <em style={{ color: 'var(--color-text-muted)' }}>({item.notes})</em>}
                              <span style={{
                                display: 'inline-block',
                                marginLeft: '5px',
                                padding: '2px 6px',
                                borderRadius: '999px',
                                background: item.source === 'provided' ? '#dcfce7' : item.source === 'substitute' ? '#fef3c7' : '#e2e8f0',
                                color: item.source === 'provided' ? '#166534' : item.source === 'substitute' ? '#92400e' : '#475569',
                                fontSize: '0.66rem',
                                fontWeight: 700,
                              }}>
                                {item.source === 'provided' ? 'Entered' : item.source === 'substitute' ? 'Substitute' : 'Suggested addition'}
                              </span>
                            </>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>No ingredients listed.</p>
                  )}
                </div>

                <div style={{ background: '#ffffff', padding: '18px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Repeat size={16} color="#d97706" />
                    Smart Ingredient Substitutions
                  </h4>
                  {recipe.substitutions && recipe.substitutions.length > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {recipe.substitutions.map((sub, idx) => {
                        const orig = sub.original || sub.original_ingredient
                        const repl = sub.substitute || sub.replacement
                        const reason = sub.note || sub.reason
                        return (
                          <li key={idx} style={{ fontSize: '0.84rem', color: 'var(--color-text-secondary)' }}>
                            <strong>{orig}:</strong> Substitute with {repl} {reason && `(${reason})`}
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                      All required pantry staples are aligned with current recipe.
                    </p>
                  )}
                </div>
              </div>

              {/* Step-by-Step Instructions with Timers & Chef Tips */}
              <div style={{ background: '#ffffff', padding: '20px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-primary-900)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={17} color="#2563eb" />
                  Step-by-Step Culinary Instructions
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {recipe.instructions?.map((step) => (
                    <div
                      key={step.step}
                      style={{
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(244, 237, 227, 0.35)',
                        borderLeft: '4px solid var(--color-primary-600)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--color-primary-900)' }}>
                          Step {step.step}: {step.title}
                        </span>
                        {step.timer_minutes && (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', color: '#b45309', background: '#fef3c7', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                            <Timer size={13} />
                            {step.timer_minutes} mins
                          </span>
                        )}
                      </div>

                      <p style={{ fontSize: '0.84rem', color: 'var(--color-text-main)', lineHeight: 1.5 }}>
                        {step.instruction}
                      </p>

                      {step.chef_tip && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#047857', marginTop: '6px', background: '#f0fdf4', padding: '6px 10px', borderRadius: '4px' }}>
                          <Lightbulb size={14} />
                          <span><strong>Chef Tip:</strong> {step.chef_tip}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Storage Tips */}
              {(recipe.storage_tips || recipe.storage) && (
                <div style={{ background: '#ffffff', padding: '14px 18px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 62, 48, 0.08)' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary-900)', display: 'block', marginBottom: '2px' }}>
                    Culinary Preservation & Storage Advice:
                  </span>
                  <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                    {recipe.storage_tips || recipe.storage}
                  </p>
                </div>
              )}

              {/* Engine Meta */}
              <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                Recipe generated via <strong>{recipe.generation_engine || 'Dynamic Culinary Engine'}</strong>. {recipe.generation_disclosure} Nutrition figures are estimates computed per serving.
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
