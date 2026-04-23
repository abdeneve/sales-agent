import { type FC } from 'react';
import { type Lead } from '../types/api';
import { User, Phone, Calendar, CheckCircle, Clock } from 'lucide-react';
import './LeadCard.css';

interface LeadCardProps {
  lead: Lead;
  onClick?: (lead: Lead) => void;
}

export const LeadCard: FC<LeadCardProps> = ({ lead, onClick }) => {
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'qualified': return 'badge--success';
      case 'scheduled': return 'badge--success';
      case 'qualifying': return 'badge--warning';
      case 'disqualified': return 'badge--danger';
      default: return 'badge--neutral';
    }
  };

  return (
    <div className="lead-card premium-card" onClick={() => onClick?.(lead)}>
      <div className="lead-card__header">
        <div className="lead-card__avatar">
          <User size={20} />
        </div>
        <div className="lead-card__info">
          <h4 className="lead-card__name">{lead.name || 'Lead Anônimo'}</h4>
          <div className="lead-card__phone">
            <Phone size={12} />
            <span>{lead.phone}</span>
          </div>
        </div>
        <span className={`badge ${getStatusBadgeClass(lead.status)}`}>
          {lead.status}
        </span>
      </div>
      
      <div className="lead-card__body">
        <div className="lead-card__intent">
          <span className="lead-card__label">Intenção:</span>
          <span className="lead-card__value">{lead.user_intent || 'Analisando...'}</span>
        </div>
      </div>

      <div className="lead-card__footer">
        <div className="lead-card__stat">
          {lead.meeting_scheduled ? (
            <div className="lead-card__stat-item success">
              <Calendar size={14} />
              <span>Agendado</span>
            </div>
          ) : lead.is_qualified ? (
            <div className="lead-card__stat-item success">
              <CheckCircle size={14} />
              <span>Qualificado</span>
            </div>
          ) : (
            <div className="lead-card__stat-item warning">
              <Clock size={14} />
              <span>Em triagem</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
