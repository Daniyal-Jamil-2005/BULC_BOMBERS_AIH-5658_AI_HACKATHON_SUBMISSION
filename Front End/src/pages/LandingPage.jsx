import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TICKER_ITEMS = [
  'EMAIL PARSING', 'OPPORTUNITY RANKING', 'STUDENT PROFILES',
  'CEREBRAS LLM', 'ZERO NOISE', 'SCORE 105', 'AUTO CLASSIFY',
  'DEADLINE ALERTS', 'INTERNSHIPS', 'HACKATHONS', 'SCHOLARSHIPS',
  'EMAIL PARSING', 'OPPORTUNITY RANKING', 'STUDENT PROFILES',
  'CEREBRAS LLM', 'ZERO NOISE', 'SCORE 105', 'AUTO CLASSIFY',
  'DEADLINE ALERTS', 'INTERNSHIPS', 'HACKATHONS', 'SCHOLARSHIPS',
];

const HOW_STEPS = [
  { num: '01', icon: 'person', title: 'BUILD YOUR PROFILE', desc: 'Input your degree, semester, CGPA, skills, and opportunity preferences. The system builds a precise student vector used for matching.' },
  { num: '02', icon: 'email', title: 'FEED YOUR INBOX', desc: 'Paste raw emails or upload .txt/.eml/.pdf files. The system handles bulk ingestion — separate emails with "---" and let the engine do the rest.' },
  { num: '03', icon: 'smart_toy', title: 'LLM EXTRACTION', desc: "Cerebras llama3.1-8b parses each email, identifies opportunities, extracts deadlines, links, and contacts with zero hallucination tolerance." },
  { num: '04', icon: 'analytics', title: 'DETERMINISTIC SCORING', desc: 'Six scoring dimensions — relevance, deadline urgency, credibility, alignment, effort-to-reward, and financial fit — produce a score out of 105.' },
  { num: '05', icon: 'filter_list', title: 'NOISE ELIMINATION', desc: 'Newsletters, spam, and irrelevant emails are automatically discarded. Every rejection is logged with a reason in the Eliminated Noise view.' },
  { num: '06', icon: 'task_alt', title: 'ACTIONABLE INTEL', desc: 'Your ranked opportunity stream surfaces with action checklists, apply links, and full score reasoning. No guesswork — only signal.' },
];

const BENEFITS = [
  { icon: 'speed', title: 'PROCESS HUNDREDS OF EMAILS IN SECONDS', desc: "Batch ingestion with Cerebras inference speed means your entire inbox is scanned before you finish your coffee." },
  { icon: 'filter_alt', title: 'SIGNAL OVER NOISE — ALWAYS', desc: 'The scoring engine is purely deterministic. No bias, no guesswork. Opportunities are ranked by hard numbers, not hunches.' },
  { icon: 'person_pin', title: 'MATCHED TO YOU SPECIFICALLY', desc: 'Your student profile vector — degree, skills, location, CGPA — is factored into every score. Generic listings don\'t make the cut.' },
  { icon: 'checklist', title: 'KNOW EXACTLY WHAT TO DO NEXT', desc: 'Every ranked opportunity includes a generated action checklist. No tab-switching, no re-reading emails. Just execution.' },
  { icon: 'lock', title: 'YOUR DATA STAYS LOCAL', desc: 'Nothing is stored server-side. Your emails, profile, and results exist only in the current session. Close the tab — it\'s gone.' },
  { icon: 'bolt', title: 'BUILT FOR STUDENT PACE', desc: 'Designed specifically for students managing internship season, hackathon deadlines, and scholarship windows simultaneously.' },
];

const STATS = [
  { value: '105', label: 'MAX SCORE' },
  { value: '6', label: 'SCORING DIMENSIONS' },
  { value: '<2s', label: 'AVG PARSE TIME' },
  { value: '∞', label: 'EMAILS PROCESSED' },
];

// Animated stat number that counts up on mount
function StatNumber({ value }) {
  const [display, setDisplay] = useState('0');
  useEffect(() => {
    const num = parseInt(value);
    if (isNaN(num)) { setDisplay(value); return; }
    let start = 0;
    const end = num;
    const dur = 1200;
    const step = dur / end;
    const timer = setInterval(() => {
      start += Math.ceil(end / 40);
      if (start >= end) { setDisplay(String(end)); clearInterval(timer); }
      else setDisplay(String(start));
    }, step);
    return () => clearInterval(timer);
  }, [value]);
  return <span className="counter-num">{display}</span>;
}

export default function LandingPage() {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const [scrolled, setScrolled] = useState(false);
  const [counter, setCounter] = useState(0);
  const [hoveredStep, setHoveredStep] = useState(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCounter(c => (c + 1) % 999);
    }, 80);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ background: '#000', minHeight: '100vh' }}>

      {/* TOP NAV */}
      <header style={{
        position: 'fixed', top: 0, left: 0, width: '100%', zIndex: 100,
        height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 40px',
        background: scrolled ? 'rgba(0,0,0,0.95)' : 'transparent',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.15)' : '1px solid transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        transition: 'background 0.3s, border-color 0.3s, backdrop-filter 0.3s',
      }}>
        <div style={{ fontWeight: 900, fontSize: 16, letterSpacing: '0.22em', textTransform: 'uppercase' }}
          className="glitch-text">
          INBOX COPILOT
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          {['HOW IT WORKS', 'BENEFITS'].map((label, i) => (
            <a key={label} href={i === 0 ? '#how' : '#benefits'}
              style={{ color: 'rgba(255,255,255,0.45)', fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', textDecoration: 'none', transition: 'color 0.15s', position: 'relative' }}
              onMouseEnter={e => e.target.style.color = '#fff'}
              onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,0.45)'}
            >{label}</a>
          ))}
          <button className="btn-primary" onClick={() => navigate('/auth')} style={{ padding: '10px 24px', fontSize: 10 }}>
            GET STARTED
          </button>
        </nav>
      </header>

      {/* HERO */}
      <section ref={heroRef} style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        position: 'relative',
        padding: '120px 40px 80px',
        borderBottom: '1px solid rgba(255,255,255,0.12)',
        overflow: 'hidden',
      }}>
        {/* Visible dot grid */}
        <div className="dot-grid" style={{ opacity: 0.55 }} />

        {/* Corner decorators */}
        <div style={{ position: 'absolute', top: 80, left: 40, width: 20, height: 20, borderTop: '2px solid rgba(255,255,255,0.4)', borderLeft: '2px solid rgba(255,255,255,0.4)' }} />
        <div style={{ position: 'absolute', top: 80, right: 40, width: 20, height: 20, borderTop: '2px solid rgba(255,255,255,0.4)', borderRight: '2px solid rgba(255,255,255,0.4)' }} />
        <div style={{ position: 'absolute', bottom: 80, left: 40, width: 20, height: 20, borderBottom: '2px solid rgba(255,255,255,0.4)', borderLeft: '2px solid rgba(255,255,255,0.4)' }} />

        {/* Scan line effect */}
        <div style={{
          position: 'absolute', left: 0, right: 0, height: 1,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.08) 30%, rgba(255,255,255,0.22) 50%, rgba(255,255,255,0.08) 70%, transparent)',
          animation: 'scanLine 5s linear infinite',
          pointerEvents: 'none',
        }} />

        {/* Live counter badge */}
        <div className="animate-fade-in" style={{ marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            border: '1px solid rgba(255,255,255,0.25)',
            padding: '6px 14px',
            animation: 'borderPulse 3s ease-in-out infinite',
          }}>
            <div className="pulse-dot" style={{ width: 6, height: 6 }} />
            <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.65)', fontFamily: 'monospace' }}>
              SYSTEM ACTIVE // OPP-{String(counter).padStart(3, '0')} PARSED
            </span>
          </div>
        </div>

        {/* Main headline */}
        <h1 className="animate-fade-up" style={{
          fontWeight: 900,
          fontSize: 'clamp(52px, 9vw, 128px)',
          lineHeight: 0.92,
          letterSpacing: '-0.04em',
          textTransform: 'uppercase',
          maxWidth: 1100,
          marginBottom: 40,
        }}>
          YOUR INBOX.<br />
          <span style={{ color: 'rgba(255,255,255,0.22)', WebkitTextStroke: '1px rgba(255,255,255,0.3)' }}>ZERO</span> NOISE.<br />
          PURE SIGNAL.
        </h1>

        {/* Subhead */}
        <p className="animate-fade-up animate-fade-up-d1" style={{
          maxWidth: 520,
          fontSize: 15,
          lineHeight: 1.7,
          color: 'rgba(255,255,255,0.6)',
          marginBottom: 48,
          fontWeight: 400,
        }}>
          Inbox Copilot parses your student email inbox using LLM intelligence and ranks every internship,
          hackathon, and scholarship by how well it matches your profile — deterministically, in seconds.
        </p>

        {/* CTAs */}
        <div className="animate-fade-up animate-fade-up-d2" style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn-primary" onClick={() => navigate('/auth')} style={{ fontSize: 12, padding: '16px 40px' }}>
            <span className="ms" style={{ color: '#000', fontSize: 16 }}>barcode_scanner</span>
            START SCANNING
          </button>
          <a href="#how" className="btn-ghost" style={{ fontSize: 12, padding: '16px 40px' }}>
            SEE HOW IT WORKS
          </a>
        </div>

        {/* Stats bar */}
        <div className="animate-fade-up animate-fade-up-d3" style={{
          display: 'flex', gap: 0, marginTop: 80,
          borderTop: '1px solid rgba(255,255,255,0.15)',
          maxWidth: 800,
          background: 'transparent',
        }}>
          {STATS.map((s, i) => (
            <div key={i} className="stat-card" style={{
              flex: 1,
              padding: '28px 0',
              borderRight: i < STATS.length - 1 ? '1px solid rgba(255,255,255,0.12)' : 'none',
              paddingRight: 32,
              paddingLeft: i > 0 ? 32 : 0,
              cursor: 'default',
              background: 'transparent',
            }}>
              <div style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1, color: '#fff' }}>
                {s.value === '105' || s.value === '6' ? <StatNumber value={s.value} /> : s.value}
              </div>
              <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.45)', marginTop: 6, textTransform: 'uppercase' }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>

        {/* Scroll indicator */}
        <div className="float-anim" style={{
          position: 'absolute', bottom: 40, right: 40,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
        }}>
          <div style={{ width: 1, height: 60, background: 'linear-gradient(to bottom, transparent, rgba(255,255,255,0.4))' }} />
          <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.35)', writingMode: 'vertical-rl', textTransform: 'uppercase' }}>SCROLL</span>
        </div>
      </section>

      {/* TICKER — white bg, bold black text */}
      <div style={{
        borderTop: '1px solid #fff',
        borderBottom: '1px solid #fff',
        padding: '0',
        background: '#fff',
        overflow: 'hidden',
      }}>
        <div className="ticker-track" style={{ gap: 0 }}>
          {TICKER_ITEMS.map((item, i) => (
            <React.Fragment key={i}>
              <span style={{
                fontSize: 11, fontWeight: 900, letterSpacing: '0.25em',
                color: '#000', textTransform: 'uppercase',
                padding: '14px 24px', whiteSpace: 'nowrap',
                display: 'inline-block',
              }}>
                {item}
              </span>
              <span style={{ color: 'rgba(0,0,0,0.35)', fontSize: 14, padding: '14px 4px', display: 'inline-block' }}>—</span>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* HOW IT WORKS */}
      <section id="how" style={{ padding: '100px 40px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 64 }}>
            <div className="section-eyebrow" style={{ marginBottom: 20 }}>HOW IT WORKS</div>
            <h2 style={{
              fontWeight: 900,
              fontSize: 'clamp(36px, 5vw, 72px)',
              letterSpacing: '-0.03em',
              textTransform: 'uppercase',
              lineHeight: 0.95,
              maxWidth: 700,
            }}>
              FROM RAW INBOX<br />
              <span style={{ color: 'rgba(255,255,255,0.25)', WebkitTextStroke: '1px rgba(255,255,255,0.25)' }}>TO RANKED</span><br />
              INTELLIGENCE
            </h2>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 0,
            border: '1px solid rgba(255,255,255,0.15)',
          }}>
            {HOW_STEPS.map((step, i) => (
              <div
                key={i}
                className="step-card"
                onMouseEnter={() => setHoveredStep(i)}
                onMouseLeave={() => setHoveredStep(null)}
                style={{
                  padding: '40px 36px',
                  borderRight: (i % 3 !== 2) ? '1px solid rgba(255,255,255,0.12)' : 'none',
                  borderBottom: i < 3 ? '1px solid rgba(255,255,255,0.12)' : 'none',
                  position: 'relative',
                  cursor: 'default',
                  overflow: 'hidden',
                }}
              >
                {/* Hover reveal bg */}
                <div style={{
                  position: 'absolute', inset: 0,
                  background: 'rgba(255,255,255,0.04)',
                  opacity: hoveredStep === i ? 1 : 0,
                  transition: 'opacity 0.2s',
                  pointerEvents: 'none',
                }} />

                {/* Step number */}
                <div style={{
                  position: 'absolute', top: 20, right: 24,
                  fontSize: 36, fontWeight: 900, letterSpacing: '-0.04em',
                  color: hoveredStep === i ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)',
                  fontFamily: 'monospace',
                  transition: 'color 0.3s, font-size 0.3s',
                  lineHeight: 1,
                }}>
                  {step.num}
                </div>

                {/* Icon */}
                <div style={{
                  width: 44, height: 44,
                  border: `1px solid ${hoveredStep === i ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.25)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 24,
                  background: hoveredStep === i ? 'rgba(255,255,255,0.07)' : 'transparent',
                  transition: 'border-color 0.2s, background 0.2s',
                }}>
                  <span className="ms" style={{ fontSize: 20, color: hoveredStep === i ? '#fff' : 'rgba(255,255,255,0.65)' }}>{step.icon}</span>
                </div>

                <h3 style={{
                  fontWeight: 900, fontSize: 13, letterSpacing: '0.1em',
                  textTransform: 'uppercase', marginBottom: 12, lineHeight: 1.3,
                  color: hoveredStep === i ? '#fff' : 'rgba(255,255,255,0.9)',
                  transition: 'color 0.2s',
                }}>
                  {step.title}
                </h3>
                <p style={{
                  fontSize: 13, lineHeight: 1.75,
                  color: hoveredStep === i ? 'rgba(255,255,255,0.65)' : 'rgba(255,255,255,0.4)',
                  fontWeight: 400, transition: 'color 0.2s',
                }}>
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VISUAL DEMO / SCORING ENGINE */}
      <section style={{
        padding: '100px 40px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: '#080808',
        position: 'relative', overflow: 'hidden',
      }}>
        <div className="dot-grid" style={{ opacity: 0.08 }} />
        <div style={{ maxWidth: 1200, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>
            <div>
              <div className="section-eyebrow" style={{ marginBottom: 20 }}>THE ENGINE</div>
              <h2 style={{
                fontWeight: 900, fontSize: 'clamp(32px, 4vw, 56px)',
                letterSpacing: '-0.03em', textTransform: 'uppercase',
                lineHeight: 0.95, marginBottom: 28,
              }}>
                SCORING THAT<br />
                <span style={{ color: 'rgba(255,255,255,0.25)', WebkitTextStroke: '1px rgba(255,255,255,0.2)' }}>NEVER</span><br />
                GUESSES
              </h2>
              <p style={{ fontSize: 14, lineHeight: 1.8, color: 'rgba(255,255,255,0.55)', marginBottom: 32 }}>
                Six deterministic dimensions. Each opportunity is evaluated against your exact profile vector.
                The result is a score out of 105 — no black box, full reasoning visible.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  ['RELEVANCE', 20], ['DEADLINE URGENCY', 18], ['CREDIBILITY', 17],
                  ['PROFILE ALIGNMENT', 20], ['EFFORT:REWARD', 15], ['FINANCIAL FIT', 15],
                ].map(([label, max], i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.5)', width: 130, textTransform: 'uppercase', flexShrink: 0 }}>{label}</span>
                    <div className="dim-bar-track" style={{ flex: 1 }}>
                      <div className="dim-bar-fill" style={{
                        width: `${(max / 20) * 100}%`,
                        animationDelay: `${i * 0.1}s`,
                      }} />
                    </div>
                    <span style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.5)', width: 24, textAlign: 'right' }}>/{max}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Sample card */}
            <div className="float-anim" style={{ border: '1px solid rgba(255,255,255,0.2)', boxShadow: '0 24px 80px rgba(0,0,0,0.8)' }}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.12)', background: '#131313', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.2em', color: 'rgba(255,255,255,0.45)', fontFamily: 'monospace' }}>SAMPLE // OPP-001</span>
                <span className="badge high">HIGH</span>
              </div>
              <div style={{ padding: '24px 20px', background: '#0e0e0e' }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 8 }}>INTERNSHIP — TECH SECTOR</div>
                <div style={{ fontWeight: 900, fontSize: 16, letterSpacing: '-0.01em', textTransform: 'uppercase', marginBottom: 4 }}>SOFTWARE ENGINEERING INTERN</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginBottom: 20 }}>Acme Corp. — Lahore, Pakistan</div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 20 }}>
                  <div>
                    <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', marginBottom: 4 }}>DEADLINE</div>
                    <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', color: '#fff' }}>2025-05-15</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase' }}>SCORE</div>
                    <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1 }}>
                      87<span style={{ fontSize: 14, color: 'rgba(255,255,255,0.3)' }}>/105</span>
                    </div>
                  </div>
                </div>

                <div style={{ height: 3, background: 'rgba(255,255,255,0.1)', marginBottom: 20, overflow: 'hidden' }}>
                  <div className="score-bar-animated" style={{ width: '83%', height: '100%', background: '#fff' }} />
                </div>

                <div style={{ display: 'flex', gap: 6 }}>
                  {['Python', 'AWS', 'React'].map(s => (
                    <span key={s} className="chip filled" style={{ fontSize: 9 }}>{s}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section id="benefits" style={{ padding: '100px 40px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 80, alignItems: 'start' }}>
            <div style={{ position: 'sticky', top: 100 }}>
              <div className="section-eyebrow" style={{ marginBottom: 20 }}>BENEFITS</div>
              <h2 style={{
                fontWeight: 900, fontSize: 'clamp(40px, 5vw, 64px)',
                letterSpacing: '-0.03em', textTransform: 'uppercase',
                lineHeight: 0.95, marginBottom: 28,
              }}>
                BUILT<br />
                FOR THE<br />
                <span style={{ color: 'rgba(255,255,255,0.25)', WebkitTextStroke: '1px rgba(255,255,255,0.2)' }}>SERIOUS</span><br />
                STUDENT
              </h2>
              <p style={{ fontSize: 13, lineHeight: 1.75, color: 'rgba(255,255,255,0.5)' }}>
                Stop manually trawling through 200 emails hoping you didn't miss the deadline that mattered.
                Inbox Copilot handles all of it.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, border: '1px solid rgba(255,255,255,0.15)' }}>
              {BENEFITS.map((b, i) => (
                <div key={i} className="benefit-row" style={{
                  padding: '32px 36px',
                  borderBottom: i < BENEFITS.length - 1 ? '1px solid rgba(255,255,255,0.08)' : 'none',
                  display: 'flex', gap: 24, alignItems: 'flex-start',
                }}>
                  <div style={{
                    width: 40, height: 40, flexShrink: 0,
                    border: '1px solid rgba(255,255,255,0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginTop: 2,
                    transition: 'background 0.2s, border-color 0.2s',
                  }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.borderColor = '#fff'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)'; }}
                  >
                    <span className="ms" style={{ fontSize: 18, color: 'rgba(255,255,255,0.75)' }}>{b.icon}</span>
                  </div>
                  <div>
                    <h3 style={{ fontWeight: 900, fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8, color: '#fff' }}>
                      {b.title}
                    </h3>
                    <p style={{ fontSize: 13, lineHeight: 1.75, color: 'rgba(255,255,255,0.5)', fontWeight: 400 }}>
                      {b.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section style={{
        padding: '120px 40px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        position: 'relative', overflow: 'hidden',
        background: '#050505',
      }}>
        <div className="dot-grid" style={{ opacity: 0.07 }} />
        {/* Large faded background text */}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none', overflow: 'hidden',
        }}>
          <span style={{
            fontSize: 'clamp(100px, 20vw, 260px)',
            fontWeight: 900, letterSpacing: '-0.06em',
            color: 'rgba(255,255,255,0.025)',
            textTransform: 'uppercase',
            whiteSpace: 'nowrap',
            userSelect: 'none',
          }}>EXECUTE</span>
        </div>

        <div style={{ maxWidth: 900, margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div className="section-eyebrow" style={{ justifyContent: 'center', marginBottom: 28 }}>READY TO EXECUTE</div>
          <h2 style={{
            fontWeight: 900, fontSize: 'clamp(52px, 9vw, 120px)',
            letterSpacing: '-0.04em', textTransform: 'uppercase',
            lineHeight: 0.9, marginBottom: 48,
          }}>
            STOP MISSING<br />
            OPPORTUNITIES
          </h2>
          <p style={{ fontSize: 16, color: 'rgba(255,255,255,0.55)', marginBottom: 48, lineHeight: 1.7, maxWidth: 500, margin: '0 auto 48px' }}>
            Join students who've replaced inbox chaos with a ranked, actionable opportunity stream. Zero setup. Instant results.
          </p>
          <button className="btn-primary" onClick={() => navigate('/auth')} style={{ fontSize: 13, padding: '20px 56px' }}>
            <span className="ms" style={{ color: '#000', fontSize: 20 }}>barcode_scanner</span>
            LAUNCH INBOX COPILOT
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{
        padding: '40px 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderTop: '1px solid rgba(255,255,255,0.1)',
      }}>
        <div style={{ fontWeight: 900, fontSize: 14, letterSpacing: '0.2em', textTransform: 'uppercase' }}>
          INBOX COPILOT
        </div>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase' }}>
          V.01 // OPPORTUNITY INTELLIGENCE ENGINE
        </div>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="pulse-dot" style={{ width: 5, height: 5 }} />
          SYS: NOMINAL
        </div>
      </footer>
    </div>
  );
}
