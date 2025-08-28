import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Activity, Database, Search, MapPin, Save, AlertCircle, Zap } from 'lucide-react';

const ReasoningDisplay: React.FC = () => {
  const { verboseMode, currentReasoning, reasoningEvents, isLoading } = useSelector(
    (state: RootState) => state.chat
  );

  // Only show if verbose mode is on
  if (!verboseMode) {
    return null;
  }
  
  // If no events yet, show a placeholder
  if (!currentReasoning && reasoningEvents.length === 0) {
    return (
      <div className="border border-gray-200 bg-gray-50 rounded-lg p-3 mt-2 mb-2">
        <div className="text-sm text-gray-500 text-center">
          Verbose mode enabled - agent reasoning will appear here during processing
        </div>
      </div>
    );
  }
  
  // Use the current reasoning if available, otherwise show the last event
  const displayEvent = currentReasoning || reasoningEvents[reasoningEvents.length - 1];

  const getIcon = (type: string) => {
    switch (type) {
      case 'tool_start':
        if (displayEvent.data.tool === 'bigquery_select') return <Database className="w-4 h-4" />;
        if (displayEvent.data.tool === 'google_search') return <Search className="w-4 h-4" />;
        if (displayEvent.data.tool === 'geocode_address') return <MapPin className="w-4 h-4" />;
        if (displayEvent.data.tool === 'save_voter_list') return <Save className="w-4 h-4" />;
        return <Activity className="w-4 h-4" />;
      case 'tool_result':
        return <Activity className="w-4 h-4 text-green-500" />;
      case 'tool_error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'adk_event':
        return <Zap className="w-4 h-4 text-blue-500" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const formatData = (data: Record<string, any>) => {
    if (data.tool === 'bigquery_select' && data.query) {
      return (
        <div className="space-y-1">
          <div className="text-xs font-mono bg-gray-100 p-2 rounded overflow-x-auto">
            {data.query}
          </div>
        </div>
      );
    }
    
    if (data.tool === 'google_search' && data.query) {
      return (
        <div className="space-y-1">
          <div className="text-xs">Searching for: "{data.query}"</div>
          {data.num_results && <div className="text-xs text-gray-500">Max results: {data.num_results}</div>}
        </div>
      );
    }

    if (data.rows !== undefined || data.results_count !== undefined) {
      return (
        <div className="text-xs space-y-1">
          {data.rows !== undefined && <div>Rows returned: {data.rows.toLocaleString()}</div>}
          {data.results_count !== undefined && <div>Results found: {data.results_count}</div>}
          {data.size_tokens && (
            <div className="text-gray-500">
              Size: ~{data.size_tokens.toLocaleString()} tokens
              {data.size_tokens > 10000 && (
                <span className="text-orange-500 ml-2">⚠️ Large result</span>
              )}
            </div>
          )}
        </div>
      );
    }

    if (data.event_type) {
      // Parse ADK event data
      if (data.event_type === 'preview' && typeof data.content === 'string') {
        // Try to parse the content string which appears to be a structured response
        try {
          // Extract the error message if present
          if (data.content.includes('"error":')) {
            const errorMatch = data.content.match(/"error":\s*"([^"]+)"/);
            if (errorMatch) {
              return (
                <div className="space-y-2">
                  <div className="text-xs font-medium text-red-600">
                    ❌ BigQuery Error
                  </div>
                  <div className="text-xs bg-red-50 border border-red-200 rounded p-2 text-red-700">
                    {errorMatch[1].replace(/\\"/g, '"')}
                  </div>
                </div>
              );
            }
          }
          
          // If it's a function response, extract the function name and response
          if (data.content.includes('function_response')) {
            const funcMatch = data.content.match(/name='([^']+)'/);
            const funcName = funcMatch ? funcMatch[1] : 'Unknown function';
            
            return (
              <div className="space-y-1">
                <div className="text-xs font-medium">
                  ADK Event #{data.event_number}: {data.event_type}
                </div>
                <div className="text-xs text-gray-600">
                  Function: <span className="font-mono">{funcName}</span>
                </div>
                {data.size_tokens && (
                  <div className="text-xs text-gray-500">
                    Size: ~{data.size_tokens.toLocaleString()} tokens
                  </div>
                )}
              </div>
            );
          }
        } catch (e) {
          // If parsing fails, show original format
        }
      }
      
      // Default ADK event display
      return (
        <div className="text-xs space-y-1">
          <div>ADK Event #{data.event_number}: {data.event_type}</div>
          {data.size_tokens && (
            <div className="text-gray-500">
              Size: ~{data.size_tokens.toLocaleString()} tokens
            </div>
          )}
          {data.content && (
            <details className="mt-1">
              <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                Show raw data
              </summary>
              <pre className="text-xs font-mono bg-gray-100 p-2 rounded overflow-x-auto mt-1 max-h-32 overflow-y-auto">
                {typeof data.content === 'string' 
                  ? data.content.substring(0, 500) + (data.content.length > 500 ? '...' : '')
                  : JSON.stringify(data.content, null, 2)}
              </pre>
            </details>
          )}
        </div>
      );
    }

    if (data.error) {
      return (
        <div className="space-y-1">
          <div className="text-xs font-medium text-red-600">⚠️ Error</div>
          <div className="text-xs bg-red-50 border border-red-200 rounded p-2 text-red-700">
            {data.error}
          </div>
        </div>
      );
    }

    // Fallback for other data - make it collapsible if it's large
    const dataStr = JSON.stringify(data, null, 2);
    if (dataStr.length > 200) {
      return (
        <details className="text-xs">
          <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
            Show details
          </summary>
          <pre className="font-mono text-gray-600 bg-gray-100 p-2 rounded overflow-x-auto mt-1 max-h-48 overflow-y-auto">
            {dataStr}
          </pre>
        </details>
      );
    }
    
    return (
      <div className="text-xs font-mono text-gray-600 bg-gray-100 p-2 rounded overflow-x-auto">
        {dataStr}
      </div>
    );
  };

  return (
    <div className={`border border-blue-200 bg-blue-50 rounded-lg p-3 mt-2 mb-2 ${isLoading ? 'animate-pulse' : ''}`}>
      <div className="flex items-start space-x-2">
        <div className="mt-0.5">{getIcon(displayEvent.type)}</div>
        <div className="flex-1">
          <div className="text-sm font-medium text-blue-900">
            {displayEvent.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
          <div className="mt-1">{formatData(displayEvent.data)}</div>
        </div>
      </div>
      
      {/* Show event count and status */}
      <div className="flex justify-between items-center mt-2">
        {reasoningEvents.length > 0 && (
          <div className="text-xs text-gray-500">
            Event {reasoningEvents.length} in chain
          </div>
        )}
        {!isLoading && reasoningEvents.length > 0 && (
          <div className="text-xs text-gray-400">
            Last event (completed)
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningDisplay;