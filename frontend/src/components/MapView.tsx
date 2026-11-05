import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import type { Issue } from '../lib/api';

const CENTER: [number, number] = [19.696, 72.765];
function FitPoints({ issues }: { issues: Issue[] }) {
  const map = useMap();
  useEffect(() => {
    if (issues.length) map.setView([issues[0].latitude, issues[0].longitude], 14);
  }, [issues, map]);
  return null;
}
function markerColor(category: string | null) {
  return category === 'pothole' ? '#2563eb' : category === 'garbage_accumulation' ? '#0f766e' : '#94a3b8';
}
export default function MapView({ issues }: { issues: Issue[] }) {
  return <div className="map-shell">
    <MapContainer center={CENTER} zoom={13} scrollWheelZoom className="leaflet-map">
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FitPoints issues={issues} />
      {issues.map(issue => <CircleMarker key={issue.id} center={[issue.latitude, issue.longitude]} radius={issue.priority_level === 'critical' ? 11 : 8} pathOptions={{ color: issue.priority_level === 'critical' ? '#dc2626' : markerColor(issue.category), weight: issue.priority_level === 'critical' ? 4 : 2, fillColor: markerColor(issue.category), fillOpacity: .82 }}>
        <Popup><strong>{issue.public_id}</strong><br />{issue.category || 'Awaiting detection'}<br />Priority: {issue.priority_level}<br />Status: {issue.status}</Popup>
      </CircleMarker>)}
    </MapContainer>
    <div className="map-attribution-note">Map data © OpenStreetMap contributors · Approximate Palghar city view; municipal boundary not yet verified.</div>
  </div>;
}
