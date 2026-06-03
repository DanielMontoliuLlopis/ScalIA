import { create } from "zustand";
import { api } from "../lib/api";

export interface ClientAccount {
  id: string;
  name: string;
  logo_url: string | null;
  business_type: string | null;
  color_palette: string;
  created_at: string;
}

interface ClientState {
  clientAccounts: ClientAccount[];
  activeClientId: string | null;
  setActiveClient: (id: string) => void;
  fetchClientAccounts: () => Promise<void>;
  reset: () => void;
}

export const useClientStore = create<ClientState>((set) => ({
  clientAccounts: [],
  activeClientId: localStorage.getItem("active_client_id"),

  setActiveClient: (id) => {
    localStorage.setItem("active_client_id", id);
    set({ activeClientId: id });
  },

  fetchClientAccounts: async () => {
    const accounts = await api.get<ClientAccount[]>("/client-accounts");
    set({ clientAccounts: accounts });

    // Si el activeClientId guardado ya no es válido, usar el primero.
    const saved = localStorage.getItem("active_client_id");
    if (!saved || !accounts.find((a) => a.id === saved)) {
      const first = accounts[0];
      if (first) {
        localStorage.setItem("active_client_id", first.id);
        set({ activeClientId: first.id });
      }
    }
  },

  reset: () => {
    localStorage.removeItem("active_client_id");
    set({ clientAccounts: [], activeClientId: null });
  },
}));
