import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import API_CONFIG from '../config';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import Tooltip from '../components/Tooltip';
import CountdownTimer from '../components/CountdownTimer';
import Autocomplete from '../components/Autocomplete';
import { saveProfile, loadProfile, getUserId } from '../utils/profileApi';
import { generateOpportunityPDF } from '../utils/pdfExport';

// ─── ANIMATED ENTRY WRAPPER ────────────────────────────────────────────────

// ─── SIDEBAR + TOPNAV LAYOUT ───────────────────────────────────────────────
function AppLayout({ children, activePage, setActivePage, stats }) {
  const navigate = useNavigate();
  const [backendStatus, setBackendStatus] = useState('CHECKING...');

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.health}`, { signal: AbortSignal.timeout(3000) });
        setBackendStatus(r.ok ? 'ONLINE' : 'ERROR');
      } catch { setBackendStatus('OFFLINE'); }
    };
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  const navItems = [
    { key: 'scan', icon: 'barcode_scanner', label: 'SCAN PROCESS' },
    { key: 'results', icon: 'analytics', label: 'SYSTEM INTELLIGENCE' },
    { key: 'bookmarks', icon: 'bookmarks', label: 'SAVED OPPORTUNITIES' },
    { key: 'noise', icon: 'delete_sweep', label: 'ELIMINATED NOISE' },
    { key: 'profile', icon: 'account_circle', label: 'USER PROFILE' },
    { key: 'report', icon: 'bar_chart', label: 'SCAN REPORT' },
  ];

  const isOnline = backendStatus === 'ONLINE';
  const isOffline = backendStatus === 'OFFLINE';

  return (
    <div style={{ minHeight: '100vh', background: '#000' }}>

      {/* TOP NAV */}
      <header style={{
        position: 'fixed', top: 0, left: 0, width: '100%', zIndex: 100,
        height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 32px', background: '#000', borderBottom: '1px solid #fff',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
          <div style={{ fontWeight: 900, fontSize: 16, letterSpacing: '0.22em', textTransform: 'uppercase' }}
            className="glitch-text">
            INBOX COPILOT
          </div>
          <nav style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
            {navItems.map(item => (
              <button
                key={item.key}
                onClick={() => setActivePage(item.key)}
                style={{
                  background: activePage === item.key ? '#fff' : 'none',
                  border: 'none', cursor: 'pointer',
                  color: activePage === item.key ? '#000' : 'rgba(255,255,255,0.35)',
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.15em',
                  textTransform: 'uppercase', padding: '8px 16px',
                  fontFamily: 'Inter, sans-serif',
                  transition: 'background 0.15s, color 0.15s',
                  height: 64, display: 'flex', alignItems: 'center',
                  position: 'relative',
                }}
                onMouseEnter={e => { if (activePage !== item.key) { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = '#fff'; } }}
                onMouseLeave={e => { if (activePage !== item.key) { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'rgba(255,255,255,0.35)'; } }}
              >
                {item.key.toUpperCase()}
              </button>
            ))}
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: 6 }}>
            {isOnline && <div className="pulse-dot" style={{ width: 5, height: 5 }} />}
            BACKEND: <span style={{ color: isOnline ? '#fff' : isOffline ? '#ffb4ab' : 'rgba(255,255,255,0.6)' }}>{backendStatus}</span>
          </span>
          {localStorage.getItem('inbox_copilot_user_name') && (
            <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.45)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              {localStorage.getItem('inbox_copilot_user_name').toUpperCase()}
            </span>
          )}
          <button
            onClick={() => {
              localStorage.removeItem('inbox_copilot_user_id');
              localStorage.removeItem('inbox_copilot_user_email');
              localStorage.removeItem('inbox_copilot_user_name');
              localStorage.removeItem('inboxScanResults');
              localStorage.removeItem('lastScanSource');
              navigate('/');
            }}
            style={{
              border: '1px solid rgba(255,255,255,0.4)', background: 'none', color: 'rgba(255,255,255,0.7)',
              fontWeight: 900, fontSize: 10, letterSpacing: '0.18em',
              textTransform: 'uppercase', padding: '8px 18px', cursor: 'pointer',
              fontFamily: 'Inter, sans-serif', transition: 'background 0.15s, color 0.15s, border-color 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.color = '#000'; e.currentTarget.style.borderColor = '#fff'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.4)'; }}
          >
            SIGN OUT
          </button>
        </div>
      </header>

      {/* SIDEBAR */}
      <aside style={{
        position: 'fixed', left: 0, top: 64, width: 260,
        height: 'calc(100vh - 64px)', zIndex: 40,
        display: 'flex', flexDirection: 'column',
        background: '#000', borderRight: '1px solid #fff',
      }}>
        <div style={{ padding: '24px', borderBottom: '1px solid rgba(255,255,255,0.15)' }}>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.2em', textTransform: 'uppercase' }}>V.01 OPPORTUNITY INBOX</div>
        </div>

        <div style={{ padding: '16px' }}>
          <button
            className="btn-primary"
            onClick={() => setActivePage('scan')}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <span className="ms" style={{ fontSize: 16 }}>barcode_scanner</span>
            EXECUTE SCAN
          </button>
          
          <button
            className="btn-ghost"
            onClick={() => navigate('/email-scan')}
            style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}
          >
            <span className="ms" style={{ fontSize: 16 }}>email</span>
            EMAIL SCAN
          </button>
        </div>

        <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
          {navItems.map(item => (
            <button
              key={item.key}
              onClick={() => setActivePage(item.key)}
              className={`nav-link-side${activePage === item.key ? ' active' : ''}`}
              style={{ width: '100%', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer' }}
            >
              <span className={activePage === item.key ? 'ms-fill' : 'ms'} style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {stats.show && (
          <div style={{ padding: '20px', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
            <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'rgba(255,255,255,0.4)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 12 }}>LAST SCAN RESULT</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[['Ranked', stats.ranked, '#fff'], ['Discarded', stats.discarded, 'rgba(255,255,255,0.5)'], ['Failed', stats.failed, '#ffb4ab']].map(([lbl, val, color]) => (
                <div key={lbl} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <span style={{ color: 'rgba(255,255,255,0.4)' }}>{lbl}</span>
                  <span style={{ color }}>{val}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
          <button
            onClick={() => {
              localStorage.removeItem('inbox_copilot_user_id');
              localStorage.removeItem('inbox_copilot_user_email');
              localStorage.removeItem('inbox_copilot_user_name');
              localStorage.removeItem('inboxScanResults');
              localStorage.removeItem('lastScanSource');
              navigate('/');
            }}
            style={{
              width: '100%', background: 'none', border: 'none', cursor: 'pointer',
              color: 'rgba(255,255,255,0.3)', fontSize: 10, fontWeight: 700,
              letterSpacing: '0.15em', textTransform: 'uppercase',
              display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0',
              fontFamily: 'Inter, sans-serif', transition: 'color 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = '#fff'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.3)'}
          >
            <span className="ms" style={{ fontSize: 16 }}>logout</span>
            RESET SESSION
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main style={{ marginLeft: 260, marginTop: 64, minHeight: 'calc(100vh - 64px)' }}>
        {children}
      </main>
    </div>
  );
}

// ─── SCAN VIEW ────────────────────────────────────────────────────────────
function ScanView({ onScanComplete }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [emailText, setEmailText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);
  const [loadingSample, setLoadingSample] = useState(false);
  const fileRef = useRef(null);

  const profile = {
    degree: 'BSCS', semester: 6, cgpa: 3.4,
    location: 'Lahore', skills: 'Python, Machine Learning, AWS, React',
    types: 'internship, hackathon, scholarship', experience: '', financial: false, totalSemesters: 8,
  };
  const [pf, setPf] = useState(profile);
  const [profileSaveStatus, setProfileSaveStatus] = useState('');

  // Load profile on component mount
  useEffect(() => {
    async function loadUserProfile() {
      try {
        const userId = getUserId();
        const loadedProfile = await loadProfile(userId);
        if (loadedProfile) {
          setPf(loadedProfile);
          setProfileSaveStatus('Profile loaded');
          setTimeout(() => setProfileSaveStatus(''), 2000);
        }
      } catch (error) {
        console.error('Failed to load profile:', error);
      }
    }
    loadUserProfile();
  }, []);

  // Save profile when it changes (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(async () => {
      try {
        const userId = getUserId();
        await saveProfile(userId, pf);
        setProfileSaveStatus('Profile saved');
        setTimeout(() => setProfileSaveStatus(''), 2000);
      } catch (error) {
        console.error('Failed to save profile:', error);
        setProfileSaveStatus('Save failed');
        setTimeout(() => setProfileSaveStatus(''), 2000);
      }
    }, 1000); // Debounce for 1 second

    return () => clearTimeout(timeoutId);
  }, [pf]);

  // Progress animation while scanning
  useEffect(() => {
    if (!scanning) { setScanProgress(0); return; }
    const interval = setInterval(() => {
      setScanProgress(p => p < 90 ? p + Math.random() * 3 : p);
    }, 200);
    return () => clearInterval(interval);
  }, [scanning]);

  async function runScan() {
    if (!emailText.trim() && selectedFiles.length === 0) {
      setError('Provide email text or upload files before scanning.');
      return;
    }
    setError('');
    setSuccessMessage('');
    setScanning(true);
    try {
      const fd = new FormData();
      fd.append('profile', JSON.stringify({
        degree: pf.degree, semester: Number(pf.semester), cgpa: Number(pf.cgpa),
        location_preference: pf.location, skills: pf.skills.split(',').map(s => s.trim()).filter(Boolean),
        preferred_opportunity_types: pf.types.split(',').map(s => s.trim()).filter(Boolean),
        past_experience: pf.experience || undefined,
        financial_need: pf.financial === 'true' || pf.financial === true,
        total_semesters: Number(pf.totalSemesters),
      }));
      // Include user_id so scan history is saved to MySQL
      const userId = getUserId();
      fd.append('user_id', userId);
      if (emailText.trim()) fd.append('email_text', emailText);
      selectedFiles.forEach(f => fd.append('files', f));
      const res = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.processFiles}`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setScanProgress(100);
      setTimeout(() => onScanComplete(data), 400);
    } catch (err) {
      setError('Backend error: ' + err.message);
      setScanning(false);
    }
  }

  async function loadSampleData() {
    setLoadingSample(true);
    setError('');
    setSuccessMessage('');
    try {
      const res = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.sampleData}`);
      if (!res.ok) throw new Error('Failed to fetch sample data');
      const data = await res.json();
      
      // Populate profile fields from sample data
      const sampleProfile = data.profile;
      setPf({
        degree: sampleProfile.degree || 'BSCS',
        semester: sampleProfile.semester || 6,
        cgpa: sampleProfile.cgpa || 3.4,
        location: sampleProfile.location_preference || 'Lahore',
        skills: (sampleProfile.skills || []).join(', '),
        types: (sampleProfile.preferred_opportunity_types || []).join(', '),
        experience: sampleProfile.past_experience || '',
        financial: sampleProfile.financial_need || false,
        totalSemesters: sampleProfile.total_semesters || 8,
      });
      
      // Populate email text with sample emails
      const emailsText = (data.emails || []).join('\n\n---\n\n');
      setEmailText(emailsText);
      
      // Clear any selected files
      setSelectedFiles([]);
      if (fileRef.current) fileRef.current.value = '';
      
      // Show success message
      setSuccessMessage(`Successfully loaded ${data.email_count || 0} sample emails and demo profile!`);
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (err) {
      setError('Failed to load sample data: ' + err.message);
    } finally {
      setLoadingSample(false);
    }
  }

  const inputStyle = {
    width: '100%', background: 'transparent', border: '1px solid rgba(255,255,255,0.2)',
    color: '#fff', fontSize: 13, padding: '14px 16px', outline: 'none',
    fontFamily: 'Inter, sans-serif', transition: 'border-color 0.2s, box-shadow 0.2s',
  };
  const LabelStyle = {
    position: 'absolute', top: 0, left: 8, padding: '0 6px',
    fontSize: 9, fontWeight: 700, letterSpacing: '0.2em',
    textTransform: 'uppercase', background: 'inherit', color: 'rgba(255,255,255,0.5)',
  };

  return (
    <div className="page-enter">
      {/* Hero */}
      <section style={{
        padding: '48px 48px 40px', borderBottom: '1px solid rgba(255,255,255,0.15)',
        background: '#0a0a0a', position: 'relative', overflow: 'hidden',
      }}>
        <div className="dot-grid" style={{ opacity: 0.35 }} />
        {/* Scan line */}
        <div style={{
          position: 'absolute', left: 0, right: 0, height: 1,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.15) 30%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0.15) 70%, transparent)',
          animation: 'scanLine 4s linear infinite',
          pointerEvents: 'none',
        }} />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 16, border: '1px solid rgba(255,255,255,0.2)', padding: '4px 12px' }}>
            <div className="pulse-dot" style={{ width: 5, height: 5 }} />
            <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.25em', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' }}>EXTRACTION ENGINE READY</span>
          </div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(24px, 3.5vw, 48px)', textTransform: 'uppercase', letterSpacing: '-0.03em', lineHeight: 1, color: '#fff' }}>
            MAPPING STUDENT PROFILE TO REAL OPPORTUNITIES
          </h1>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.3em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginTop: 12 }}>
            DATA EXTRACTION ACTIVE
          </div>
        </div>
      </section>

      {/* Profile + Email grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.15)' }}>

        {/* LEFT: Profile */}
        <div style={{ padding: 40, borderRight: '1px solid rgba(255,255,255,0.15)', background: '#0d0d0d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
            <h2 style={{ fontWeight: 900, fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#fff' }}>STUDENT PROFILE VECTORS</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {profileSaveStatus && (
                <span style={{ 
                  fontSize: 9, 
                  fontWeight: 700, 
                  letterSpacing: '0.15em', 
                  color: profileSaveStatus.includes('failed') ? '#ffb4ab' : '#4ade80',
                  textTransform: 'uppercase'
                }}>
                  {profileSaveStatus}
                </span>
              )}
              <span className="badge medium">INPUT REQUIRED</span>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {[
              ['DEGREE PROGRAM', 'degree', 'select', ['BSCS','BSEE','BSMath','BBA','BSSE','BSAI','BSCY']],
              ['SEMESTER INDEX', 'semester', 'number'],
              ['CGPA METRIC', 'cgpa', 'number'],
              ['LOCATION', 'location', 'text'],
            ].map(([lbl, key, type, opts]) => (
              <div key={key} style={{ position: 'relative', paddingTop: 12 }}>
                <label style={{ ...LabelStyle, background: '#0d0d0d' }}>{lbl}</label>
                {type === 'select' ? (
                  <select
                    value={pf[key]}
                    onChange={e => setPf(p => ({ ...p, [key]: e.target.value }))}
                    style={{ ...inputStyle, appearance: 'none', background: '#0d0d0d' }}
                    onFocus={e => { e.target.style.borderColor = '#fff'; e.target.style.boxShadow = '0 0 0 1px rgba(255,255,255,0.1)'; }}
                    onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.2)'; e.target.style.boxShadow = 'none'; }}
                  >
                    {opts.map(o => <option key={o} value={o} style={{ background: '#0d0d0d' }}>{o}</option>)}
                  </select>
                ) : (
                  <input
                    type={type}
                    value={pf[key]}
                    step={key === 'cgpa' ? 0.01 : 1}
                    onChange={e => setPf(p => ({ ...p, [key]: e.target.value }))}
                    style={inputStyle}
                    onFocus={e => { e.target.style.borderColor = '#fff'; e.target.style.boxShadow = '0 0 0 1px rgba(255,255,255,0.1)'; }}
                    onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.2)'; e.target.style.boxShadow = 'none'; }}
                  />
                )}
              </div>
            ))}
            {/* Skills field with Autocomplete */}
            <div style={{ position: 'relative', paddingTop: 12, gridColumn: '1 / -1' }}>
              <label style={{ ...LabelStyle, background: '#0d0d0d' }}>CORE COMPETENCIES (comma-separated)</label>
              <Autocomplete
                value={pf.skills}
                onChange={e => setPf(p => ({ ...p, skills: e.target.value }))}
                placeholder="Type to search skills..."
              />
            </div>
            {/* Preferred types field */}
            <div style={{ position: 'relative', paddingTop: 12, gridColumn: '1 / -1' }}>
              <label style={{ ...LabelStyle, background: '#0d0d0d' }}>PREFERRED TYPES (comma-separated)</label>
              <input 
                type="text" 
                value={pf.types} 
                onChange={e => setPf(p => ({ ...p, types: e.target.value }))} 
                style={inputStyle}
                onFocus={e => { e.target.style.borderColor = '#fff'; e.target.style.boxShadow = '0 0 0 1px rgba(255,255,255,0.1)'; }}
                onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.2)'; e.target.style.boxShadow = 'none'; }} 
              />
            </div>
            <div style={{ position: 'relative', paddingTop: 12, gridColumn: '1 / -1' }}>
              <label style={{ ...LabelStyle, background: '#0d0d0d' }}>FINANCIAL NEED INDEX</label>
              <select value={pf.financial} onChange={e => setPf(p => ({ ...p, financial: e.target.value }))} style={{ ...inputStyle, appearance: 'none', background: '#0d0d0d' }}
                onFocus={e => { e.target.style.borderColor = '#fff'; }}
                onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.2)'; }}>
                <option value="false" style={{ background: '#0d0d0d' }}>NO FUNDING REQUIRED</option>
                <option value="true" style={{ background: '#0d0d0d' }}>HIGH PRIORITY FUNDING REQUIRED</option>
              </select>
            </div>
          </div>
        </div>

        {/* RIGHT: Email intake */}
        <div style={{ padding: 40, background: '#080808', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <h2 style={{ fontWeight: 900, fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#fff' }}>RAW DATA INTAKE</h2>
            <span className="ms" style={{ color: 'rgba(255,255,255,0.45)', fontSize: 18 }}>data_object</span>
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', display: 'block', marginBottom: 8 }}>
              UPLOAD FILES (.txt, .eml, .pdf)
            </label>
            <input
              type="file" ref={fileRef} multiple accept=".txt,.eml,.pdf"
              onChange={e => setSelectedFiles(Array.from(e.target.files))}
              style={{ ...inputStyle, padding: '10px 16px', fontSize: 12 }}
            />
            {selectedFiles.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.55)', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {selectedFiles.map((f, i) => (
                  <span key={i} style={{ border: '1px solid rgba(255,255,255,0.2)', padding: '2px 8px', fontSize: 9, letterSpacing: '0.05em' }}>
                    {f.name}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{ position: 'relative', paddingTop: 12, flex: 1, display: 'flex', flexDirection: 'column' }}>
            <label style={{ ...LabelStyle, background: '#080808' }}>OR PASTE EMAILS — SEPARATE WITH "---"</label>
            <textarea
              value={emailText}
              onChange={e => setEmailText(e.target.value)}
              placeholder={'Paste emails here, separated by ---\n\nSubject: Internship Opportunity...\n\n---\n\nSubject: Scholarship...'}
              style={{
                ...inputStyle, flex: 1, minHeight: 220,
                resize: 'vertical', fontFamily: 'monospace', fontSize: 12,
                paddingTop: 20, lineHeight: 1.6,
              }}
              onFocus={e => { e.target.style.borderColor = '#fff'; e.target.style.boxShadow = '0 0 0 1px rgba(255,255,255,0.08)'; }}
              onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.2)'; e.target.style.boxShadow = 'none'; }}
            />
          </div>

          {/* Floating Toast Notifications */}
          <div style={{ position: 'fixed', top: 80, right: 32, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {error && (
              <div style={{ border: '1px solid #ffb4ab', background: 'rgba(147,0,10,0.9)', backdropFilter: 'blur(10px)', padding: '16px 24px', animation: 'slideInRight 0.3s ease both', minWidth: 300 }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: '#ffb4ab', marginBottom: 4, textTransform: 'uppercase' }}>ERROR VECTOR DETECTED</div>
                <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#fff' }}>{error}</div>
              </div>
            )}
            {successMessage && (
              <div style={{ border: '1px solid #4caf50', background: 'rgba(76,175,80,0.9)', backdropFilter: 'blur(10px)', padding: '16px 24px', animation: 'slideInRight 0.3s ease both', minWidth: 300 }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: '#4caf50', marginBottom: 4, textTransform: 'uppercase' }}>SUCCESS</div>
                <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#fff' }}>{successMessage}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scan action bar */}
      <div style={{ padding: '28px 40px', background: '#0a0a0a', borderBottom: '1px solid rgba(255,255,255,0.15)', display: 'flex', gap: 24, flexDirection: 'column', alignItems: 'stretch' }}>
        {/* Progress bar (visible when scanning) */}
        {scanning && (
          <div style={{ height: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden', animation: 'fadeIn 0.3s ease both' }}>
            <div style={{
              height: '100%', background: '#fff',
              width: scanProgress + '%',
              transition: 'width 0.3s ease',
            }} />
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <button
            onClick={runScan}
            disabled={scanning}
            style={{
              background: scanning ? 'rgba(255,255,255,0.8)' : '#fff',
              color: '#000', border: 'none',
              fontWeight: 900, fontSize: 12, letterSpacing: '0.18em', textTransform: 'uppercase',
              padding: '16px 40px', cursor: scanning ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 12,
              fontFamily: 'Inter, sans-serif',
              transition: 'background 0.15s, transform 0.15s',
              transform: scanning ? 'none' : undefined,
            }}
            onMouseEnter={e => { if (!scanning) { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(255,255,255,0.15)'; } }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
          >
            <span className="ms" style={{ color: '#000', fontSize: 18 }}>barcode_scanner</span>
            {scanning ? 'SCANNING...' : 'INITIALIZE SCAN'}
          </button>
          
          <button
            onClick={loadSampleData}
            disabled={loadingSample || scanning}
            style={{
              background: 'none',
              color: loadingSample ? 'rgba(255,255,255,0.5)' : '#fff',
              border: '1px solid ' + (loadingSample ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.5)'),
              fontWeight: 900, fontSize: 12, letterSpacing: '0.18em', textTransform: 'uppercase',
              padding: '16px 32px', cursor: (loadingSample || scanning) ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 12,
              fontFamily: 'Inter, sans-serif',
              transition: 'background 0.15s, color 0.15s, border-color 0.15s, transform 0.15s',
            }}
            onMouseEnter={e => { 
              if (!loadingSample && !scanning) { 
                e.currentTarget.style.background = '#fff'; 
                e.currentTarget.style.color = '#000'; 
                e.currentTarget.style.borderColor = '#fff';
                e.currentTarget.style.transform = 'translateY(-1px)';
              } 
            }}
            onMouseLeave={e => { 
              e.currentTarget.style.background = 'none'; 
              e.currentTarget.style.color = loadingSample ? 'rgba(255,255,255,0.5)' : '#fff'; 
              e.currentTarget.style.borderColor = loadingSample ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.5)';
              e.currentTarget.style.transform = 'none';
            }}
          >
            <span className="ms" style={{ fontSize: 18 }}>download</span>
            {loadingSample ? 'LOADING...' : 'LOAD SAMPLE DATA'}
          </button>
          
          {scanning && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, animation: 'fadeIn 0.3s ease both' }}>
              <div className="pulse-dot" />
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.6)' }}>
                PROCESSING INBOX VIA GROQ API... {Math.round(scanProgress)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── CHECKLIST SECTION ────────────────────────────────────────────────────
function ChecklistSection({ opportunityId, initialChecklist }) {
  const [checklist, setChecklist] = useState(initialChecklist || []);

  // Load checklist from backend on mount
  useEffect(() => {
    async function loadChecklist() {
      try {
        const { getChecklist } = await import('../utils/checklistApi');
        const loadedChecklist = await getChecklist(opportunityId);
        
        // Merge with initial checklist, preferring backend state
        const merged = initialChecklist.map(item => {
          const saved = loadedChecklist.find(l => l.task === item.task);
          return saved ? { ...item, done: saved.done } : item;
        });
        
        setChecklist(merged);
      } catch (error) {
        console.error('Failed to load checklist:', error);
      }
    }
    
    if (opportunityId) {
      loadChecklist();
    }
  }, [opportunityId, initialChecklist]);

  const toggleChecklistItem = async (task, currentDone) => {
    const newDone = !currentDone;
    
    // Optimistic update
    setChecklist(prev => prev.map(item => 
      item.task === task ? { ...item, done: newDone } : item
    ));

    try {
      const { saveChecklistItem } = await import('../utils/checklistApi');
      await saveChecklistItem(opportunityId, task, newDone);
    } catch (error) {
      console.error('Failed to save checklist item:', error);
      // Revert on error
      setChecklist(prev => prev.map(item => 
        item.task === task ? { ...item, done: currentDone } : item
      ));
    }
  };

  if (!checklist || checklist.length === 0) {
    return null;
  }

  return (
    <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 20 }}>
      <h3 style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: 16, paddingLeft: 12, borderLeft: '2px solid #fff' }}>
        ACTION CHECKLIST
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {checklist.map((item, idx) => (
          <label
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 16px',
              border: '1px solid rgba(255,255,255,0.1)',
              background: item.done ? 'rgba(74, 222, 128, 0.05)' : 'rgba(255,255,255,0.02)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = item.done ? 'rgba(74, 222, 128, 0.1)' : 'rgba(255,255,255,0.05)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = item.done ? 'rgba(74, 222, 128, 0.05)' : 'rgba(255,255,255,0.02)';
            }}
          >
            <input
              type="checkbox"
              checked={item.done || false}
              onChange={() => toggleChecklistItem(item.task, item.done)}
              style={{
                width: 18,
                height: 18,
                cursor: 'pointer',
                accentColor: '#4ade80',
              }}
            />
            <span style={{
              fontSize: 12,
              fontWeight: 500,
              color: item.done ? 'rgba(255,255,255,0.5)' : '#fff',
              textDecoration: item.done ? 'line-through' : 'none',
              flex: 1,
            }}>
              {item.task}
            </span>
            {item.priority === 1 && (
              <span className="badge critical" style={{ fontSize: 8 }}>URGENT</span>
            )}
          </label>
        ))}
      </div>
    </div>
  );
}

// ─── RESULTS VIEW ─────────────────────────────────────────────────────────
function ResultsView({ ranked, analytics, inboxScanInfo }) {
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [bookmarks, setBookmarks] = useState([]);
  const [bookmarkStatus, setBookmarkStatus] = useState({});

  // Load bookmarks on mount
  useEffect(() => {
    async function loadBookmarks() {
      try {
        const { getBookmarks } = await import('../utils/bookmarkApi');
        const loadedBookmarks = await getBookmarks();
        setBookmarks(loadedBookmarks);
      } catch (error) {
        console.error('Failed to load bookmarks:', error);
      }
    }
    loadBookmarks();
  }, []);

  // Check if opportunity is bookmarked
  const isBookmarked = (opportunityId) => {
    return bookmarks.some(b => b.opportunity_id === opportunityId.toString());
  };

  // Toggle bookmark
  const toggleBookmark = async (opportunity, e) => {
    e.stopPropagation();
    const oppId = opportunity.id.toString();
    
    try {
      const { addBookmark, removeBookmark } = await import('../utils/bookmarkApi');
      
      if (isBookmarked(oppId)) {
        await removeBookmark(oppId);
        setBookmarks(prev => prev.filter(b => b.opportunity_id !== oppId));
        setBookmarkStatus({ [oppId]: 'Removed' });
      } else {
        await addBookmark(opportunity);
        setBookmarks(prev => [...prev, { opportunity_id: oppId, opportunity_data: opportunity }]);
        setBookmarkStatus({ [oppId]: 'Saved' });
      }
      
      setTimeout(() => setBookmarkStatus({}), 2000);
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
      setBookmarkStatus({ [oppId]: 'Error' });
      setTimeout(() => setBookmarkStatus({}), 2000);
    }
  };

  const uc = b => ({ 'CRITICAL': 'critical', 'HIGH': 'high', 'MEDIUM': 'medium', 'LOW': 'low' }[b] || 'low');

  if (ranked.length === 0) {
    return (
      <div className="page-enter">
        <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a' }}>
          <div className="section-eyebrow" style={{ marginBottom: 16 }}>SYSTEM INTELLIGENCE</div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(40px, 6vw, 72px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, color: '#fff' }}>
            OPPORTUNITY<br />STREAM
          </h1>
        </div>
        <div style={{ padding: '80px', textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, border: '1px solid rgba(255,255,255,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px',
          }}>
            <span className="ms" style={{ fontSize: 28, color: 'rgba(255,255,255,0.2)' }}>analytics</span>
          </div>
          <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.2)', marginBottom: 12 }}>NO DATA STREAM</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>Run a scan to populate the opportunity stream</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-enter">
      {/* Inbox Scan Banner */}
      {inboxScanInfo && (
        <div style={{ 
          padding: '20px 48px', 
          background: 'linear-gradient(135deg, rgba(76,175,80,0.15) 0%, rgba(33,150,243,0.15) 100%)',
          borderBottom: '1px solid rgba(76,175,80,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          animation: 'fadeIn 0.5s ease'
        }}>
          <div>
            <div style={{ 
              fontSize: 11, 
              fontWeight: 700, 
              letterSpacing: '0.15em', 
              textTransform: 'uppercase',
              color: '#4caf50',
              marginBottom: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <span className="ms" style={{ fontSize: 16 }}>email</span>
              INBOX SCAN RESULTS
            </div>
            <div style={{ 
              fontSize: 13, 
              color: 'rgba(255,255,255,0.8)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              flexWrap: 'wrap'
            }}>
              <span>
                <strong style={{ color: '#fff' }}>{inboxScanInfo.email}</strong>
              </span>
              <span style={{ color: 'rgba(255,255,255,0.5)' }}>•</span>
              <span>
                Provider: <strong style={{ color: '#fff' }}>{inboxScanInfo.provider?.toUpperCase() || 'UNKNOWN'}</strong>
              </span>
              <span style={{ color: 'rgba(255,255,255,0.5)' }}>•</span>
              <span>
                Scanned: <strong style={{ color: '#fff' }}>{inboxScanInfo.totalScanned || 0}</strong> emails
              </span>
              <span style={{ color: 'rgba(255,255,255,0.5)' }}>•</span>
              <span>
                {new Date(inboxScanInfo.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
          <div style={{
            padding: '8px 16px',
            background: 'rgba(76,175,80,0.2)',
            border: '1px solid rgba(76,175,80,0.5)',
            borderRadius: 6,
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: '#4caf50'
          }}>
            LIVE DATA
          </div>
        </div>
      )}
      
      <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div className="section-eyebrow" style={{ marginBottom: 16 }}>SYSTEM INTELLIGENCE</div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(40px, 6vw, 72px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, color: '#fff' }}>
            OPPORTUNITY<br />STREAM
          </h1>
        </div>
        <div className="b1" style={{ padding: '16px 20px', background: '#000', textAlign: 'right', minWidth: 120 }}>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.45)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 4 }}>RANKED ENTITIES</div>
          <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: '-0.04em', color: '#fff' }}>{ranked.length}</div>
        </div>
      </div>
      
      {/* Analytics Dashboard */}
      {analytics && (
        <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0d0d0d' }}>
          <AnalyticsDashboard analytics={analytics} />
        </div>
      )}
      
      <div>
        {ranked.map((opp, i) => {
          const sb = opp.score_breakdown;
          const pct = ((sb.total / 105) * 100).toFixed(0);
          const isExpanded = expandedIndex === i;
          return (
            <div key={i}
              className="result-card"
              onClick={() => setExpandedIndex(isExpanded ? null : i)}
              style={{
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                cursor: 'pointer',
                animation: `fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) ${i * 0.05}s both`,
              }}
            >
              <div style={{ padding: '28px 48px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace', marginBottom: 8, textTransform: 'uppercase' }}>
                      OPP-{String(opp.id || i).padStart(3, '0')} {'//'} {(opp.type || 'OTHER').toUpperCase()}
                    </div>
                    <div style={{ fontWeight: 900, fontSize: 18, letterSpacing: '-0.01em', textTransform: 'uppercase', marginBottom: 4, color: '#fff' }}>{opp.title}</div>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>{opp.org}</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      <Tooltip 
                        content={sb.urgency?.date_confidence ? `Urgency: ${opp.urgency_badge}\nDate Confidence: ${sb.urgency.date_confidence.toUpperCase()}\n${sb.urgency.reason || ''}` : `Urgency: ${opp.urgency_badge}`}
                        position="bottom"
                      >
                        <span className={`badge ${uc(opp.urgency_badge)}`} style={{ cursor: 'help' }}>
                          {opp.urgency_badge || 'LOW'}
                        </span>
                      </Tooltip>
                      {opp.deadline_iso && (
                        <>
                          <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.45)', letterSpacing: '0.05em' }}>
                            DEADLINE: {opp.deadline_iso}
                          </span>
                          <CountdownTimer deadlineIso={opp.deadline_iso} urgencyBadge={opp.urgency_badge} />
                        </>
                      )}
                    </div>
                  </div>
                  <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 8, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', marginBottom: 2 }}>SCORE</div>
                      <div style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, color: '#fff' }}>
                        {sb.total > 0 ? (
                          <>{sb.total}<span style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)' }}>/105</span></>
                        ) : (
                          <span style={{ fontSize: 16, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.05em' }}>N/A</span>
                        )}
                      </div>
                    </div>
                    <div style={{ width: 80, height: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                      <div className="score-bar-animated" style={{ width: sb.total > 0 ? pct + '%' : '0%', height: '100%', background: '#fff', animationDelay: `${i * 0.05}s` }} />
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {/* Bookmark button */}
                      <button
                        onClick={(e) => toggleBookmark(opp, e)}
                        style={{
                          border: '1px solid rgba(255,255,255,0.5)',
                          background: isBookmarked(opp.id) ? '#fff' : 'none',
                          color: isBookmarked(opp.id) ? '#000' : '#fff',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontSize: 16,
                          display: 'flex',
                          alignItems: 'center',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => {
                          if (!isBookmarked(opp.id)) {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                          }
                        }}
                        onMouseLeave={e => {
                          if (!isBookmarked(opp.id)) {
                            e.currentTarget.style.background = 'none';
                          }
                        }}
                        title={isBookmarked(opp.id) ? 'Remove bookmark' : 'Add bookmark'}
                      >
                        <span className={isBookmarked(opp.id) ? 'ms-fill' : 'ms'}>bookmark</span>
                      </button>
                      {/* Export to PDF button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          try {
                            generateOpportunityPDF(opp);
                          } catch (error) {
                            console.error('PDF export failed:', error);
                            alert('Failed to export PDF: ' + error.message);
                          }
                        }}
                        style={{
                          border: '1px solid rgba(255,255,255,0.5)',
                          background: 'none',
                          color: '#fff',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontSize: 16,
                          display: 'flex',
                          alignItems: 'center',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.background = 'none';
                        }}
                        title="Export to PDF"
                      >
                        <span className="ms">picture_as_pdf</span>
                      </button>
                      {bookmarkStatus[opp.id] && (
                        <span style={{
                          fontSize: 9,
                          fontWeight: 700,
                          letterSpacing: '0.1em',
                          color: bookmarkStatus[opp.id] === 'Error' ? '#ffb4ab' : '#4ade80',
                          textTransform: 'uppercase',
                        }}>
                          {bookmarkStatus[opp.id]}
                        </span>
                      )}
                      {opp.link && (
                        <a href={opp.link.startsWith('http') ? opp.link : 'https://' + opp.link} target="_blank" rel="noreferrer"
                          onClick={e => e.stopPropagation()}
                          style={{ border: '1px solid rgba(255,255,255,0.5)', fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '8px 14px', color: '#fff', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, transition: 'background 0.15s, color 0.15s, border-color 0.15s' }}
                          onMouseEnter={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.color = '#000'; e.currentTarget.style.borderColor = '#fff'; }}
                          onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.5)'; }}>
                          APPLY NOW
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {/* Expanded score details and checklist */}
              {isExpanded && (
                <div style={{ padding: '0 48px 28px', animation: 'fadeUp 0.3s ease both', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  {sb.total === 0 ? (
                    /* Inbox scan — show extracted metadata instead of scores */
                    <div style={{ paddingTop: 20, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 24 }}>
                      {opp.snippet && (
                        <div style={{ gridColumn: '1 / -1', padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>EMAIL SNIPPET</div>
                          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', fontFamily: 'monospace', lineHeight: 1.5 }}>{opp.snippet}</div>
                        </div>
                      )}
                      {(opp.meeting_time || opp.interview_time) && (
                        <div style={{ padding: '12px 16px', border: '1px solid rgba(33,150,243,0.3)', background: 'rgba(33,150,243,0.05)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(33,150,243,0.7)', textTransform: 'uppercase', marginBottom: 6 }}>DATE / TIME</div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: '#64b5f6' }}>{opp.meeting_time || opp.interview_time}</div>
                        </div>
                      )}
                      {opp.grant_amount && (
                        <div style={{ padding: '12px 16px', border: '1px solid rgba(156,39,176,0.3)', background: 'rgba(156,39,176,0.05)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(156,39,176,0.7)', textTransform: 'uppercase', marginBottom: 6 }}>GRANT AMOUNT</div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: '#ce93d8' }}>{opp.grant_amount}</div>
                        </div>
                      )}
                      {opp.location && (
                        <div style={{ padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>LOCATION</div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: '#fff' }}>{opp.location}</div>
                        </div>
                      )}
                      {opp.contact && (
                        <div style={{ padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>CONTACT</div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: '#fff' }}>{opp.contact}</div>
                        </div>
                      )}
                      {opp.requirements && opp.requirements.length > 0 && (
                        <div style={{ gridColumn: '1 / -1', padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 8 }}>REQUIREMENTS</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {opp.requirements.map((req, ri) => (
                              <span key={ri} className="chip" style={{ fontSize: 10 }}>{req}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {opp.required_docs && opp.required_docs.length > 0 && (
                        <div style={{ gridColumn: '1 / -1', padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                          <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 8 }}>REQUIRED DOCUMENTS</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {opp.required_docs.map((doc, di) => (
                              <span key={di} className="chip" style={{ fontSize: 10 }}>{doc}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {!opp.snippet && !opp.location && !opp.contact && !opp.meeting_time && !opp.interview_time && (!opp.requirements || opp.requirements.length === 0) && (
                        <div style={{ gridColumn: '1 / -1', padding: '12px 16px', color: 'rgba(255,255,255,0.3)', fontSize: 12, fontStyle: 'italic' }}>
                          No additional details extracted from this email.
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Profile-based scan — show score breakdown */
                    <div style={{ paddingTop: 20, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
                      {Object.entries(sb).filter(([k]) => k !== 'total').map(([key, val]) => {
                        const scoreDetail = val;
                        const tooltipContent = scoreDetail?.reason || `${key.replace(/_/g, ' ')}: ${typeof val === 'object' ? val.score : val} points`;
                        const dateConfidence = scoreDetail?.date_confidence;
                        const fullTooltip = dateConfidence 
                          ? `${tooltipContent}\n\nDate Confidence: ${dateConfidence.toUpperCase()}`
                          : tooltipContent;
                        
                        return (
                          <Tooltip key={key} content={fullTooltip} position="top">
                            <div style={{ padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)', cursor: 'help' }}>
                              <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>
                                {key.replace(/_/g, ' ')}
                              </div>
                              <div style={{ fontWeight: 900, fontSize: 18, color: '#fff' }}>
                                {typeof val === 'object' ? val.score : val}
                              </div>
                            </div>
                          </Tooltip>
                        );
                      })}
                    </div>
                  )}
                  
                  {/* Checklist (profile-based only) */}
                  {sb.total > 0 && opp.checklist && opp.checklist.length > 0 && (
                    <ChecklistSection opportunityId={opp.id} initialChecklist={opp.checklist} />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── NOISE VIEW ───────────────────────────────────────────────────────────
function NoiseView({ discarded, failed }) {
  const all = [...(discarded || []), ...(failed || [])];
  return (
    <div className="page-enter">
      <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div className="section-eyebrow" style={{ marginBottom: 16 }}>SYSTEM LOG VIEW</div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(40px, 6vw, 72px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, color: '#fff' }}>
            ELIMINATED<br />NOISE
          </h1>
        </div>
        <div className="b1" style={{ padding: '16px 20px', background: '#000', textAlign: 'right' }}>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.45)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 4 }}>TOTAL REJECTED</div>
          <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: '-0.04em', color: '#fff' }}>{all.length}</div>
        </div>
      </div>
      {all.length === 0 ? (
        <div style={{ padding: 80, textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, border: '1px solid rgba(255,255,255,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px',
          }}>
            <span className="ms" style={{ fontSize: 28, color: 'rgba(255,255,255,0.15)' }}>delete_sweep</span>
          </div>
          <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.15)', marginBottom: 8 }}>LOG EMPTY</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>Discarded emails will appear here after a scan</div>
        </div>
      ) : (
        all.map((item, i) => {
          const isFail = item.reason?.startsWith('LLM') || item.reason?.startsWith('Schema');
          const isCategory = ['Meeting', 'Interview', 'Deadline', 'Grant', 'Other important'].some(c => item.reason?.startsWith(c));
          const borderColor = isFail ? '#ffb4ab' : isCategory ? 'rgba(33,150,243,0.5)' : 'rgba(255,255,255,0.3)';
          const textColor = isFail ? '#ffb4ab' : isCategory ? '#64b5f6' : 'rgba(255,255,255,0.55)';
          const label = isFail ? 'PARSE FAILURE' : isCategory ? 'CATEGORIZED' : 'NON OPPORTUNITY';
          return (
            <div key={i}
              style={{
                borderBottom: '1px solid rgba(255,255,255,0.08)', padding: '24px 48px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16,
                transition: 'background 0.2s',
                animation: `fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) ${i * 0.04}s both`,
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div>
                <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'rgba(255,255,255,0.3)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  SEQ: {(1000 + i).toString(16).toUpperCase()} {'//'} {label}
                </div>
                <div style={{ fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.02em', color: '#fff' }}>
                  {(item.snippet || 'Email #' + item.id || '').substring(0, 80)}
                </div>
              </div>
              <div style={{
                border: `1px solid ${borderColor}`,
                color: textColor,
                padding: '6px 14px', fontSize: 9, fontWeight: 700, letterSpacing: '0.15em',
                textTransform: 'uppercase', flexShrink: 0, maxWidth: 280, textAlign: 'center',
              }}>
                {item.reason}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

// ─── PROFILE VIEW ─────────────────────────────────────────────────────────
function ProfileView({ profile, ranked, inboxScanInfo }) {
  const [skillRecs, setSkillRecs] = useState([]);

  useEffect(() => {
    async function fetchRecs() {
      try {
        const userId = getUserId();
        const res = await fetch(`${API_CONFIG.baseURL}/graph/recommendations/${userId}`);
        if (res.ok) {
          const data = await res.json();
          setSkillRecs(data.recommended_skills || []);
        }
      } catch (e) { /* non-critical */ }
    }
    fetchRecs();
  }, [ranked]); // re-fetch after a new scan
  const p = profile || {
    cgpa: '—', semester: '—', degree: '—', location_preference: '—',
    financial_need: false, skills: [], preferred_opportunity_types: [],
  };

  return (
    <div className="page-enter">
      <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a', position: 'relative', overflow: 'hidden' }}>
        <div className="dot-grid" style={{ opacity: 0.25 }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(36px, 5vw, 64px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, marginBottom: 12, color: '#fff' }}>
            USER PROFILE<br />COMMAND CENTER
          </h1>
          <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="pulse-dot" style={{ width: 5, height: 5 }} />
            VECTOR STATUS: <span style={{ color: '#fff' }}>{ranked.length > 0 ? 'CALIBRATED' : 'PENDING CALIBRATION'}</span>
            <span style={{ color: 'rgba(255,255,255,0.25)' }}>{'//'} NODE: 408A</span>
          </p>
        </div>
      </div>

      {/* Email Connection Info (if from inbox scan) */}
      {inboxScanInfo && (
        <div style={{ 
          padding: '32px 40px', 
          background: 'linear-gradient(135deg, rgba(76,175,80,0.08) 0%, rgba(33,150,243,0.08) 100%)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          animation: 'fadeIn 0.5s ease'
        }}>
          <h2 style={{ 
            fontWeight: 900, 
            fontSize: 14, 
            letterSpacing: '0.08em', 
            textTransform: 'uppercase', 
            marginBottom: 24,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: '#fff'
          }}>
            <span className="ms-fill" style={{ color: '#4caf50' }}>email</span> 
            EMAIL CONNECTION
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 24 }}>
            <div>
              <label style={{ 
                fontSize: 10, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.45)', 
                display: 'block', 
                marginBottom: 8 
              }}>
                EMAIL ADDRESS
              </label>
              <div style={{ 
                fontWeight: 700, 
                fontSize: 16, 
                letterSpacing: '0.02em', 
                color: '#fff',
                fontFamily: 'monospace'
              }}>
                {inboxScanInfo.email}
              </div>
            </div>
            
            <div>
              <label style={{ 
                fontSize: 10, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.45)', 
                display: 'block', 
                marginBottom: 8 
              }}>
                PROVIDER
              </label>
              <div style={{ 
                fontWeight: 900, 
                fontSize: 16, 
                textTransform: 'uppercase', 
                letterSpacing: '0.05em', 
                color: '#4caf50'
              }}>
                {inboxScanInfo.provider || 'UNKNOWN'}
              </div>
            </div>
            
            <div>
              <label style={{ 
                fontSize: 10, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.45)', 
                display: 'block', 
                marginBottom: 8 
              }}>
                LAST SCAN
              </label>
              <div style={{ 
                fontWeight: 700, 
                fontSize: 14, 
                color: 'rgba(255,255,255,0.8)',
                fontFamily: 'monospace'
              }}>
                {new Date(inboxScanInfo.timestamp).toLocaleString()}
              </div>
            </div>
            
            <div>
              <label style={{ 
                fontSize: 10, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.45)', 
                display: 'block', 
                marginBottom: 8 
              }}>
                EMAILS SCANNED
              </label>
              <div style={{ 
                fontWeight: 900, 
                fontSize: 24, 
                letterSpacing: '-0.02em', 
                color: '#fff'
              }}>
                {inboxScanInfo.totalScanned || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24, padding: 40 }}>
        {/* Academic metrics */}
        <div className="b1 stat-card" style={{ background: '#0d0d0d', padding: 40, position: 'relative', display: 'flex', flexDirection: 'column' }}>
          <div style={{ position: 'absolute', top: 0, right: 0, background: '#fff', color: '#000', padding: '4px 12px', fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase' }}>
            STATIC RECORD
          </div>
          <h2 style={{ fontWeight: 900, fontSize: 14, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 40, display: 'flex', alignItems: 'center', gap: 10, color: '#fff' }}>
            <span className="ms-fill">school</span> ACADEMIC METRICS
          </h2>
          <div style={{ marginBottom: 32 }}>
            <label style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', display: 'block', marginBottom: 8 }}>CUMULATIVE GRADE POINT</label>
            <div style={{ fontSize: 56, fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, color: '#fff' }}>{p.cgpa}</div>
            <div style={{ marginTop: 12, height: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
              <div className="score-bar-animated" style={{ width: p.cgpa !== '—' ? ((p.cgpa / 4) * 100) + '%' : '0%', height: '100%', background: '#fff' }} />
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <div>
              <label style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', display: 'block', marginBottom: 4 }}>PROGRESSION</label>
              <div style={{ fontWeight: 900, fontSize: 18, letterSpacing: '-0.02em', color: '#fff' }}>
                {p.semester !== '—' ? `SEMESTER 0${p.semester}` : '—'}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>DEGREE</div>
              <div style={{ fontWeight: 700, fontSize: 16, letterSpacing: '0.05em', color: '#fff' }}>{p.degree}</div>
            </div>
          </div>
        </div>

        {/* Competency matrix */}
        <div className="b1 stat-card" style={{ background: '#0d0d0d', padding: 40 }}>
          <h2 style={{ fontWeight: 900, fontSize: 14, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 32, display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 20, borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}>
            <span className="ms">account_tree</span> COMPETENCY MATRIX
          </h2>
          <h3 style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: 12, paddingLeft: 12, borderLeft: '2px solid #fff' }}>CORE COMPETENCIES</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 28 }}>
            {(p.skills || []).map(s => <span key={s} className="chip filled" style={{ fontSize: 9 }}>{s}</span>)}
            {(!p.skills || p.skills.length === 0) && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.25)' }}>—</span>}
          </div>
          <h3 style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: 12, paddingLeft: 12, borderLeft: '2px solid #fff' }}>PREFERRED TYPES</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 28 }}>
            {(p.preferred_opportunity_types || []).map(t => <span key={t} className="chip">{t}</span>)}
            {(!p.preferred_opportunity_types || p.preferred_opportunity_types.length === 0) && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.25)' }}>—</span>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 20, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 4 }}>LOCATION PREFERENCE</div>
              <div style={{ fontWeight: 900, fontSize: 16, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#fff' }}>{p.location_preference || '—'}</div>
            </div>
            <div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 4 }}>FINANCIAL NEED</div>
              <div style={{ fontWeight: 900, fontSize: 16, textTransform: 'uppercase', letterSpacing: '0.05em', color: p.financial_need ? '#f59e0b' : '#fff' }}>{p.financial_need ? 'HIGH PRIORITY' : 'NOT REQUIRED'}</div>
            </div>
          </div>

          {/* Neo4j skill recommendations */}
          {skillRecs.length > 0 && (
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: 12, paddingLeft: 12, borderLeft: '2px solid #f59e0b' }}>
                GRAPH-RECOMMENDED SKILLS TO LEARN
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {skillRecs.map(s => (
                  <span key={s} style={{
                    border: '1px solid rgba(245,158,11,0.4)',
                    color: '#f59e0b',
                    padding: '4px 10px',
                    fontSize: 9,
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    background: 'rgba(245,158,11,0.06)',
                  }}>
                    + {s}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.25)', marginTop: 8, letterSpacing: '0.1em' }}>
                Based on skills required by opportunities matched to your profile
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── BOOKMARKS VIEW ───────────────────────────────────────────────────────
function BookmarksView() {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    async function loadBookmarks() {
      try {
        const { getBookmarks } = await import('../utils/bookmarkApi');
        const loadedBookmarks = await getBookmarks();
        setBookmarks(loadedBookmarks);
      } catch (error) {
        console.error('Failed to load bookmarks:', error);
      } finally {
        setLoading(false);
      }
    }
    loadBookmarks();
  }, []);

  const removeBookmark = async (opportunityId, e) => {
    e.stopPropagation();
    try {
      const { removeBookmark: removeBookmarkApi } = await import('../utils/bookmarkApi');
      await removeBookmarkApi(opportunityId);
      setBookmarks(prev => prev.filter(b => b.opportunity_id !== opportunityId));
    } catch (error) {
      console.error('Failed to remove bookmark:', error);
    }
  };

  if (loading) {
    return (
      <div className="page-enter">
        <div style={{ padding: '80px', textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)' }}>
            LOADING BOOKMARKS...
          </div>
        </div>
      </div>
    );
  }

  if (bookmarks.length === 0) {
    return (
      <div className="page-enter">
        <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a' }}>
          <div className="section-eyebrow" style={{ marginBottom: 16 }}>SAVED OPPORTUNITIES</div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(40px, 6vw, 72px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, color: '#fff' }}>
            BOOKMARKED<br />OPPORTUNITIES
          </h1>
        </div>
        <div style={{ padding: '80px', textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, border: '1px solid rgba(255,255,255,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px',
          }}>
            <span className="ms" style={{ fontSize: 28, color: 'rgba(255,255,255,0.2)' }}>bookmarks</span>
          </div>
          <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.2)', marginBottom: 12 }}>NO BOOKMARKS</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>Bookmark opportunities to save them for later</div>
        </div>
      </div>
    );
  }

  const uc = b => ({ 'CRITICAL': 'critical', 'HIGH': 'high', 'MEDIUM': 'medium', 'LOW': 'low' }[b] || 'low');

  return (
    <div className="page-enter">
      <div style={{ padding: '40px 48px', borderBottom: '1px solid rgba(255,255,255,0.15)', background: '#0a0a0a', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div className="section-eyebrow" style={{ marginBottom: 16 }}>SAVED OPPORTUNITIES</div>
          <h1 style={{ fontWeight: 900, fontSize: 'clamp(40px, 6vw, 72px)', textTransform: 'uppercase', letterSpacing: '-0.04em', lineHeight: 0.9, color: '#fff' }}>
            BOOKMARKED<br />OPPORTUNITIES
          </h1>
        </div>
        <div className="b1" style={{ padding: '16px 20px', background: '#000', textAlign: 'right', minWidth: 120 }}>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.45)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 4 }}>SAVED COUNT</div>
          <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: '-0.04em', color: '#fff' }}>{bookmarks.length}</div>
        </div>
      </div>

      <div>
        {bookmarks.map((bookmark, i) => {
          const opp = bookmark.opportunity_data;
          const sb = opp.score_breakdown || {};
          const pct = sb.total ? ((sb.total / 105) * 100).toFixed(0) : 0;
          const isExpanded = expandedIndex === i;
          
          return (
            <div key={i}
              className="result-card"
              onClick={() => setExpandedIndex(isExpanded ? null : i)}
              style={{
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                cursor: 'pointer',
                animation: `fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) ${i * 0.05}s both`,
              }}
            >
              <div style={{ padding: '28px 48px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace', marginBottom: 8, textTransform: 'uppercase' }}>
                      OPP-{String(opp.id || i).padStart(3, '0')} {'//'} {(opp.type || 'OTHER').toUpperCase()}
                    </div>
                    <div style={{ fontWeight: 900, fontSize: 18, letterSpacing: '-0.01em', textTransform: 'uppercase', marginBottom: 4, color: '#fff' }}>{opp.title}</div>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>{opp.org}</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span className={`badge ${uc(opp.urgency_badge)}`}>{opp.urgency_badge || 'LOW'}</span>
                      {opp.deadline_iso && (
                        <>
                          <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.45)', letterSpacing: '0.05em' }}>
                            DEADLINE: {opp.deadline_iso}
                          </span>
                          <CountdownTimer deadlineIso={opp.deadline_iso} urgencyBadge={opp.urgency_badge} />
                        </>
                      )}
                      <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#4ade80', letterSpacing: '0.05em' }}>
                        ★ BOOKMARKED
                      </span>
                    </div>
                  </div>
                  <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
                    {sb.total && (
                      <>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 8, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', marginBottom: 2 }}>SCORE</div>
                          <div style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, color: '#fff' }}>
                            {sb.total}<span style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)' }}>/105</span>
                          </div>
                        </div>
                        <div style={{ width: 80, height: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                          <div className="score-bar-animated" style={{ width: pct + '%', height: '100%', background: '#fff', animationDelay: `${i * 0.05}s` }} />
                        </div>
                      </>
                    )}
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={(e) => removeBookmark(bookmark.opportunity_id, e)}
                        style={{
                          border: '1px solid #ffb4ab',
                          background: 'none',
                          color: '#ffb4ab',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontSize: 9,
                          fontWeight: 700,
                          letterSpacing: '0.15em',
                          textTransform: 'uppercase',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.background = '#ffb4ab';
                          e.currentTarget.style.color = '#000';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.background = 'none';
                          e.currentTarget.style.color = '#ffb4ab';
                        }}
                      >
                        REMOVE
                      </button>
                      {opp.link && (
                        <a href={opp.link.startsWith('http') ? opp.link : 'https://' + opp.link} target="_blank" rel="noreferrer"
                          onClick={e => e.stopPropagation()}
                          style={{ border: '1px solid rgba(255,255,255,0.5)', fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '8px 14px', color: '#fff', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, transition: 'background 0.15s, color 0.15s, border-color 0.15s' }}
                          onMouseEnter={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.color = '#000'; e.currentTarget.style.borderColor = '#fff'; }}
                          onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.5)'; }}>
                          APPLY NOW
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {isExpanded && sb.total && (
                <div style={{ padding: '0 48px 28px', animation: 'fadeUp 0.3s ease both', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  {/* Score breakdown */}
                  <div style={{ paddingTop: 20, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
                    {Object.entries(sb).filter(([k]) => k !== 'total').map(([key, val]) => (
                      <div key={key} style={{ padding: '12px 16px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
                        <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div style={{ fontWeight: 900, fontSize: 18, color: '#fff' }}>{val}</div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Checklist */}
                  {opp.checklist && opp.checklist.length > 0 && (
                    <ChecklistSection opportunityId={opp.id} initialChecklist={opp.checklist} />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── REPORT VIEW ────────────────────────────────────────────────────────────
function ReportView({ scanData }) {
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const hasData = scanData.ranked.length > 0;
  const isInboxScan = hasData && scanData.ranked[0]?.score_breakdown?.total === 0;
  const mode = isInboxScan ? 'inbox' : 'copypaste';

  useEffect(() => {
    if (!hasData) return;
    setLoading(true);
    setError('');

    const payload = mode === 'inbox'
      ? { mode: 'inbox', data: { results: {
          opportunities: scanData.ranked.filter(r => r.category === 'opportunity'),
          meetings:      scanData.ranked.filter(r => r.category === 'meeting'),
          interviews:    scanData.ranked.filter(r => r.category === 'interview'),
          deadlines:     scanData.ranked.filter(r => r.category === 'deadline'),
          grants:        scanData.ranked.filter(r => r.category === 'grant'),
          other_important: scanData.ranked.filter(r => r.category === 'other'),
        }}}
      : { mode: 'copypaste', data: {
          ranked_opportunities: scanData.ranked,
          profile: scanData.profile,
        }};

    fetch(`${API_CONFIG.baseURL}/generate-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(t)))
      .then(data => { setCharts(data.charts); setLoading(false); })
      .catch(err => { setError(String(err)); setLoading(false); });
  }, [scanData.ranked.length, mode]);

  const sectionStyle = {
    padding: '48px',
    minHeight: 'calc(100vh - 64px)',
    background: '#000',
  };

  const cardStyle = {
    background: '#0d0d0d',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 24,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  };

  if (!hasData) return (
    <div style={sectionStyle}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 32 }}>SCAN REPORT</div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 400, color: 'rgba(255,255,255,0.2)', gap: 16 }}>
        <span className="ms" style={{ fontSize: 64 }}>bar_chart</span>
        <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>No scan data yet</div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>Run a scan first to generate your visual report.</div>
      </div>
    </div>
  );

  return (
    <div style={sectionStyle} className="page-enter">
      {/* Header */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 8 }}>SCAN REPORT</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: '-0.02em', color: '#fff', margin: 0 }}>
            {mode === 'inbox' ? 'INBOX INTELLIGENCE REPORT' : 'OPPORTUNITY MATCH REPORT'}
          </h2>
          <div style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', color: mode === 'inbox' ? '#2196f3' : '#4caf50',
            border: `1px solid ${mode === 'inbox' ? 'rgba(33,150,243,0.4)' : 'rgba(76,175,80,0.4)'}`,
            padding: '3px 10px', textTransform: 'uppercase'
          }}>
            {mode === 'inbox' ? 'INBOX MODE' : 'SCORED MODE'}
          </div>
        </div>
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginTop: 8 }}>
          {scanData.ranked.length} items analysed · Generated fresh for this scan
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24, padding: '80px 0' }}>
          <div style={{ width: 48, height: 48, border: '2px solid rgba(255,255,255,0.1)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>GENERATING CHARTS...</div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)' }}>matplotlib + seaborn rendering your data</div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div style={{ padding: 20, background: 'rgba(244,67,54,0.08)', border: '1px solid rgba(244,67,54,0.3)', borderRadius: 8, color: '#ef9a9a', fontSize: 12, marginBottom: 32 }}>
          Failed to generate report: {error}
        </div>
      )}

      {/* Charts Grid */}
      {charts && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 24 }}>
          {charts.map((chart, idx) => (
            <div
              key={idx}
              style={{
                ...cardStyle,
                gridColumn: charts.length % 2 !== 0 && idx === charts.length - 1 ? '1 / -1' : undefined,
                animation: `fadeIn 0.4s ease ${idx * 0.1}s both`,
              }}
            >
              {/* Chart title */}
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase' }}>
                {chart.title}
              </div>

              {/* Chart image */}
              {chart.image ? (
                <img
                  src={`data:image/png;base64,${chart.image}`}
                  alt={chart.title}
                  style={{ width: '100%', borderRadius: 8, display: 'block' }}
                />
              ) : (
                <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>
                  Chart unavailable
                </div>
              )}

              {/* Caption */}
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', lineHeight: 1.6, paddingTop: 4, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                {chart.caption}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── MAIN APP PAGE ─────────────────────────────────────────────────────────
export default function AppPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [activePage, setActivePage] = useState('scan');
  const [scanData, setScanData] = useState({ ranked: [], discarded: [], failed: [], profile: null, inboxScanInfo: null });
  const [analytics, setAnalytics] = useState(null);

  // Auth guard — redirect to /auth if not logged in
  useEffect(() => {
    const userId = localStorage.getItem('inbox_copilot_user_id');
    if (!userId) navigate('/auth', { replace: true });
  }, [navigate]);

  async function handleScanComplete(data) {
    setScanData({
      ranked: data.ranked_opportunities || data.ranked || [],
      discarded: data.discarded || [],
      failed: data.failed || [],
      profile: data.profile || null,
      inboxScanInfo: data.inboxScanInfo || null,  // Store inbox scan info
    });
    
    // Fetch analytics if we have ranked opportunities
    if (data.ranked && data.ranked.length > 0) {
      try {
        // Use the analytics data if it's already in the response
        if (data.analytics) {
          setAnalytics(data.analytics);
        }
      } catch (err) {
        console.error('Failed to load analytics:', err);
        setAnalytics(null);
      }
    }
    
    setActivePage('results');
  }

  // Check if we received scan results from EmailScanPage
  useEffect(() => {
    if (location.state?.scanResults) {
      const results = location.state.scanResults;
      handleScanComplete(results);
      // Clear the location state to prevent re-triggering
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Check for inbox scan results in localStorage
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const source = urlParams.get('source');
    
    if (source === 'inbox_scan') {
      const inboxResults = localStorage.getItem('inboxScanResults');
      
      if (inboxResults) {
        try {
          const data = JSON.parse(inboxResults);
          
          // Map deadline_proximity to urgency_badge values
          const proximityToUrgency = { urgent: 'CRITICAL', soon: 'HIGH', upcoming: 'MEDIUM', later: 'LOW', expired: 'LOW' };
          
          // Convert inbox scan format to AppPage format
          // Helper to map a categorized email to a ranked opportunity card
          const toRanked = (item, idx, typeLabel, baseIdx) => ({
            id: baseIdx + idx,
            title: item.title,
            org: item.org || '',
            type: typeLabel,
            category: item.category || typeLabel,
            deadline_iso: item.deadline_iso,
            deadline_proximity: item.deadline_proximity,
            urgency_badge: proximityToUrgency[item.deadline_proximity] || 'LOW',
            score_breakdown: {
              total: 0,
              skill_alignment: { score: 0 },
              urgency: { score: 0 },
              type_match: { score: 0 },
              location: { score: 0 },
              financial_bonus: { score: 0 },
              completeness: { score: 0 }
            },
            checklist: [],
            link: item.link,
            contact: item.contact,
            requirements: item.requirements,
            required_docs: item.required_docs,
            location: item.location,
            snippet: item.snippet,
            // Extra metadata for expanded view
            meeting_time: item.meeting_time,
            interview_time: item.interview_time,
            grant_amount: item.grant_amount,
          });

          const opportunities = data.results.opportunities || [];
          const meetings     = data.results.meetings || [];
          const interviews   = data.results.interviews || [];
          const deadlines    = data.results.deadlines || [];
          const grants       = data.results.grants || [];
          const other        = data.results.other_important || [];

          const convertedData = {
            ranked: [
              // Opportunities
              ...opportunities.map((opp, idx) => toRanked(opp, idx, opp.type || 'opportunity', 0)),
              // Meetings — actionable, have dates/times
              ...meetings.map((m, idx) => toRanked(m, idx, 'meeting', opportunities.length)),
              // Interviews — highly actionable
              ...interviews.map((i, idx) => toRanked(i, idx, 'interview', opportunities.length + meetings.length)),
              // Deadlines — time-sensitive
              ...deadlines.map((d, idx) => toRanked(d, idx, 'deadline', opportunities.length + meetings.length + interviews.length)),
              // Grants
              ...grants.map((g, idx) => toRanked(g, idx, 'grant', opportunities.length + meetings.length + interviews.length + deadlines.length)),
              // Other important
              ...other.map((o, idx) => toRanked(o, idx, 'other', opportunities.length + meetings.length + interviews.length + deadlines.length + grants.length)),
            ],
            discarded: [
              // Only truly unimportant: LLM-classified non-opportunities
              ...(data.results.discarded || []).map(d => ({
                id: d.id,
                reason: d.reason || 'Non-opportunity',
                snippet: d.snippet || ''
              })),
              // LLM parse failures
              ...(data.results.failed || []).map(f => ({
                id: f.id,
                reason: f.reason || 'LLM parse failure',
                snippet: f.snippet || ''
              })),
            ],
            failed: [],
            profile: null,
            inboxScanInfo: {
              email: data.email,
              provider: data.provider,
              timestamp: data.timestamp,
              totalScanned: data.totalScanned
            }
          };
          
          handleScanComplete(convertedData);
          
          // Clear URL parameter
          window.history.replaceState({}, document.title, '/app');
          
        } catch (err) {
          console.error('Failed to load inbox scan results:', err);
        }
      }
    }
  }, [location.search]);

  const stats = {
    show: scanData.ranked.length > 0 || scanData.discarded.length > 0,
    ranked: scanData.ranked.length,
    discarded: scanData.discarded.length,
    failed: scanData.failed.length,
  };

  return (
    <AppLayout activePage={activePage} setActivePage={setActivePage} stats={stats}>
      {activePage === 'scan' && <ScanView key="scan" onScanComplete={handleScanComplete} />}
      {activePage === 'results' && <ResultsView key="results" ranked={scanData.ranked} analytics={analytics} inboxScanInfo={scanData.inboxScanInfo} />}
      {activePage === 'bookmarks' && <BookmarksView key="bookmarks" />}
      {activePage === 'noise' && <NoiseView key="noise" discarded={scanData.discarded} failed={scanData.failed} />}
      {activePage === 'profile' && <ProfileView key="profile" profile={scanData.profile} ranked={scanData.ranked} inboxScanInfo={scanData.inboxScanInfo} />}
      {activePage === 'report' && <ReportView key="report" scanData={scanData} />}
    </AppLayout>
  );
}
