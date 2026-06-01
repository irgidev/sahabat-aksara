

import { House, PencilLine, UserCircle, SignOut } from '@phosphor-icons/react';

const NAV_ITEMS = [
  {
    id: 'home',
    label: 'Beranda',
    icon: House,
    color: 'text-blue-500',
    activeColor: 'text-blue-600 bg-blue-50',
  },
  {
    id: 'menu',
    label: 'Pelajaran',
    icon: PencilLine,
    color: 'text-emerald-500',
    activeColor: 'text-emerald-600 bg-emerald-50',
  },
  {
    id: 'profile',
    label: 'Profil',
    icon: UserCircle,
    color: 'text-purple-500',
    activeColor: 'text-purple-600 bg-purple-50',
  },
];

export default function KidNavBar({ activePage = 'home', onNavigate, student }) {
  const handleNav = (id) => {
    switch (id) {
      case 'home':
        
        if (onNavigate) onNavigate('berandaSiswa');
        break;
      case 'menu':
        
        if (onNavigate) onNavigate('menuSiswa');
        break;
      case 'profile':
        
        if (onNavigate) onNavigate('profilSiswa');
        break;
    }
  };

  return (
    <nav className="kid-nav-bar shrink-0 bg-white/90 backdrop-blur-xl border-t border-slate-100 shadow-[0_-4px_20px_rgba(0,0,0,0.04)]">
      <div className="max-w-lg mx-auto flex items-center justify-around px-2 py-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`kid-nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon
                weight={isActive ? 'fill' : 'regular'}
                className={`kid-nav-icon text-2xl transition-colors ${
                  isActive ? item.color.split(' ')[0] : 'text-slate-400'
                }`}
              />
              <span
                className={`kid-nav-label text-[11px] font-semibold transition-colors ${
                  isActive ? item.color.split(' ')[0] : 'text-slate-400'
                }`}
              >
                {item.label}
              </span>
            </button>
          );
        })}

        {}
        <button
          onClick={() => {
            if (onNavigate) onNavigate('home');
          }}
          className="kid-nav-item group"
          title="Keluar"
        >
          <SignOut
            weight="regular"
            className="kid-nav-icon text-2xl text-slate-300 group-hover:text-red-400 transition-colors"
          />
          <span className="kid-nav-label text-[11px] font-medium text-slate-300 group-hover:text-red-400 transition-colors">
            Keluar
          </span>
        </button>
      </div>
    </nav>
  );
}
