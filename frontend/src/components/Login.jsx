import { QrCode, Camera } from "@phosphor-icons/react";

export default function Login({ onNavigate }) {
  return (
    <main
      id="view-login"
      className="view-section view-active bg-gradient-to-tr from-pastel-lavender/40 via-white to-pastel-mint/20 flex items-center justify-center"
    >
      {}
      <div className="absolute top-20 right-20 w-72 h-72 bg-pastel-mint/50 rounded-full filter blur-[80px]"></div>
      <div className="absolute bottom-20 left-20 w-96 h-96 bg-pastel-sky/40 rounded-full filter blur-[100px]"></div>

      <div className="relative z-10 flex flex-col items-center">
        <h2 className="text-3xl md:text-4xl font-bold text-slate-700 mb-2 drop-shadow-sm">
          Tunjukkan Kartumu!
        </h2>
        <p className="text-slate-500 font-medium mb-10">
          Scan kartu QR untuk masuk ke portal ajaib.
        </p>

        {}
        <div className="relative w-80 h-80 md:w-96 md:h-96 rounded-[3rem] glass-panel border-4 border-dashed border-white/80 shadow-glow-mint flex items-center justify-center mb-12 overflow-hidden group">
          {}
          <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-transparent to-pastel-mint/20 border-b-2 border-pastel-mint/50 animate-[float_3s_ease-in-out_infinite]"></div>

          <div className="text-center opacity-50 group-hover:opacity-100 transition-opacity duration-300">
            <QrCode className="text-7xl text-slate-400 mb-4 block mx-auto" />
            <span className="font-bold text-slate-400">Area Kamera</span>
          </div>

          {}
          <div className="absolute top-6 left-6 w-12 h-12 border-t-4 border-l-4 border-white rounded-tl-2xl"></div>
          <div className="absolute top-6 right-6 w-12 h-12 border-t-4 border-r-4 border-white rounded-tr-2xl"></div>
          <div className="absolute bottom-6 left-6 w-12 h-12 border-b-4 border-l-4 border-white rounded-bl-2xl"></div>
          <div className="absolute bottom-6 right-6 w-12 h-12 border-b-4 border-r-4 border-white rounded-br-2xl"></div>
        </div>

        {}
        <button 
          onClick={() => onNavigate('canvas')}
          className="group relative px-12 py-5 rounded-full bg-gradient-to-r from-pastel-sky to-pastel-lavender shadow-xl shadow-pastel-sky/30 text-white font-bold text-2xl tracking-wide transition-all duration-300 hover:shadow-2xl hover:scale-105 active:scale-95 flex items-center gap-3"
        >
          <Camera weight="fill" className="text-3xl group-hover:rotate-12 transition-transform" />
          Mulai Scan
        </button>
      </div>
    </main>
  );
}
