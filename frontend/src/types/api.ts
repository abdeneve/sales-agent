export type LeadStatus = 'new' | 'qualifying' | 'qualified' | 'disqualified' | 'scheduled';

export interface Lead {
  id: string;
  name: string | null;
  phone: string;
  status: LeadStatus;
  user_intent: string | null;
  is_qualified: boolean;
  meeting_scheduled: boolean;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  lead_id: string;
  messages: Message[];
  status: 'active' | 'archived';
}

export interface DashboardStats {
  total_leads: number;
  qualified_leads: number;
  scheduled_meetings: number;
  avg_speed_to_lead: number;
  sla_status: {
    green: number;
    yellow: number;
    red: number;
  };
}

export interface AgentEvent {
  type: 'state_change' | 'message' | 'notification';
  lead_id: string;
  payload: any;
  timestamp: string;
}
