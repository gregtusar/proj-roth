import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl } from 'react-leaflet';
import { useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Spinner } from 'baseui/spinner';
import 'leaflet/dist/leaflet.css';
import apiClient from '../../services/api';
import { RootState } from '../../store';

const { BaseLayer } = LayersControl;

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#f5f5f5',
}));

const MapWrapper = styled('div', {
  flex: 1,
  position: 'relative',
});

const LoadingContainer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  backgroundColor: $isDarkMode ? '#111827' : '#ffffff',
  color: $isDarkMode ? '#f3f4f6' : '#1a1a1a',
}));

const Legend = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  position: 'absolute',
  bottom: '20px',
  left: '20px',
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

interface StreetData {
  street_name: string;
  city: string;
  county: string;
  zip_code: number;
  republican_count: number;
  democrat_count: number;
  unaffiliated_count: number;
  total_voters: number;
  republican_pct: number;
  democrat_pct: number;
  unaffiliated_pct: number;
  latitude: number;
  longitude: number;
}

interface MapData {
  streets: StreetData[];
  center_lat: number;
  center_lon: number;
}

const StreetMap: React.FC = () => {
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<MapData>('/maps/street-party-data', {
        params: { min_voters: 5 }
      });
      setMapData(response);
    } catch (err) {
      setError('Failed to load map data');
      console.error('Error fetching map data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getPartyColor = (street: StreetData): string => {
    const { republican_pct, democrat_pct } = street;
    
    if (republican_pct > democrat_pct + 10) {
      return '#dc2626'; // Strong Republican (red)
    } else if (democrat_pct > republican_pct + 10) {
      return '#2563eb'; // Strong Democrat (blue)
    } else if (republican_pct > democrat_pct) {
      return '#f87171'; // Lean Republican (light red)
    } else if (democrat_pct > republican_pct) {
      return '#60a5fa'; // Lean Democrat (light blue)
    } else {
      return '#a855f7'; // Competitive (purple)
    }
  };

  const getMarkerSize = (totalVoters: number): number => {
    return Math.max(5, Math.min(20, totalVoters / 2));
  };

  if (isLoading) {
    return (
      <Container $isDarkMode={isDarkMode}>
        <LoadingContainer $isDarkMode={isDarkMode}>
          <Spinner />
        </LoadingContainer>
      </Container>
    );
  }

  if (error || !mapData) {
    return (
      <Container $isDarkMode={isDarkMode}>
        <LoadingContainer $isDarkMode={isDarkMode}>
          <div>{error || 'No data available'}</div>
        </LoadingContainer>
      </Container>
    );
  }

  return (
    <Container $isDarkMode={isDarkMode}>
      <MapWrapper>
        <MapContainer
          center={[mapData.center_lat, mapData.center_lon]}
          zoom={11}
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

          {mapData.streets.map((street, index) => (
              <CircleMarker
                key={index}
                center={[street.latitude, street.longitude]}
                radius={getMarkerSize(street.total_voters)}
                fillColor={getPartyColor(street)}
                color="#000"
                weight={1}
                opacity={1}
                fillOpacity={0.7}
              >
              <Popup>
                <div>
                  <strong>{street.street_name}</strong><br />
                  {street.city}, {street.county} County<br />
                  <hr />
                  <strong>Total Voters:</strong> {street.total_voters}<br />
                  <strong>Republican:</strong> {street.republican_count} ({street.republican_pct.toFixed(1)}%)<br />
                  <strong>Democrat:</strong> {street.democrat_count} ({street.democrat_pct.toFixed(1)}%)<br />
                  <strong>Unaffiliated:</strong> {street.unaffiliated_count} ({street.unaffiliated_pct.toFixed(1)}%)<br />
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        <Legend $isDarkMode={isDarkMode}>
          <LegendTitle $isDarkMode={isDarkMode}>Party Concentration</LegendTitle>
          <LegendItem>
            <LegendColor $color="#dc2626" />
            <span>Strong Republican (&gt;10% lead)</span>
          </LegendItem>
          <LegendItem>
            <LegendColor $color="#f87171" />
            <span>Lean Republican</span>
          </LegendItem>
          <LegendItem>
            <LegendColor $color="#2563eb" />
            <span>Strong Democrat (&gt;10% lead)</span>
          </LegendItem>
          <LegendItem>
            <LegendColor $color="#60a5fa" />
            <span>Lean Democrat</span>
          </LegendItem>
          <LegendItem>
            <LegendColor $color="#a855f7" />
            <span>Competitive</span>
          </LegendItem>
        </Legend>
      </MapWrapper>
    </Container>
  );
};

export default StreetMap;