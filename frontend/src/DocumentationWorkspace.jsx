import React from 'react'
import {
  HelpCircle,
  Sparkles,
  Server,
  ScanLine,
  Leaf,
  Store,
  ChefHat,
  CalendarDays,
  CheckCircle2,
  Code
} from 'lucide-react'

export default function DocumentationWorkspace() {
  const apis = [
    {
      method: 'POST',
      path: '/api/v1/food/recognize',
      module: 'Food Recognition',
      icon: ScanLine,
      description: 'Runs the Food-101 dish classifier and returns its ranked class candidates. Nutrition is a separate reference estimate; the classifier does not detect ingredients or estimate portions.',
      input: 'multipart/form-data with file: image (PNG, JPG, WEBP; maximum 25 MB)',
      output: 'JSON: { predicted_label, candidate_label, confidence (uncalibrated model score), confidence_tier (provisional threshold band), is_uncertain, confidence_note, top_5, model_id, nutrition }'
    },
    {
      method: 'POST',
      path: '/api/v1/food/freshness',
      module: 'Freshness Detection',
      icon: Leaf,
      description: 'Evaluates visible color and texture cues and returns conservative freshness guidance. The response discloses whether the active classifier or visual heuristics produced the result.',
      input: 'multipart/form-data with file: image; optional food_hint query parameter',
      output: 'JSON: { detected_food, food_category, confidence, analysis_mode, freshness_score, freshness_label, safety_status, extracted_features, pipeline_disclosure, limitations }'
    },
    {
      method: 'POST',
      path: '/api/v1/hygiene/audit',
      module: 'Restaurant Hygiene',
      icon: Store,
      description: 'Audits observable conditions in a still image or sampled video frames. Depending on available models and configuration, results may use object detection, a vision API, or local visual heuristics; the result includes the active engine and limitations.',
      input: 'multipart/form-data with file: image or video (bounded size, duration, and frame sampling)',
      output: 'JSON: { audit_id, compliance_score, audit_status, violations, observations, inspection_engine, analysis_mode, sampling_metadata, limitations, disclaimer }'
    },
    {
      method: 'POST',
      path: '/api/v1/cooking/assistant',
      module: 'Smart Cooking Assistant',
      icon: ChefHat,
      description: 'Builds a structured recipe from ingredients entered as text. Food-101 is a prepared-dish classifier, not an ingredient detector, so an image alone cannot provide recipe ingredients.',
      input: 'multipart/form-data: ingredients (required), dietary_preference, cuisine, max_time_minutes, skill_level; image uploads are not used to identify ingredients',
      output: 'JSON: { dish_name, ingredients, instructions, nutrition_estimates, engine_mode, generation_engine, generation_disclosure, food_safety_guidance }'
    },
    {
      method: 'POST',
      path: '/api/v1/meal-plan/generate',
      module: 'Personalized Meal Planner',
      icon: CalendarDays,
      description: 'Computes profile-based nutrition targets and builds meal schedules using deterministic planning rules and a food catalog; it is not generative AI.',
      input: 'JSON: { age, gender, height_cm, weight_kg, activity_level, primary_goal, diet_type, allergies, food_restrictions, days, meals_per_day, servings }',
      output: 'JSON: { biometric_calculations, daily_nutrition_totals, meals, alternative_meals, weekly_overview, daily_plans, consolidated_shopping_list, disclaimer }'
    },
    {
      method: 'GET/POST',
      path: '/api/v1/user/profile',
      module: 'User Profile & Preferences',
      icon: Server,
      description: 'Retrieves and updates saved user identity, biometric traits, and dietary constraints with persistent local storage.',
      input: 'JSON: UserProfile object',
      output: 'JSON: { status: "success", profile }'
    },
    {
      method: 'GET/POST',
      path: '/api/v1/user/settings',
      module: 'Application Settings',
      icon: Server,
      description: 'Manages user application preferences including measurement units (metric/imperial), default cuisine, and confidence thresholds.',
      input: 'JSON: AppSettings object',
      output: 'JSON: { status: "success", settings }'
    }
  ]

  return (
    <div className="module-view">
      {/* Header Banner */}
      <section className="welcome-section">
        <div className="welcome-content">
          <div className="welcome-tag">
            <Sparkles size={14} />
            <span>Developer Reference & Architecture</span>
          </div>
          <h1 className="welcome-title">System Documentation</h1>
          <p className="welcome-description">
            Complete technical specification of Food Verse AI services, computer vision pipelines, metabolic calculation algorithms, and RESTful endpoint interfaces.
          </p>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-box bg-purple">
              <Code size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">7 Endpoints</span>
              <span className="metric-label">Active API Surface</span>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-box bg-emerald">
              <Server size={20} />
            </div>
            <div className="metric-data">
              <span className="metric-value">FastAPI + ViT</span>
              <span className="metric-label">Core Engine Stack</span>
            </div>
          </div>
        </div>
      </section>

      {/* API Reference Cards */}
      <section className="modules-section">
        <div className="modules-header">
          <div>
            <h2 className="section-title">RESTful API Endpoints</h2>
            <p className="section-subtitle">
              Interactive endpoints available via FastAPI backend gateway at <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>/api/v1</code>.
            </p>
          </div>
          <span className="card-badge badge-blue">OpenAPI 3.1</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {apis.map((api, idx) => {
            const Icon = api.icon
            return (
              <div key={idx} className="module-card" style={{ padding: '22px 26px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'var(--color-primary-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary-700)' }}>
                      <Icon size={18} />
                    </div>
                    <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--color-primary-900)' }}>
                      {api.module}
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      padding: '4px 10px',
                      borderRadius: '4px',
                      background: api.method.includes('POST') ? '#ecfdf5' : '#eff6ff',
                      color: api.method.includes('POST') ? '#047857' : '#1d4ed8',
                      border: '1px solid rgba(0, 0, 0, 0.08)',
                    }}
                  >
                    {api.method} {api.path}
                  </span>
                </div>

                <p style={{ fontSize: '0.84rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '12px' }}>
                  {api.description}
                </p>

                <div style={{ background: 'rgba(244, 237, 227, 0.4)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div>
                    <strong style={{ color: 'var(--color-primary-900)' }}>Payload:</strong>{' '}
                    <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>{api.input}</span>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--color-primary-900)' }}>Response:</strong>{' '}
                    <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>{api.output}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
