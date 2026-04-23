import { useEffect, useRef } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import { type AgentEvent } from '../types/api';

export const useWebSocket = (url: string) => {
  const socketRef = useRef<WebSocket | null>(null);
  const { addEvent, setConnected, updateLead } = useDashboardStore();

  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('Connected to WebSocket');
        setConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const data: AgentEvent = JSON.parse(event.data);
          addEvent(data);
          
          if (data.type === 'state_change') {
            // If it's a lead update, we might want to update the lead list
            // Depending on how the payload is structured
            if (data.payload.lead) {
               updateLead(data.payload.lead);
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      socket.onclose = () => {
        console.log('Disconnected from WebSocket. Reconnecting...');
        setConnected(false);
        setTimeout(connect, 3000); // Reconnect after 3 seconds
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        socket.close();
      };
    };

    connect();

    return () => {
      socketRef.current?.close();
    };
  }, [url, addEvent, setConnected, updateLead]);

  return socketRef.current;
};
