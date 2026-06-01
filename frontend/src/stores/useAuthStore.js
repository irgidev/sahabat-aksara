import { create } from 'zustand';

const INIT_TIMEOUT_MS = 8000; 

const useAuthStore = create((set, get) => ({
  
  user: null,
  isAuthenticated: false,
  isLoading: true,

  
  initialize: async (supabase) => {
    
    const timer = setTimeout(() => {
      console.warn('[Auth] Init timed out, falling back to unauthenticated');
      set({ isLoading: false });
    }, INIT_TIMEOUT_MS);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      clearTimeout(timer);

      if (session?.user) {
        
        const { data: profile } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', session.user.id)
          .single();

        set({
          user: profile || {
            id: session.user.id,
            email: session.user.email,
            nama: session.user.user_metadata?.nama || 'Guru',
            role: 'teacher',
          },
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      clearTimeout(timer);
      console.error('Auth init error:', error);
      set({ isLoading: false });
    }
  },

  
  login: (userData) => {
    set({
      user: userData,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  
  logout: async (supabase) => {
    if (supabase) {
      await supabase.auth.signOut();
    }
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  
  setLoading: (loading) => set({ isLoading: loading }),
}));

export default useAuthStore;
