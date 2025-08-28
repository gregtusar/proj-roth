import React, { useEffect, useRef, useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Activity, Database, Search, MapPin, Save, AlertCircle, Zap, ChevronDown, ChevronRight } from 'lucide-react';
import { styled } from 'baseui';

// Styled components for better formatting
const VerboseContainer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  backgroundColor: $isDarkMode ? '#1f2937' : '#f9fafb',
  border: `1px solid ${$isDarkMode ? '#374151' : '#e5e7eb'}`,
  borderRadius: '8px',
  marginBottom: '12px',
  maxHeight: '500px', // Increased from 400px for better visibility
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
  cursor: 'pointer',
  userSelect: 'none',
  ':hover': {
    backgroundColor: $isDarkMode ? '#1f2937' : '#e5e7eb',
  },
}));

const VerboseContent = styled('div', {
  flex: 1,
  overflowY: 'auto',
  padding: '8px',
  fontSize: '13px',
  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
  lineHeight: '1.5',
});

const EventGroup = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  marginBottom: '12px',
  border: `1px solid ${$isDarkMode ? '#374151' : '#e5e7eb'}`,
  borderRadius: '6px',
  backgroundColor: $isDarkMode ? '#1f2937' : '#ffffff',
}));

const EventGroupHeader = styled('div', ({ $isDarkMode, $isExpanded }: { $isDarkMode: boolean; $isExpanded: boolean }) => ({
  padding: '8px 12px',
  backgroundColor: $isDarkMode ? '#111827' : '#f3f4f6',
  borderBottom: $isExpanded ? `1px solid ${$isDarkMode ? '#374151' : '#e5e7eb'}` : 'none',
  borderRadius: $isExpanded ? '6px 6px 0 0' : '6px',
  cursor: 'pointer',
  userSelect: 'none',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  ':hover': {
    backgroundColor: $isDarkMode ? '#1f2937' : '#e5e7eb',
  },
}));

const EventGroupContent = styled('div', {
  padding: '8px',
  maxHeight: '400px',
  overflowY: 'auto',
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

const TokenInfo = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '10px',
  color: $isDarkMode ? '#9ca3af' : '#6b7280',
  marginTop: '4px',
  fontStyle: 'italic',
}));

const ReasoningDisplay: React.FC = () => {
  const { verboseMode, currentReasoning, reasoningEvents, isLoading, messages } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());
  const [isMainExpanded, setIsMainExpanded] = useState(true);
  
  // Group events by message index
  const groupedEvents = useMemo(() => {
    const groups: { [key: number]: any[] } = {};
    let currentMessageIndex = 0;
    
    reasoningEvents.forEach(event => {
      // Check if this is a new message start (when we clear events)
      if (event.type === 'message_start') {
        currentMessageIndex++;
      }
      
      if (!groups[currentMessageIndex]) {
        groups[currentMessageIndex] = [];
      }
      groups[currentMessageIndex].push(event);
    });
    
    // Add current reasoning to the latest group if it exists
    if (currentReasoning) {
      const lastIndex = Math.max(0, ...Object.keys(groups).map(Number));
      if (!groups[lastIndex]) {
        groups[lastIndex] = [];
      }
      if (groups[lastIndex][groups[lastIndex].length - 1] !== currentReasoning) {
        groups[lastIndex].push(currentReasoning);
      }
    }
    
    return groups;
  }, [reasoningEvents, currentReasoning]);
  
  // Calculate running token count
  const runningTokenCount = useMemo(() => {
    let total = 0;
    const counts: { [key: number]: number } = {};
    
    Object.entries(groupedEvents).forEach(([index, events]) => {
      let groupTotal = 0;
      events.forEach(event => {
        const tokens = event.data?.size_tokens || event.data?.total_size_tokens || 0;
        groupTotal += tokens;
        total += tokens;
      });
      counts[Number(index)] = groupTotal;
    });
    
    return { total, counts };
  }, [groupedEvents]);
  
  // Auto-expand latest group when loading
  useEffect(() => {
    if (isLoading && Object.keys(groupedEvents).length > 0) {
      const latestIndex = Math.max(...Object.keys(groupedEvents).map(Number));
      setExpandedGroups(prev => new Set(prev).add(latestIndex));
    }
  }, [isLoading, groupedEvents]);
  
  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (scrollRef.current && isLoading) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [reasoningEvents, currentReasoning, isLoading]);

  // Only show if verbose mode is on
  if (!verboseMode) {
    return null;
  }

  const toggleGroup = (index: number) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

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
      case 'adk_complete':
      case 'adk_tool_activity':
        return <Zap {...iconProps} style={{ color: '#3b82f6' }} />;
      default:
        return <Activity {...iconProps} style={{ color: '#6b7280' }} />;
    }
  };

  const formatEventData = (type: string, data: Record<string, any>) => {
    // Format the event data in a human-readable way
    if (type === 'tool_start') {
      if (data.tool === 'bigquery_select' && data.query) {
        // Show full SQL query with proper formatting
        const formattedQuery = data.query
          .replace(/\s+/g, ' ')
          .trim();
        return (
          <div style={{ fontFamily: 'monospace', fontSize: '11px' }}>
            <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>SQL Query:</div>
            <div style={{ 
              backgroundColor: isDarkMode ? '#111827' : '#f3f4f6',
              padding: '8px',
              borderRadius: '4px',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              maxHeight: '200px',
              overflowY: 'auto'
            }}>
              {formattedQuery}
            </div>
            {data.parameters && (
              <div style={{ marginTop: '4px' }}>
                <span style={{ fontWeight: 'bold' }}>Parameters:</span> {JSON.stringify(data.parameters, null, 2)}
              </div>
            )}
          </div>
        );
      }
      if (data.tool === 'google_search') {
        return (
          <div>
            <div>Searching Google for: "{data.query || 'Unknown query'}"</div>
            {data.num_results && <div style={{ fontSize: '10px', marginTop: '2px' }}>Max results: {data.num_results}</div>}
          </div>
        );
      }
      if (data.tool === 'geocode_address') {
        return (
          <div>
            <div>Geocoding address: {data.address || 'Unknown address'}</div>
            {data.bounds && <div style={{ fontSize: '10px', marginTop: '2px' }}>Bounds: {JSON.stringify(data.bounds)}</div>}
          </div>
        );
      }
      if (data.tool === 'save_voter_list') {
        return (
          <div>
            <div>Saving voter list: {data.name || 'Untitled'}</div>
            {data.description && <div style={{ fontSize: '10px', marginTop: '2px' }}>Description: {data.description}</div>}
            {data.query && (
              <div style={{ fontSize: '10px', marginTop: '2px' }}>
                <details>
                  <summary style={{ cursor: 'pointer' }}>Show query</summary>
                  <pre style={{ fontSize: '10px', marginTop: '4px' }}>{data.query}</pre>
                </details>
              </div>
            )}
          </div>
        );
      }
      // Show all parameters for unknown tools
      return (
        <div>
          <div>Starting tool: {data.tool || 'Unknown'}</div>
          {Object.keys(data).length > 1 && (
            <div style={{ fontSize: '10px', marginTop: '4px' }}>
              <details>
                <summary style={{ cursor: 'pointer' }}>Show parameters</summary>
                <pre style={{ fontSize: '10px', marginTop: '4px' }}>{JSON.stringify(data, null, 2)}</pre>
              </details>
            </div>
          )}
        </div>
      );
    }
    
    if (type === 'tool_result') {
      const results = [];
      
      if (data.rows !== undefined) {
        results.push(`Query returned ${data.rows.toLocaleString()} rows`);
      }
      if (data.results_count !== undefined) {
        results.push(`Found ${data.results_count} results`);
      }
      if (data.columns && Array.isArray(data.columns)) {
        results.push(`Columns: ${data.columns.slice(0, 5).join(', ')}${data.columns.length > 5 ? '...' : ''}`);
      }
      if (data.execution_time) {
        results.push(`Execution time: ${data.execution_time.toFixed(2)}s`);
      }
      if (data.result) {
        const resultStr = typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2);
        results.push(
          <details style={{ marginTop: '4px' }}>
            <summary style={{ cursor: 'pointer' }}>Show result data</summary>
            <pre style={{ fontSize: '10px', marginTop: '4px', maxHeight: '150px', overflowY: 'auto' }}>
              {resultStr}
            </pre>
          </details>
        );
      }
      if (data.error) {
        results.push(<span style={{ color: '#ef4444' }}>Error: {data.error}</span>);
      }
      
      return results.length > 0 ? (
        <div style={{ fontSize: '11px' }}>
          {results.map((item, idx) => (
            <div key={idx} style={{ marginTop: idx > 0 ? '2px' : 0 }}>{item}</div>
          ))}
        </div>
      ) : 'Tool completed';
    }
    
    if (type === 'tool_error') {
      return (
        <div style={{ color: '#ef4444' }}>
          <div style={{ fontWeight: 'bold' }}>Error occurred:</div>
          <div style={{ fontSize: '11px', marginTop: '4px' }}>{data.error || 'Unknown error'}</div>
          {data.details && (
            <details style={{ marginTop: '4px' }}>
              <summary style={{ cursor: 'pointer', fontSize: '10px' }}>Show details</summary>
              <pre style={{ fontSize: '10px', marginTop: '4px' }}>{JSON.stringify(data.details, null, 2)}</pre>
            </details>
          )}
        </div>
      );
    }
    
    if (type === 'adk_event' || type === 'adk_complete' || type === 'adk_tool_activity') {
      const eventNum = data.event_number || '?';
      const eventType = data.event_type || type.replace('adk_', '');
      
      return (
        <div>
          <div style={{ fontWeight: 'bold' }}>ADK Event #{eventNum}: {eventType}</div>
          {data.size_tokens && (
            <div style={{ fontSize: '10px' }}>Tokens: {data.size_tokens.toLocaleString()}</div>
          )}
          {data.total_size_tokens && (
            <div style={{ fontSize: '10px' }}>Total tokens: {data.total_size_tokens.toLocaleString()}</div>
          )}
          {data.content && (
            <details style={{ marginTop: '4px' }}>
              <summary style={{ cursor: 'pointer', fontSize: '10px' }}>Show raw content</summary>
              <pre style={{ 
                fontSize: '10px', 
                marginTop: '4px',
                backgroundColor: isDarkMode ? '#111827' : '#f3f4f6',
                padding: '4px',
                borderRadius: '4px',
                maxHeight: '200px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {typeof data.content === 'string' 
                  ? data.content.split('\n').map((line, i) => (
                      <React.Fragment key={i}>
                        {line}
                        {i < data.content.split('\n').length - 1 && '\n'}
                      </React.Fragment>
                    ))
                  : JSON.stringify(data.content, null, 2)}
              </pre>
            </details>
          )}
        </div>
      );
    }
    
    // Try to extract meaningful data from generic objects
    if (data.total_events !== undefined) {
      return (
        <div>
          <div>Chain complete: {data.total_events} events</div>
          {data.total_size_tokens && (
            <div style={{ fontSize: '10px' }}>Total tokens: {data.total_size_tokens.toLocaleString()}</div>
          )}
          {data.total_size_chars && (
            <div style={{ fontSize: '10px' }}>Total characters: {data.total_size_chars.toLocaleString()}</div>
          )}
        </div>
      );
    }
    
    // For unknown event types, show all data
    return (
      <div>
        <div style={{ fontSize: '11px' }}>Event type: {type}</div>
        <details style={{ marginTop: '4px' }}>
          <summary style={{ cursor: 'pointer', fontSize: '10px' }}>Show full data</summary>
          <pre style={{ 
            fontSize: '10px', 
            marginTop: '4px',
            backgroundColor: isDarkMode ? '#111827' : '#f3f4f6',
            padding: '4px',
            borderRadius: '4px',
            maxHeight: '200px',
            overflowY: 'auto'
          }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </details>
      </div>
    );
  };

  const getPromptForGroup = (index: number) => {
    // Find the message_start event for this group which contains the prompt text
    const groupEvents = groupedEvents[index];
    if (groupEvents && groupEvents.length > 0) {
      const messageStartEvent = groupEvents.find(e => e.type === 'message_start');
      if (messageStartEvent && messageStartEvent.data?.message) {
        const text = messageStartEvent.data.message;
        return text.length > 100 ? text.substring(0, 100) + '...' : text;
      }
    }
    
    // Fallback: Try to find the corresponding user message
    const userMessages = messages.filter(m => m.message_type === 'user');
    if (userMessages[index - 1]) { // index - 1 because message index starts at 1
      const text = userMessages[index - 1].message_text;
      return text.length > 100 ? text.substring(0, 100) + '...' : text;
    }
    return `Prompt ${index}`;
  };

  return (
    <VerboseContainer $isDarkMode={isDarkMode}>
      <VerboseHeader 
        $isDarkMode={isDarkMode}
        onClick={() => setIsMainExpanded(!isMainExpanded)}
      >
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          fontSize: '12px',
          fontWeight: 600,
          color: isDarkMode ? '#f3f4f6' : '#111827'
        }}>
          {isMainExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Activity size={14} />
          Agent Reasoning
          {Object.keys(groupedEvents).length > 0 && (
            <span style={{ 
              fontSize: '11px', 
              fontWeight: 400,
              color: isDarkMode ? '#9ca3af' : '#6b7280'
            }}>
              ({Object.keys(groupedEvents).length} {Object.keys(groupedEvents).length === 1 ? 'prompt' : 'prompts'}, {runningTokenCount.total.toLocaleString()} total tokens)
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
      
      {isMainExpanded && (
        <VerboseContent ref={scrollRef}>
          {Object.keys(groupedEvents).length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '20px',
              color: isDarkMode ? '#9ca3af' : '#6b7280',
              fontSize: '12px'
            }}>
              Agent reasoning will appear here during processing...
            </div>
          ) : (
            Object.entries(groupedEvents).map(([index, events]) => {
              const groupIndex = Number(index);
              const isExpanded = expandedGroups.has(groupIndex);
              const isLatest = groupIndex === Math.max(...Object.keys(groupedEvents).map(Number));
              const groupTokens = runningTokenCount.counts[groupIndex] || 0;
              
              return (
                <EventGroup key={index} $isDarkMode={isDarkMode}>
                  <EventGroupHeader 
                    $isDarkMode={isDarkMode}
                    $isExpanded={isExpanded}
                    onClick={() => toggleGroup(groupIndex)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      <span style={{ fontSize: '12px', fontWeight: 600 }}>
                        {getPromptForGroup(groupIndex)}
                      </span>
                      {isLatest && isLoading && (
                        <span className="animate-pulse" style={{ fontSize: '10px', color: '#10b981' }}>●</span>
                      )}
                    </div>
                    <div style={{ fontSize: '10px', color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
                      {events.length} events • {groupTokens.toLocaleString()} tokens
                    </div>
                  </EventGroupHeader>
                  
                  {isExpanded && (
                    <EventGroupContent>
                      {events.map((event, eventIndex) => {
                        const eventTokens = event.data?.size_tokens || event.data?.total_size_tokens || 0;
                        const runningTotal = events.slice(0, eventIndex + 1).reduce((sum, e) => 
                          sum + (e.data?.size_tokens || e.data?.total_size_tokens || 0), 0
                        );
                        
                        return (
                          <EventItem 
                            key={eventIndex} 
                            $isDarkMode={isDarkMode}
                            $isActive={isLatest && eventIndex === events.length - 1 && isLoading}
                          >
                            <EventHeader>
                              {getIcon(event.type, event.data)}
                              <EventTitle $isDarkMode={isDarkMode}>
                                Step {eventIndex + 1}: {event.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </EventTitle>
                            </EventHeader>
                            <EventDetail $isDarkMode={isDarkMode}>
                              {formatEventData(event.type, event.data)}
                            </EventDetail>
                            {eventTokens > 0 && (
                              <TokenInfo $isDarkMode={isDarkMode}>
                                Event tokens: {eventTokens.toLocaleString()} | Running total: {runningTotal.toLocaleString()}
                              </TokenInfo>
                            )}
                          </EventItem>
                        );
                      })}
                    </EventGroupContent>
                  )}
                </EventGroup>
              );
            })
          )}
        </VerboseContent>
      )}
    </VerboseContainer>
  );
};

export default ReasoningDisplay;