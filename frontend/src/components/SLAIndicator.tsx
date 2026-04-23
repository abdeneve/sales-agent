import { type FC, useMemo } from 'react';
import { Clock } from 'lucide-react';
import './SLAIndicator.css';

interface SLAIndicatorProps {
  /** Time in seconds since the first contact */
  elapsedSeconds: number;
}

type SLALevel = 'green' | 'yellow' | 'red';

function getSLALevel(seconds: number): SLALevel {
  if (seconds < 60) return 'green';
  if (seconds < 120) return 'yellow';
  return 'red';
}

export const SLAIndicator: FC<SLAIndicatorProps> = ({ elapsedSeconds }) => {
  const level = useMemo(() => getSLALevel(elapsedSeconds), [elapsedSeconds]);

  return (
    <div className={`sla-indicator sla-indicator--${level}`} id="sla-indicator">
      <div className="sla-indicator__icon">
        <Clock size={16} />
      </div>
      <div className="sla-indicator__content">
        <span className="sla-indicator__time">{elapsedSeconds}s</span>
        <span className="sla-indicator__label">Speed to Lead</span>
      </div>
    </div>
  );
};
