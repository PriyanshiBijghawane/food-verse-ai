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
      description: 'Ingests food imagery, performs spatial quadrant cropping for multi-dish thali/platter parsing, and returns top-5 classifications with estimated macronutrients and calories.',
      input: 'multipart/form-data with file: Image (PNG, JPG, WEBP)',
      output: 'JSON: { predicted_label, confidence, top_5, detected_items, nutrition: { calories, protein_g, carbs_g, fat_g } }'
    },
    {
      method: 'POST',
      path: '/api/v1/food/freshness',
      module: 'Freshness Detection',
      icon: Leaf,
      description: 'Evaluates multi-spectral color distributions in HSV and RGB spaces, measures browning and surface rot variance, detects mold pigmentation, and estimates shelf-life.',
      input: 'multipart/form-data with file: Image, storage_condition: ambient | refrigerated | frozen',
      output: 'JSON: { freshness_score (0-100), classification: fresh | decaying | spoiled, surface_metrics, preservation_advice }'
    },
    {
      method: 'POST',
      path: '/api/v1/hygiene/audit',
      module: 'Restaurant Hygiene',
      icon: Store,
      description: 'Runs automated sanitation auditing over kitchen prep stations, checking clutter, surface spills, protocol hazards, and generating itemized violation scorecards.',
      input: 'multipart/form-data with file: Image or Video (MP4, MOV)',
      output: 'JSON: { overall_hygiene_score, compliance_grade (A/B/C/F), violations: [ { category, severity, description } ], audit_report_id }'
    },
    {
      method: 'POST',
      path: '/api/v1/cooking/assistant',
      module: 'Smart Cooking Assistant',
      icon: ChefHat,
      description: 'Accepts ingredient text or pantry/fridge photos, detects items via vision, validates inputs, and synthesizes step-by-step instructions with timers and nutrient estimates.',
      input: 'multipart/form-data: ingredients, dietary_preference, cuisine, max_time_minutes, skill_level, optional image',
      output: 'JSON: { dish_name, summary, prep_time, cook_time, total_time, ingredients, instructions: [ { step, title, instruction, timer_minutes, chef_tip } ], nutrition_estimates }'
    },
    {
      method: 'POST',
      path: '/api/v1/meal-plan/generate',
      module: 'Personalized Meal Planner',
      icon: CalendarDays,
      description: 'Computes physiological BMR and TDEE using the Mifflin-St Jeor equation, enforces strict allergen exclusions, and constructs a 5-meal daily plan and 7-day schedule.',
      input: 'JSON: { age, gender, height_cm, weight_kg, activity_level, primary_goal, diet_type, allergies: [], food_restrictions: [] }',
      output: 'JSON: { biometric_calculations, daily_nutrition_totals, meals: [ 5 occasions ], alternative_meals, weekly_overview, hydration_guidance }'
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
