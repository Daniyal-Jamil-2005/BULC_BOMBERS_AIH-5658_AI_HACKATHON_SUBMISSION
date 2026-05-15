import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API_CONFIG from '../config';

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePassword(pw) {
  return pw.length >= 8;
}

const FIELD_LABEL_STYLE = {
  fontSize: 9,
  fontWeight: 700,
  letterSpacing: '0.2em',
  textTransform: 'uppercase',
  color: 'rgba(255,255,255,0.4)',
  display: 'block',
  marginBottom: 8,
};

function Field({ label, type = 'text', value, onChange, error, placeholder, autoComplete }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 24 }}>
      <label style={FIELD_LABEL_STYLE}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          width: '100%',
          background: 'transparent',
          border: `1px solid ${error ? '#ffb4ab' : focused ? '#fff' : 'rgba(255,255,255,0.2)'}`,
          color: '#fff',
          fontSize: 13,
          padding: '14px 16px',
          outline: 'none',
          transition: 'border-color 0.15s',
          fontFamily: 'Inter, sans-serif',
        }}
      />
      {error && (
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
          textTransform: 'uppercase', color: '#ffb4ab', marginTop: 5, display: 'block',
        }}>
          {error}
        </span>
      )}
    </div>
  );
}

export default function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('signup'); // 'signup' | 'login'
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  // Signup fields
  const [signupData, setSignupData] = useState({ name: '', email: '', password: '', confirm: '' });
  const [signupErrors, setSignupErrors] = useState({});

  // Login fields
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [loginErrors, setLoginErrors] = useState({});

  function validateSignup() {
    const errs = {};
    if (!signupData.name.trim()) errs.name = 'Full name is required';
    if (!validateEmail(signupData.email)) errs.email = 'Enter a valid email address';
    if (!validatePassword(signupData.password)) errs.password = 'Password must be at least 8 characters';
    if (signupData.password !== signupData.confirm) errs.confirm = 'Passwords do not match';
    return errs;
  }

  function validateLogin() {
    const errs = {};
    if (!validateEmail(loginData.email)) errs.email = 'Enter a valid email address';
    if (!loginData.password) errs.password = 'Password is required';
    return errs;
  }

  async function handleSignup(e) {
    e.preventDefault();
    const errs = validateSignup();
    setSignupErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_CONFIG.baseURL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: signupData.name,
          email: signupData.email,
          password: signupData.password,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Signup failed');
      // Store user info in localStorage
      localStorage.setItem('inbox_copilot_user_id', data.user_id);
      localStorage.setItem('inbox_copilot_user_email', data.email);
      localStorage.setItem('inbox_copilot_user_name', data.name);
      setSuccess(true);
      setTimeout(() => navigate('/app'), 1200);
    } catch (err) {
      setSignupErrors({ submit: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    const errs = validateLogin();
    setLoginErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_CONFIG.baseURL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: loginData.email,
          password: loginData.password,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      // Store user info in localStorage
      localStorage.setItem('inbox_copilot_user_id', data.user_id);
      localStorage.setItem('inbox_copilot_user_email', data.email);
      localStorage.setItem('inbox_copilot_user_name', data.name);
      setSuccess(true);
      setTimeout(() => navigate('/app'), 1200);
    } catch (err) {
      setLoginErrors({ submit: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#000',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
    }}>

      {/* LEFT PANEL — branding */}
      <div style={{
        borderRight: '1px solid rgba(255,255,255,0.1)',
        padding: '48px 56px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.035,
          backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)',
          backgroundSize: '24px 24px',
          pointerEvents: 'none',
        }} />

        {/* Logo */}
        <div>
          <button onClick={() => navigate('/')} style={{
            background: 'none', border: 'none', color: '#fff', cursor: 'pointer',
            fontWeight: 900, fontSize: 15, letterSpacing: '0.22em', textTransform: 'uppercase',
            padding: 0, display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <span className="ms" style={{ fontSize: 16 }}>arrow_back</span>
            INBOX COPILOT
          </button>
        </div>

        {/* Center content */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.3em',
            color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase',
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32,
          }}>
            <div style={{ width: 8, height: 8, background: '#fff' }} />
            INTELLIGENCE ENGINE
          </div>

          <h2 style={{
            fontWeight: 900, fontSize: 'clamp(48px, 6vw, 88px)',
            lineHeight: 0.9, letterSpacing: '-0.04em', textTransform: 'uppercase',
            marginBottom: 40,
          }}>
            SIGNAL.<br />
            NOT<br />
            <span style={{ color: 'rgba(255,255,255,0.18)' }}>NOISE.</span>
          </h2>

          {/* Feature list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {[
              ['barcode_scanner', 'SCAN HUNDREDS OF EMAILS INSTANTLY'],
              ['analytics', 'SCORE EVERY OPPORTUNITY OUT OF 105'],
              ['delete_sweep', 'ELIMINATE IRRELEVANT NOISE AUTOMATICALLY'],
              ['task_alt', 'GET ACTION CHECKLISTS FOR EACH OPPORTUNITY'],
            ].map(([icon, text], i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 32, height: 32,
                  border: '1px solid rgba(255,255,255,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <span className="ms" style={{ fontSize: 15, color: 'rgba(255,255,255,0.6)' }}>{icon}</span>
                </div>
                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)' }}>
                  {text}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.2)', textTransform: 'uppercase', fontFamily: 'monospace', position: 'relative', zIndex: 1 }}>
          V.01 // OPPORTUNITY INTELLIGENCE
        </div>
      </div>

      {/* RIGHT PANEL — form */}
      <div style={{
        padding: '48px 56px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}>
        <div style={{ maxWidth: 500, width: '100%', margin: '0 auto' }}>

          {/* Mode toggle */}
          <div style={{
            display: 'flex',
            border: '1px solid rgba(255,255,255,0.15)',
            marginBottom: 48,
          }}>
            <button
              onClick={() => { setMode('signup'); setSignupErrors({}); setLoginErrors({}); setSuccess(false); }}
              style={{
                flex: 1, padding: '12px 0',
                background: mode === 'signup' ? '#fff' : 'transparent',
                color: mode === 'signup' ? '#000' : 'rgba(255,255,255,0.4)',
                border: 'none',
                fontWeight: 900, fontSize: 10, letterSpacing: '0.18em',
                textTransform: 'uppercase', cursor: 'pointer',
                transition: 'background 0.15s, color 0.15s',
                fontFamily: 'Inter, sans-serif',
              }}
            >
              SIGN UP
            </button>
            <button
              onClick={() => { setMode('login'); setSignupErrors({}); setLoginErrors({}); setSuccess(false); }}
              style={{
                flex: 1, padding: '12px 0',
                background: mode === 'login' ? '#fff' : 'transparent',
                color: mode === 'login' ? '#000' : 'rgba(255,255,255,0.4)',
                border: 'none',
                borderLeft: '1px solid rgba(255,255,255,0.15)',
                fontWeight: 900, fontSize: 10, letterSpacing: '0.18em',
                textTransform: 'uppercase', cursor: 'pointer',
                transition: 'background 0.15s, color 0.15s',
                fontFamily: 'Inter, sans-serif',
              }}
            >
              LOG IN
            </button>
          </div>

          {/* Success state */}
          {success && (
            <div style={{
              border: '1px solid rgba(255,255,255,0.3)',
              padding: '20px 24px',
              marginBottom: 24,
              display: 'flex', alignItems: 'center', gap: 14,
              animation: 'fadeIn 0.4s ease both',
            }}>
              <div className="pulse-dot" style={{ background: '#fff' }} />
              <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.8)' }}>
                AUTHENTICATION SUCCESSFUL — REDIRECTING...
              </span>
            </div>
          )}

          {/* SIGNUP FORM */}
          {mode === 'signup' && !success && (
            <div className="animate-fade-in">
              <h1 style={{
                fontWeight: 900, fontSize: 28, letterSpacing: '-0.02em',
                textTransform: 'uppercase', marginBottom: 8, lineHeight: 1,
              }}>
                CREATE ACCOUNT
              </h1>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 36, lineHeight: 1.6 }}>
                Set up your Inbox Copilot profile to start scanning.
              </p>

              <form onSubmit={handleSignup} noValidate>
                <Field
                  label="Full Name"
                  value={signupData.name}
                  onChange={e => setSignupData(d => ({ ...d, name: e.target.value }))}
                  error={signupErrors.name}
                  placeholder="Your full name"
                  autoComplete="name"
                />
                <Field
                  label="Email Address"
                  type="email"
                  value={signupData.email}
                  onChange={e => setSignupData(d => ({ ...d, email: e.target.value }))}
                  error={signupErrors.email}
                  placeholder="you@university.edu"
                  autoComplete="email"
                />
                <Field
                  label="Password"
                  type="password"
                  value={signupData.password}
                  onChange={e => setSignupData(d => ({ ...d, password: e.target.value }))}
                  error={signupErrors.password}
                  placeholder="Min. 8 characters"
                  autoComplete="new-password"
                />
                <Field
                  label="Confirm Password"
                  type="password"
                  value={signupData.confirm}
                  onChange={e => setSignupData(d => ({ ...d, confirm: e.target.value }))}
                  error={signupErrors.confirm}
                  placeholder="Repeat password"
                  autoComplete="new-password"
                />

                {signupErrors.submit && (
                  <div style={{ marginBottom: 16, padding: '12px 16px', border: '1px solid #ffb4ab', background: 'rgba(147,0,10,0.1)', fontSize: 11, color: '#ffb4ab', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                    {signupErrors.submit}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    width: '100%',
                    background: submitting ? 'rgba(255,255,255,0.7)' : '#fff',
                    color: '#000',
                    border: '1px solid #fff',
                    fontWeight: 900, fontSize: 11, letterSpacing: '0.18em',
                    textTransform: 'uppercase', padding: '16px',
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    transition: 'background 0.15s',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                    fontFamily: 'Inter, sans-serif',
                    marginTop: 8,
                  }}
                >
                  {submitting ? (
                    <>
                      <div className="pulse-dot" style={{ background: '#000', width: 6, height: 6 }} />
                      CREATING ACCOUNT...
                    </>
                  ) : (
                    <>
                      <span className="ms" style={{ color: '#000', fontSize: 16 }}>barcode_scanner</span>
                      CREATE ACCOUNT
                    </>
                  )}
                </button>
              </form>

              <div style={{ marginTop: 32, textAlign: 'center' }}>
                <button
                  onClick={() => { setMode('login'); setSignupErrors({}); }}
                  className="btn-primary"
                  style={{
                    width: '100%',
                    padding: '14px',
                    fontSize: 10,
                    fontWeight: 900,
                    letterSpacing: '0.15em',
                    textTransform: 'uppercase',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    transition: 'transform 0.2s, background 0.2s',
                  }}
                  onMouseEnter={e => e.target.style.transform = 'translateY(-2px)'}
                  onMouseLeave={e => e.target.style.transform = 'translateY(0)'}
                >
                  <span className="ms" style={{ color: '#000', fontSize: 14 }}>login</span>
                  ALREADY HAVE AN ACCOUNT? LOG IN
                </button>
              </div>
            </div>
          )}

          {/* LOGIN FORM */}
          {mode === 'login' && !success && (
            <div className="animate-fade-in">
              <h1 style={{
                fontWeight: 900, fontSize: 28, letterSpacing: '-0.02em',
                textTransform: 'uppercase', marginBottom: 8, lineHeight: 1,
              }}>
                WELCOME BACK
              </h1>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 36, lineHeight: 1.6 }}>
                Sign in to access your opportunity stream.
              </p>

              <form onSubmit={handleLogin} noValidate>
                <Field
                  label="Email Address"
                  type="email"
                  value={loginData.email}
                  onChange={e => setLoginData(d => ({ ...d, email: e.target.value }))}
                  error={loginErrors.email}
                  placeholder="you@university.edu"
                  autoComplete="email"
                />
                <Field
                  label="Password"
                  type="password"
                  value={loginData.password}
                  onChange={e => setLoginData(d => ({ ...d, password: e.target.value }))}
                  error={loginErrors.password}
                  placeholder="Your password"
                  autoComplete="current-password"
                />

                {loginErrors.submit && (
                  <div style={{ marginBottom: 16, padding: '12px 16px', border: '1px solid #ffb4ab', background: 'rgba(147,0,10,0.1)', fontSize: 11, color: '#ffb4ab', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                    {loginErrors.submit}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    width: '100%',
                    background: submitting ? 'rgba(255,255,255,0.7)' : '#fff',
                    color: '#000',
                    border: '1px solid #fff',
                    fontWeight: 900, fontSize: 11, letterSpacing: '0.18em',
                    textTransform: 'uppercase', padding: '16px',
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    transition: 'background 0.15s',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                    fontFamily: 'Inter, sans-serif',
                    marginTop: 8,
                  }}
                >
                  {submitting ? (
                    <>
                      <div className="pulse-dot" style={{ background: '#000', width: 6, height: 6 }} />
                      AUTHENTICATING...
                    </>
                  ) : (
                    <>
                      <span className="ms" style={{ color: '#000', fontSize: 16 }}>login</span>
                      SIGN IN
                    </>
                  )}
                </button>
              </form>

              <div style={{ marginTop: 32, textAlign: 'center' }}>
                <button
                  onClick={() => { setMode('signup'); setLoginErrors({}); }}
                  className="btn-primary"
                  style={{
                    width: '100%',
                    padding: '14px',
                    fontSize: 10,
                    fontWeight: 900,
                    letterSpacing: '0.15em',
                    textTransform: 'uppercase',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    transition: 'transform 0.2s, background 0.2s',
                  }}
                  onMouseEnter={e => e.target.style.transform = 'translateY(-2px)'}
                  onMouseLeave={e => e.target.style.transform = 'translateY(0)'}
                >
                  <span className="ms" style={{ color: '#000', fontSize: 14 }}>person_add</span>
                  DON'T HAVE AN ACCOUNT? SIGN UP
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
