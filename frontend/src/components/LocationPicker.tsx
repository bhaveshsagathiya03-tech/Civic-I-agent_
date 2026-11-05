import { MapContainer, TileLayer, CircleMarker, useMapEvents } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';

const PALGHAR_APPROX: LatLngExpression = [19.696, 72.765];
function ClickTarget({position,onChange}:{position:[number,number]|null;onChange:(p:[number,number])=>void}) {
  useMapEvents({ click(event) { onChange([event.latlng.lat,event.latlng.lng]); } });
  return position ? <CircleMarker center={position} radius={9} pathOptions={{color:'#0f766e',fillColor:'#2dd4bf',fillOpacity:.95,weight:3}}/> : null;
}
export default function LocationPicker({position,onChange}:{position:[number,number]|null;onChange:(p:[number,number])=>void}) {
  return <div className="location-picker"><MapContainer center={PALGHAR_APPROX} zoom={14} scrollWheelZoom={false} className="picker-map">
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"/>
    <ClickTarget position={position} onChange={onChange}/>
  </MapContainer><div className="picker-hint">Click the map to place the issue pin. The initial map centre is approximate, not a municipal boundary.</div></div>;
}
