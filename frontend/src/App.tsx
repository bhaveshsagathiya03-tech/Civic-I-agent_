import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowRight, CheckCircle2, ChevronDown, CircleHelp,
  ClipboardList, Clock3, Database, FileImage, Filter, Gauge, HardHat, Home, ImagePlus,
  Layers3, Leaf, LocateFixed, LogIn, LogOut, Map as MapIcon, MapPinned, Menu, RefreshCw,
  Search, ShieldCheck, Siren, UploadCloud, X, Zap,
} from 'lucide-react';
import MapView from './components/MapView';
import LocationPicker from './components/LocationPicker';
import { API_BASE, api, type Issue, type Overview } from './lib/api';

type Page = 'overview' | 'issues' | 'map' | 'priority' | 'report' | 'health';
const blankOverview: Overview = { total:0,potholes:0,garbage:0,critical:0,high:0,medium:0,low:0,awaiting_review:0,resolved:0,model_status:'unknown' };
const labelFor = (value: string | null | undefined) => value === 'garbage_accumulation' ? 'Garbage' : value === 'pothole' ? 'Pothole' : 'Unclassified';
const pretty = (value: string | null | undefined) => (value || 'unknown').replaceAll('_',' ').replace(/\b\w/g, c => c.toUpperCase());

function App() {
  const [page, setPage] = useState<Page>('overview');
  const [issues, setIssues] = useState<Issue[]>([]);
  const [overview, setOverview] = useState<Overview>(blankOverview);
  const [token, setToken] = useState(sessionStorage.getItem('civic_token') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [selected, setSelected] = useState<Issue | null>(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [query, setQuery] = useState('');
  const [mobileNav, setMobileNav] = useState(false);
  const [toast, setToast] = useState('');

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true); setApiError('');
    try {
      const [rows, stats] = await Promise.all([
        api<Issue[]>('/api/v1/issues?limit=250'),
        api<Overview>('/api/v1/analytics/overview'),
      ]);
      setIssues(rows); setOverview(stats);
    } catch (err) { setApiError(err instanceof Error ? err.message : 'Could not load the dashboard.'); }
    finally { setLoading(false); }
  }, [token]);
  useEffect(() => { refresh(); }, [refresh]);

  const filtered = useMemo(() => issues.filter(i =>
    (filterCategory === 'all' || i.category === filterCategory) &&
    (filterPriority === 'all' || i.priority_level === filterPriority) &&
    `${i.public_id} ${i.location_label || ''} ${i.description || ''}`.toLowerCase().includes(query.toLowerCase())
  ), [issues, filterCategory, filterPriority, query]);

  async function signIn(e: FormEvent) {
    e.preventDefault(); setLoginError('');
    try {
      const response = await api<{access_token:string}>('/api/v1/auth/login', { method:'POST', body:JSON.stringify({email,password}) });
      sessionStorage.setItem('civic_token', response.access_token); setToken(response.access_token); setPassword('');
    } catch (err) { setLoginError(err instanceof Error ? err.message : 'Sign-in failed.'); }
  }
  function signOut() { sessionStorage.removeItem('civic_token'); setToken(''); setIssues([]); setOverview(blankOverview); setSelected(null); }
  async function updateIssue(id: number, status: string, categoryOverride?: string) {
    try {
      const updated = await api<Issue>(`/api/v1/issues/${id}/review`, { method:'PATCH', body:JSON.stringify({status, category_override: categoryOverride || undefined, notes:'Updated through the CIVIC-I review console.'}) });
      setIssues(current => current.map(i => i.id === id ? updated : i)); setSelected(updated); setToast('Issue status updated.'); setTimeout(()=>setToast(''),3000); refresh();
    } catch (err) { setToast(err instanceof Error ? err.message : 'Update failed.'); setTimeout(()=>setToast(''),4000); }
  }

  async function updatePriority(issueId: number, context: Record<string, unknown>) {
    try {
      const updated = await api<Issue>(`/api/v1/issues/${issueId}/priority-context`, { method:'PATCH', body:JSON.stringify(context) });
      setIssues(current => current.map(i => i.id === issueId ? updated : i)); setSelected(updated);
      setToast('Priority assessment updated.'); setTimeout(()=>setToast(''),3000);
    } catch (err) { setToast(err instanceof Error ? err.message : 'Priority update failed.'); setTimeout(()=>setToast(''),4000); }
  }

  const nav = [
    { id:'overview' as Page, label:'Overview', icon:Home },
    { id:'issues' as Page, label:'Civic issues', icon:ClipboardList, count:issues.length || undefined },
    { id:'map' as Page, label:'Palghar issue map', icon:MapPinned },
    { id:'priority' as Page, label:'Priority queue', icon:Siren, count:overview.critical || undefined },
    { id:'report' as Page, label:'Submit a report', icon:ImagePlus },
    { id:'health' as Page, label:'Model & system health', icon:Activity },
  ];

  return <div className="app-frame">
    <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
      <div className="brand-lockup"><div className="brand-mark"><ShieldCheck size={22}/></div><div><div className="brand-name">CIVIC<span>-I</span></div><div className="brand-sub">PALGHAR CIVIC INTELLIGENCE</div></div><button className="icon-button mobile-close" onClick={()=>setMobileNav(false)} aria-label="Close menu"><X size={18}/></button></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="side-nav">{nav.map(item => <button key={item.id} className={`nav-item ${page===item.id?'active':''}`} onClick={()=>{setPage(item.id);setMobileNav(false);setSelected(null);}}><item.icon size={18}/><span>{item.label}</span>{item.count ? <b>{item.count}</b> : null}</button>)}</nav>
      <div className="sidebar-bottom">
        <div className="scope-card"><div className="scope-icon"><MapIcon size={16}/></div><div><strong>Palghar City</strong><span>Two-category pilot scope</span></div></div>
        <div className="sidebar-user"><div className="avatar">{token?'AD':'CI'}</div><div className="user-label"><strong>{token?'Administrator':'Public access'}</strong><span>{token?'Review workspace':'Citizen reporting'}</span></div>{token ? <button onClick={signOut} className="icon-button" title="Sign out"><LogOut size={17}/></button> : <button onClick={()=>setPage('health')} className="icon-button" title="Admin sign in"><LogIn size={17}/></button>}</div>
      </div>
    </aside>
    {mobileNav && <button aria-label="Close navigation" className="mobile-overlay" onClick={()=>setMobileNav(false)} />}

    <main className="main-area">
      <header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" onClick={()=>setMobileNav(true)} aria-label="Open menu"><Menu size={20}/></button><div className="breadcrumbs">CIVIC-I <span>/</span> <strong>{nav.find(n=>n.id===page)?.label}</strong></div></div><div className="topbar-right"><div className="system-pill"><span className="status-dot"/> API workspace</div><button className="icon-button" onClick={refresh} title="Refresh data"><RefreshCw size={17}/></button><div className="topbar-avatar">{token?'A':'C'}</div></div></header>
      {!token && <div className="prototype-banner"><AlertTriangle size={16}/><span><strong>Prototype mode.</strong> Citizen reports can be submitted. Admin analytics and issue records require an administrator account.</span><button onClick={()=>setPage('health')}>Admin sign in <ArrowRight size={14}/></button></div>}
      {apiError && <div className="alert-banner"><AlertTriangle size={17}/><span>{apiError} Confirm that the API is running and sign in again.</span></div>}

      {page==='overview' && <OverviewPage overview={overview} issues={issues} loading={loading} onNavigate={setPage}/>}
      {page==='issues' && <IssuesPage issues={filtered} query={query} setQuery={setQuery} category={filterCategory} setCategory={setFilterCategory} priority={filterPriority} setPriority={setFilterPriority} onSelect={setSelected} token={token}/>}
      {page==='map' && <MapPage issues={issues} token={token}/>}
      {page==='priority' && <PriorityPage issues={issues} onSelect={setSelected} token={token}/>}
      {page==='report' && <ReportPage onSuccess={(id)=>{setToast(`Report submitted: ${id}`);setTimeout(()=>setToast(''),6000);if(token)refresh();}}/>}
      {page==='health' && <HealthPage token={token} email={email} setEmail={setEmail} password={password} setPassword={setPassword} signIn={signIn} loginError={loginError} overview={overview}/>}
    </main>

    {selected && <IssueDrawer issue={selected} onClose={()=>setSelected(null)} onUpdate={updateIssue} onPriorityUpdate={updatePriority} token={token}/>}
    {toast && <div className="toast"><CheckCircle2 size={17}/>{toast}</div>}
  </div>;
}

function PageHeading({eyebrow,title,description,actions}:{eyebrow:string;title:string;description:string;actions?:React.ReactNode}) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions}</div>;
}
function Metric({label,value,detail,icon:Icon,tone='navy'}:{label:string;value:string|number;detail:string;icon:any;tone?:string}) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={19}/></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div>;
}
function OverviewPage({overview,issues,loading,onNavigate}:{overview:Overview;issues:Issue[];loading:boolean;onNavigate:(p:Page)=>void}) {
  const latest = [...issues].slice(0,5);
  const bars = [{label:'Potholes',value:overview.potholes,color:'blue'},{label:'Garbage',value:overview.garbage,color:'teal'}];
  return <div className="page-content"><PageHeading eyebrow="CITY OPERATIONS / PALGHAR" title="Civic overview" description="A live view of citizen-reported potholes and garbage accumulation." actions={<button className="button primary" onClick={()=>onNavigate('report')}><ImagePlus size={16}/> Submit issue</button>}/>
    <div className="model-notice"><div className="notice-icon"><AlertTriangle size={18}/></div><div><strong>Model readiness: {pretty(overview.model_status)}</strong><span>{overview.model_status==='ready'?'YOLO inference is ready. Continue to monitor validation and model metrics.':'The application does not fabricate image predictions. Configure validated two-class YOLO weights to activate automated detection.'}</span></div><button className="text-button" onClick={()=>onNavigate('health')}>View model status <ArrowRight size={14}/></button></div>
    <div className="metric-grid"><Metric label="Total reports" value={overview.total} detail="All submitted civic reports" icon={ClipboardList}/><Metric label="Potholes" value={overview.potholes} detail="AI-classified reports" icon={AlertTriangle} tone="blue"/><Metric label="Garbage issues" value={overview.garbage} detail="AI-classified reports" icon={Layers3} tone="teal"/><Metric label="Needs review" value={overview.awaiting_review} detail="Awaiting human verification" icon={Clock3} tone="amber"/></div>
    <div className="content-grid two-col">
      <section className="panel"><div className="panel-header"><div><h2>Issue distribution</h2><p>Reports classified by the configured AI pipeline</p></div><span className="panel-tag">2 categories</span></div><div className="distribution-wrap">{bars.map(b=><div className="dist-row" key={b.label}><div className="dist-head"><span>{b.label}</span><strong>{b.value}</strong></div><div className="bar-track"><div className={`bar-fill ${b.color}`} style={{width:`${overview.total?Math.max(2,b.value/overview.total*100):0}%`}}/></div></div>)}{overview.total===0 && <div className="empty-inline">No classified reports yet. Submit a photograph to begin.</div>}</div></section>
      <section className="panel"><div className="panel-header"><div><h2>Priority distribution</h2><p>Based on available issue context</p></div><Gauge size={18} className="muted-icon"/></div><div className="priority-counts"><div><span className="priority-bullet critical"/> <span>Critical</span><strong>{overview.critical}</strong></div><div><span className="priority-bullet high"/> <span>High</span><strong>{overview.high}</strong></div><div><span className="priority-bullet medium"/> <span>Medium</span><strong>{overview.medium}</strong></div><div><span className="priority-bullet low"/> <span>Low</span><strong>{overview.low}</strong></div></div><div className="panel-footnote">Priority is provisional until contextual information is verified.</div></section>
    </div>
    <section className="panel table-panel"><div className="panel-header"><div><h2>Recent civic reports</h2><p>Latest reports received by CIVIC-I</p></div><button className="text-button" onClick={()=>onNavigate('issues')}>View all <ArrowRight size={14}/></button></div>{!issues.length ? <EmptyState title="No reports available" text="Submitted issues appear here after administrator sign-in and successful data retrieval."/> : <IssueTable issues={latest} onSelect={()=>onNavigate('issues')}/>}</section>
    <div className="bottom-note"><ShieldCheck size={16}/> CIVIC-I provides AI-assisted triage. Final verification and municipal action remain with authorised people.</div>
  </div>;
}
function EmptyState({title,text}:{title:string;text:string}) { return <div className="empty-state"><div className="empty-icon"><Database size={22}/></div><strong>{title}</strong><p>{text}</p></div>; }
function IssueTable({issues,onSelect}:{issues:Issue[];onSelect:(id:number)=>void}) {
  return <div className="table-scroll"><table className="data-table"><thead><tr><th>Issue</th><th>Category</th><th>Location</th><th>Priority</th><th>Status</th><th>Reported</th><th/></tr></thead><tbody>{issues.map(i=><tr key={i.id} onClick={()=>onSelect(i.id)}><td><strong className="issue-id">{i.public_id}</strong></td><td><span className="category-tag">{labelFor(i.category)}</span></td><td>{i.location_label || `${i.latitude.toFixed(4)}, ${i.longitude.toFixed(4)}`}</td><td><PriorityTag level={i.priority_level}/></td><td><span className="status-text">{pretty(i.status)}</span></td><td>{new Date(i.created_at).toLocaleDateString()}</td><td><ArrowRight size={15} className="muted-icon"/></td></tr>)}</tbody></table></div>;
}
function PriorityTag({level}:{level:string}) { return <span className={`priority-tag ${level}`}><i/> {pretty(level)}</span>; }
function IssuesPage({issues,query,setQuery,category,setCategory,priority,setPriority,onSelect,token}:{issues:Issue[];query:string;setQuery:(v:string)=>void;category:string;setCategory:(v:string)=>void;priority:string;setPriority:(v:string)=>void;onSelect:(i:Issue)=>void;token:string}) {
  return <div className="page-content"><PageHeading eyebrow="REPORT MANAGEMENT" title="Civic issues" description="Review submitted pothole and garbage reports, their evidence and current status."/><section className="panel"><div className="filter-toolbar"><div className="search-field"><Search size={16}/><input placeholder="Search report ID or locality" value={query} onChange={e=>setQuery(e.target.value)}/></div><div className="filter-field"><Filter size={15}/><select value={category} onChange={e=>setCategory(e.target.value)}><option value="all">All categories</option><option value="pothole">Potholes</option><option value="garbage_accumulation">Garbage</option></select></div><div className="filter-field"><Gauge size={15}/><select value={priority} onChange={e=>setPriority(e.target.value)}><option value="all">All priorities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div></div>{!token ? <EmptyState title="Administrator sign-in required" text="Sign in from Model & System Health to view private report records."/> : issues.length ? <IssueTable issues={issues} onSelect={id=>{const issue=issues.find(x=>x.id===id);if(issue)onSelect(issue);}}/> : <EmptyState title="No matching reports" text="Try changing your filters or submit a new report."/>}</section></div>;
}
function MapPage({issues,token}:{issues:Issue[];token:string}) {
  return <div className="page-content map-page"><PageHeading eyebrow="GEOSPATIAL INTELLIGENCE" title="Palghar issue map" description="Explore reported civic issues by location, category and priority."/><div className="map-legend"><span><i className="legend-dot pothole-dot"/> Pothole</span><span><i className="legend-dot garbage-dot"/> Garbage</span><span><i className="legend-dot critical-dot"/> Critical</span><span className="map-scope-note">Pilot view · approximate city centre</span></div>{token ? <MapView issues={issues}/> : <EmptyState title="Sign in to view issue locations" text="The administrative map contains private issue records and requires an authorised account."/>}</div>;
}
function PriorityPage({issues,onSelect,token}:{issues:Issue[];onSelect:(i:Issue)=>void;token:string}) {
  const rows = [...issues].filter(i=>i.priority_score!==null).sort((a,b)=>(b.priority_score||0)-(a.priority_score||0));
  return <div className="page-content"><PageHeading eyebrow="TRIAGE AND REVIEW" title="Priority queue" description="Issues ranked using the available visual and contextual evidence."/><div className="model-notice"><div className="notice-icon"><Gauge size={18}/></div><div><strong>Priority is an aid to human review</strong><span>Unknown context is not guessed. A score based only on image extent is provisional and should not be treated as an engineering safety assessment.</span></div></div>{!token ? <EmptyState title="Administrator sign-in required" text="Sign in to access the priority queue."/> : !rows.length ? <EmptyState title="No assessed issues" text="Issues appear after a supported category is detected and sufficient scoring information is available."/> : <div className="priority-list">{rows.map(i=><button className="priority-row" key={i.id} onClick={()=>onSelect(i)}><div className="priority-score">{Math.round(i.priority_score||0)}<small>/100</small></div><div className="priority-info"><strong>{i.public_id} · {labelFor(i.category)}</strong><span>{i.location_label || `${i.latitude.toFixed(4)}, ${i.longitude.toFixed(4)}`}</span><small>{i.priority_breakdown?.warning || 'Review the score breakdown before taking action.'}</small></div><PriorityTag level={i.priority_level}/><ArrowRight size={17}/></button>)}</div>}</div>;
}
function ReportPage({onSuccess}:{onSuccess:(id:string)=>void}) {
  const [file,setFile]=useState<File|null>(null); const [preview,setPreview]=useState(''); const [lat,setLat]=useState(''); const [lon,setLon]=useState(''); const [label,setLabel]=useState(''); const [description,setDescription]=useState(''); const [category,setCategory]=useState(''); const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [result,setResult]=useState<Issue|null>(null); const [trackId,setTrackId]=useState(''); const [tracked,setTracked]=useState<any>(null); const [trackError,setTrackError]=useState('');
  function onFile(f:File|null) { setFile(f); setResult(null); if(f){ if(!f.type.startsWith('image/')){setError('Please choose an image file.');return;} setPreview(URL.createObjectURL(f)); setError(''); } else setPreview(''); }
  function setPickedLocation(point:[number,number]) { setLat(point[0].toFixed(6)); setLon(point[1].toFixed(6)); }
  function locate() { if(!navigator.geolocation){setError('Location is not available in this browser.');return;} navigator.geolocation.getCurrentPosition(p=>{setLat(String(p.coords.latitude));setLon(String(p.coords.longitude));},()=>setError('Location permission was denied. You can enter coordinates manually.'),{enableHighAccuracy:true,timeout:10000}); }
  async function submit(e:FormEvent) { e.preventDefault(); setError(''); if(!file){setError('Choose a photograph first.');return;} const form=new FormData(); form.append('image',file); form.append('latitude',lat); form.append('longitude',lon); if(label)form.append('location_label',label);if(description)form.append('description',description);if(category)form.append('declared_category',category); setBusy(true); try {const issue=await api<Issue>('/api/v1/issues',{method:'POST',body:form});setResult(issue);setTrackId(issue.public_id);onSuccess(issue.public_id);}catch(err){setError(err instanceof Error?err.message:'Report could not be submitted.');}finally{setBusy(false);} }
  async function trackReport(e:FormEvent) { e.preventDefault(); setTrackError(''); setTracked(null); try { const item=await api<any>(`/api/v1/issues/track/${encodeURIComponent(trackId.trim())}`); setTracked(item); } catch(err) { setTrackError(err instanceof Error ? err.message : 'Could not find report.'); } }
  return <div className="page-content"><PageHeading eyebrow="CITIZEN REPORTING" title="Report a civic issue" description="Share a photograph and location to create a structured Palghar civic report."/><div className="report-grid"><form className="panel report-form" onSubmit={submit}><div className="form-section-title"><span>01</span><div><strong>Issue information</strong><small>Tell us what you observed.</small></div></div><label className="field-label">Issue category <span>Optional</span><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">Let AI identify the issue</option><option value="pothole">Pothole</option><option value="garbage_accumulation">Garbage accumulation</option></select></label><label className="field-label">Photograph <span>Required · JPEG, PNG or WEBP</span></label><label className="upload-zone">{preview?<img src={preview} alt="Selected civic issue"/>:<><UploadCloud size={28}/><strong>Choose or capture a photograph</strong><span>Use a clear photograph of the pothole or garbage accumulation.</span></>}<input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={e=>onFile(e.target.files?.[0]||null)}/></label>{preview&&<button type="button" className="text-button remove-file" onClick={()=>onFile(null)}><X size={14}/> Remove photo</button>}<div className="field-label">Location <span>Required · use GPS, click the map or enter coordinates</span><LocationPicker position={lat!==''&&lon!==''?[Number(lat),Number(lon)]:null} onChange={setPickedLocation}/><div className="coordinate-grid"><input required type="number" step="any" min="-90" max="90" value={lat} onChange={e=>setLat(e.target.value)} placeholder="Latitude"/><input required type="number" step="any" min="-180" max="180" value={lon} onChange={e=>setLon(e.target.value)} placeholder="Longitude"/></div></div><button type="button" className="button secondary location-button" onClick={locate}><LocateFixed size={16}/> Use my current location</button><label className="field-label">Locality / landmark <span>Optional</span><input value={label} onChange={e=>setLabel(e.target.value)} placeholder="e.g. near a landmark or locality" maxLength={255}/></label><label className="field-label">Description <span>Optional · 2,000 characters max</span><textarea value={description} onChange={e=>setDescription(e.target.value)} maxLength={2000} rows={3} placeholder="Describe what you noticed..."/></label>{error&&<div className="form-error"><AlertTriangle size={15}/>{error}</div>}<button className="button primary submit-button" disabled={busy}>{busy?<><RefreshCw className="spin" size={16}/> Submitting...</>:<>Submit civic report <ArrowRight size={16}/></>}</button><p className="privacy-note"><ShieldCheck size={14}/> Your photograph and location are used to assess this civic report. Avoid including identifiable people where possible.</p></form><div className="report-side"><div className="panel side-info"><div className="side-info-icon"><Zap size={20}/></div><h3>What happens next?</h3><ol><li><strong>Image validation</strong><span>The system checks that your image is valid.</span></li><li><strong>AI recognition</strong><span>When validated YOLO weights are configured, it checks for potholes or garbage accumulation.</span></li><li><strong>Priority assessment</strong><span>Available evidence is used to calculate a provisional score.</span></li><li><strong>Human review</strong><span>An authorised reviewer checks the result and records further action.</span></li></ol></div><div className="model-state-card"><div className="state-icon"><CircleHelp size={18}/></div><div><strong>AI availability matters</strong><p>If a validated model is not configured, your report is still recorded, but no AI prediction or priority will be fabricated.</p></div></div><div className="panel track-card"><h3>Track an existing report</h3><form onSubmit={trackReport}><input required value={trackId} onChange={e=>setTrackId(e.target.value)} placeholder="Enter CIV- reference ID"/><button className="button secondary">Check status</button></form>{trackError&&<div className="form-error">{trackError}</div>}{tracked&&<div className="track-result"><strong>{tracked.public_id}</strong><span>{pretty(tracked.category)} · {pretty(tracked.status)}</span><small>Priority: {pretty(tracked.priority_level)}</small></div>}</div>{result&&<div className="success-card"><CheckCircle2 size={19}/><div><strong>Report received</strong><p>Reference: <b>{result.public_id}</b></p><p>Detection: {pretty(result.detection_status)}</p><p>Status: {pretty(result.status)}</p></div></div>}</div></div></div>;
}
function HealthPage({token,email,setEmail,password,setPassword,signIn,loginError,overview}:{token:string;email:string;setEmail:(x:string)=>void;password:string;setPassword:(x:string)=>void;signIn:(e:FormEvent)=>void;loginError:string;overview:Overview}) {
  const checks=[{name:'Backend API',state:'Available when API responds',detail:'FastAPI service and health endpoint'},{name:'Database',state:'Configured by backend',detail:'SQLite local fallback; PostgreSQL recommended for deployment'},{name:'Computer Vision',state:pretty(overview.model_status),detail:'Requires validated two-class YOLO weights'},{name:'GIS map',state:'Configured',detail:'Leaflet with OpenStreetMap attribution'},{name:'Priority engine',state:'Available',detail:'Explainable rule-based scoring; provisional until field-calibrated'}];
  return <div className="page-content"><PageHeading eyebrow="SYSTEM OPERATIONS" title="Model & system health" description="Review the readiness of the services that power CIVIC-I."/><div className="health-grid">{checks.map((c,i)=><div className="health-card" key={c.name}><div className="health-icon"><Activity size={18}/></div><div><strong>{c.name}</strong><span>{c.state}</span><small>{c.detail}</small></div></div>)}</div><section className="panel model-config"><div className="panel-header"><div><h2>AI model readiness</h2><p>Automated recognition is activated only when a compatible two-class checkpoint is available.</p></div><span className={`state-label ${overview.model_status==='ready'?'good':'pending'}`}>{pretty(overview.model_status)}</span></div><div className="class-row"><span>Class 0</span><strong>pothole</strong><span>Class 1</span><strong>garbage_accumulation</strong></div><div className="notice-soft"><AlertTriangle size={16}/> A general-purpose COCO checkpoint is not a CIVIC-I model. Configure weights trained for the exact two target classes.</div></section>{!token&&<section className="panel login-panel"><div><div className="eyebrow">RESTRICTED WORKSPACE</div><h2>Administrator sign in</h2><p>Use credentials configured in the backend environment.</p></div><form onSubmit={signIn}><label className="field-label">Email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="admin@example.local"/></label><label className="field-label">Password<input type="password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter administrator password"/></label>{loginError&&<div className="form-error">{loginError}</div>}<button className="button primary">Sign in <ArrowRight size={15}/></button></form></section>}</div>;
}
function PrivateImage({path,alt,className}:{path:string;alt:string;className?:string}) {
  const [src,setSrc]=useState('');
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    let objectUrl=''; const controller=new AbortController();
    const accessToken=sessionStorage.getItem('civic_token');
    fetch(`${API_BASE}${path}`,{headers:accessToken?{Authorization:`Bearer ${accessToken}`}:{},signal:controller.signal})
      .then(response=>{if(!response.ok)throw new Error('Image unavailable');return response.blob();})
      .then(blob=>{objectUrl=URL.createObjectURL(blob);setSrc(objectUrl);setFailed(false);})
      .catch(error=>{if(error.name!=='AbortError')setFailed(true);});
    return ()=>{controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl);};
  },[path]);
  if(failed)return <div className="private-image-fallback">Evidence image unavailable</div>;
  return src?<img className={className} src={src} alt={alt}/>:<div className="private-image-fallback">Loading secure evidence…</div>;
}

function IssueDrawer({issue,onClose,onUpdate,onPriorityUpdate,token}:{issue:Issue;onClose:()=>void;onUpdate:(id:number,s:string,categoryOverride?:string)=>void;onPriorityUpdate:(id:number,context:Record<string,unknown>)=>void;token:string}) {
  const factorDefs = issue.category === 'pothole' ? [
    ['visible_severity','Visible defect severity'],['road_exposure','Road exposure'],['safety_context','Safety context'],['recurrence','Recurrence'],['duration','Reported duration']
  ] : issue.category === 'garbage_accumulation' ? [
    ['visible_extent','Visible accumulation extent'],['public_obstruction','Public obstruction'],['location_context','Location context'],['recurrence','Recurrence'],['duration','Reported duration']
  ] : [];
  const [factorValues,setFactorValues] = useState<Record<string,string>>({});
  const [factorNotes,setFactorNotes] = useState('');
  const [evidenceFile,setEvidenceFile] = useState<File|null>(null);
  const [evidenceMessage,setEvidenceMessage] = useState('');
  const [actions,setActions] = useState<any[]>([]);
  useEffect(()=>{ if(!token)return; api<any>(`/api/v1/issues/${issue.id}`).then(data=>setActions(data.actions||[])).catch(()=>setActions([])); },[issue.id,token]);
  async function submitEvidence() {
    if(!evidenceFile) { setEvidenceMessage('Choose a completion photograph first.'); return; }
    const form=new FormData(); form.append('image',evidenceFile); form.append('notes','Completion evidence uploaded for human verification.');
    try { const result=await api<any>(`/api/v1/issues/${issue.id}/resolution-evidence`,{method:'POST',body:form}); setEvidenceMessage(result.message); }
    catch(err) { setEvidenceMessage(err instanceof Error?err.message:'Evidence upload failed.'); }
  }
  function submitFactors(e:FormEvent) {
    e.preventDefault(); const context:Record<string,unknown>={notes:factorNotes};
    Object.entries(factorValues).forEach(([key,value])=>{if(value.trim()!=='') context[key]=Number(value);});
    onPriorityUpdate(issue.id,context);
  }
  return <div className="drawer-backdrop" onMouseDown={onClose}><aside className="issue-drawer" onMouseDown={e=>e.stopPropagation()}><div className="drawer-header"><div><div className="eyebrow">ISSUE DETAIL</div><h2>{issue.public_id}</h2></div><button className="icon-button" onClick={onClose}><X size={19}/></button></div><PrivateImage className="drawer-image" path={issue.annotated_image_url || issue.image_url} alt="Reported civic issue"/><div className="drawer-tags"><span className="category-tag">{labelFor(issue.category)}{issue.classification_source==='human_verified'?' · manually verified':''}</span><PriorityTag level={issue.priority_level}/></div><div className="drawer-metric-row"><div><small>Detection confidence</small><strong>{issue.detection_confidence===null?'Not available':`${(issue.detection_confidence*100).toFixed(1)}%`}</strong></div><div><small>Priority score</small><strong>{issue.priority_score===null?'Unassessed':`${Math.round(issue.priority_score)}/100`}</strong></div></div><div className="drawer-section"><h3>Location</h3><p>{issue.location_label || 'Locality not supplied'}</p><code>{issue.latitude.toFixed(6)}, {issue.longitude.toFixed(6)}</code></div><div className="drawer-section"><h3>AI assessment</h3>{issue.declared_category&&<p>Citizen category hint: <strong>{labelFor(issue.declared_category)}</strong> (not an AI-confirmed classification).</p>}<p>{issue.detection_payload?.message || issue.priority_breakdown?.warning || 'Review the available evidence before taking action.'}</p>{issue.priority_breakdown?.components?.map((c:any)=><div className="factor-row" key={c.factor}><span>{pretty(c.factor)}</span><strong>{c.value.toFixed(1)}</strong></div>)}</div><div className="drawer-section"><h3>Report details</h3><p>{issue.description || 'No description provided.'}</p><small>Submitted {new Date(issue.created_at).toLocaleString()}</small></div>{token&&factorDefs.length>0&&<div className="drawer-section"><h3>Reviewer priority context</h3><p>Enter verified contextual factors from 0 (none/lowest) to 100 (highest). Leave unknown values blank. These inputs recalculate the provisional priority score.</p><form className="priority-context-form" onSubmit={submitFactors}>{factorDefs.map(([key,label])=><label key={key}>{label}<input type="number" min="0" max="100" step="1" value={factorValues[key]||''} onChange={e=>setFactorValues(current=>({...current,[key]:e.target.value}))} placeholder="Unknown"/></label>)}<label>Review notes<input value={factorNotes} onChange={e=>setFactorNotes(e.target.value)} placeholder="Basis for the entered values"/></label><button className="button secondary">Recalculate priority</button></form></div>}{token&&<div className="drawer-section"><h3>Resolution evidence</h3><p>Upload a photograph showing reported completion. An authorised reviewer must still verify the evidence before marking the issue resolved.</p><input type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>setEvidenceFile(e.target.files?.[0]||null)}/><button className="button secondary evidence-button" onClick={submitEvidence}>Upload completion evidence</button>{evidenceMessage&&<small>{evidenceMessage}</small>}</div>}{token&&<div className="drawer-section"><h3>Action history</h3>{actions.length?actions.map((a:any)=><div className="history-item" key={a.created_at+a.action_type}><div className="history-dot"/><div><strong>{pretty(a.action_type)}</strong><span>{a.actor} · {new Date(a.created_at).toLocaleString()}</span>{a.notes&&<small>{a.notes}</small>}{a.evidence_url&&<PrivateImage className="history-evidence" path={a.evidence_url} alt="Resolution evidence"/>}</div></div>):<p>No administrative actions recorded yet.</p>}</div>}{token&&<div className="drawer-actions"><h3>Administrative review</h3><label className="drawer-field">Verified category<select defaultValue={issue.verified_category || issue.category || ""} id="drawer-category"><option value="">Not verified</option><option value="pothole">Pothole</option><option value="garbage_accumulation">Garbage accumulation</option></select></label><label className="drawer-field">Issue status<select defaultValue={issue.status} id="drawer-status"><option value="needs_review">Needs review</option><option value="verified">Verified</option><option value="under_action">Under action</option><option value="work_reported_completed">Work reported completed</option><option value="resolution_verified">Resolution verified</option><option value="reopened">Reopened</option><option value="rejected">Rejected</option></select></label><button className="button primary" onClick={()=>{const el=document.getElementById('drawer-status') as HTMLSelectElement;const cat=document.getElementById('drawer-category') as HTMLSelectElement;onUpdate(issue.id,el.value,cat.value || undefined);}}>Save review</button></div>}</aside></div>;
}

export default App;
