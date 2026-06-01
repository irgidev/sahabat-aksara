import { Sparkle, RocketLaunch, ChalkboardTeacher } from '@phosphor-icons/react';

export default function Home({ onNavigate }) {
  return (
    <main className="view-section view-active bg-gradient-to-br from-pastel-sky/30 via-pastel-lavender/30 to-pastel-peach/30">
      {}
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-pastel-sky/40 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-float" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-pastel-peach/40 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-float-delayed" />

      <div className="relative h-full flex flex-col items-center justify-center p-4 md:p-8 lg:p-12 max-w-7xl mx-auto">
        {}
        <div className="text-center mb-8 md:mb-14 lg:mb-16 z-10">
          <div className="inline-flex items-center gap-2 px-3 md:px-4 py-1.5 md:py-2 rounded-full glass-panel text-xs md:text-sm font-bold text-slate-500 mb-4 md:mb-6 uppercase tracking-wider">
            <Sparkle weight="fill" className="text-pastel-yellow text-sm md:text-lg" />
            Platform Belajar Interaktif
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl font-bold text-slate-800 tracking-tight leading-tight mb-2 md:mb-4 drop-shadow-sm">
            Selamat Datang di{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-500">
              Sahabat Aksara
            </span>
          </h1>
          <p className="text-base md:text-lg lg:text-xl text-slate-600 max-w-xl md:max-w-2xl mx-auto font-medium px-4">
            Petualangan seru belajar membaca dan menulis dimulai dari sini!
          </p>
        </div>

        {}
        <div className="flex flex-col md:flex-row items-center gap-6 md:gap-8 z-10 w-full max-w-4xl lg:max-w-5xl justify-center">

          {}
          <button
            onClick={() => onNavigate('loginSiswa')}
            className="group relative w-full md:w-[26rem] lg:w-[28rem] h-64 md:h-72 lg:h-80 glass-panel rounded-[2rem] md:rounded-[2.5rem] shadow-glass-strong p-6 md:p-8 flex flex-col items-center justify-center transition-all duration-500 hover:-translate-y-3 md:hover:-translate-y-4 hover:shadow-2xl overflow-hidden cursor-pointer border-2 border-white/80 active:scale-[0.98]"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/10 z-0" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 md:w-48 h-40 md:h-48 bg-pastel-mint rounded-full filter blur-3xl opacity-50 group-hover:scale-150 transition-transform duration-700" />

            <div className="relative z-10 flex flex-col items-center">
              <div className="w-20 h-20 md:w-28 md:h-28 bg-white rounded-2xl md:rounded-3xl shadow-md flex items-center justify-center mb-4 md:mb-6 group-hover:rotate-12 transition-transform duration-300">
                <RocketLaunch weight="fill" className="text-4xl md:text-5xl lg:text-6xl text-pastel-sky" />
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-slate-800 mb-1 md:mb-2">
                Masuk Siswa
              </h2>
              <p className="text-slate-500 font-medium text-base md:text-lg">
                Mulai Belajar & Bermain! 🎨
              </p>
            </div>
          </button>

          {}
          <button
            onClick={() => onNavigate('loginGuru')}
            className="group relative w-full md:w-72 lg:w-80 h-56 md:h-60 lg:h-64 glass-panel rounded-2xl md:rounded-3xl shadow-glass p-6 md:p-8 flex flex-col items-center justify-center transition-all duration-300 hover:-translate-y-2 hover:shadow-xl cursor-pointer active:scale-[0.98]"
          >
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-14 h-14 md:w-16 md:h-16 bg-slate-50 rounded-xl md:rounded-2xl shadow-sm flex items-center justify-center mb-3 md:mb-4 group-hover:scale-110 transition-transform duration-300 border border-slate-100">
                <ChalkboardTeacher weight="fill" className="text-2xl md:text-3xl text-slate-400" />
              </div>
              <h2 className="text-lg md:text-xl font-bold text-slate-700 mb-1">Portal Guru</h2>
              <p className="text-slate-400 font-medium text-sm md:text-base">
                Dashboard & Laporan 📊
              </p>
            </div>
          </button>
        </div>

        {}
        <div className="mt-6 md:mt-10 text-center z-10">
          <p className="text-xs md:text-sm text-slate-400 font-medium px-4">
            Dibuat dengan ❤️ untuk anak-anak Indonesia
          </p>
        </div>
      </div>
    </main>
  );
}
