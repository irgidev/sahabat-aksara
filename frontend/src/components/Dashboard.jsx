import { useState, useEffect, useCallback, useMemo, useRef, Component } from 'react';
import {
  BookOpenText,
  SquaresFour,
  Users,
  ChartLineUp,
  Books,
  Bell,
  PlusCircle,
  Plus,
  UsersThree,
  CheckCircle,
  Star,
  User,
  SignOut,
  Camera,
  Upload,
  ArrowRight,
  ArrowLeft,
  Funnel,
  CaretUpDown,
  CaretUp,
  CaretDown,
  MagnifyingGlass,
  XCircle,
  PencilSimple,
  Trash,
  X,
  WarningCircle,
  Spinner,
  TrendUp,
  TrendDown,
  Clock,
  Target,
  ChartBar,
  Eye,
  Check,
  ChartPieSlice,
  DownloadSimple,
} from '@phosphor-icons/react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  LineChart,
  Line,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import useAuthStore from '../stores/useAuthStore';
import FaceEnrollmentForm from './FaceEnrollmentForm';
import API_BASE, { apiFetch } from '../lib/api';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: SquaresFour },
  { id: 'students', label: 'Data Siswa', icon: Users },
  { id: 'enroll', label: 'Upload Wajah', icon: Camera },
  { id: 'reports', label: 'Laporan Nilai', icon: ChartLineUp },
  { id: 'analytics', label: 'Analitik', icon: ChartPieSlice },
  { id: 'modules', label: 'Modul Materi', icon: Books },
];

const CATEGORIES = [
  { value: '', label: 'Semua Kategori' },
  { value: 'besar', label: 'Huruf Besar A-Z' },
  { value: 'kecil', label: 'Huruf Kecil a-z' },
  { value: 'angka', label: 'Angka 0-9' },
];

const STAR_FILTERS = [
  { value: '', label: 'Semua Bintang' },
  { value: '3', label: '⭐⭐⭐ (3)' },
  { value: '2', label: '⭐⭐ (2)' },
  { value: '1', label: '⭐ (1)' },
  { value: '0', label: '☆ (0)' },
];

const PAGE_SIZE = 12;



function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  try {
    const data = payload[0]?.payload;
    if (!data) return null;
    const dateStr = data.date || '';
    const dateObj = new Date(dateStr + 'T00:00:00');
    if (isNaN(dateObj.getTime())) return null;
    const dayName = dateObj.toLocaleDateString('id-ID', { weekday: 'short' });
    const dayMonth = dateObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });

    return (
      <div className="bg-white rounded-xl shadow-lg border border-slate-100 p-3 min-w-[160px]">
        <p className="text-xs font-bold text-slate-500 mb-1">{dayName}, {dayMonth}</p>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-sm bg-blue-400" />
          <span className="text-sm font-bold text-slate-700">{data.count ?? 0} latihan</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-emerald-400" />
          <span className="text-sm text-slate-500">Rata-rata: <strong>{data.avg_accuracy ?? 0}%</strong></span>
        </div>
      </div>
    );
  } catch (err) {
    console.warn('[CustomTooltip]', err);
    return null;
  }
}


class SectionErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('[SectionErrorBoundary]', this.props.section || 'unknown', error.message, info.componentStack);
  }
  render() {
    if (this.state.hasError) {
      const errMsg = this.state.error?.message || this.state.error?.toString() || 'Unknown error';
      return (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <p className="text-sm font-bold text-red-600 mb-1">
            ⚠️ Error di bagian <span className="underline">{this.props.section || 'tidak diketahui'}</span>
          </p>
          <p className="text-xs text-red-500 font-mono mb-3 break-all">{errMsg}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="text-xs font-bold text-white bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg transition-colors"
          >
            🔄 Coba Lagi
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}



export default function Dashboard({ supabase, onLogout }) {
  const { user, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [activities, setActivities] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState(null); 
  const [studentDetail, setStudentDetail] = useState(null);
  const [studentChart, setStudentChart] = useState([]);

  
  const [heatmapData, setHeatmapData] = useState(null);
  const [charRankings, setCharRankings] = useState([]);
  const [classComparison, setClassComparison] = useState([]);
  const [studentTrend, setStudentTrend] = useState(null);

  

  const fetchSummary = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/summary');
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  }, []);

  const fetchChartData = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/chart-data?days=7');
      const data = await res.json();
      setChartData(data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    }
  }, []);

  const fetchActivities = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/activity?limit=10');
      const data = await res.json();
      setActivities(data.activities || []);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
    }
  }, []);

  const fetchStudents = useCallback(async () => {
    try {
      if (supabase) {
        const { data, error } = await supabase
          .from('profiles')
          .select('*')
          .eq('role', 'student')
          .order('nama');
        if (!error && data) setStudents(data);
      } else {
        
        const res = await apiFetch('/api/students');
        const data = await res.json();
        setStudents(data);
      }
    } catch (err) {
      console.error('Failed to fetch students:', err);
    }
  }, [supabase]);

  const fetchStudentDetail = useCallback(async (studentId) => {
    try {
      const [progressRes, studentProgress] = await Promise.all([
        apiFetch(`/api/student/${studentId}/progress`),
        apiFetch(`/api/dashboard/reports?student_id=${studentId}&limit=50`),
      ]);
      const progressData = await progressRes.json();
      const reportsData = await studentProgress.json();

      
      const reports = reportsData.reports || [];
      const trend = reports.slice(0, 10).reverse().map((r, i) => ({
        index: i + 1,
        char: r.char_target,
        accuracy: r.accuracy,
        stars: r.stars,
      }));

      setStudentDetail(progressData || []);
      setStudentChart(trend);
    } catch (err) {
      console.error('Failed to fetch student detail:', err);
    }
  }, []);

  

  const fetchHeatmap = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/heatmap');
      const data = await res.json();
      setHeatmapData(data);
    } catch (err) {
        console.error('Failed to fetch heatmap:', err);
    }
  }, []);

  const fetchCharRankings = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/character-rankings');
      const data = await res.json();
      setCharRankings(data.rankings || []);
    } catch (err) {
      console.error('Failed to fetch char rankings:', err);
    }
  }, []);

  const fetchClassComparison = useCallback(async () => {
    try {
      const res = await apiFetch('/api/dashboard/class-comparison');
      const data = await res.json();
      setClassComparison(data.classes || []);
    } catch (err) {
      console.error('Failed to fetch class comparison:', err);
    }
  }, []);

  

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      await Promise.all([
        fetchSummary(),
        fetchChartData(),
        fetchActivities(),
        fetchStudents(),
        fetchHeatmap(),
        fetchCharRankings(),
        fetchClassComparison(),
      ]);
      setLoading(false);
    };
    loadAll();

    
    const interval = setInterval(() => {
      fetchSummary();
      fetchActivities();
      fetchChartData();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchSummary, fetchChartData, fetchActivities, fetchStudents]);

  
  useEffect(() => {
    if (selectedStudent) {
      fetchStudentDetail(selectedStudent.id);
    } else {
      setStudentDetail(null);
      setStudentChart([]);
    }
  }, [selectedStudent, fetchStudentDetail]);

  

  const handleLogout = async () => {
    if (onLogout) {
      await onLogout();
    } else {
      await logout(supabase);
    }
  };

  const handleStudentClick = (student) => {
    setSelectedStudent(student);
  };

  const handleCloseDetail = () => {
    setSelectedStudent(null);
  };

  

  return (
    <main className="view-section view-active bg-slate-50 flex h-full w-full">
      {}
      <aside className="w-64 bg-white shadow-[4px_0_24px_rgba(0,0,0,0.02)] h-full flex flex-col py-8 z-10 shrink-0">
        {}
        <div className="px-8 mb-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pastel-sky to-blue-400 flex items-center justify-center text-white shadow-md">
            <BookOpenText weight="bold" className="text-xl" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">PortalGuru</h1>
        </div>

        {}
        <nav className="flex-1 px-4 flex flex-col gap-2">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setSelectedStudent(null); }}
                className={`flex items-center gap-3 px-4 py-3 rounded-2xl font-medium transition-all relative overflow-hidden group ${
                  isActive
                    ? 'bg-pastel-sky/10 text-blue-600'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-r-full" />
                )}
                <Icon
                  weight={isActive ? 'fill' : 'regular'}
                  className={`text-xl ${!isActive ? 'group-hover:scale-110 transition-transform' : ''}`}
                />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {}
        <div className="px-6 mt-auto space-y-3">
          <div className="flex items-center gap-3 p-3 rounded-2xl border border-slate-100 bg-slate-50/50">
            <div className="w-10 h-10 rounded-full bg-pastel-lavender flex items-center justify-center overflow-hidden shrink-0">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt={user.nama} className="w-full h-full object-cover" />
              ) : (
                <span className="text-sm font-bold text-slate-600">
                  {user?.nama?.charAt(0)?.toUpperCase() || 'G'}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-slate-700 truncate">{user?.nama || 'Guru'}</p>
              <p className="text-xs text-slate-400 font-medium truncate">{user?.email || 'Wali Kelas'}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-red-400 hover:bg-red-50 font-medium text-sm transition-colors"
          >
            <SignOut weight="bold" /> Keluar
          </button>
        </div>
      </aside>

      {}
      <div className="flex-1 flex flex-col p-8 overflow-y-auto no-scrollbar relative">
        {selectedStudent ? (
          
          <StudentDetailPanel
            student={selectedStudent}
            progress={studentDetail}
            chartData={studentChart}
            onClose={handleCloseDetail}
            loading={!studentDetail}
          />
        ) : (
          
          <>
            {activeTab === 'dashboard' && (
              <DashboardMain
                summary={summary}
                chartData={chartData}
                activities={activities}
                students={students}
                loading={loading}
                onStudentClick={handleStudentClick}
              />
            )}
            {activeTab === 'students' && (
              <StudentsTab
                students={students}
                onStudentClick={handleStudentClick}
                onStudentsChanged={fetchStudents}
              />
            )}
            {activeTab === 'enroll' && <EnrollTab supabase={supabase} students={students} />}
            {activeTab === 'reports' && <ReportsTabEnhanced />}
            {activeTab === 'analytics' && (
              <AnalyticsTab
                heatmapData={heatmapData}
                charRankings={charRankings}
                classComparison={classComparison}
                students={students}
                onStudentClick={handleStudentClick}
              />
            )}
            {activeTab === 'modules' && <ModulesTab />}
          </>
        )}
      </div>
    </main>
  );
}





function DashboardMain({ summary, chartData, activities, students, loading, onStudentClick }) {
  const now = new Date();
  const [notifOpen, setNotifOpen] = useState(false);
  const notifRef = useRef(null);

  
  useEffect(() => {
    if (!notifOpen) return;
    const handleClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [notifOpen]);
  const greeting = getGreeting(now);

  
  const studentStatuses = useMemo(() => {
    if (!students.length) return [];
    const recentMap = {};
    (activities || []).forEach((a) => {
      if (!recentMap[a.student_id]) {
        recentMap[a.student_id] = a;
      }
    });

    return students.map((s) => {
      const recent = recentMap[s.id];
      const minsAgo = recent
        ? Math.floor((Date.now() - new Date(recent.created_at).getTime()) / 60000)
        : null;
      return {
        ...s,
        lastActivity: recent,
        isOnline: minsAgo !== null && minsAgo <= 30,
        activityLabel: recent
          ? minsAgo <= 5
            ? `Latihan ${recent.char_target}`
            : minsAgo <= 30
              ? `Aktif ${minsAgo} menit lalu`
              : `Terakhir: ${formatTimeAgo(recent.created_at)}`
          : 'Belum ada aktivitas',
      };
    });
  }, [students, activities]);

  
  const maxCount = Math.max(...chartData.map((d) => d.count), 5);

  return (
    <>
      {}
      <header className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 mb-1">
            {greeting}, {userDisplayName()} 👋
          </h2>
          <p className="text-slate-500 font-medium text-sm">
            {now.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {}
          <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-500 bg-emerald-50 px-3 py-1.5 rounded-full shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live — refresh otomatis
          </span>
          {}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setNotifOpen(!notifOpen)}
              className="w-11 h-11 rounded-full bg-white shadow-sm border border-slate-100 flex items-center justify-center text-slate-400 hover:text-blue-500 hover:border-blue-200 transition-all relative"
            >
              <Bell className={`text-xl transition-transform ${notifOpen ? 'rotate-12' : ''}`} weight={notifOpen ? 'fill' : 'regular'} />
              {(summary?.latihan_hari_ini ?? 0) > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-400 rounded-full text-white text-[10px] font-bold flex items-center justify-center border-2 border-white animate-bounce">
                  {summary?.latihan_hari_ini > 9 ? '9+' : summary?.latihan_hari_ini}
                </span>
              )}
            </button>

            {}
            {notifOpen && (
              <div className="absolute right-0 top-12 w-[380px] bg-white rounded-2xl shadow-2xl border border-slate-100 z-50 overflow-hidden animate-fadeInUp">
                {}
                <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 border-b border-slate-100">
                  <h4 className="text-sm font-bold text-slate-700">🔔 Notifikasi Latihan</h4>
                  <button
                    onClick={() => setNotifOpen(false)}
                    className="w-6 h-6 rounded-full hover:bg-slate-200 flex items-center justify-center text-slate-400 transition-colors"
                  >
                    <X weight="bold" className="text-xs" />
                  </button>
                </div>

                {}
                <div className="max-h-[340px] overflow-y-auto no-scrollbar">
                  {activities.length === 0 ? (
                    <div className="py-10 text-center">
                      <Bell weight="duotone" className="text-3xl text-slate-200 mx-auto mb-2" />
                      <p className="text-xs text-slate-400 font-medium">Belum ada notifikasi</p>
                      <p className="text-[10px] text-slate-300 mt-1">Latihan siswa akan muncul di sini</p>
                    </div>
                  ) : (
                    activities.slice(0, 15).map((act, idx) => {
                      const timeAgo = formatTimeAgo(act.created_at);
                      const isToday = act.created_at?.startsWith(new Date().toISOString().slice(0, 10));
                      return (
                        <div
                          key={act.id || idx}
                          className={`flex items-start gap-3 px-4 py-3 hover:bg-slate-50 transition-colors cursor-pointer ${idx < activities.length - 1 ? 'border-b border-slate-50' : ''}`}
                          onClick={() => {
                            if (act.student_id) {
                              const student = students.find((s) => s.id === act.student_id);
                              if (student) {
                                setNotifOpen(false);
                                handleStudentClick(student);
                              }
                            }
                          }}
                        >
                          {}
                          <img
                            src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${act.nama || 'siswa'}`}
                            className="w-9 h-9 rounded-full bg-slate-100 shrink-0 mt-0.5"
                            alt={act.nama}
                          />

                          {}
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-bold text-slate-700 truncate">
                              {act.nama || 'Siswa'}
                            </p>
                            <p className="text-xs text-slate-500 mt-0.5 truncate">
                              Berhasil latihan{' '}
                              <span className="font-bold text-blue-600">&quot;{act.char_target || '?'}&quot;</span>{' '}
                              — akurasi{' '}
                              <span className={`font-bold ${
                                (act.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                                (act.accuracy ?? 0) >= 50 ? 'text-amber-600' : 'text-red-500'
                              }`}>
                                {act.accuracy ?? 0}%
                              </span>
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[11px]">{renderStars(act.stars)}</span>
                              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${isToday ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                                {isToday ? 'Hari ini' : timeAgo}
                              </span>
                            </div>
                          </div>

                          {}
                          <div className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-xs font-black ${
                            (act.accuracy ?? 0) >= 80 ? 'bg-emerald-100 text-emerald-600' :
                            (act.accuracy ?? 0) >= 50 ? 'bg-amber-100 text-amber-600' :
                            'bg-red-50 text-red-500'
                          }`}>
                            {act.accuracy ?? 0}%
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {}
                {activities.length > 0 && (
                  <div className="border-t border-slate-100 px-4 py-2.5 bg-slate-50/50">
                    <button
                      onClick={() => { setNotifOpen(false); if (onStudentClick) onStudentClick({ _navigateToReports: true }); }}
                      className="w-full text-center text-xs font-bold text-blue-500 hover:text-blue-600 transition-colors py-1"
                    >
                      Lihat Semua Laporan →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {}
      <SectionErrorBoundary section="Metric Cards">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <MetricCardV2
          icon={UsersThree}
          iconBg="bg-blue-50"
          iconColor="text-blue-500"
          label="Total Siswa"
          value={loading ? '...' : summary?.total_siswa ?? 0}
          sublabel={`${summary?.siswa_belum_latihan ?? 0} belum latihan minggu ini`}
          subColor="text-amber-500"
        />
        <MetricCardV2
          icon={Target}
          iconBg="bg-emerald-50"
          iconColor="text-emerald-500"
          label="Latihan Hari Ini"
          value={loading ? '...' : summary?.latihan_hari_ini ?? 0}
          sublabel={`Total: ${summary?.total_latihan ?? 0} latihan`}
          subColor="text-slate-400"
          highlight
        />
        <MetricCardV2
          icon={ChartBar}
          iconBg="bg-purple-50"
          iconColor="text-purple-500"
          label="Rata-rata Akurasi"
          value={loading ? '...' : `${summary?.rata_rata_akurasi ?? 0}%`}
          sublabel="Kelas keseluruhan"
          subColor="text-slate-400"
        />
        <MetricCardV2
          icon={Star}
          iconBg="bg-amber-50"
          iconColor="text-amber-500"
          label="Top Performer"
          value={
            loading
              ? '...'
              : (summary?.top_performers?.[0]?.nama || '-')
          }
          sublabel={
            summary?.top_performers?.[0]
              ? `${summary.top_performers[0].avg_accuracy}% akurasi · ${summary.top_performers[0].total_latihan} latihan`
              : 'Belum ada data'
          }
          subColor="text-slate-400"
        />
      </div>
      </SectionErrorBoundary>

      {}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8 items-start">
        {}
        <SectionErrorBoundary section="Grafik Perkembangan">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold text-slate-800">Perkembangan Latihan</h3>
              <p className="text-xs text-slate-400 mt-0.5">7 hari terakhir</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-blue-400" /> Jumlah Latihan</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-400" /> Rata-rata Akurasi (%)</span>
            </div>
          </div>

          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(val) => {
                    const d = new Date(val + 'T00:00:00');
                    return d.toLocaleDateString('id-ID', { weekday: 'short' });
                  }}
                  tick={{ fontSize: 12, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  cursor={{ fill: '#f1f5f9', radius: 8 }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="bg-white rounded-xl shadow-lg border border-slate-100 p-3 min-w-[140px]">
                        <p className="text-xs font-bold text-slate-500 mb-1">
                          {new Date(d.date + 'T00:00:00').toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric', month: 'short' })}
                        </p>
                        <p className="text-sm font-bold text-slate-700">{d.count ?? 0} latihan</p>
                        <p className="text-xs text-slate-400">Akurasi rata-rata: <strong>{d.avg_accuracy ?? 0}%</strong></p>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={40} name="Latihan">
                  {chartData.map((entry, idx) => (
                    <Cell
                      key={'cnt-' + idx}
                      fill={entry.count > 0 ? '#60a5fa' : '#e2e8f0'}
                      opacity={entry.count > 0 ? 1 : 0.5}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-slate-300">
              <p className="text-sm font-medium">Belum ada data grafik</p>
            </div>
          )}
        </div>
        </SectionErrorBoundary>

        {}
        <SectionErrorBoundary section="Feed Aktivitas">
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm flex flex-col">
          <div className="flex justify-between items-center mb-5">
            <h3 className="text-lg font-bold text-slate-800">Aktivitas Terbaru</h3>
            <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-500 bg-emerald-50 px-2 py-1 rounded-md">
              <Clock weight="bold" className="text-[10px]" /> Live
            </span>
          </div>

          <div className="flex-1 flex flex-col gap-3 min-h-[280px]">
            {activities.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
                <Clock weight="fill" className="text-4xl mb-2" />
                <p className="text-sm font-medium">Belum ada aktivitas</p>
              </div>
            ) : (
              activities.map((act) => (
                <ActivityItem key={act.id || act.created_at} activity={act} />
              ))
            )}
          </div>

          {activities.length >= 10 && (
            <button
              onClick={() => {} }
              className="mt-3 w-full py-2.5 rounded-xl border-2 border-dashed border-slate-200 text-slate-500 font-bold text-xs hover:border-pastel-sky hover:text-blue-500 transition-colors"
            >
              Lihat Semua Aktivitas →
            </button>
          )}
        </div>
        </SectionErrorBoundary>
      </div>

      {}
      <SectionErrorBoundary section="Status Siswa">
      <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Status Siswa — Live</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Klik nama siswa untuk melihat detail perkembangan
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Aktif
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-300" /> Offline
            </span>
          </div>
        </div>

        {studentStatuses.length === 0 ? (
          <div className="py-12 text-center text-slate-300">
            <Users weight="fill" className="text-5xl mx-auto mb-3" />
            <p className="text-sm font-medium">Belum ada data siswa</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {studentStatuses.map((s) => (
              <button
                key={s.id}
                onClick={() => onStudentClick(s)}
                className={`flex items-center gap-3 p-3.5 rounded-2xl border transition-all text-left ${
                  s.isOnline
                    ? 'border-emerald-100 bg-emerald-50/30 hover:bg-emerald-50 hover:shadow-sm'
                    : 'border-slate-100 bg-white hover:bg-slate-50 hover:shadow-sm'
                }`}
              >
                <div className="relative shrink-0">
                  <img
                    src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${s.nama}`}
                    className="w-11 h-11 rounded-full bg-slate-100"
                    alt={s.nama}
                  />
                  <span
                    className={`absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-white ${
                      s.isOnline ? 'bg-emerald-400' : 'bg-slate-300'
                    }`}
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-slate-700 truncate">{s.nama}</p>
                  <p className={`text-xs truncate ${s.isOnline ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                    {s.activityLabel}
                  </p>
                </div>
                <Eye weight="bold" className="text-slate-300 shrink-0 text-sm" />
              </button>
            ))}
          </div>
        )}
      </div>
      </SectionErrorBoundary>
    </>
  );
}





function ActivityItem({ activity }) {
  if (!activity) return null;
  const timeAgo = formatTimeAgo(activity.created_at);
  const starDisplay = renderStars(activity.stars);

  return (
    <div className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 transition-colors group">
      <img
        src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${activity.nama}`}
        className="w-8 h-8 rounded-full bg-slate-100 shrink-0"
        alt={activity.nama}
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-slate-700 truncate group-hover:text-blue-600 transition-colors">
          {activity.nama}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs font-bold">
            Karakter &quot;{activity.char_target}&quot;
          </span>
          <span className="text-xs text-slate-400">{starDisplay}</span>
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className="text-xs font-bold text-slate-700">{activity.accuracy}%</p>
        <p className="text-[10px] text-slate-400">{timeAgo}</p>
      </div>
    </div>
  );
}





function MetricCardV2({ icon: Icon, iconBg, iconColor, label, value, sublabel, subColor = 'text-slate-400', highlight = false }) {
  return (
    <div
      className={`bg-white rounded-2xl p-5 border shadow-sm flex flex-col gap-2 transition-all hover:shadow-md ${
        highlight ? 'border-emerald-200 ring-1 ring-emerald-100' : 'border-slate-100'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className={`w-11 h-11 rounded-xl ${iconBg} flex items-center justify-center ${iconColor}`}>
          <Icon weight="fill" className="text-xl" />
        </div>
        {highlight && (
          <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full animate-pulse">
            <TrendUp weight="bold" /> Hari ini
          </span>
        )}
      </div>
      <div>
        <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{label}</p>
        <h3 className="text-2xl font-bold text-slate-800 mt-0.5 leading-tight">{value}</h3>
      </div>
      {sublabel && (
        <p className={`text-xs font-medium ${subColor}`}>{sublabel}</p>
      )}
    </div>
  );
}





function StudentDetailPanel({ student, progress, chartData, onClose, loading }) {
  
  const stats = useMemo(() => {
    if (!progress || !progress.length) {
      return { total: 0, avgAcc: 0, perfectCount: 0, bestChar: '-', categories: {} };
    }

    let accSum = 0;
    let perfectCount = 0;
    const charScores = {};
    const catTotals = {};

    progress.forEach((p) => {
      const acc = p.accuracy ?? 0;
      accSum += acc;
      if (acc >= 90) perfectCount++;

      const char = (p.lessons?.char_target || p.char_target || '?').toUpperCase();
      if (!charScores[char]) charScores[char] = { total: 0, accSum: 0, best: 0 };
      charScores[char].total += 1;
      charScores[char].accSum += acc;
      if (acc > charScores[char].best) charScores[char].best = acc;

      const cat = p.lessons?.category || '';
      if (cat) {
        if (!catTotals[cat]) catTotals[cat] = { total: 0, accSum: 0 };
        catTotals[cat].total += 1;
        catTotals[cat].accSum += acc;
      }
    });

    const bestChar = Object.entries(charScores)
      .sort(([, a], [, b]) => b.accSum / b.total - a.accSum / a.total)[0];

    return {
      total: progress.length,
      avgAcc: Math.round(accSum / progress.length),
      perfectCount,
      bestChar: bestChar ? bestChar[0] : '-',
      bestCharAvg: bestChar ? Math.round(bestChar[1].accSum / bestChar[1].total) : 0,
      charScores,
      catTotals,
    };
  }, [progress]);

  return (
    <div className="animate-fadeInUp">
      {}
      <button
        onClick={onClose}
        className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-blue-600 mb-6 transition-colors"
      >
        <ArrowLeft weight="bold" /> Kembali ke Dashboard
      </button>

      {}
      <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm mb-6">
        <div className="flex items-center gap-5">
          <img
            src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${student.nama}`}
            className="w-20 h-20 rounded-2xl bg-slate-100"
            alt={student.nama}
          />
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-slate-800">{student.nama}</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              {student.kelas || 'TK-A'} · NIS: {student.nis || '-'}
            </p>
            <div className="flex items-center gap-3 mt-2">
              <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full ${
                student.face_descriptor
                  ? 'text-emerald-600 bg-emerald-50'
                  : 'text-amber-600 bg-amber-50'
              }`}>
                <Camera weight="bold" className="text-[10px]" />
                {student.face_descriptor ? 'Wajah Terdaftar' : 'Wajah Belum'}
              </span>
            </div>
          </div>

          {}
          {!loading && (
            <div className="flex gap-4">
              <div className="text-center px-4 py-2 rounded-xl bg-blue-50">
                <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
                <p className="text-[10px] text-blue-400 font-bold uppercase">Latihan</p>
              </div>
              <div className="text-center px-4 py-2 rounded-xl bg-purple-50">
                <p className="text-2xl font-bold text-purple-600">{stats.avgAcc}%</p>
                <p className="text-[10px] text-purple-400 font-bold uppercase">Rata-rata</p>
              </div>
              <div className="text-center px-4 py-2 rounded-xl bg-amber-50">
                <p className="text-2xl font-bold text-amber-600">{stats.perfectCount}</p>
                <p className="text-[10px] text-amber-400 font-bold uppercase">Sempurna ⭐⭐⭐</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {}
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-1">Trend Akurasi (10 Terakhir)</h3>
          <p className="text-xs text-slate-400 mb-4">Perkembangan terbaru</p>

          {loading ? (
            <div className="h-[220px] flex items-center justify-center text-slate-300">
              <p className="text-sm">Memuat data...</p>
            </div>
          ) : chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="char"
                  tick={{ fontSize: 13, fill: '#64748b', fontWeight: 700 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  unit="%"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="bg-white rounded-lg shadow-lg border border-slate-100 p-2.5">
                        <p className="text-sm font-bold text-slate-700">&quot;{d.char}&quot; → {d.accuracy}%</p>
                        <p className="text-xs text-slate-400">{renderStars(d.stars)}</p>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="accuracy" radius={[6, 6, 0, 0]} maxBarSize={36}>
                  {chartData.map((entry, idx) => (
                    <Cell
                      key={idx}
                      fill={
                        entry.accuracy >= 90 ? '#fbbf24' :
                        entry.accuracy >= 70 ? '#60a5fa' :
                        entry.accuracy >= 50 ? '#fb923c' : '#e2e8f0'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-slate-300">
              <p className="text-sm">Belum ada riwayat latihan</p>
            </div>
          )}
        </div>

        {}
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-1">Per Karakter</h3>
          <p className="text-xs text-slate-400 mb-4">Rincian per huruf/angka</p>

          {loading || !stats.charScores || Object.keys(stats.charScores).length === 0 ? (
            <div className="h-[220px] flex items-center justify-center text-slate-300">
              <p className="text-sm">Belum ada data karakter</p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[240px] overflow-y-auto pr-1 no-scrollbar">
              {Object.entries(stats.charScores)
                .sort(([, a], [, b]) => b.total - a.total)
                .map(([char, data]) => {
                  const avg = Math.round(data.accSum / data.total);
                  return (
                    <div key={char} className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-sm font-bold text-slate-600 shrink-0">
                        {char}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-slate-600">{data.total}x latihan</span>
                          <span className="text-xs font-bold text-slate-700">{avg}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              avg >= 80 ? 'bg-gradient-to-r from-emerald-300 to-emerald-500' :
                              avg >= 60 ? 'bg-gradient-to-r from-blue-300 to-blue-500' :
                              avg >= 40 ? 'bg-gradient-to-r from-orange-300 to-orange-500' :
                              'bg-gradient-to-r from-slate-300 to-slate-400'
                            }`}
                            style={{ width: `${Math.min(avg, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      </div>

      {}
      {!loading && progress && progress.length > 0 && (
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm mt-6">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Riwayat Lengkap</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Karakter</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Kategori</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Akurasi</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Bintang</th>
                  <th className="text-right px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Tanggal</th>
                </tr>
              </thead>
              <tbody>
                {progress.slice(0, 20).map((p, i) => (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-bold text-slate-700">
                      &quot;{(p.lessons?.char_target || '?')}&quot;
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-medium text-slate-500 capitalize">
                        {p.lessons?.category || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-pastel-mint to-emerald-400"
                            style={{ width: `${p.accuracy ?? 0}%` }}
                          />
                        </div>
                        <span className="text-sm font-bold text-slate-600">{p.accuracy ?? 0}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">{renderStars(p.stars)}</td>
                    <td className="px-4 py-3 text-sm text-slate-400 text-right">
                      {p.created_at
                        ? new Date(p.created_at).toLocaleDateString('id-ID', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}





function StudentsTab({ students, onStudentClick, onStudentsChanged }) {
  
  const [modalMode, setModalMode] = useState(null); 
  const [selectedForEdit, setSelectedForEdit] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null); 
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({ nama: '', kelas: '', nis: '', email: '' });

  
  const openAddModal = () => {
    setFormData({ nama: '', kelas: 'TK-A', nis: '', email: '' });
    setFormError('');
    setModalMode('add');
    setSelectedForEdit(null);
  };

  
  const openEditModal = (student, e) => {
    e.stopPropagation();
    setFormData({
      nama: student.nama || '',
      kelas: student.kelas || '',
      nis: student.nis || '',
      email: student.email || '',
    });
    setFormError('');
    setModalMode('edit');
    setSelectedForEdit(student);
  };

  
  const handleSubmit = async () => {
    
    if (!formData.nama.trim()) {
      setFormError('Nama siswa wajib diisi.');
      return;
    }

    setFormLoading(true);
    setFormError('');

    try {
      if (modalMode === 'add') {
        const res = await apiFetch('/api/students', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nama: formData.nama.trim(),
            kelas: formData.kelas.trim() || null,
            nis: formData.nis.trim() || null,
            email: formData.email.trim() || null,
          }),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Gagal menambahkan siswa.');
        if (onStudentsChanged) onStudentsChanged();
      } else {
        
        const res = await apiFetch(`/api/students/${selectedForEdit.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...(formData.nama.trim() !== selectedForEdit.nama && { nama: formData.nama.trim() }),
            ...(formData.kelas.trim() !== (selectedForEdit.kelas || '') && { kelas: formData.kelas.trim() || null }),
            ...(formData.nis.trim() !== (selectedForEdit.nis || '') && { nis: formData.nis.trim() || null }),
            ...(formData.email.trim() !== (selectedForEdit.email || '') && { email: formData.email.trim() || null }),
          }),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Gagal memperbarui data siswa.');
        if (onStudentsChanged) onStudentsChanged();
      }

      setModalMode(null);
      setSelectedForEdit(null);
    } catch (err) {
      console.error('[StudentsTab] Submit error:', err);
      setFormError(err.message || 'Terjadi kesalahan.');
    } finally {
      setFormLoading(false);
    }
  };

  
  const handleDelete = async () => {
    if (!deleteConfirm) return;

    setFormLoading(true);
    try {
      const res = await apiFetch(`/api/students/${deleteConfirm.id}`, {
        method: 'DELETE',
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Gagal menghapus siswa.');
      setDeleteConfirm(null);
      if (onStudentsChanged) onStudentsChanged();
    } catch (err) {
      console.error('[StudentsTab] Delete error:', err);
      setFormError(err.message || 'Gagal menghapus siswa.');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <>
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 mb-1">Data Siswa</h2>
            <p className="text-slate-500 font-medium text-sm">Kelola data siswa — tambah, edit, atau hapus</p>
          </div>
          <button
            onClick={openAddModal}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold text-sm shadow-lg shadow-blue-300/30 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            <Plus weight="bold" /> Tambah Siswa
          </button>
        </div>
      </header>

      {students.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-100 shadow-sm text-center">
          <Users weight="fill" className="text-6xl text-slate-200 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-700 mb-2">Belum ada siswa terdaftar</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
            Tambahkan siswa pertama untuk memulai.
          </p>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-500 text-white font-bold text-sm hover:bg-blue-600 transition-colors"
          >
            <Plus weight="bold" /> Tambah Siswa Pertama
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Nama</th>
                <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Kelas</th>
                <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">NIS</th>
                <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Status Wajah</th>
                <th className="text-right px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <button
                      onClick={() => onStudentClick(s)}
                      className="flex items-center gap-3 hover:text-blue-600 transition-colors"
                    >
                      <img
                        src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${s.nama}`}
                        className="w-9 h-9 rounded-full bg-slate-100"
                        alt=""
                      />
                      <span className="font-bold text-sm text-slate-700">{s.nama}</span>
                    </button>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">{s.kelas || '-'}</td>
                  <td className="px-6 py-4 text-sm text-slate-500">{s.nis || '-'}</td>
                  <td className="px-6 py-4">
                    {s.face_descriptor ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                        <CheckCircle weight="bold" className="text-xs" /> Terdaftar
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
                        <Camera weight="bold" className="text-xs" /> Belum
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => onStudentClick(s)}
                        className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-blue-500 hover:bg-blue-50 transition-colors"
                        title="Lihat Detail"
                      >
                        <Eye weight="bold" className="text-sm" />
                      </button>
                      <button
                        onClick={(e) => openEditModal(s, e)}
                        className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-amber-500 hover:bg-amber-50 transition-colors"
                        title="Edit"
                      >
                        <PencilSimple weight="bold" className="text-sm" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteConfirm(s); }}
                        className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-red-500 hover:bg-red-50 transition-colors"
                        title="Hapus"
                      >
                        <Trash weight="bold" className="text-sm" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {}
      {(modalMode === 'add' || modalMode === 'edit') && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fadeIn"
            onClick={() => setModalMode(null)}
          />

          {}
          <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-fadeInUp z-10">
            {}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-800">
                {modalMode === 'add' ? '✏️ Tambah Siswa Baru' : `📝 Edit: ${selectedForEdit?.nama}`}
              </h3>
              <button
                onClick={() => setModalMode(null)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
              >
                <X weight="bold" className="text-lg" />
              </button>
            </div>

            {}
            <div className="px-6 py-5 space-y-4">
              {}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Nama Lengkap <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.nama}
                  onChange={(e) => setFormData((f) => ({ ...f, nama: e.target.value }))}
                  placeholder="Contoh: Budi Santoso"
                  autoFocus={modalMode === 'add'}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-all placeholder:text-slate-300"
                />
              </div>

              {}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Kelas
                </label>
                <select
                  value={formData.kelas}
                  onChange={(e) => setFormData((f) => ({ ...f, kelas: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 bg-white"
                >
                  <option value="">— Pilih Kelas —</option>
                  <option value="TK-A">TK-A</option>
                  <option value="TK-B">TK-B</option>
                  <option value="TK-A1">TK-A1</option>
                  <option value="TK-A2">TK-A2</option>
                  <option value="TK-B1">TK-B1</option>
                  <option value="TK-B2">TK-B2</option>
                </select>
              </div>

              {}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  NIS (Nomor Induk Siswa)
                </label>
                <input
                  type="text"
                  value={formData.nis}
                  onChange={(e) => setFormData((f) => ({ ...f, nis: e.target.value }))}
                  placeholder="Contoh: 2024001"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-all placeholder:text-slate-300"
                />
              </div>

              {}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Email <span className="text-slate-300 font-normal">(opsional)</span>
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData((f) => ({ ...f, email: e.target.value }))}
                  placeholder="Contoh: budi@sekolah.id"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-all placeholder:text-slate-300"
                />
              </div>

              {}
              {formError && (
                <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                  <WarningCircle weight="bold" className="shrink-0" />
                  {formError}
                </div>
              )}
            </div>

            {}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100 bg-slate-50/50">
              <button
                onClick={() => setModalMode(null)}
                disabled={formLoading}
                className="px-5 py-2.5 rounded-xl border border-slate-200 text-slate-500 font-bold text-sm hover:bg-slate-100 transition-colors disabled:opacity-50"
              >
                Batal
              </button>
              <button
                onClick={handleSubmit}
                disabled={formLoading}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold text-sm shadow-md shadow-blue-300/20 hover:shadow-lg active:scale-[0.98] transition-all disabled:opacity-60 flex items-center gap-2"
              >
                {formLoading ? (
                  <><Spinner weight="bold" className="animate-spin" /> Menyimpan...</>
                ) : modalMode === 'add' ? (
                  <><Plus weight="bold" /> Tambahkan</>
                ) : (
                  <><CheckCircle weight="bold" /> Simpan Perubahan</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fadeIn"
            onClick={() => setDeleteConfirm(null)}
          />

          {}
          <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-fadeInUp z-10">
            {}
            <div className="px-6 pt-8 pb-5 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
                <Trash weight="fill" className="text-3xl text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">Hapus Siswa?</h3>
              <p className="text-sm text-slate-500">
                <strong className="text-slate-700">{deleteConfirm.nama}</strong> akan dihapus secara permanen,
                bersama semua riwayat latihannya.
              </p>
              <p className="text-xs text-red-400 mt-2 font-medium">⚠️ Tindakan ini tidak bisa dibatalkan.</p>
            </div>

            {}
            {formError && (
              <div className="mx-6 mb-3 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
                <WarningCircle weight="bold" className="shrink-0" />
                {formError}
              </div>
            )}

            {}
            <div className="flex items-center gap-3 px-6 py-4 border-t border-slate-100">
              <button
                onClick={() => { setDeleteConfirm(null); setFormError(''); }}
                disabled={formLoading}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-500 font-bold text-sm hover:bg-slate-100 transition-colors disabled:opacity-50"
              >
                Batal
              </button>
              <button
                onClick={handleDelete}
                disabled={formLoading}
                className="flex-1 py-2.5 rounded-xl bg-red-500 text-white font-bold text-sm hover:bg-red-600 active:scale-[0.98] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {formLoading ? (
                  <><Spinner weight="bold" className="animate-spin" /> Menghapus...</>
                ) : (
                  <><Trash weight="bold" /> Ya, Hapus</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}





function ReportsTabEnhanced() {
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    stars: '',
    search: '',
    sortField: 'created_at',
    sortDir: 'desc',
  });
  const [page, setPage] = useState(1);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: PAGE_SIZE.toString(),
        offset: ((page - 1) * PAGE_SIZE).toString(),
        ...(filters.category && { category: filters.category }),
        ...(filters.stars !== '' && { min_stars: filters.stars }),
      });

      const res = await apiFetch(`/api/dashboard/reports?${params}`);
      const data = await res.json();

      let result = data.reports || [];

      
      if (filters.search) {
        const q = filters.search.toLowerCase();
        result = result.filter(
          (r) =>
            r.nama?.toLowerCase().includes(q) ||
            r.char_target?.toLowerCase().includes(q)
        );
      }

      
      result.sort((a, b) => {
        const aVal = a[filters.sortField] ?? '';
        const bVal = b[filters.sortField] ?? '';
        const cmp = typeof aVal === 'string' ? aVal.localeCompare(bVal) : aVal - bVal;
        return filters.sortDir === 'asc' ? cmp : -cmp;
      });

      setReports(result);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleSort = (field) => {
    setFilters((prev) => ({
      ...prev,
      sortField: field,
      sortDir: prev.sortField === field && prev.sortDir === 'desc' ? 'asc' : 'desc',
    }));
  };

  const SortIcon = ({ field }) => {
    if (filters.sortField !== field) return <CaretUpDown weight="bold" className="text-slate-300" />;
    return filters.sortDir === 'desc' ? (
      <CaretDown weight="bold" className="text-blue-500" />
    ) : (
      <CaretUp weight="bold" className="text-blue-500" />
    );
  };

  return (
    <>
      <header className="mb-6">
        <h2 className="text-3xl font-bold text-slate-800 mb-1">Laporan Nilai</h2>
        <p className="text-slate-500 font-medium text-sm">Riwayat latihan dan perkembangan siswa</p>
      </header>

      {}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-6">
        <div className="flex flex-wrap items-center gap-3">
          {}
          <div className="relative flex-1 min-w-[200px]">
            <MagnifyingGlass weight="bold" className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300 text-sm" />
            <input
              type="text"
              placeholder="Cari nama siswa atau karakter..."
              value={filters.search}
              onChange={(e) => { setFilters((p) => ({ ...p, search: e.target.value })); setPage(1); }}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-50 transition-all"
            />
            {filters.search && (
              <button
                onClick={() => setFilters((p) => ({ ...p, search: '' }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500"
              >
                <XCircle weight="bold" className="text-sm" />
              </button>
            )}
          </div>

          {}
          <select
            value={filters.category}
            onChange={(e) => { setFilters((p) => ({ ...p, category: e.target.value })); setPage(1); }}
            className="px-3 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-300 bg-white"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>

          {}
          <select
            value={filters.stars}
            onChange={(e) => { setFilters((p) => ({ ...p, stars: e.target.value })); setPage(1); }}
            className="px-3 py-2.5 rounded-xl border border-slate-200 text-sm font-medium outline-none focus:border-blue-300 bg-white"
          >
            {STAR_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          {}
          {[filters.category, filters.stars, filters.search].filter(Boolean).length > 0 && (
            <span className="flex items-center gap-1 text-xs font-bold text-blue-500 bg-blue-50 px-2.5 py-1.5 rounded-lg">
              <Funnel weight="bold" />
              {[filters.category, filters.stars, filters.search].filter(Boolean).length} filter aktif
            </span>
          )}
        </div>
      </div>

      {}
      <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
        {loading && reports.length === 0 ? (
          <div className="py-20 text-center text-slate-300">
            <ChartLineUp weight="fill" className="text-5xl mx-auto mb-3 animate-pulse" />
            <p className="text-sm font-medium">Memuat data laporan...</p>
          </div>
        ) : reports.length === 0 ? (
          <div className="py-20 text-center text-slate-300">
            <ChartLineUp weight="fill" className="text-5xl mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700 mb-2">Tidak ada data</h3>
            <p className="text-slate-400 text-sm">
              {filters.search || filters.category || filters.stars
                ? 'Coba ubah filter pencarian Anda'
                : 'Data latihan akan muncul di sini setelah siswa mulai berlatih'}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-blue-500 select-none" onClick={() => handleSort('nama')}>
                      <div className="flex items-center gap-1">Siswa <SortIcon field="nama" /></div>
                    </th>
                    <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Kelas</th>
                    <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-blue-500 select-none" onClick={() => handleSort('char_target')}>
                      <div className="flex items-center gap-1">Karakter <SortIcon field="char_target" /></div>
                    </th>
                    <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-blue-500 select-none" onClick={() => handleSort('accuracy')}>
                      <div className="flex items-center gap-1">Akurasi <SortIcon field="accuracy" /></div>
                    </th>
                    <th className="text-left px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-blue-500 select-none" onClick={() => handleSort('stars')}>
                      <div className="flex items-center gap-1">Bintang <SortIcon field="stars" /></div>
                    </th>
                    <th className="text-right px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-blue-500 select-none" onClick={() => handleSort('created_at')}>
                      <div className="flex items-center justify-end gap-1">Tanggal <SortIcon field="created_at" /></div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${r.nama}`}
                            className="w-8 h-8 rounded-full bg-slate-100"
                            alt=""
                          />
                          <span className="font-bold text-sm text-slate-700">{r.nama}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">{r.kelas || '-'}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-sm font-bold">
                          &quot;{r.char_target}&quot;
                          {r.category && (
                            <span className="ml-1.5 text-[10px] font-medium text-slate-400 normal-case">
                              ({r.category})
                            </span>
                          )}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2.5 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                r.accuracy >= 80 ? 'bg-gradient-to-r from-emerald-300 to-emerald-500' :
                                r.accuracy >= 60 ? 'bg-gradient-to-r from-blue-300 to-blue-500' :
                                r.accuracy >= 40 ? 'bg-gradient-to-r from-orange-300 to-orange-500' :
                                'bg-gradient-to-r from-slate-300 to-slate-400'
                              }`}
                              style={{ width: `${Math.min(r.accuracy, 100)}%` }}
                            />
                          </div>
                          <span className="text-sm font-bold text-slate-600 w-10">{r.accuracy}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-base">{renderStars(r.stars)}</td>
                      <td className="px-6 py-4 text-sm text-slate-400 text-right whitespace-nowrap">
                        {r.created_at
                          ? new Date(r.created_at).toLocaleDateString('id-ID', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100">
                <p className="text-xs text-slate-400 font-medium">
                  Menampilkan {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} dari {total} data
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 text-slate-500 disabled:opacity-30 hover:bg-slate-50 transition-colors"
                  >
                    ← Sebelumnya
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter(
                      (p) =>
                        p === 1 ||
                        p === totalPages ||
                        Math.abs(p - page) <= 1
                    )
                    .map((p, i, arr) => (
                      <span key={p}>
                        {i > 0 && arr[i - 1] !== p - 1 && (
                          <span className="px-1 text-slate-300">…</span>
                        )}
                        <button
                          onClick={() => setPage(p)}
                          className={`w-8 h-8 rounded-lg text-xs font-bold transition-colors ${
                            p === page
                              ? 'bg-blue-500 text-white'
                              : 'border border-slate-200 text-slate-500 hover:bg-slate-50'
                          }`}
                        >
                          {p}
                        </button>
                      </span>
                    ))}
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 text-slate-500 disabled:opacity-30 hover:bg-slate-50 transition-colors"
                  >
                    Selanjutnya →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}




function EnrollTab({ supabase, students }) {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleEnrolled = useCallback(() => {
    
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <>
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 mb-1">Upload Wajah Siswa</h2>
        <p className="text-slate-500 font-medium text-sm">Daftarkan foto wajah siswa agar bisa login dengan deteksi wajah</p>
      </header>

      <FaceEnrollmentForm
        key={refreshKey}
        students={students}
        onEnrolled={handleEnrolled}
      />
    </>
  );
}

function ModulesTab() {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/lessons')
      .then((res) => res.json())
      .then((data) => {
        setLessons(data || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  
  const categories = useMemo(() => {
    const groups = {
      besar: { label: 'Huruf Besar', subtitle: 'A – Z', icon: '🔤', color: 'from-blue-400 to-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', textColor: 'text-blue-600' },
      kecil: { label: 'Huruf Kecil', subtitle: 'a – z', icon: '✏️', color: 'from-emerald-400 to-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', textColor: 'text-emerald-600' },
      angka: { label: 'Angka', subtitle: '0 – 9', icon: '🔢', color: 'from-orange-400 to-orange-600', bg: 'bg-orange-50', border: 'border-orange-200', textColor: 'text-orange-600' },
    };

    
    const seen = {};
    (lessons || []).forEach((l) => {
      const cat = l.category || '';
      if (!groups[cat]) groups[cat] = { label: cat, subtitle: '', icon: '📚', color: 'from-slate-400 to-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', textColor: 'text-slate-600' };
      if (!groups[cat].items) groups[cat].items = [];
      const key = cat + ':' + l.char_target;
      if (!seen[key]) {
        seen[key] = true;
        groups[cat].items.push(l);
      }
    });

    
    if (!lessons || lessons.length === 0) {
      for (let i = 0; i < 26; i++) {
        if (!groups.besar.items) groups.besar.items = [];
        groups.besar.items.push({ id: i + 1, char_target: String.fromCharCode(65 + i), category: 'besar', is_active: true });
      }
      for (let i = 0; i < 26; i++) {
        if (!groups.kecil.items) groups.kecil.items = [];
        groups.kecil.items.push({ id: 26 + i + 1, char_target: String.fromCharCode(97 + i), category: 'kecil', is_active: true });
      }
      for (let i = 0; i < 10; i++) {
        if (!groups.angka.items) groups.angka.items = [];
        groups.angka.items.push({ id: 52 + i + 1, char_target: String(i), category: 'angka', is_active: true });
      }
    }

    return Object.entries(groups).filter(([, g]) => g.items && g.items.length > 0);
  }, [lessons]);

  return (
    <>
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 mb-1">Modul Materi</h2>
        <p className="text-slate-500 font-medium text-sm">
          Kelola modul pelajaran — {loading ? '...' : lessons.length || 62} modul tersedia
        </p>
      </header>

      {categories.map(([catKey, cat]) => (
        <div key={catKey} className="mb-8 last:mb-0">
          {}
          <div className={`flex items-center gap-3 mb-4 ${cat.bg} rounded-2xl px-5 py-3 border ${cat.border}`}>
            <span className="text-2xl">{cat.icon}</span>
            <div>
              <h3 className={`font-bold ${cat.textColor} text-lg`}>
                {cat.label}{' '}
                <span className="text-slate-400 font-normal text-base">{cat.subtitle}</span>
              </h3>
              <p className="text-xs text-slate-400">
                {cat.items?.length || 0} modul · Semua aktif
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs font-bold text-emerald-600 bg-white px-2.5 py-1 rounded-full shadow-sm">
                ✓ Aktif
              </span>
            </div>
          </div>

          {}
          <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-13 xl:grid-cols-16 gap-2">
            {(cat.items || []).map((lesson) => (
              <div
                key={lesson.id || lesson.char_target}
                className={`${cat.bg} ${cat.border} rounded-xl p-2 md:p-3 flex flex-col items-center gap-1 hover:shadow-md transition-all group cursor-pointer`}
                title={`Modul ${cat.label} "${lesson.char_target}"`}
              >
                <span className={`text-lg md:text-2xl lg:text-3xl font-bold ${cat.textColor} group-hover:scale-110 transition-transform`}>
                  {lesson.char_target}
                </span>
                <span className="text-[9px] md:text-[10px] text-slate-400 font-medium leading-tight text-center">
                  {lesson.char_target.length === 1 && lesson.char_target >= 'A' && lesson.char_target <= 'Z'
                    ? `Huruf ${lesson.char_target}`
                    : lesson.char_target >= 'a' && lesson.char_target <= 'z'
                    ? `huruf ${lesson.char_target}`
                    : `Angka ${lesson.char_target}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {}
      {!loading && (
        <div className="mt-6 bg-gradient-to-r from-pastel-sky/10 via-purple-50/30 to-pastel-mint/10 rounded-2xl p-5 border border-slate-100">
          <div className="flex items-center justify-center gap-6 flex-wrap">
            {categories.map(([catKey, cat]) => (
              <div key={catKey} className="flex items-center gap-2">
                <span>{cat.icon}</span>
                <span className="text-sm font-medium text-slate-600">
                  {cat.label}: <strong className={cat.textColor}>{cat.items?.length || 0}</strong> modul
                </span>
              </div>
            ))}
            <div className="w-px h-5 bg-slate-200" />
            <span className="text-sm font-bold text-slate-700">
              Total: <strong className="text-blue-600">{lessons.length || 62}</strong> modul
            </span>
          </div>
        </div>
      )}
    </>
  );
}






function AnalyticsTab({ heatmapData, charRankings, classComparison, students, onStudentClick }) {
  const [trendStudentId, setTrendStudentId] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [trendLoading, setTrendLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState('');

  useEffect(() => {
    if (!trendStudentId) { setTrendData(null); return; }
    setTrendLoading(true);
    apiFetch(`/api/dashboard/student-trend/${trendStudentId}?window=30`)
      .then(r => r.json())
      .then(d => { setTrendData(d); setTrendLoading(false); })
      .catch(() => setTrendLoading(false));
  }, [trendStudentId]);

  const handleExport = async (fmt) => {
    setExporting(true);
    setExportMsg('');
    try {
      const res = await apiFetch(`/api/dashboard/export?format=${fmt}`);
      if (fmt === 'csv') {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `sahabat_aksara_laporan_${new Date().toISOString().slice(0,10)}.csv`;
        a.click(); URL.revokeObjectURL(url);
        setExportMsg('CSV berhasil diunduh!');
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `sahabat_aksara_laporan_${new Date().toISOString().slice(0,10)}.json`;
        a.click(); URL.revokeObjectURL(url);
        setExportMsg(`JSON: ${data.total_records} records`);
      }
    } catch (e) { setExportMsg('Gagal export: ' + e.message); }
    setExporting(false);
    setTimeout(() => setExportMsg(''), 4000);
  };

  const heatColor = (val) => {
    if (val == null) return '#f1f5f9';
    if (val >= 80) return '#22c55e'; if (val >= 60) return '#84cc16';
    if (val >= 45) return '#eab308'; if (val >= 25) return '#f97316';
    return '#ef4444';
  };
  const catColor = (cat) => cat === 'besar' ? '#3b82f6' : cat === 'kecil' ? '#10b981' : '#f59e0b';

  return (
    <>
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 mb-1">Analitik Lanjutan</h2>
            <p className="text-slate-500 font-medium text-sm">PSD-4: Visualisasi mendalam untuk guru</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => handleExport('json')} disabled={exporting} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 text-blue-600 font-bold text-sm hover:bg-blue-100 transition-colors disabled:opacity-50">
              <DownloadSimple weight="bold" /> Export JSON
            </button>
            <button onClick={() => handleExport('csv')} disabled={exporting} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-50 text-emerald-600 font-bold text-sm hover:bg-emerald-100 transition-colors disabled:opacity-50">
              <DownloadSimple weight="bold" /> Export CSV
            </button>
          </div>
        </div>
        {exportMsg && (<div className="mt-2 flex items-center gap-2 text-sm font-bold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg"><Check weight="bold" /> {exportMsg}</div>)}
      </header>

      {}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {}
        <SectionErrorBoundary section="Heatmap Akurasi">
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div><h3 className="text-lg font-bold text-slate-800">Heatmap Akurasi</h3><p className="text-xs text-slate-400">Siswa x Karakter</p></div>
            <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">PSD-4.1</span>
          </div>
          {!heatmapData ? (
            <div className="h-[300px] flex items-center justify-center text-slate-300"><p className="text-sm">Memuat...</p></div>
          ) : !heatmapData.matrix?.length ? (
            <div className="h-[300px] flex items-center justify-center text-slate-300"><p className="text-sm">Belum ada data</p></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr><th className="px-2 py-1.5 text-left text-slate-400 font-bold sticky left-0 bg-white z-10 min-w-[100px]">Siswa</th>
                  {(heatmapData.characters || []).slice(0, 15).map(c => <th key={c} className="px-1 py-1.5 text-center text-slate-500 font-bold min-w-[32px]">{c}</th>)}</tr></thead>
                <tbody>{heatmapData.matrix.map(row => (
                  <tr key={row.student_id} className="hover:bg-slate-50">
                    <td className="px-2 py-1 font-bold text-slate-700 sticky left-0 bg-white whitespace-nowrap cursor-pointer hover:text-blue-600" onClick={() => { const s = students.find(s => s.id === row.student_id); if (s) onStudentClick(s); }}>{row.nama}</td>
                    {(heatmapData.characters || []).slice(0, 15).map(c => {
                      const val = row.scores[c];
                      return (<td key={c} className="px-0.5 py-1 text-center" style={{ backgroundColor: val != null ? heatColor(val) + '20' : 'transparent' }}>
                        <span className={`inline-flex items-center justify-center w-7 h-6 rounded text-[10px] font-black ${val != null ? 'text-white' : 'text-slate-300'}`} style={{ backgroundColor: val != null ? heatColor(val) : undefined }}>{val != null ? Math.round(val) : '-'}</span>
                      </td>);
                    })}
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>
        </SectionErrorBoundary>

        {}
        <SectionErrorBoundary section="Ranking Huruf">
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div><h3 className="text-lg font-bold text-slate-800">Ranking Kesulitan Huruf</h3><p className="text-xs text-slate-400">Mudah ke Sulit (bawah = sulit)</p></div>
            <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">PSD-4.3</span>
          </div>
          {charRankings.length === 0 ? (
            <div className="h-[320px] flex items-center justify-center text-slate-300"><p className="text-sm">Memuat...</p></div>
          ) : (
            <ResponsiveContainer width="100%" height={320}><BarChart data={charRankings.slice(0, 25)} layout="vertical" margin={{ left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} unit="%" />
              <YAxis dataKey="character" type="category" width={28} tick={{ fontSize: 13, fill: '#475569', fontWeight: 700 }} axisLine={false} tickLine={false} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload;
                return (<div className="bg-white rounded-xl shadow-lg border border-slate-100 p-3 min-w-[180px]"><p className="text-sm font-bold text-slate-700">{d.character} ({d.category})</p><p className="text-xs text-slate-500 mt-1">Avg: <strong>{d.avg_accuracy}%</strong> ({d.attempts}x)</p><p className="text-xs text-slate-400">{d.min_accuracy}% - {d.max_accuracy}%</p></div>);
              }} />
              <Bar dataKey="avg_accuracy" radius={[0, 4, 4, 0]} maxBarSize={24} name="Akurasi %">
                {charRankings.slice(0, 25).map((entry, idx) => (<Cell key={idx} fill={catColor(entry.category)} opacity={0.85} />))}
              </Bar>
              <ReferenceLine x={60} stroke="#94a3b8" strokeDasharray="4 4" label="Target 60%" fontSize={9} fill="#94a3b8" />
            </BarChart></ResponsiveContainer>
          )}
          <div className="flex items-center justify-center gap-4 mt-3 pt-3 border-t border-slate-100">
            {[{c:'besar',l:'Huruf Besar'},{c:'kecil',l:'Huruf Kecil'},{c:'angka',l:'Angka'}].map(x => (
              <span key={x.c} className="flex items-center gap-1.5 text-xs font-medium text-slate-500"><span className="w-3 h-3 rounded-sm" style={{backgroundColor: catColor(x.c)}} /> {x.l}</span>
            ))}
          </div>
        </div>
        </SectionErrorBoundary>
      </div>

      {}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {}
        <SectionErrorBoundary section="Trend Siswa">
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div><h3 className="text-lg font-bold text-slate-800">Trend Perkembangan Siswa</h3><p className="text-xs text-slate-400">30 hari terakhir</p></div>
            <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">PSD-4.2</span>
          </div>
          <select value={trendStudentId || ''} onChange={(e) => setTrendStudentId(e.target.value || null)} className="w-full mb-4 px-3 py-2 rounded-xl border border-slate-200 text-sm outline-none focus:border-blue-300 bg-white">
            <option value="">-- Pilih Siswa --</option>
            {(students || []).map(s => (<option key={s.id} value={s.id}>{s.nama} ({s.kelas || '-'})</option>))}
          </select>
          {trendLoading ? (
            <div className="h-[250px] flex items-center justify-center text-slate-300"><p className="text-sm">Memuat trend...</p></div>
          ) : !trendData ? (
            <div className="h-[250px] flex items-center justify-center text-slate-300"><p className="text-sm">Pilih siswa untuk melihat trend</p></div>
          ) : (
            <>
              <div className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full mb-3 ${trendData.trend === 'improving' ? 'bg-emerald-50 text-emerald-600' : trendData.trend === 'declining' ? 'bg-red-50 text-red-500' : 'bg-slate-100 text-slate-500'}`}>
                {trendData.trend === 'improving' && <TrendUp weight="bold" />}{trendData.trend === 'declining' && <TrendDown weight="bold" />}
                Trend: {trendData.trend === 'improving' ? 'Meningkat!' : trendData.trend === 'declining' ? 'Menurun' : 'Stabil'} ({trendData.slope_per_day > 0 ? '+' : ''}{trendData.slope_per_day}%/hari)
              </div>
              <ResponsiveContainer width="100%" height={240}><LineChart data={trendData.series.filter(s => s.avg_accuracy != null)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" tickFormatter={(v) => v.slice(5)} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (<div className="bg-white rounded-lg shadow-lg border border-slate-100 p-2.5"><p className="text-xs font-bold text-slate-500">{d.date}</p><p className="text-sm font-bold text-slate-700">{d.avg_accuracy}% ({d.exercise_count} latihan)</p>{d.moving_avg_7d && <p className="text-[10px] text-slate-400">MA7: {d.moving_avg_7d}%</p>}</div>);
                }} />
                <Line type="monotone" dataKey="avg_accuracy" stroke="#3b82f6" strokeWidth={2.5} dot={false} />
                {trendData.series.some(s => s.moving_avg_7d) && <Line type="monotone" dataKey="moving_avg_7d" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />}
              </LineChart></ResponsiveContainer>
              <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-50 rounded-lg py-2"><p className="text-lg font-bold text-slate-700">{trendData.total_exercises}</p><p className="text-[10px] text-slate-400 uppercase">Latihan</p></div>
                <div className="bg-blue-50 rounded-lg py-2"><p className="text-lg font-bold text-blue-600">{trendData.best_day ? (trendData.series.find(s => s.date === trendData.best_day)?.avg_accuracy ?? '-') : '-'}</p><p className="text-[10px] text-blue-400 uppercase">Terbaik</p></div>
                <div className="bg-purple-50 rounded-lg py-2"><p className="text-lg font-bold text-purple-600">{trendData.window_days}</p><p className="text-[10px] text-purple-400 uppercase">Hari</p></div>
              </div>
            </>
          )}
        </div>
        </SectionErrorBoundary>

        {}
        <SectionErrorBoundary section="Perbandingan Kelas">
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div><h3 className="text-lg font-bold text-slate-800">Perbandingan Kelas</h3><p className="text-xs text-slate-400">7 hari terakhir</p></div>
            <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">PSD-4.4</span>
          </div>
          {classComparison.length === 0 ? (
            <div className="h-[350px] flex items-center justify-center text-slate-300"><p className="text-sm">Memuat...</p></div>
          ) : (
            <ResponsiveContainer width="100%" height={340}><BarChart data={classComparison} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis dataKey="class_name" type="category" width={75} tick={{ fontSize: 12, fill: '#475569', fontWeight: 700 }} axisLine={false} tickLine={false} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload;
                return (<div className="bg-white rounded-xl shadow-lg border border-slate-100 p-3 min-w-[200px]"><p className="text-sm font-bold text-slate-700">{d.class_name}</p><div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 text-xs"><span className="text-slate-500">Siswa:</span><span className="font-bold">{d.total_students}</span><span className="text-slate-500">Aktif:</span><span className="font-bold text-emerald-600">{d.active_students_week}</span><span className="text-slate-500">Latihan:</span><span className="font-bold">{d.total_exercises_week}</span><span className="text-slate-500">Avg Acc:</span><span className="font-bold text-blue-600">{d.avg_accuracy}%</span><span className="text-slate-500">Top:</span><span className="font-bold text-emerald-600">{d.top_accuracy}%</span><span className="text-slate-500">Bottom:</span><span className="font-bold text-red-500">{d.bottom_accuracy}%</span></div></div>);
              }} />
              <Bar dataKey="avg_accuracy" radius={[0, 4, 4, 0]} maxBarSize={36} fill="#8b5cf6" />
              <ReferenceLine x={60} stroke="#94a3b8" strokeDasharray="4 4" label="Target" fontSize={9} />
            </BarChart></ResponsiveContainer>
          )}
          <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-100">
            {classComparison.map(cls => (<div key={cls.class_name} className="bg-slate-50 rounded-xl p-3"><p className="text-sm font-bold text-slate-700">{cls.class_name}</p><div className="flex items-center justify-between mt-1"><span className="text-[10px] text-slate-400">{cls.total_students} siswa · {cls.active_students_week} aktif</span><span className="text-xs font-bold text-blue-600">{cls.avg_accuracy ?? '-'}%</span></div></div>))}
          </div>
        </div>
        </SectionErrorBoundary>
      </div>

      {}
      <SectionErrorBoundary section="Pie Chart Stars">
      <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <div><h3 className="text-lg font-bold text-slate-800">Distribusi Bintang</h3><p className="text-xs text-slate-400">Proporsi per kategori bintang</p></div>
          <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">PSD-4.5</span>
        </div>
        <StarsPieChartInline summary={null} />
      </div>
      </SectionErrorBoundary>
    </>
  );
}

function StarsPieChartInline({ summary }) {
  const [starDist, setStarDist] = useState([]);
  useEffect(() => {
    apiFetch('/api/dashboard/reports?limit=9999').then(r => r.json()).then(data => {
      const reports = data.reports || [];
      const counts = [0, 0, 0, 0];
      reports.forEach(r => { const s = r.stars ?? 0; if (s >= 0 && s <= 3) counts[s] += 1; });
      setStarDist([{ name: '3 Bintang', value: counts[3], color: '#fbbf24' }, { name: '2 Bintang', value: counts[2], color: '#fb923c' }, { name: '1 Bintang', value: counts[1], color: '#f87171' }, { name: '0 Bintang', value: counts[0], color: '#e2e8f0' }].filter(d => d.value > 0));
    }).catch(() => {});
  }, []);
  const total = starDist.reduce((s, d) => s + d.value, 0);
  return (
    <div className="flex items-center gap-8">
      <ResponsiveContainer width={220} height={220}><PieChart>
        <Pie data={starDist} cx="50%" cy="50%" innerRadius={55} outerRadius={95} paddingAngle={3} dataKey="value" nameKey="name">
          {starDist.map((entry, idx) => (<Cell key={idx} fill={entry.color} stroke="white" strokeWidth={2} />))}
        </Pie>
        <Tooltip formatter={(v, n) => [`${v} (${total > 0 ? ((v/total)*100).toFixed(1) : 0}%)`, n]} />
      </PieChart></ResponsiveContainer>
      <div className="flex-1 space-y-2.5">
        {starDist.map(d => (<div key={d.name} className="flex items-center gap-3">
          <span className="w-4 h-4 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
          <span className="text-sm font-bold text-slate-600 w-24">{d.name}</span>
          <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden"><div className="h-full rounded-full" style={{ width: `${total > 0 ? (d.value/total)*100 : 0}%`, backgroundColor: d.color }} /></div>
          <span className="text-sm font-bold text-slate-700 w-14 text-right">{d.value}</span>
          <span className="text-[10px] text-slate-400 w-12">{total > 0 ? ((d.value/total)*100).toFixed(0) : 0}%</span>
        </div>))}
        <div className="pt-2 border-t border-slate-100 mt-2"><p className="text-xs text-slate-400">Total: <strong className="text-slate-700">{total}</strong> latihan</p></div>
      </div>
    </div>
  );
}




function userDisplayName() {
  
  try {
    const authState = useAuthStore.getState();
    return authState.user?.nama?.split(' ')[0] || 'Guru';
  } catch {
    return 'Guru';
  }
}

function getGreeting(date) {
  const hour = date.getHours();
  if (hour < 11) return 'Selamat Pagi';
  if (hour < 15) return 'Selamat Siang';
  if (hour < 18) return 'Selamat Sore';
  return 'Selamat Malam';
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '-';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Baru saja';
  if (mins < 60) return `${mins} menit lalu`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} jam lalu`;
  const days = Math.floor(hours / 24);
  return `${days} hari lalu`;
}

function renderStars(count) {
  const n = count ?? 0;
  return (
    <span className="text-sm">
      {'⭐'.repeat(Math.min(n, 3))}{'☆'.repeat(Math.max(0, 3 - n))}
    </span>
  );
}
