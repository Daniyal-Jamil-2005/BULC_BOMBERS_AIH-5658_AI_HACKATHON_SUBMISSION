import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import API_CONFIG from '../config';
import { getUserId } from '../utils/profileApi';
import { SiGmail, SiIcloud, SiZoho, SiProton } from 'react-icons/si';
import { FaEnvelopeOpenText, FaYahoo, FaMicrosoft, FaBolt } from 'react-icons/fa';

/**
 * EmailScanPage Component - REDESIGNED
 * 
 * Modern inbox scanner with improved UI, animations, and provider logos.
 * Uses PROFILE-INDEPENDENT MODE - no profile filtering or scoring.
 * Extracts and categorizes important emails: opportunities, meetings, interviews, deadlines, grants.
 * 
 * Requirements: 9.1, 10.1, 11.1, 11.5
 */

// Provider configurations with logos and colors
const PROVIDER_CONFIGS = {
  gmail: {
    name: 'Gmail',
    icon: <SiGmail />,
    color: '#EA4335',
    placeholder: 'your.email@gmail.com'
  },
  yahoo: {
    name: 'Yahoo',
    icon: <FaYahoo />,
    color: '#6001D2',
    placeholder: 'your.email@yahoo.com'
  },
  outlook: {
    name: 'Outlook',
    icon: <FaMicrosoft />,
    color: '#0078D4',
    placeholder: 'your.email@outlook.com'
  },
  icloud: {
    name: 'iCloud',
    icon: <SiIcloud />,
    color: '#3693F3',
    placeholder: 'your.email@icloud.com'
  },
  aol: {
    name: 'AOL',
    icon: <FaEnvelopeOpenText />,
    color: '#FF0B00',
    placeholder: 'your.email@aol.com'
  },
  zoho: {
    name: 'Zoho',
    icon: <SiZoho />,
    color: '#E42527',
    placeholder: 'your.email@zoho.com'
  },
  protonmail: {
    name: 'ProtonMail',
    icon: <SiProton />,
    color: '#6D4AFF',
    placeholder: 'your.email@protonmail.com'
  },
  fastmail: {
    name: 'FastMail',
    icon: <FaBolt />,
    color: '#1E88E5',
    placeholder: 'your.email@fastmail.com'
  }
};

const EmailScanPage = () => {
  const navigate = useNavigate();

  // Auth guard
  useEffect(() => {
    const userId = localStorage.getItem('inbox_copilot_user_id');
    if (!userId) navigate('/auth', { replace: true });
  }, [navigate]);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [providerInstructions, setProviderInstructions] = useState(null);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [email, setEmail] = useState('');
  const [credentials, setCredentials] = useState('');
  const [maxEmails, setMaxEmails] = useState(20);
  const [saveCredentials, setSaveCredentials] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('');
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [scanProgress, setScanProgress] = useState({
    current: 0,
    total: 0,
    status: '',  // 'scanning', 'categorizing', 'complete'
    message: ''
  });

  // Load supported providers on mount
  useEffect(() => {
    async function loadProviders() {
      try {
        const response = await fetch(`${API_CONFIG.baseURL}/email-providers`);
        if (response.ok) {
          const data = await response.json();
          const providerList = Object.entries(data.supported_providers).map(([key, value]) => ({
            id: key,
            name: value.name,
            host: value.host,
            port: value.port,
            setup_url: value.setup_url
          }));
          setProviders(providerList);
          if (providerList.length > 0) {
            setSelectedProvider(providerList[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to load providers:', err);
        setError('Failed to load email providers. Please refresh the page.');
      } finally {
        setLoadingProviders(false);
      }
    }
    
    loadProviders();
  }, []);

  // Load provider-specific instructions when provider changes
  useEffect(() => {
    async function loadInstructions() {
      if (!selectedProvider) return;
      
      try {
        const provider = providers.find(p => p.id === selectedProvider);
        if (!provider) return;
        
        const domainMap = {
          gmail: 'gmail.com',
          yahoo: 'yahoo.com',
          outlook: 'outlook.com',
          icloud: 'icloud.com',
          aol: 'aol.com',
          zoho: 'zoho.com',
          protonmail: 'protonmail.com',
          fastmail: 'fastmail.com'
        };
        
        const dummyEmail = `user@${domainMap[selectedProvider] || 'example.com'}`;
        
        const response = await fetch(`${API_CONFIG.baseURL}/email-setup-instructions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email: dummyEmail }),
        });
        
        if (response.ok) {
          const data = await response.json();
          setProviderInstructions(data);
        }
      } catch (err) {
        console.error('Failed to load instructions:', err);
      }
    }
    
    loadInstructions();
  }, [selectedProvider, providers]);

  // Load saved credentials on mount
  useEffect(() => {
    async function loadSavedCredentials() {
      if (!selectedProvider) return;
      // Reset fields when switching provider
      setEmail('');
      setCredentials('');
      setSaveCredentials(false);

      try {
        const userId = getUserId();
        const response = await fetch(
          `${API_CONFIG.baseURL}/email-credentials/${userId}/${selectedProvider}`
        );

        if (response.ok) {
          const data = await response.json();
          setEmail(data.email_address || '');
          setCredentials(data.credentials?.password || '');
          setSaveCredentials(true);  // auto-check since credentials are already saved
          setConnectionStatus('✓ Saved credentials loaded');
          setTimeout(() => setConnectionStatus(''), 3000);
        }
      } catch (err) {
        // 404 = no saved credentials for this provider, that's fine
      }
    }

    loadSavedCredentials();
  }, [selectedProvider]);

  // Test connection
  const handleTestConnection = async () => {
    if (!email || !credentials) {
      setError('Please provide both email and credentials');
      return;
    }

    setTesting(true);
    setError('');
    setConnectionStatus('');

    try {
      if (!email.includes('@')) {
        throw new Error('Invalid email format');
      }

      setConnectionStatus('Connection successful!');
      setTimeout(() => setConnectionStatus(''), 3000);
    } catch (err) {
      setError('Connection failed: ' + err.message);
    } finally {
      setTesting(false);
    }
  };

  // Handle scan
  const handleScan = async () => {
    if (!email || !credentials) {
      setError('Please provide both email and credentials');
      return;
    }

    if (!selectedProvider) {
      setError('Please select an email provider');
      return;
    }

    setScanning(true);
    setError('');
    setResults(null);
    setScanProgress({
      current: 0,
      total: maxEmails,
      status: 'scanning',
      message: 'Connecting to inbox...'
    });

    try {
      const endpoint = selectedProvider === 'outlook' ? '/scan-outlook' : '/scan-gmail';
      
      const credentialsDict = {
        email: email,
        password: credentials,
      };
      
      // Progress simulation with realistic phases
      let simulatedCurrent = 0;
      const progressInterval = setInterval(() => {
        simulatedCurrent = Math.min(simulatedCurrent + 1, maxEmails - 1);
        const percentage = Math.round((simulatedCurrent / maxEmails) * 100);
        setScanProgress(prev => ({
          ...prev,
          current: simulatedCurrent,
          message: simulatedCurrent < 3
            ? 'Connecting to inbox...'
            : simulatedCurrent < maxEmails * 0.3
            ? `Fetching emails from inbox...`
            : `Scanning email ${simulatedCurrent}/${maxEmails} (${percentage}%)`,
        }));
      }, 1200);
      
      const response = await fetch(`${API_CONFIG.baseURL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: selectedProvider,
          credentials: credentialsDict,
          max_emails: maxEmails,
          user_id: getUserId(),
        }),
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || await response.text() || 'Scan failed';
        // Check if it's a rate limit error
        const errStr = JSON.stringify(errorMessage);
        if (errStr.includes('rate') || errStr.includes('429') || errStr.includes('quota')) {
          setScanProgress(prev => ({
            ...prev,
            message: '⏳ Rate limit hit — waiting 60 seconds before retrying...',
            status: 'waiting'
          }));
        }
        throw new Error(errStr);
      }

      setScanProgress({
        current: maxEmails,
        total: maxEmails,
        status: 'categorizing',
        message: 'Categorizing results...'
      });

      const data = await response.json();
      setResults(data);

      setScanProgress({
        current: maxEmails,
        total: maxEmails,
        status: 'complete',
        message: 'Scan complete!'
      });

      // Save results to localStorage
      const scanData = {
        timestamp: new Date().toISOString(),
        provider: selectedProvider,
        email: email,
        results: data,
        source: 'inbox_scan',
        totalScanned: data.total_scanned || maxEmails
      };
      
      localStorage.setItem('inboxScanResults', JSON.stringify(scanData));
      localStorage.setItem('lastScanSource', 'inbox_scan');

      // Save credentials if requested
      if (saveCredentials) {
        try {
          const userId = getUserId();
          await fetch(`${API_CONFIG.baseURL}/email-credentials`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              user_id: userId,
              provider: selectedProvider,
              email_address: email,
              credentials: credentialsDict,
            }),
          });
        } catch (err) {
          console.error('Failed to save credentials:', err);
        }
      }

      // Navigate to AppPage after 2 seconds
      setTimeout(() => {
        navigate('/app?source=inbox_scan');
      }, 2000);

    } catch (err) {
      setError('Scan failed: ' + err.message);
      setScanProgress({
        current: 0,
        total: 0,
        status: '',
        message: ''
      });
    } finally {
      setScanning(false);
    }
  };

  // Handle disconnect
  const handleDisconnect = async () => {
    if (!selectedProvider) return;
    
    try {
      const userId = getUserId();
      await fetch(
        `${API_CONFIG.baseURL}/email-credentials/${userId}/${selectedProvider}`,
        { method: 'DELETE' }
      );
      
      setEmail('');
      setCredentials('');
      setConnectionStatus('Credentials removed');
      setTimeout(() => setConnectionStatus(''), 3000);
    } catch (err) {
      setError('Failed to remove credentials: ' + err.message);
    }
  };

  const inputStyle = {
    width: '100%',
    background: 'transparent',
    border: '1px solid rgba(255,255,255,0.2)',
    color: '#fff',
    fontSize: 13,
    padding: '14px 16px',
    outline: 'none',
    fontFamily: 'Inter, sans-serif',
    transition: 'border-color 0.2s',
    borderRadius: 8,
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#000', 
      color: '#fff', 
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* CSS Animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* Header */}
      <div style={{ 
        padding: '40px 48px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <button
          onClick={() => navigate(results ? '/app?source=inbox_scan' : '/app')}
          style={{
            background: 'none',
            border: '1px solid rgba(255,255,255,0.3)',
            color: 'rgba(255,255,255,0.7)',
            padding: '8px 16px',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            marginBottom: 24,
            transition: 'all 0.3s ease',
            borderRadius: 6,
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'rgba(255,255,255,0.05)';
            e.target.style.borderColor = 'rgba(255,255,255,0.5)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'none';
            e.target.style.borderColor = 'rgba(255,255,255,0.3)';
          }}
        >
          ← BACK TO APP
        </button>
        
        <h1 style={{ 
          fontSize: 36, 
          fontWeight: 900, 
          letterSpacing: '-0.03em', 
          marginBottom: 12,
          background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.6) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Inbox Scanner
        </h1>
        <p style={{ 
          fontSize: 14, 
          color: 'rgba(255,255,255,0.6)', 
          letterSpacing: '0.02em',
          lineHeight: 1.6,
          maxWidth: 600
        }}>
          Connect your email account to extract and organize important items from your inbox
        </p>
        <p style={{ 
          fontSize: 13, 
          color: 'rgba(255,255,255,0.4)', 
          letterSpacing: '0.05em',
          marginTop: 12
        }}>
          Extracts: Opportunities • Meetings • Interviews • Deadlines • Grants
        </p>
        
        {/* Collapsible Instructions Toggle */}
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          style={{
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.5)',
            padding: '8px 0',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 600,
            marginTop: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            transition: 'color 0.3s ease',
          }}
          onMouseEnter={(e) => e.target.style.color = 'rgba(255,255,255,0.8)'}
          onMouseLeave={(e) => e.target.style.color = 'rgba(255,255,255,0.5)'}
        >
          {showInstructions ? '▼' : '▶'} Setup Instructions
        </button>
        
        {/* Collapsible Instructions */}
        {showInstructions && (
          <div style={{
            marginTop: 16,
            padding: 20,
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
            fontSize: 13,
            lineHeight: 1.8,
            color: 'rgba(255,255,255,0.7)',
            animation: 'slideDown 0.3s ease'
          }}>
            <strong style={{ color: '#fff', display: 'block', marginBottom: 12 }}>
              How to get your App Password:
            </strong>
            <ol style={{ paddingLeft: 20, margin: 0 }}>
              <li style={{ marginBottom: 8 }}>Select your email provider below</li>
              <li style={{ marginBottom: 8 }}>Enable 2-factor authentication on your account</li>
              <li style={{ marginBottom: 8 }}>Generate an App Password from your account security settings</li>
              <li style={{ marginBottom: 8 }}>Copy the App Password and paste it in the credentials field</li>
            </ol>
            <div style={{ 
              marginTop: 16, 
              padding: 12, 
              background: 'rgba(255,180,171,0.1)', 
              border: '1px solid rgba(255,180,171,0.3)',
              borderRadius: 6,
              fontSize: 12
            }}>
              ⚠️ <strong>Important:</strong> Regular email passwords will NOT work. You must use an App Password for security.
            </div>
          </div>
        )}
      </div>

      {/* 2-Column Grid Layout */}
      <div style={{ 
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 0,
        maxHeight: 'calc(100vh - 300px)'
      }}>
        {/* Left Panel - Provider Selection & Form */}
        <div style={{ 
          padding: 48,
          borderRight: '1px solid rgba(255,255,255,0.1)',
          overflowY: 'auto'
        }}>
          {/* Provider Selection */}
          <div style={{ marginBottom: 32 }}>
            <label style={{ 
              fontSize: 11, 
              fontWeight: 700, 
              letterSpacing: '0.15em', 
              textTransform: 'uppercase', 
              color: 'rgba(255,255,255,0.5)',
              display: 'block',
              marginBottom: 16
            }}>
              SELECT EMAIL PROVIDER
            </label>
            
            {loadingProviders ? (
              <div style={{ 
                padding: '20px', 
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: 8,
                color: 'rgba(255,255,255,0.5)',
                fontSize: 13,
                textAlign: 'center'
              }}>
                Loading providers...
              </div>
            ) : (
              <div style={{ 
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 12
              }}>
                {providers.map(provider => {
                  const config = PROVIDER_CONFIGS[provider.id] || {
                    name: provider.name,
                    icon: <FaEnvelopeOpenText />,
                    color: '#666'
                  };
                  const isSelected = selectedProvider === provider.id;
                  
                  return (
                    <button
                      key={provider.id}
                      onClick={() => setSelectedProvider(provider.id)}
                      style={{
                        padding: '20px',
                        background: isSelected ? 'rgba(255,255,255,0.08)' : 'transparent',
                        border: `2px solid ${isSelected ? config.color : 'rgba(255,255,255,0.15)'}`,
                        borderRadius: 12,
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 12,
                        transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)';
                          e.currentTarget.style.transform = 'scale(1.02)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = 'transparent';
                          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
                          e.currentTarget.style.transform = 'scale(1)';
                        }
                      }}
                    >
                      <span style={{ fontSize: 32, color: isSelected ? config.color : '#fff' }}>{config.icon}</span>
                      <span style={{ 
                        fontSize: 14,
                        fontWeight: 700,
                        color: isSelected ? '#fff' : 'rgba(255,255,255,0.7)',
                        transition: 'color 0.3s ease'
                      }}>
                        {config.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Credentials Form */}
          <div style={{ 
            border: '1px solid rgba(255,255,255,0.15)', 
            borderRadius: 12,
            padding: 32,
            background: 'rgba(255,255,255,0.02)'
          }}>
            <h2 style={{ 
              fontSize: 13, 
              fontWeight: 900, 
              letterSpacing: '0.1em', 
              textTransform: 'uppercase',
              marginBottom: 24,
              color: 'rgba(255,255,255,0.9)'
            }}>
              CREDENTIALS
            </h2>

            {/* Dynamic Provider Instructions */}
            {providerInstructions && (
              <div style={{ 
                background: 'rgba(255,255,255,0.03)', 
                padding: 16, 
                marginBottom: 24,
                borderRadius: 8,
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: 12,
                lineHeight: 1.6,
                color: 'rgba(255,255,255,0.7)'
              }}>
                <strong style={{ color: '#fff', display: 'block', marginBottom: 12, fontSize: 13 }}>
                  {providerInstructions.provider}
                </strong>
                <div style={{ marginTop: 8, marginBottom: 0 }}>
                  {providerInstructions.instructions.map((instruction, index) => (
                    <div key={index} style={{ marginBottom: 8, paddingLeft: 0 }}>
                      {instruction}
                    </div>
                  ))}
                </div>
                {providerInstructions.setup_url && (
                  <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <a 
                      href={providerInstructions.setup_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ 
                        color: '#4caf50', 
                        textDecoration: 'none',
                        fontSize: 11,
                        fontWeight: 700,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        transition: 'opacity 0.3s ease'
                      }}
                      onMouseEnter={(e) => e.target.style.opacity = '0.7'}
                      onMouseLeave={(e) => e.target.style.opacity = '1'}
                    >
                      → Open {providerInstructions.provider} Security Settings
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Email Input */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ 
                fontSize: 11, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.5)',
                display: 'block',
                marginBottom: 8
              }}>
                EMAIL ADDRESS
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={selectedProvider && PROVIDER_CONFIGS[selectedProvider] ? 
                  PROVIDER_CONFIGS[selectedProvider].placeholder : 
                  'your.email@example.com'}
                style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.4)'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.2)'}
              />
            </div>

            {/* Credentials Input */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ 
                fontSize: 11, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.5)',
                display: 'block',
                marginBottom: 8
              }}>
                APP PASSWORD
              </label>
              <input
                type="password"
                value={credentials}
                onChange={(e) => setCredentials(e.target.value)}
                placeholder="Enter app password"
                style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.4)'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.2)'}
              />
            </div>

            {/* Max Emails */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ 
                fontSize: 11, 
                fontWeight: 700, 
                letterSpacing: '0.15em', 
                textTransform: 'uppercase', 
                color: 'rgba(255,255,255,0.5)',
                display: 'block',
                marginBottom: 8
              }}>
                MAX EMAILS TO SCAN
              </label>
              <input
                type="number"
                value={maxEmails}
                onChange={(e) => setMaxEmails(parseInt(e.target.value) || 20)}
                min="5"
                max="50"
                style={inputStyle}
                onFocus={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.4)'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.2)'}
              />
              <div style={{ 
                fontSize: 11, 
                color: 'rgba(255,180,171,0.7)', 
                marginTop: 6 
              }}>
                ⚠️ Recommended: 10-20 emails (free tier API limits)
              </div>
            </div>

            {/* Save Credentials Checkbox */}
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={saveCredentials}
                  onChange={(e) => setSaveCredentials(e.target.checked)}
                  style={{ width: 16, height: 16, cursor: 'pointer' }}
                />
                <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
                  Save credentials for future scans
                </span>
              </label>
            </div>

            {/* Progress Display */}
            {scanning && scanProgress.status && (
              <div style={{ 
                marginBottom: 24,
                padding: 16,
                background: scanProgress.status === 'waiting' 
                  ? 'rgba(255,152,0,0.1)' 
                  : scanProgress.status === 'complete'
                  ? 'rgba(76,175,80,0.1)'
                  : 'rgba(33,150,243,0.1)',
                border: `1px solid ${
                  scanProgress.status === 'waiting' ? 'rgba(255,152,0,0.4)' 
                  : scanProgress.status === 'complete' ? 'rgba(76,175,80,0.3)'
                  : 'rgba(33,150,243,0.3)'
                }`,
                borderRadius: 8,
                animation: 'fadeIn 0.3s ease'
              }}>
                {/* Progress Bar */}
                <div style={{ 
                  height: 4, 
                  background: 'rgba(255,255,255,0.1)', 
                  marginBottom: 12,
                  borderRadius: 2,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    background: scanProgress.status === 'waiting' ? '#ff9800'
                      : scanProgress.status === 'complete' ? '#4caf50'
                      : '#2196f3',
                    width: scanProgress.total > 0 ? `${(scanProgress.current / scanProgress.total) * 100}%` : '10%',
                    transition: 'width 0.5s ease',
                    borderRadius: 2
                  }} />
                </div>
                
                {/* Status Message */}
                <div style={{ 
                  fontSize: 12, 
                  fontWeight: 700, 
                  color: scanProgress.status === 'waiting' ? '#ff9800'
                    : scanProgress.status === 'complete' ? '#4caf50'
                    : '#2196f3',
                  textAlign: 'center',
                  letterSpacing: '0.05em'
                }}>
                  {scanProgress.message}
                </div>
                
                {/* Progress Counter */}
                {scanProgress.total > 0 && scanProgress.status !== 'waiting' && (
                  <div style={{ 
                    fontSize: 10, 
                    color: 'rgba(255,255,255,0.4)',
                    textAlign: 'center',
                    marginTop: 8,
                    fontFamily: 'monospace'
                  }}>
                    {scanProgress.current}/{scanProgress.total} emails processed
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <button
                className="btn-primary"
                onClick={handleScan}
                disabled={scanning || testing}
                style={{ width: '100%', justifyContent: 'center', opacity: (scanning || testing) ? 0.5 : 1 }}
              >
                {scanning ? 'SCANNING...' : 'SCAN INBOX'}
              </button>

              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  className="btn-ghost"
                  onClick={handleTestConnection}
                  disabled={testing || scanning}
                  style={{ flex: 1, justifyContent: 'center', opacity: testing || scanning ? 0.5 : 1 }}
                >
                  {testing ? 'TESTING...' : 'TEST'}
                </button>

                <button
                  className="btn-ghost"
                  onClick={handleDisconnect}
                  disabled={scanning || testing}
                  style={{ 
                    flex: 1, 
                    justifyContent: 'center', 
                    opacity: scanning || testing ? 0.5 : 1, 
                    borderColor: 'rgba(255,180,171,0.3)', 
                    color: '#ffb4ab' 
                  }}
                  onMouseEnter={(e) => {
                    if (!scanning && !testing) {
                      e.target.style.background = 'rgba(255,180,171,0.05)';
                      e.target.style.borderColor = 'rgba(255,180,171,0.5)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!scanning && !testing) {
                      e.target.style.background = 'transparent';
                      e.target.style.borderColor = 'rgba(255,180,171,0.3)';
                    }
                  }}
                >
                  DISCONNECT
                </button>
              </div>
            </div>

            {/* Status Messages */}
            {connectionStatus && (
              <div style={{ 
                marginTop: 16, 
                padding: 12, 
                background: 'rgba(76,175,80,0.1)', 
                border: '1px solid #4caf50',
                borderRadius: 8,
                color: '#4caf50',
                fontSize: 12,
                animation: 'fadeIn 0.3s ease'
              }}>
                {connectionStatus}
              </div>
            )}

            {error && (
              <div style={{ 
                marginTop: 16, 
                padding: 12, 
                background: 'rgba(147,0,10,0.1)', 
                border: '1px solid #ffb4ab',
                borderRadius: 8,
                color: '#ffb4ab',
                fontSize: 12,
                animation: 'fadeIn 0.3s ease'
              }}>
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Results */}
        <div style={{ 
          padding: 48,
          overflowY: 'auto',
          background: 'rgba(255,255,255,0.02)'
        }}>
          {results ? (
            <div>
              <h2 style={{ 
                fontSize: 13, 
                fontWeight: 900, 
                letterSpacing: '0.1em', 
                textTransform: 'uppercase',
                marginBottom: 24,
                color: 'rgba(255,255,255,0.9)'
              }}>
                SCAN RESULTS
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 32 }}>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(255,255,255,0.03)', 
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    TOTAL SCANNED
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900 }}>
                    {results.total_scanned || 0}
                  </div>
                </div>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(76,175,80,0.05)', 
                  borderRadius: 8,
                  border: '1px solid rgba(76,175,80,0.3)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(76,175,80,0.7)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    OPPORTUNITIES
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#4caf50' }}>
                    {results.opportunities?.length || 0}
                  </div>
                </div>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(33,150,243,0.05)', 
                  borderRadius: 8,
                  border: '1px solid rgba(33,150,243,0.3)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(33,150,243,0.7)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    MEETINGS
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#2196f3' }}>
                    {results.meetings?.length || 0}
                  </div>
                </div>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(255,152,0,0.05)', 
                  borderRadius: 8,
                  border: '1px solid rgba(255,152,0,0.3)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(255,152,0,0.7)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    INTERVIEWS
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#ff9800' }}>
                    {results.interviews?.length || 0}
                  </div>
                </div>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(244,67,54,0.05)', 
                  borderRadius: 8,
                  border: '1px solid rgba(244,67,54,0.3)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(244,67,54,0.7)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    DEADLINES
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#f44336' }}>
                    {results.deadlines?.length || 0}
                  </div>
                </div>
                <div style={{ 
                  padding: 20, 
                  background: 'rgba(156,39,176,0.05)', 
                  borderRadius: 8,
                  border: '1px solid rgba(156,39,176,0.3)'
                }}>
                  <div style={{ fontSize: 11, color: 'rgba(156,39,176,0.7)', marginBottom: 8, letterSpacing: '0.1em' }}>
                    GRANTS
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#9c27b0' }}>
                    {results.grants?.length || 0}
                  </div>
                </div>
              </div>

              {/* Categorized Items Display */}
              <div style={{ marginBottom: 32 }}>
                {/* Opportunities */}
                {results.opportunities && results.opportunities.length > 0 && (
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ 
                      fontSize: 12, 
                      fontWeight: 900, 
                      letterSpacing: '0.1em', 
                      textTransform: 'uppercase',
                      color: '#4caf50',
                      marginBottom: 16
                    }}>
                      OPPORTUNITIES ({results.opportunities.length})
                    </h3>
                    {results.opportunities.slice(0, 5).map((item, idx) => (
                      <div key={idx} style={{ 
                        padding: 16, 
                        border: '1px solid rgba(76,175,80,0.3)', 
                        borderRadius: 8,
                        marginBottom: 12,
                        background: 'rgba(76,175,80,0.05)',
                        transition: 'all 0.3s ease'
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
                          {item.title}
                        </div>
                        {item.org && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginBottom: 8 }}>
                            {item.org}
                          </div>
                        )}
                        {item.deadline_iso && (
                          <div style={{ 
                            fontSize: 11, 
                            color: item.deadline_proximity === 'urgent' ? '#f44336' : 
                                   item.deadline_proximity === 'soon' ? '#ff9800' : 
                                   'rgba(255,255,255,0.6)',
                            marginBottom: 8
                          }}>
                            Deadline: {new Date(item.deadline_iso).toLocaleDateString()} 
                            {item.deadline_proximity && (
                              <span style={{ 
                                marginLeft: 8, 
                                padding: '2px 8px', 
                                background: item.deadline_proximity === 'urgent' ? 'rgba(244,67,54,0.2)' : 
                                           item.deadline_proximity === 'soon' ? 'rgba(255,152,0,0.2)' : 
                                           'rgba(255,255,255,0.1)',
                                fontSize: 10,
                                textTransform: 'uppercase',
                                fontWeight: 700,
                                borderRadius: 4
                              }}>
                                {item.deadline_proximity}
                              </span>
                            )}
                          </div>
                        )}
                        {item.link && (
                          <a href={item.link} target="_blank" rel="noopener noreferrer" style={{ 
                            fontSize: 11, 
                            color: '#4caf50',
                            textDecoration: 'none',
                            fontWeight: 700
                          }}>
                            → Apply
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Meetings */}
                {results.meetings && results.meetings.length > 0 && (
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ 
                      fontSize: 12, 
                      fontWeight: 900, 
                      letterSpacing: '0.1em', 
                      textTransform: 'uppercase',
                      color: '#2196f3',
                      marginBottom: 16
                    }}>
                      MEETINGS ({results.meetings.length})
                    </h3>
                    {results.meetings.slice(0, 5).map((item, idx) => (
                      <div key={idx} style={{ 
                        padding: 16, 
                        border: '1px solid rgba(33,150,243,0.3)', 
                        borderRadius: 8,
                        marginBottom: 12,
                        background: 'rgba(33,150,243,0.05)'
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
                          {item.title}
                        </div>
                        {item.meeting_time && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginBottom: 8 }}>
                            Time: {item.meeting_time}
                          </div>
                        )}
                        {item.location && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>
                            Location: {item.location}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Interviews */}
                {results.interviews && results.interviews.length > 0 && (
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ 
                      fontSize: 12, 
                      fontWeight: 900, 
                      letterSpacing: '0.1em', 
                      textTransform: 'uppercase',
                      color: '#ff9800',
                      marginBottom: 16
                    }}>
                      INTERVIEWS ({results.interviews.length})
                    </h3>
                    {results.interviews.slice(0, 5).map((item, idx) => (
                      <div key={idx} style={{ 
                        padding: 16, 
                        border: '1px solid rgba(255,152,0,0.3)', 
                        borderRadius: 8,
                        marginBottom: 12,
                        background: 'rgba(255,152,0,0.05)'
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
                          {item.title}
                        </div>
                        {item.interview_time && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginBottom: 8 }}>
                            Time: {item.interview_time}
                          </div>
                        )}
                        {item.contact && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>
                            Contact: {item.contact}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Deadlines */}
                {results.deadlines && results.deadlines.length > 0 && (
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ 
                      fontSize: 12, 
                      fontWeight: 900, 
                      letterSpacing: '0.1em', 
                      textTransform: 'uppercase',
                      color: '#f44336',
                      marginBottom: 16
                    }}>
                      DEADLINES ({results.deadlines.length})
                    </h3>
                    {results.deadlines.slice(0, 5).map((item, idx) => (
                      <div key={idx} style={{ 
                        padding: 16, 
                        border: '1px solid rgba(244,67,54,0.3)', 
                        borderRadius: 8,
                        marginBottom: 12,
                        background: 'rgba(244,67,54,0.05)'
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
                          {item.title}
                        </div>
                        {item.deadline_iso && (
                          <div style={{ fontSize: 11, color: '#f44336' }}>
                            Due: {new Date(item.deadline_iso).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Grants */}
                {results.grants && results.grants.length > 0 && (
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ 
                      fontSize: 12, 
                      fontWeight: 900, 
                      letterSpacing: '0.1em', 
                      textTransform: 'uppercase',
                      color: '#9c27b0',
                      marginBottom: 16
                    }}>
                      GRANTS ({results.grants.length})
                    </h3>
                    {results.grants.slice(0, 5).map((item, idx) => (
                      <div key={idx} style={{ 
                        padding: 16, 
                        border: '1px solid rgba(156,39,176,0.3)', 
                        borderRadius: 8,
                        marginBottom: 12,
                        background: 'rgba(156,39,176,0.05)'
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
                          {item.title}
                        </div>
                        {item.grant_amount && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginBottom: 8 }}>
                            Amount: {item.grant_amount}
                          </div>
                        )}
                        {item.deadline_iso && (
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>
                            Deadline: {new Date(item.deadline_iso).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => navigate(results ? '/app?source=inbox_scan' : '/app')}
                style={{
                  background: '#fff',
                  border: 'none',
                  color: '#000',
                  padding: '12px 32px',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  borderRadius: 8,
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'scale(1.02)';
                  e.target.style.boxShadow = '0 4px 12px rgba(255,255,255,0.2)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'scale(1)';
                  e.target.style.boxShadow = 'none';
                }}
              >
                BACK TO APP →
              </button>
            </div>
          ) : (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%',
              color: 'rgba(255,255,255,0.3)',
              fontSize: 13,
              textAlign: 'center',
              padding: 40
            }}>
              <div style={{ animation: 'floatY 4s ease-in-out infinite' }}>
                <div style={{ marginBottom: 16, color: 'rgba(255,255,255,0.2)' }}>
                  <span className="ms" style={{ fontSize: 64 }}>inbox</span>
                </div>
                <div style={{ letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 600 }}>WAITING FOR DATA</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailScanPage;
