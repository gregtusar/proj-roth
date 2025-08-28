import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Activity, Database, Search, MapPin, Save, AlertCircle, Zap } from 'lucide-react';

const ReasoningDisplay: React.FC = () => {
  const { verboseMode, currentReasoning, reasoningEvents } = useSelector(
    (state: RootState) => state.chat
  );

  if (!verboseMode || !currentReasoning) {
    return null;
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'tool_start':
        if (currentReasoning.data.tool === 'bigquery_select') return <Database className="w-4 h-4" />;
        if (currentReasoning.data.tool === 'google_search') return <Search className="w-4 h-4" />;
        if (currentReasoning.data.tool === 'geocode_address') return <MapPin className="w-4 h-4" />;
        if (currentReasoning.data.tool === 'save_voter_list') return <Save className="w-4 h-4" />;
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
      return (
        <div className="text-xs space-y-1">
          <div>ADK Event #{data.event_number}: {data.event_type}</div>
          {data.size_tokens && (
            <div className="text-gray-500">
              Size: ~{data.size_tokens.toLocaleString()} tokens
            </div>
          )}
        </div>
      );
    }

    if (data.error) {
      return <div className="text-xs text-red-600">{data.error}</div>;
    }

    // Fallback for other data
    return (
      <div className="text-xs font-mono text-gray-600">
        {JSON.stringify(data, null, 2)}
      </div>
    );
  };

  return (
    <div className="animate-pulse border border-blue-200 bg-blue-50 rounded-lg p-3 mt-2">
      <div className="flex items-start space-x-2">
        <div className="mt-0.5">{getIcon(currentReasoning.type)}</div>
        <div className="flex-1">
          <div className="text-sm font-medium text-blue-900">
            {currentReasoning.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
          <div className="mt-1">{formatData(currentReasoning.data)}</div>
        </div>
      </div>
      
      {/* Show event count */}
      {reasoningEvents.length > 0 && (
        <div className="text-xs text-gray-500 mt-2">
          Event {reasoningEvents.length} in chain
        </div>
      )}
    </div>
  );
};

export default ReasoningDisplay;