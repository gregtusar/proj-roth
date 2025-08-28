import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Activity, Database, Search, MapPin, Save, AlertCircle, Zap, ChevronRight } from 'lucide-react';
import { styled } from 'baseui';

// Styled components for better formatting
const VerboseContainer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  backgroundColor: $isDarkMode ? '#1f2937' : '#f9fafb',
  border: `1px solid ${$isDarkMode ? '#374151' : '#e5e7eb'}`,
  borderRadius: '8px',
  marginBottom: '12px',
  maxHeight: '240px',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.3s ease',
}));

const VerboseHeader = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '8px 12px',
  borderBottom: `1px solid ${$isDarkMode ? '#374151' : '#e5e7eb'}`,
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  backgroundColor: $isDarkMode ? '#111827' : '#f3f4f6',
  borderTopLeftRadius: '8px',
  borderTopRightRadius: '8px',
}));

const VerboseContent = styled('div', {
  flex: 1,
  overflowY: 'auto',
  padding: '8px',
  fontSize: '13px',
  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
  lineHeight: '1.5',
});

const EventItem = styled('div', ({ $isDarkMode, $isActive }: { $isDarkMode: boolean, $isActive: boolean }) => ({
  padding: '6px 8px',
  marginBottom: '4px',
  backgroundColor: $isActive 
    ? ($isDarkMode ? '#374151' : '#dbeafe')
    : ($isDarkMode ? '#1f2937' : '#ffffff'),
  border: `1px solid ${$isActive 
    ? ($isDarkMode ? '#4b5563' : '#93c5fd')
    : ($isDarkMode ? '#374151' : '#e5e7eb')}`,
  borderRadius: '4px',
  transition: 'all 0.2s ease',
}));

const EventHeader = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  marginBottom: '4px',
});

const EventTitle = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '12px',
  fontWeight: 600,
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const EventDetail = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '11px',
  color: $isDarkMode ? '#9ca3af' : '#6b7280',
  marginLeft: '24px',
  wordBreak: 'break-word',
}));

const ReasoningDisplay: React.FC = () => {
  const { verboseMode, currentReasoning, reasoningEvents, isLoading } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [reasoningEvents, currentReasoning]);

  // Only show if verbose mode is on
  if (!verboseMode) {
    return null;
  }
  
  // Combine all events for display
  const allEvents = [...reasoningEvents];
  if (currentReasoning && (!allEvents.length || allEvents[allEvents.length - 1] !== currentReasoning)) {
    allEvents.push(currentReasoning);
  }

  const getIcon = (type: string, data?: any) => {
    const iconProps = { size: 14 };
    switch (type) {
      case 'tool_start':
        if (data?.tool === 'bigquery_select') return <Database {...iconProps} style={{ color: '#059669' }} />;
        if (data?.tool === 'google_search') return <Search {...iconProps} style={{ color: '#3b82f6' }} />;
        if (data?.tool === 'geocode_address') return <MapPin {...iconProps} style={{ color: '#8b5cf6' }} />;
        if (data?.tool === 'save_voter_list') return <Save {...iconProps} style={{ color: '#f59e0b' }} />;
        return <Activity {...iconProps} style={{ color: '#6b7280' }} />;
      case 'tool_result':
        return <Activity {...iconProps} style={{ color: '#10b981' }} />;
      case 'tool_error':
        return <AlertCircle {...iconProps} style={{ color: '#ef4444' }} />;
      case 'adk_event':
        return <Zap {...iconProps} style={{ color: '#3b82f6' }} />;
      default:
        return <Activity {...iconProps} style={{ color: '#6b7280' }} />;
    }
  };

  const formatEventData = (type: string, data: Record<string, any>) => {
    // Format the event data in a human-readable way
    if (type === 'tool_start') {
      if (data.tool === 'bigquery_select' && data.query) {
        // Clean up SQL for display
        const cleanQuery = data.query
          .replace(/\s+/g, ' ')
          .trim()
          .substring(0, 200);
        return `Executing SQL: ${cleanQuery}${data.query.length > 200 ? '...' : ''}`;
      }
      if (data.tool === 'google_search' && data.query) {
        return `Searching Google for: "${data.query}"`;
      }
      if (data.tool === 'geocode_address' && data.address) {
        return `Geocoding address: ${data.address}`;
      }
      if (data.tool === 'save_voter_list') {
        return `Saving voter list: ${data.name || 'Untitled'}`;
      }
      return `Starting tool: ${data.tool || 'Unknown'}`;
    }
    
    if (type === 'tool_result') {
      if (data.rows !== undefined) {
        return `Query returned ${data.rows.toLocaleString()} rows`;
      }
      if (data.results_count !== undefined) {
        return `Found ${data.results_count} results`;
      }
      if (data.result && typeof data.result === 'string') {
        return data.result.substring(0, 100) + (data.result.length > 100 ? '...' : '');
      }
      return 'Tool completed successfully';
    }
    
    if (type === 'tool_error') {
      return `Error: ${data.error || 'Unknown error occurred'}`;
    }

    if (type === 'adk_event') {
      const eventNum = data.event_number || '?';
      const eventType = data.event_type || 'unknown';
      
      // Parse different event types
      if (eventType === 'start') {
        return `ADK Chain Started (Event #${eventNum})`;
      }
      if (eventType === 'preview') {
        // Try to extract meaningful info from preview content
        if (typeof data.content === 'string') {
          if (data.content.includes('"error":')) {
            const errorMatch = data.content.match(/"error":\s*"([^"]+)"/);
            if (errorMatch) {
              return `❌ Error: ${errorMatch[1].replace(/\\"/g, '"')}`;
            }
          }
          if (data.content.includes('function_response')) {
            const funcMatch = data.content.match(/name='([^']+)'/);
            const funcName = funcMatch ? funcMatch[1] : 'function';
            return `Processing ${funcName} (${data.size_tokens || 0} tokens)`;
          }
        }
        return `ADK Preview #${eventNum} (${data.size_tokens || 0} tokens)`;
      }
      if (eventType === 'completion') {
        const totalTokens = data.total_size_tokens || data.size_tokens || 0;
        return `✅ ADK Complete (${totalTokens.toLocaleString()} total tokens)`;
      }
      
      return `ADK Event #${eventNum}: ${eventType}`;
    }
    
    // Try to extract meaningful data from generic objects
    if (data.total_events !== undefined) {
      return `Chain complete: ${data.total_events} events, ${(data.total_size_tokens || 0).toLocaleString()} tokens`;
    }
    
    // Fallback - show key info if available
    const keys = Object.keys(data).slice(0, 3);
    if (keys.length > 0) {
      const preview = keys.map(k => `${k}: ${JSON.stringify(data[k]).substring(0, 50)}`).join(', ');
      return preview.length > 100 ? preview.substring(0, 100) + '...' : preview;
    }
    
    return 'Processing...';
  };

  return (
    <VerboseContainer $isDarkMode={isDarkMode}>
      <VerboseHeader $isDarkMode={isDarkMode}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          fontSize: '12px',
          fontWeight: 600,
          color: isDarkMode ? '#f3f4f6' : '#111827'
        }}>
          <Activity size={14} />
          Agent Reasoning
          {allEvents.length > 0 && (
            <span style={{ 
              fontSize: '11px', 
              fontWeight: 400,
              color: isDarkMode ? '#9ca3af' : '#6b7280'
            }}>
              ({allEvents.length} {allEvents.length === 1 ? 'event' : 'events'})
            </span>
          )}
        </div>
        {isLoading && (
          <div style={{ 
            fontSize: '11px',
            color: isDarkMode ? '#10b981' : '#059669',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <div className="animate-pulse">●</div>
            Processing...
          </div>
        )}
      </VerboseHeader>
      
      <VerboseContent ref={scrollRef}>
        {allEvents.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px',
            color: isDarkMode ? '#9ca3af' : '#6b7280',
            fontSize: '12px'
          }}>
            Agent reasoning will appear here during processing...
          </div>
        ) : (
          allEvents.map((event, index) => (
            <EventItem 
              key={index} 
              $isDarkMode={isDarkMode}
              $isActive={index === allEvents.length - 1 && isLoading}
            >
              <EventHeader>
                {getIcon(event.type, event.data)}
                <EventTitle $isDarkMode={isDarkMode}>
                  Step {index + 1}: {event.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </EventTitle>
              </EventHeader>
              <EventDetail $isDarkMode={isDarkMode}>
                {formatEventData(event.type, event.data)}
              </EventDetail>
            </EventItem>
          ))
        )}
      </VerboseContent>
    </VerboseContainer>
  );
};

export default ReasoningDisplay;