'use client'

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MapPin, Search } from "lucide-react"
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api"
import { useEffect, useState } from "react"

const mapContainerStyle = {
  width: '100%',
  height: '400px',
};

const defaultCenter = {
  lat: 40.712776,
  lng: -74.005974,
};

interface MarkerProps {
  lat: number;
  lng: number;
  color: string;
}

const markers: MarkerProps[] = [
  { lat: 40.732776, lng: -74.035974, color: 'blue' },
  { lat: 40.752776, lng: -74.025974, color: 'green' },
];

const haversineDistance = (coords1: { lat: number; lng: number }, coords2: { lat: number; lng: number }) => {
  const toRad = (value: number) => (value * Math.PI) / 180;

  const lat1 = coords1.lat;
  const lon1 = coords1.lng;
  const lat2 = coords2.lat;
  const lon2 = coords2.lng;

  const R = 6371; // Radius of the Earth in kilometers
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // Distance in kilometers
};

export default function MapViewComponent({ userType = 'donor' }) {
  const [currentPosition, setCurrentPosition] = useState<{ lat: number; lng: number } | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [searchInput, setSearchInput] = useState<string>('');
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number }>(defaultCenter);
  const [distance, setDistance] = useState<number | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
  });

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const positionData = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          setCurrentPosition(positionData);
          setMapCenter(positionData);
        },
        (error) => {
          console.error("Error getting location:", error);
        }
      );
    }
  }, []);

  const handleSearch = async () => {
    if (!searchInput) return;

    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: searchInput }, (results, status) => {
      if (status === 'OK' && results && results[0]) {
        const location = results[0].geometry.location;
        const searchedLocation = { lat: location.lat(), lng: location.lng() };

        if (currentPosition) {
          const dist = haversineDistance(currentPosition, searchedLocation);
          setDistance(dist);
        }

        setMapCenter(searchedLocation);
        setSearchInput('');
      } else {
        console.error('Geocode was not successful for the following reason: ' + status);
      }
    });
  };

  if (!isLoaded) {
    return <div>Loading Map...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="location">Location</Label>
        <div className="relative">
          <MapPin className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            id="location"
            placeholder="Enter your location"
            className="pl-8"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <Button onClick={handleSearch} className="absolute right-0 top-0">Search</Button>
        </div>
      </div>
      {distance !== null && (
        <div className="text-lg">
          Distance: {distance.toFixed(2)} km
        </div>
      )}
      <Tabs defaultValue={userType === 'donor' ? 'receivers' : 'donations'}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="donations">Donations</TabsTrigger>
          <TabsTrigger value="receivers">Receivers</TabsTrigger>
        </TabsList>
        <TabsContent value="donations" className="space-y-4">
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="Select food type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="prepared">Prepared Meals</SelectItem>
              <SelectItem value="produce">Fresh Produce</SelectItem>
              <SelectItem value="canned">Canned Goods</SelectItem>
            </SelectContent>
          </Select>
        </TabsContent>
        <TabsContent value="receivers" className="space-y-4">
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="Select receiver type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="foodbank">Food Bank</SelectItem>
              <SelectItem value="shelter">Shelter</SelectItem>
              <SelectItem value="school">School</SelectItem>
            </SelectContent>
          </Select>
        </TabsContent>
      </Tabs>
      <Button className="w-full">Apply Filters</Button>
      <div className="aspect-video relative">
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={mapCenter}
          zoom={12}
          onLoad={map => setMap(map)}
        >
          {currentPosition && (
            <Marker
              position={currentPosition}
              icon={{
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: 'green',
                fillOpacity: 1,
                strokeWeight: 0,
              }}
            />
          )}
          {markers.map((marker, index) => (
            <Marker
              key={index}
              position={{ lat: marker.lat, lng: marker.lng }}
              icon={{
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: marker.color,
                fillOpacity: 1,
                strokeWeight: 0,
              }}
            />
          ))}
        </GoogleMap>
      </div>
    </div>
  )
}