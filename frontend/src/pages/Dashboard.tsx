import { type FC } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import { SLAIndicator } from '../components/SLAIndicator';
import { LiveFeed } from '../components/LiveFeed';
import { LeadCard } from '../components/LeadCard';
import { useWebSocket } from '../hooks/useWebSocket';
import { Users, CheckCircle, Calendar, Zap } from 'lucide-react';
import './Dashboard.css';

export const Dashboard: FC = () => {
  const { stats, leads, isConnected } = useDashboardStore();
  
  // Connect to WebSocket (replace with actual backend URL in production)
  useWebSocket('ws://localhost:8000/ws/dashboard');

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header__left">
          <h1 className="dashboard-title">Centro de Operações</h1>
          <p className="dashboard-subtitle">Monitoramento em tempo real do Agente de Vendas</p>
        </div>
        <div className="dashboard-header__right">
          <div className={`connection-status ${isConnected ? 'online' : 'offline'}`}>
            {isConnected ? 'Sistema Online' : 'Tentando conectar...'}
          </div>
        </div>
      </header>

      <section className="stats-grid">
        <div className="stat-card premium-card">
          <div className="stat-card__icon users">
            <Users size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">Total de Leads</span>
            <span className="stat-card__value">{stats?.total_leads || 0}</span>
          </div>
        </div>

        <div className="stat-card premium-card">
          <div className="stat-card__icon qualified">
            <CheckCircle size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">Leads Qualificados</span>
            <span className="stat-card__value">{stats?.qualified_leads || 0}</span>
          </div>
        </div>

        <div className="stat-card premium-card">
          <div className="stat-card__icon scheduled">
            <Calendar size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">Agendamentos</span>
            <span className="stat-card__value">{stats?.scheduled_meetings || 0}</span>
          </div>
        </div>

        <div className="stat-card premium-card">
          <div className="stat-card__icon sla">
            <Zap size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">SLA Médio</span>
            <span className="stat-card__value">{stats?.avg_speed_to_lead || 0}s</span>
          </div>
        </div>
      </section>

      <div className="dashboard-main">
        <div className="dashboard-left-col">
          <div className="section-header">
            <h2 className="section-title">Leads Recentes</h2>
            <button className="view-all-btn">Ver todos</button>
          </div>
          <div className="leads-list">
            {leads.length === 0 ? (
              <div className="empty-state">Nenhum lead processado ainda.</div>
            ) : (
              leads.map((lead) => (
                <LeadCard key={lead.id} lead={lead} />
              ))
            )}
          </div>
        </div>

        <div className="dashboard-right-col">
          <div className="section-header">
            <h2 className="section-title">Timeline do Agente</h2>
          </div>
          <LiveFeed />
          
          <div className="sla-monitor-section">
            <h3 className="section-subtitle">Monitoramento de SLA Ativo</h3>
            <div className="sla-indicators-grid">
               {/* Example indicator, usually we would map active leads here */}
               <SLAIndicator elapsedSeconds={45} />
               <SLAIndicator elapsedSeconds={110} />
               <SLAIndicator elapsedSeconds={150} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
