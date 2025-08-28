import React, { useState, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl } from 'react-leaflet';
import { useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { Input } from 'baseui/input';
import { Spinner } from 'baseui/spinner';
import { Heading, HeadingLevel } from 'baseui/heading';
import 'leaflet/dist/leaflet.css';
import apiClient from '../../services/api';
import { RootState } from '../../store';
import { useAuthCheck } from '../../hooks/useAuthCheck';

const { BaseLayer } = LayersControl;

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  height: '100%',
  display: 'flex',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#f5f5f5',
}));

const LeftPanel = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  width: '400px',
  backgroundColor: $isDarkMode ? '#1f2937' : '#ffffff',
  borderRight: $isDarkMode ? '1px solid #374151' : '1px solid #e0e0e0',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const ChatHeader = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '20px',
  borderBottom: $isDarkMode ? '1px solid #374151' : '1px solid #e0e0e0',
  backgroundColor: $isDarkMode ? '#111827' : '#f9fafb',
}));

const ChatInput = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '16px',
  borderTop: $isDarkMode ? '1px solid #374151' : '1px solid #e0e0e0',
  backgroundColor: $isDarkMode ? '#1f2937' : '#ffffff',
}));

const SampleDataContainer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
  backgroundColor: $isDarkMode ? '#1f2937' : '#ffffff',
}));

const SampleDataTable = styled('table', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  width: '100%',
  fontSize: '12px',
  borderCollapse: 'collapse',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const TableHeader = styled('th', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '8px 4px',
  textAlign: 'left',
  borderBottom: $isDarkMode ? '1px solid #374151' : '1px solid #e0e0e0',
  backgroundColor: $isDarkMode ? '#111827' : '#f3f4f6',
  fontWeight: 600,
  fontSize: '11px',
}));

const TableCell = styled('td', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '6px 4px',
  borderBottom: $isDarkMode ? '1px solid #374151' : '1px solid #e0e0e0',
  fontSize: '11px',
  maxWidth: '150px',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
}));

const MapWrapper = styled('div', {
  flex: 1,
  position: 'relative',
});

const LoadingOverlay = styled('div', {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  zIndex: 1000,
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  padding: '20px',
  borderRadius: '8px',
  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
});

const Legend = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  position: 'absolute',
  bottom: '20px',
  right: '20px',
  backgroundColor: $isDarkMode ? '#1f2937' : 'white',
  border: $isDarkMode ? '2px solid #374151' : '2px solid #ccc',
  borderRadius: '8px',
  padding: '12px',
  zIndex: 1000,
  fontSize: '14px',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  color: $isDarkMode ? '#f3f4f6' : '#1a1a1a',
}));

const LegendTitle = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontWeight: 'bold',
  marginBottom: '8px',
  fontSize: '16px',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const LegendItem = styled('div', {
  display: 'flex',
  alignItems: 'center',
  marginBottom: '4px',
});

const LegendColor = styled('div', ({ $color }: { $color: string }) => ({
  width: '20px',
  height: '20px',
  borderRadius: '50%',
  backgroundColor: $color,
  marginRight: '8px',
  border: '1px solid #333',
}));

const QueryInfo = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '12px',
  backgroundColor: $isDarkMode ? '#111827' : '#f3f4f6',
  borderRadius: '4px',
  marginBottom: '12px',
  fontSize: '13px',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const ErrorMessage = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '12px',
  backgroundColor: $isDarkMode ? '#7f1d1d' : '#fee2e2',
  color: $isDarkMode ? '#fecaca' : '#dc2626',
  borderRadius: '4px',
  marginBottom: '12px',
  fontSize: '13px',
}));

interface VisualizationData {
  type: 'voters' | 'streets';
  data: Array<{
    id?: string;
    name?: string;
    street_name?: string;
    city?: string;
    county?: string;
    party?: string;
    demo_party?: string;
    latitude: number;
    longitude: number;
    republican_count?: number;
    democrat_count?: number;
    unaffiliated_count?: number;
    total_voters?: number;
    republican_pct?: number;
    democrat_pct?: number;
  }>;
  query: string;
  description: string;
  total_count: number;
  center_lat: number;
  center_lon: number;
}

const Visualizer: React.FC = () => {
  useAuthCheck();
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visualizationData, setVisualizationData] = useState<VisualizationData | null>(null);
  const [mapKey, setMapKey] = useState(0); // Force map re-render

  const handleVisualize = useCallback(async () => {
    if (!prompt.trim()) {
      setError('Please enter a query');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<VisualizationData>('/visualize', { 
        prompt: prompt.trim() 
      });
      
      setVisualizationData(response);
      setMapKey(prev => prev + 1); // Force map re-render with new data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate visualization';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [prompt]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleVisualize();
    }
  };

  const getMarkerColor = (item: any): string => {
    // For streets, use party percentages
    if (visualizationData?.type === 'streets') {
      const repPct = item.republican_pct || 0;
      const demPct = item.democrat_pct || 0;
      
      if (repPct > demPct + 10) return '#dc2626'; // Strong Republican
      if (demPct > repPct + 10) return '#2563eb'; // Strong Democrat
      if (repPct > demPct) return '#f87171'; // Lean Republican
      if (demPct > repPct) return '#60a5fa'; // Lean Democrat
      return '#a855f7'; // Competitive
    }
    
    // For voters, use party affiliation
    const party = (item.party || item.demo_party || '').toLowerCase();
    if (party.includes('rep')) return '#dc2626'; // Republican
    if (party.includes('dem')) return '#2563eb'; // Democrat
    return '#6b7280'; // Unaffiliated/Other
  };

  const getMarkerSize = (item: any): number => {
    if (visualizationData?.type === 'streets') {
      const total = item.total_voters || 1;
      return Math.max(8, Math.min(25, total / 3));
    }
    return 6; // Fixed size for individual voters
  };

  const formatSampleData = (item: any): any => {
    if (visualizationData?.type === 'streets') {
      return {
        Street: item.street_name || '',
        City: item.city || '',
        'Total Voters': item.total_voters || 0,
        'Rep %': item.republican_pct ? `${item.republican_pct.toFixed(1)}%` : '0%',
        'Dem %': item.democrat_pct ? `${item.democrat_pct.toFixed(1)}%` : '0%',
      };
    }
    
    return {
      Name: item.name || '',
      Party: item.party || item.demo_party || '',
      City: item.city || '',
      County: item.county || '',
    };
  };

  const sampleData = visualizationData?.data.slice(0, 10) || [];
  const sampleColumns = sampleData.length > 0 ? Object.keys(formatSampleData(sampleData[0])) : [];

  return (
    <Container $isDarkMode={isDarkMode}>
      <LeftPanel $isDarkMode={isDarkMode}>
        <ChatHeader $isDarkMode={isDarkMode}>
          <HeadingLevel>
            <Heading styleLevel={5} color={isDarkMode ? '#f3f4f6' : '#111827'}>
              Visualization Query
            </Heading>
          </HeadingLevel>
          <div style={{ fontSize: '13px', color: isDarkMode ? '#9ca3af' : '#6b7280', marginTop: '8px' }}>
            Enter a natural language query to visualize voters or streets on the map
          </div>
        </ChatHeader>

        <SampleDataContainer $isDarkMode={isDarkMode}>
          {error && (
            <ErrorMessage $isDarkMode={isDarkMode}>
              {error}
            </ErrorMessage>
          )}

          {visualizationData && (
            <>
              <QueryInfo $isDarkMode={isDarkMode}>
                <strong>Query:</strong> {visualizationData.description}
                <br />
                <strong>Type:</strong> {visualizationData.type === 'voters' ? 'Individual Voters' : 'Streets'}
                <br />
                <strong>Results:</strong> {visualizationData.total_count.toLocaleString()} {visualizationData.type}
              </QueryInfo>
              
              {/* SQL Query Display */}
              <div style={{
                marginTop: '16px',
                marginBottom: '16px',
                padding: '12px',
                backgroundColor: isDarkMode ? '#111827' : '#f9fafb',
                borderRadius: '6px',
                border: isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  fontWeight: 600,
                  color: isDarkMode ? '#9ca3af' : '#6b7280',
                  marginBottom: '8px'
                }}>
                  SQL Query:
                </div>
                <pre style={{
                  margin: 0,
                  fontSize: '11px',
                  color: isDarkMode ? '#d1d5db' : '#4b5563',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                }}>
                  {visualizationData.query}
                </pre>
              </div>

              {sampleData.length > 0 && (
                <>
                  <div style={{ 
                    marginBottom: '12px', 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: isDarkMode ? '#f3f4f6' : '#111827'
                  }}>
                    Sample Data (first 10 rows)
                  </div>
                  <SampleDataTable $isDarkMode={isDarkMode}>
                    <thead>
                      <tr>
                        {sampleColumns.map((col) => (
                          <TableHeader key={col} $isDarkMode={isDarkMode}>
                            {col}
                          </TableHeader>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleData.map((item, index) => {
                        const formatted = formatSampleData(item);
                        return (
                          <tr key={index}>
                            {sampleColumns.map((col) => (
                              <TableCell key={col} $isDarkMode={isDarkMode}>
                                {formatted[col]}
                              </TableCell>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </SampleDataTable>
                </>
              )}
            </>
          )}
        </SampleDataContainer>

        <ChatInput $isDarkMode={isDarkMode}>
          <Input
            value={prompt}
            onChange={(e) => setPrompt((e.target as HTMLInputElement).value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., Show all Democratic voters in Westfield"
            disabled={isLoading}
            overrides={{
              Root: {
                style: {
                  marginBottom: '12px',
                },
              },
            }}
          />
          <Button
            onClick={handleVisualize}
            kind={KIND.primary}
            size={SIZE.compact}
            disabled={!prompt.trim() || isLoading}
            isLoading={isLoading}
            overrides={{
              BaseButton: {
                style: {
                  width: '100%',
                },
              },
            }}
          >
            Visualize
          </Button>
        </ChatInput>
      </LeftPanel>

      <MapWrapper>
        {isLoading && (
          <LoadingOverlay>
            <Spinner />
          </LoadingOverlay>
        )}

        <MapContainer
          key={mapKey}
          center={[
            visualizationData?.center_lat || 40.6431, 
            visualizationData?.center_lon || -74.5464
          ]}
          zoom={visualizationData ? 12 : 11}
          style={{ height: '100%', width: '100%' }}
        >
          <LayersControl position="topright">
            <BaseLayer checked={!isDarkMode} name="OpenStreetMap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </BaseLayer>
            <BaseLayer name="CartoDB Light">
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
                url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
              />
            </BaseLayer>
            <BaseLayer checked={isDarkMode} name="CartoDB Dark">
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
              />
            </BaseLayer>
          </LayersControl>

          {visualizationData?.data.map((item, index) => (
            <CircleMarker
              key={index}
              center={[item.latitude, item.longitude]}
              radius={getMarkerSize(item)}
              fillColor={getMarkerColor(item)}
              color="#000"
              weight={1}
              opacity={1}
              fillOpacity={0.7}
            >
              <Popup>
                <div>
                  {visualizationData.type === 'streets' ? (
                    <>
                      <strong>{item.street_name}</strong><br />
                      {item.city}, {item.county} County<br />
                      <hr />
                      <strong>Total Voters:</strong> {item.total_voters}<br />
                      <strong>Republican:</strong> {item.republican_count} ({item.republican_pct?.toFixed(1)}%)<br />
                      <strong>Democrat:</strong> {item.democrat_count} ({item.democrat_pct?.toFixed(1)}%)<br />
                    </>
                  ) : (
                    <>
                      <strong>{item.name}</strong><br />
                      <strong>Party:</strong> {item.party || item.demo_party}<br />
                      {item.city && <><strong>City:</strong> {item.city}<br /></>}
                      {item.county && <><strong>County:</strong> {item.county}<br /></>}
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        <Legend $isDarkMode={isDarkMode}>
          <LegendTitle $isDarkMode={isDarkMode}>
            {visualizationData?.type === 'streets' ? 'Street Party Concentration' : 'Voter Party'}
          </LegendTitle>
          {visualizationData?.type === 'streets' ? (
            <>
              <LegendItem>
                <LegendColor $color="#dc2626" />
                <span>Strong Republican</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#f87171" />
                <span>Lean Republican</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#2563eb" />
                <span>Strong Democrat</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#60a5fa" />
                <span>Lean Democrat</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#a855f7" />
                <span>Competitive</span>
              </LegendItem>
            </>
          ) : (
            <>
              <LegendItem>
                <LegendColor $color="#dc2626" />
                <span>Republican</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#2563eb" />
                <span>Democrat</span>
              </LegendItem>
              <LegendItem>
                <LegendColor $color="#6b7280" />
                <span>Unaffiliated/Other</span>
              </LegendItem>
            </>
          )}
        </Legend>
      </MapWrapper>
    </Container>
  );
};

export default Visualizer;