import { type FC } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import { format } from 'date-fns';
import { Activity, MessageSquare, Info, AlertCircle } from 'lucide-react';
import './LiveFeed.css';

export const LiveFeed: FC = () => {
  const events = useDashboardStore((state) => state.events);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'message': return <MessageSquare size={14} />;
      case 'state_change': return <Activity size={14} />;
      case 'notification': return <Info size={14} />;
      default: return <AlertCircle size={14} />;
    }
  };

  return (
    <div className="live-feed glass-panel">
      <div className="live-feed__header">
        <h3 className="live-feed__title">Centro de Operações</h3>
        <span className="live-feed__status">Live</span>
      </div>
      <div className="live-feed__content">
        {events.length === 0 ? (
          <div className="live-feed__empty">Aguardando eventos...</div>
        ) : (
          events.map((event, index) => (
            <div key={`${event.timestamp}-${index}`} className="live-feed__item">
              <div className="live-feed__item-icon">
                {getEventIcon(event.type)}
              </div>
              <div className="live-feed__item-content">
                <div className="live-feed__item-header">
                  <span className="live-feed__item-type">{event.type}</span>
                  <span className="live-feed__item-time">
                    {format(new Date(event.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                <div className="live-feed__item-payload">
                  {typeof event.payload === 'string' 
                    ? event.payload 
                    : JSON.stringify(event.payload).substring(0, 100) + '...'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
