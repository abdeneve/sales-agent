import { create } from 'zustand';
import { type Lead, type DashboardStats, type AgentEvent } from '../types/api';

interface DashboardState {
  leads: Lead[];
  stats: DashboardStats | null;
  events: AgentEvent[];
  isConnected: boolean;
  
  setLeads: (leads: Lead[]) => void;
  updateLead: (lead: Lead) => void;
  setStats: (stats: DashboardStats) => void;
  addEvent: (event: AgentEvent) => void;
  setConnected: (connected: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  leads: [],
  stats: null,
  events: [],
  isConnected: false,

  setLeads: (leads) => set({ leads }),
  
  updateLead: (updatedLead) => set((state) => ({
    leads: state.leads.map((l) => l.id === updatedLead.id ? updatedLead : l)
  })),

  setStats: (stats) => set({ stats }),

  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 50) // Keep last 50 events
  })),

  setConnected: (isConnected) => set({ isConnected }),
}));
