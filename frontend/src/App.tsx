import React, { useState, useEffect } from 'react';
import { 
  BrowserRouter, 
  Routes, 
  Route, 
  Navigate, 
  Link, 
  useNavigate, 
  useParams 
} from 'react-router-dom';
import { 
  FolderGit2, 
  Terminal, 
  LogOut, 
  Upload, 
  GitBranch, 
  Trash2, 
  Play, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Download, 
  Activity
} from 'lucide-react';

import { getTokens, setTokens, clearTokens, authApi, repositoryApi, analysisApi, reportApi, dashboardApi } from './services/api';
import type { User, Repository, Analysis, Report, DashboardStats } from './types';

// ==========================================
// CUSTOM MARKDOWN TO HTML PREVIEW RENDERER
// ==========================================
const parseMarkdownToReact = (markdown: string): React.ReactNode => {
  if (!markdown) return null;
  const lines = markdown.split('\n');
  let inList = false;
  let inCode = false;
  let codeBlockContent = '';

  const parsedElements: React.ReactNode[] = [];

  lines.forEach((line, idx) => {
    // Code block close/open
    if (line.trim().startsWith('```')) {
      if (inCode) {
        // Close code block
        parsedElements.push(
          <pre key={`code-${idx}`} style={{
            background: '#151922',
            padding: '16px',
            borderRadius: '8px',
            overflowX: 'auto',
            border: '1px solid rgba(255,255,255,0.08)',
            marginBottom: '16px',
            fontFamily: 'var(--font-mono)'
          }}>
            <code>{codeBlockContent}</code>
          </pre>
        );
        codeBlockContent = '';
        inCode = false;
      } else {
        inCode = true;
      }
      return;
    }

    if (inCode) {
      codeBlockContent += line + '\n';
      return;
    }

    // List item check
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      inList = true;
      const text = line.trim().substring(2);
      parsedElements.push(<li key={`li-${idx}`} style={{ marginLeft: '20px', marginBottom: '8px', color: 'hsl(var(--text-secondary))' }}>{parseInlineFormatting(text)}</li>);
      return;
    } else if (inList && line.trim() === '') {
      inList = false;
    }

    // Alert note check
    if (line.trim().startsWith('> [!NOTE]') || line.trim().startsWith('> [!IMPORTANT]') || line.trim().startsWith('> [!WARNING]')) {
      const type = line.includes('NOTE') ? 'note' : line.includes('WARNING') ? 'warning' : 'important';
      const border = type === 'warning' ? 'hsl(var(--warning))' : type === 'important' ? 'hsl(var(--danger))' : 'hsl(var(--primary))';
      const bg = type === 'warning' ? 'rgba(255, 165, 2, 0.05)' : type === 'important' ? 'rgba(255, 71, 87, 0.05)' : 'rgba(125, 95, 255, 0.05)';
      parsedElements.push(
        <div key={`alert-${idx}`} style={{
          borderLeft: `4px solid ${border}`,
          background: bg,
          padding: '12px 16px',
          borderRadius: '0 8px 8px 0',
          marginBottom: '16px',
          fontSize: '0.9rem'
        }}>
          <strong>{type.toUpperCase()}:</strong> {lines[idx + 1] ? lines[idx + 1].replace('>', '').trim() : ''}
        </div>
      );
      // Skip next line since we embedded it
      lines[idx + 1] = '';
      return;
    }

    if (line.trim() === '') return;

    // Headers
    if (line.startsWith('# ')) {
      parsedElements.push(<h1 key={`h1-${idx}`} style={{ fontSize: '2rem', marginTop: '24px', marginBottom: '16px', borderBottom: '1px solid hsl(var(--border-color))', paddingBottom: '8px' }}>{parseInlineFormatting(line.substring(2))}</h1>);
    } else if (line.startsWith('## ')) {
      parsedElements.push(<h2 key={`h2-${idx}`} style={{ fontSize: '1.5rem', marginTop: '20px', marginBottom: '12px' }}>{parseInlineFormatting(line.substring(3))}</h2>);
    } else if (line.startsWith('### ')) {
      parsedElements.push(<h3 key={`h3-${idx}`} style={{ fontSize: '1.25rem', marginTop: '16px', marginBottom: '8px' }}>{parseInlineFormatting(line.substring(4))}</h3>);
    } else {
      // Check if line was an alert content we skipped
      if (line.startsWith('>')) return;
      parsedElements.push(<p key={`p-${idx}`} style={{ marginBottom: '14px', color: 'hsl(var(--text-secondary))', lineHeight: '1.6' }}>{parseInlineFormatting(line)}</p>);
    }
  });

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>{parsedElements}</div>;
};

const parseInlineFormatting = (text: string): React.ReactNode => {
  // Simple token parser implementation for bold and code
  const tokens: (string | React.ReactNode)[] = [];
  const boldParts = text.split('**');
  
  boldParts.forEach((part, i) => {
    if (i % 2 === 1) {
      tokens.push(<strong key={`b-${i}`} style={{ color: 'hsl(var(--text-primary))' }}>{part}</strong>);
    } else {
      // Check for code inside non-bold text
      const codeParts = part.split('`');
      codeParts.forEach((codePart, j) => {
        if (j % 2 === 1) {
          tokens.push(<code key={`c-${i}-${j}`} style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.85em' }}>{codePart}</code>);
        } else {
          tokens.push(codePart);
        }
      });
    }
  });

  return <>{tokens}</>;
};

// ==========================================
// SIDE NAVIGATION LAYOUT WRAPPER
// ==========================================
const SidebarLayout = ({ children, user, onLogout }: { children: React.ReactNode; user: User; onLogout: () => void }) => {
  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
            <div className="bg-gradient" style={{ padding: '8px', borderRadius: '8px' }}>
              <Terminal size={24} color="#fff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, letterSpacing: '0' }}>AI REVIEWER</h3>
              <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', fontWeight: 600 }}>GOOGLE SE PORTFOLIO</p>
            </div>
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <Link to="/dashboard" className="btn btn-secondary" style={{ justifyContent: 'flex-start', background: 'transparent', border: 'none', padding: '12px 16px' }}>
              <Activity size={18} />
              Dashboard
            </Link>
            <Link to="/repositories" className="btn btn-secondary" style={{ justifyContent: 'flex-start', background: 'transparent', border: 'none', padding: '12px 16px' }}>
              <FolderGit2 size={18} />
              Repositories
            </Link>
          </nav>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'hsl(var(--primary))', width: '36px', height: '36px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
              {user.full_name ? user.full_name[0].toUpperCase() : user.email[0].toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <p style={{ fontSize: '0.85rem', fontWeight: 600, textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>{user.full_name || 'Active User'}</p>
              <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'capitalize' }}>{user.role}</p>
            </div>
          </div>
          <button className="btn btn-secondary" onClick={onLogout} style={{ width: '100%', justifyContent: 'center', background: 'rgba(255, 71, 87, 0.05)', color: 'hsl(var(--danger))', borderColor: 'rgba(255, 71, 87, 0.1)' }}>
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>
      <main className="content-area">
        {children}
      </main>
    </div>
  );
};

// ==========================================
// LOGIN & REGISTRATION PAGES
// ==========================================
const AuthPage = ({ setSessionUser }: { setSessionUser: (user: User) => void }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const data = await authApi.login(formData);
        setTokens(data.access_token, data.refresh_token);
        
        const user = await authApi.me();
        setSessionUser(user);
        navigate('/dashboard');
      } else {
        await authApi.register({ email, password, full_name: fullName });
        setIsLogin(true);
        setEmail('');
        setPassword('');
        setFullName('');
        alert('Registration successful! Please log in.');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at top right, rgba(125,95,255,0.08), transparent)' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '36px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div className="bg-gradient" style={{ display: 'inline-flex', padding: '12px', borderRadius: '12px', marginBottom: '16px', color: '#fff' }}>
            <Terminal size={32} />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>AI Code Reviewer</h2>
          <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.9rem', marginTop: '6px' }}>
            {isLogin ? 'Sign in to access your portfolio metrics' : 'Create an account to analyze codebases'}
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(255,71,87,0.1)', color: 'hsl(var(--danger))', padding: '12px', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '20px', border: '1px solid rgba(255,71,87,0.2)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {!isLogin && (
            <div>
              <label className="label-text">Full Name</label>
              <div style={{ position: 'relative' }}>
                <input type="text" className="input-field" required value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Google Engineer" />
              </div>
            </div>
          )}

          <div>
            <label className="label-text">Email Address</label>
            <input type="email" className="input-field" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@domain.com" />
          </div>

          <div>
            <label className="label-text">Password</label>
            <input type="password" className="input-field" required value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }} disabled={loading}>
            {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.85rem', color: 'hsl(var(--text-secondary))' }}>
          {isLogin ? (
            <p>Don't have an account? <span onClick={() => setIsLogin(false)} style={{ color: 'hsl(var(--primary))', cursor: 'pointer', fontWeight: 600 }}>Sign up</span></p>
          ) : (
            <p>Already have an account? <span onClick={() => setIsLogin(true)} style={{ color: 'hsl(var(--primary))', cursor: 'pointer', fontWeight: 600 }}>Sign in</span></p>
          )}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// DASHBOARD PAGE
// ==========================================
const Dashboard = ({ user }: { user: User }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardApi.getStats();
        setStats(data);
      } catch (err) {
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', height: '80vh', alignItems: 'center', justifyContent: 'center' }}>Loading dashboard metrics...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.2rem' }}>Welcome Back, <span className="text-gradient">{user.full_name || 'Engineer'}</span></h1>
        <p style={{ color: 'hsl(var(--text-secondary))', marginTop: '6px' }}>Here is the AI code review pipeline and codebase health summary.</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div>
            <p style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'hsl(var(--text-secondary))', fontWeight: 600 }}>Repositories</p>
            <h2 className="stat-card-value">{stats?.total_repositories || 0}</h2>
          </div>
          <FolderGit2 size={32} style={{ opacity: 0.15, alignSelf: 'flex-end', marginTop: '-10px' }} />
        </div>

        <div className="glass-card stat-card">
          <div>
            <p style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'hsl(var(--text-secondary))', fontWeight: 600 }}>Analyses Run</p>
            <h2 className="stat-card-value">{stats?.total_analyses || 0}</h2>
          </div>
          <Activity size={32} style={{ opacity: 0.15, alignSelf: 'flex-end', marginTop: '-10px' }} />
        </div>

        <div className="glass-card stat-card">
          <div>
            <p style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'hsl(var(--text-secondary))', fontWeight: 600 }}>Avg Quality Score</p>
            <h2 className="stat-card-value text-gradient">{stats?.average_quality_score || 100}%</h2>
          </div>
          <CheckCircle size={32} style={{ opacity: 0.15, alignSelf: 'flex-end', marginTop: '-10px' }} />
        </div>
      </div>

      {/* Recent Reviews Table */}
      <div className="glass-card" style={{ marginBottom: '40px' }}>
        <h3 style={{ marginBottom: '20px' }}>Recent AI Analyses</h3>
        {(!stats?.recent_analyses || stats.recent_analyses.length === 0) ? (
          <p style={{ color: 'hsl(var(--text-muted))', padding: '20px 0' }}>No recent analyses run. Go to Repositories to analyze code.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Analysis ID</th>
                  <th>Status</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_analyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{analysis.id.substring(0, 8)}...</td>
                    <td>
                      <span className={`badge badge-${analysis.status}`}>
                        {analysis.status}
                      </span>
                    </td>
                    <td>{new Date(analysis.created_at).toLocaleString()}</td>
                    <td>
                      {analysis.status === 'completed' && (
                        <button className="btn btn-secondary" onClick={() => navigate(`/report/${analysis.id}`)} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                          View Report
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// ==========================================
// REPOSITORIES MANAGEMENT PAGE
// ==========================================
const Repositories = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Upload inputs
  const [repoName, setRepoName] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  
  // Clone inputs
  const [cloneName, setCloneName] = useState('');
  const [gitUrl, setGitUrl] = useState('');
  
  const [actionLoading, setActionLoading] = useState(false);
  const navigate = useNavigate();

  const fetchRepos = async () => {
    try {
      const data = await repositoryApi.list();
      setRepositories(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  const handleZipUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return alert('Please select a ZIP file.');

    setActionLoading(true);
    const fd = new FormData();
    fd.append('name', repoName);
    fd.append('file', uploadFile);

    try {
      await repositoryApi.upload(fd);
      setRepoName('');
      setUploadFile(null);
      await fetchRepos();
    } catch (err: any) {
      alert(err.message || 'ZIP upload failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGitClone = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    const fd = new FormData();
    fd.append('name', cloneName);
    fd.append('git_url', gitUrl);

    try {
      await repositoryApi.clone(fd);
      setCloneName('');
      setGitUrl('');
      await fetchRepos();
    } catch (err: any) {
      alert(err.message || 'Git clone failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this repository and purge its files?')) return;

    try {
      await repositoryApi.delete(id);
      await fetchRepos();
    } catch (err: any) {
      alert(err.message || 'Deletion failed.');
    }
  };

  const handleStartAnalysis = async (repoId: string) => {
    try {
      const analysis = await analysisApi.create(repoId);
      navigate(`/report/${analysis.id}`);
    } catch (err: any) {
      alert(err.message || 'Failed to start AI analysis.');
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', height: '80vh', alignItems: 'center', justifyContent: 'center' }}>Loading repositories...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.2rem' }}>Repository Management</h1>
        <p style={{ color: 'hsl(var(--text-secondary))', marginTop: '6px' }}>Upload source directories or import directly from Git.</p>
      </div>

      <div className="split-view" style={{ marginBottom: '40px' }}>
        {/* Upload ZIP Form */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Upload size={20} color="hsl(var(--primary))" />
            <h3>Upload Local ZIP</h3>
          </div>
          <form onSubmit={handleZipUpload} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="label-text">Project Name</label>
              <input type="text" className="input-field" required value={repoName} onChange={e => setRepoName(e.target.value)} placeholder="e.g. My Express Server" />
            </div>
            <div>
              <label className="label-text">Source Zip File</label>
              <input type="file" accept=".zip" required className="input-field" onChange={e => setUploadFile(e.target.files?.[0] || null)} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={actionLoading}>
              {actionLoading ? 'Uploading...' : 'Upload ZIP'}
            </button>
          </form>
        </div>

        {/* Git Clone Form */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <GitBranch size={20} color="hsl(var(--secondary))" />
            <h3>Import Git Repository</h3>
          </div>
          <form onSubmit={handleGitClone} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="label-text">Repository Name</label>
              <input type="text" className="input-field" required value={cloneName} onChange={e => setCloneName(e.target.value)} placeholder="e.g. Flask API Client" />
            </div>
            <div>
              <label className="label-text">Git HTTP URL</label>
              <input type="url" className="input-field" required value={gitUrl} onChange={e => setGitUrl(e.target.value)} placeholder="https://github.com/owner/repo.git" />
            </div>
            <button type="submit" className="btn btn-primary" style={{ background: 'linear-gradient(135deg, hsl(var(--secondary)) 0%, hsl(var(--primary)) 100%)', boxShadow: 'none' }} disabled={actionLoading}>
              {actionLoading ? 'Cloning...' : 'Import Git Repository'}
            </button>
          </form>
        </div>
      </div>

      {/* Repositories Table */}
      <div className="glass-card">
        <h3 style={{ marginBottom: '20px' }}>Your Codebases</h3>
        {repositories.length === 0 ? (
          <p style={{ color: 'hsl(var(--text-muted))', padding: '20px 0' }}>No repositories uploaded yet.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Date Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {repositories.map(repo => (
                  <tr key={repo.id}>
                    <td style={{ fontWeight: 600 }}>{repo.name}</td>
                    <td style={{ textTransform: 'capitalize' }}>{repo.type}</td>
                    <td>{new Date(repo.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn btn-primary" onClick={() => handleStartAnalysis(repo.id)} style={{ padding: '6px 12px', fontSize: '0.8rem', boxShadow: 'none' }}>
                          <Play size={12} />
                          Analyze
                        </button>
                        <button className="btn btn-danger" onClick={() => handleDelete(repo.id)} style={{ padding: '6px 12px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center' }}>
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// ==========================================
// ANALYSIS STATUS / REPORT VIEW PAGE
// ==========================================
const ReportView = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'metrics' | 'markdown'>('metrics');
  
  const navigate = useNavigate();

  const fetchStatus = async () => {
    if (!analysisId) return;

    try {
      const data = await analysisApi.getStatus(analysisId);
      setAnalysis(data);
      
      if (data.status === 'completed') {
        const reportData = await reportApi.getByAnalysis(analysisId);
        setReport(reportData);
      } else if (data.status === 'failed') {
        setError(data.error_message || 'Analysis processing failed.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve analysis status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Set up polling interval if analysis is not complete/failed
    let interval: any;
    if (analysis && (analysis.status === 'pending' || analysis.status === 'processing')) {
      interval = setInterval(() => {
        fetchStatus();
      }, 3000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [analysisId, analysis?.status]);

  const handleExport = async () => {
    if (!report) return;
    try {
      const markdown = await reportApi.exportMarkdown(report.id);
      
      // Trigger browser file download
      const blob = new Blob([markdown], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `review_report_${analysisId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download markdown report.');
    }
  };

  if (loading && !analysis) {
    return <div style={{ display: 'flex', height: '80vh', alignItems: 'center', justifyContent: 'center' }}>Initializing review logs...</div>;
  }

  // Pending/Processing status view
  if (analysis && (analysis.status === 'pending' || analysis.status === 'processing')) {
    return (
      <div style={{ display: 'flex', height: '80vh', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px' }}>
        <div style={{ position: 'relative', width: '80px', height: '80px' }}>
          <div className="bg-gradient" style={{ width: '100%', height: '100%', borderRadius: '50%', animation: 'pulse 1.5s infinite ease-in-out' }}></div>
          <Clock size={40} color="#fff" style={{ position: 'absolute', top: '20px', left: '20px' }} />
        </div>
        <h2 style={{ textTransform: 'capitalize' }}>AI Review is {analysis.status}...</h2>
        <p style={{ color: 'hsl(var(--text-secondary))' }}>Google Gemini is scanning files, detecting bug patterns, and measuring metrics. This takes ~5-15s.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', height: '80vh', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
        <div style={{ background: 'rgba(255, 71, 87, 0.1)', color: 'hsl(var(--danger))', padding: '16px', borderRadius: '50%' }}>
          <AlertTriangle size={48} />
        </div>
        <h2>Analysis Run Failed</h2>
        <p style={{ color: 'hsl(var(--text-secondary))', maxWidth: '500px', textAlign: 'center' }}>{error}</p>
        <button className="btn btn-secondary" onClick={() => navigate('/repositories')}>Back to Repositories</button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '40px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="badge badge-completed" style={{ textTransform: 'uppercase' }}>COMPLETED</span>
            <span style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', fontFamily: 'var(--font-mono)' }}>ID: {analysisId}</span>
          </div>
          <h1 style={{ fontSize: '2.2rem', marginTop: '10px' }}>Google AI Review Report</h1>
        </div>
        {report && (
          <button className="btn btn-primary" onClick={handleExport}>
            <Download size={16} />
            Export Markdown
          </button>
        )}
      </div>

      {report && (
        <>
          {/* Tab selectors */}
          <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid hsl(var(--border-color))', marginBottom: '32px' }}>
            <button 
              className={`btn`} 
              onClick={() => setActiveTab('metrics')}
              style={{ 
                background: 'transparent', 
                border: 'none', 
                color: activeTab === 'metrics' ? 'hsl(var(--primary))' : 'hsl(var(--text-secondary))',
                borderBottom: activeTab === 'metrics' ? '2px solid hsl(var(--primary))' : 'none',
                borderRadius: '0',
                padding: '12px 16px'
              }}
            >
              Metrics & Findings
            </button>
            <button 
              className={`btn`} 
              onClick={() => setActiveTab('markdown')}
              style={{ 
                background: 'transparent', 
                border: 'none', 
                color: activeTab === 'markdown' ? 'hsl(var(--primary))' : 'hsl(var(--text-secondary))',
                borderBottom: activeTab === 'markdown' ? '2px solid hsl(var(--primary))' : 'none',
                borderRadius: '0',
                padding: '12px 16px'
              }}
            >
              Full Detailed Report
            </button>
          </div>

          {activeTab === 'metrics' ? (
            <div className="split-view">
              {/* Score Rings Left */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div className="glass-card">
                  <h3 style={{ marginBottom: '20px' }}>Quality Scores</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div className={`metric-ring ${report.score_quality >= 80 ? 'metric-ring-success' : report.score_quality >= 50 ? 'metric-ring-warning' : 'metric-ring-danger'}`}>
                        {report.score_quality}
                      </div>
                      <p style={{ marginTop: '8px', fontSize: '0.85rem', fontWeight: 600 }}>Code Quality</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div className={`metric-ring ${report.score_security >= 80 ? 'metric-ring-success' : report.score_security >= 50 ? 'metric-ring-warning' : 'metric-ring-danger'}`}>
                        {report.score_security}
                      </div>
                      <p style={{ marginTop: '8px', fontSize: '0.85rem', fontWeight: 600 }}>Security</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div className={`metric-ring ${report.score_performance >= 80 ? 'metric-ring-success' : report.score_performance >= 50 ? 'metric-ring-warning' : 'metric-ring-danger'}`}>
                        {report.score_performance}
                      </div>
                      <p style={{ marginTop: '8px', fontSize: '0.85rem', fontWeight: 600 }}>Performance</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div className={`metric-ring ${report.score_maintainability >= 80 ? 'metric-ring-success' : report.score_maintainability >= 50 ? 'metric-ring-warning' : 'metric-ring-danger'}`}>
                        {report.score_maintainability}
                      </div>
                      <p style={{ marginTop: '8px', fontSize: '0.85rem', fontWeight: 600 }}>Maintainability</p>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <h3 style={{ marginBottom: '16px' }}>AI Review Statistics</h3>
                  <p style={{ color: 'hsl(var(--text-secondary))', marginBottom: '8px' }}>Total Issues Detected: <strong>{report.findings.length}</strong></p>
                  <p style={{ color: 'hsl(var(--text-secondary))', marginBottom: '8px' }}>High Severity: <strong>{report.findings.filter(f => f.severity === 'high').length}</strong></p>
                  <p style={{ color: 'hsl(var(--text-secondary))', marginBottom: '8px' }}>Medium Severity: <strong>{report.findings.filter(f => f.severity === 'medium').length}</strong></p>
                </div>
              </div>

              {/* Findings Right */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="glass-card">
                  <h3 style={{ marginBottom: '20px' }}>Codebase Findings</h3>
                  {report.findings.length === 0 ? (
                    <p style={{ color: 'hsl(var(--text-muted))' }}>Zero anomalies detected by Google Gemini. Excellent code health!</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '500px', overflowY: 'auto', paddingRight: '8px' }}>
                      {report.findings.map((finding, idx) => (
                        <div key={idx} style={{
                          background: 'rgba(255,255,255,0.02)',
                          border: '1px solid hsl(var(--border-color))',
                          borderRadius: '10px',
                          padding: '16px',
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <span className="badge" style={{
                              background: finding.severity === 'high' ? 'rgba(255,71,87,0.15)' : finding.severity === 'medium' ? 'rgba(255,165,2,0.15)' : 'rgba(46,213,115,0.15)',
                              color: finding.severity === 'high' ? 'hsl(var(--danger))' : finding.severity === 'medium' ? 'hsl(var(--warning))' : 'hsl(var(--success))',
                              textTransform: 'uppercase'
                            }}>
                              {finding.severity}
                            </span>
                            <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', fontFamily: 'var(--font-mono)' }}>
                              {finding.file} {finding.line ? `: L${finding.line}` : ''}
                            </span>
                          </div>
                          
                          <p style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '6px' }}>{finding.message}</p>
                          <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', background: '#151922', padding: '10px', borderRadius: '6px', fontFamily: 'var(--font-mono)', border: '1px solid rgba(255,255,255,0.04)', overflowX: 'auto' }}>
                            {finding.suggestion}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* Markdown Report View */
            <div className="glass-card" style={{ padding: '40px', background: 'rgba(22, 26, 35, 0.8)' }}>
              {parseMarkdownToReact(report.markdown_content)}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ==========================================
// CORE APP ROUTER CONFIGURATION
// ==========================================
function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const checkCurrentUser = async () => {
      const { access } = getTokens();
      if (!access) {
        setCheckingAuth(false);
        return;
      }

      try {
        const u = await authApi.me();
        setUser(u);
      } catch (err) {
        clearTokens();
      } finally {
        setCheckingAuth(false);
      }
    };
    checkCurrentUser();

    // Listen to session expired events from custom API fetch handler
    const handleSessionExpired = () => {
      setUser(null);
      alert('Your session has expired. Please sign in again.');
    };

    window.addEventListener('auth_session_expired', handleSessionExpired);
    return () => window.removeEventListener('auth_session_expired', handleSessionExpired);
  }, []);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // Continue client logout even on API network errors
    } finally {
      clearTokens();
      setUser(null);
    }
  };

  if (checkingAuth) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-base))' }}>
        Loading platform profile...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/login" 
          element={user ? <Navigate to="/dashboard" replace /> : <AuthPage setSessionUser={setUser} />} 
        />
        
        <Route 
          path="/dashboard" 
          element={
            user ? (
              <SidebarLayout user={user} onLogout={handleLogout}>
                <Dashboard user={user} />
              </SidebarLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />

        <Route 
          path="/repositories" 
          element={
            user ? (
              <SidebarLayout user={user} onLogout={handleLogout}>
                <Repositories />
              </SidebarLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />

        <Route 
          path="/report/:analysisId" 
          element={
            user ? (
              <SidebarLayout user={user} onLogout={handleLogout}>
                <ReportView />
              </SidebarLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />

        {/* Fallback routing */}
        <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
