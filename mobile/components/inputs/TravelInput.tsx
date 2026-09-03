import React, { useState, useEffect } from 'react';
import { View, TextInput, StyleSheet, TouchableOpacity, Text, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { tc } from '../../design/tokens';
import type { UserLocation } from '../../screens/LocationGate';

interface TravelInputProps {
  onSearch: (origin: string, destination: string) => void;
  isLoading: boolean;
  userLocation?: UserLocation;
}

interface Place {
  icon: string;
  title: string;
  subtitle: string;
}

const SAVED_PLACES: Place[] = [
  { icon: 'map-pin', title: 'Mumbai', subtitle: 'BOM - Chhatrapati Shivaji Int.' },
  { icon: 'map-pin', title: 'Delhi', subtitle: 'DEL - Indira Gandhi Int.' },
  { icon: 'map-pin', title: 'Bangalore', subtitle: 'BLR - Kempegowda Int.' },
];

export default function TravelInput({ onSearch, isLoading, userLocation }: TravelInputProps) {
  const [origin, setOrigin] = useState('Delhi');
  const [destination, setDestination] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [liveSuggestions, setLiveSuggestions] = useState<Place[]>([]);
  const [isFetching, setIsFetching] = useState(false);

  useEffect(() => {
    if (!destination.trim() || destination.trim().length < 2) {
      setLiveSuggestions([]);
      setIsFetching(false);
      return;
    }

    setIsFetching(true);
    const timeout = setTimeout(async () => {
      try {
        const lat = userLocation?.latitude ?? 21.1702;
        const lon = userLocation?.longitude ?? 72.8311;
        
        // Use OSM Photon API for free flight destination suggestions (biased by location)
        const res = await fetch(
          `https://photon.komoot.io/api/?q=${encodeURIComponent(destination.trim())}&lat=${lat}&lon=${lon}&limit=5`
        );
        const data = await res.json();
        
        if (data && data.features) {
          const parsed = data.features.map((f: any) => {
            const p = f.properties;
            const subtitleParts = [p.district, p.city, p.state].filter(Boolean);
            return {
              icon: 'navigation',
              title: p.name || p.city || 'Unknown Location',
              subtitle: subtitleParts.join(', '),
            };
          });
          setLiveSuggestions(parsed);
        }
      } catch (err) {
        console.warn('Autocomplete fetch error:', err);
      } finally {
        setIsFetching(false);
      }
    }, 400);

    return () => clearTimeout(timeout);
  }, [destination, userLocation]);

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  const handleSubmit = () => {
    if (origin.trim() && destination.trim()) {
      setShowSuggestions(false);
      onSearch(origin, destination);
    }
  };

  const selectPlace = (place: Place) => {
    setDestination(place.title);
    setShowSuggestions(false);
    onSearch(origin, place.title);
  };

  const displaySuggestions = destination.trim().length > 1 ? liveSuggestions : SAVED_PLACES;

  const getTomorrowDateString = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return `Tomorrow, ${tomorrow.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.row}>
          <View style={styles.inputWrapper}>
            <Text style={styles.label}>From</Text>
            <TextInput
              style={styles.input}
              value={origin}
              onChangeText={setOrigin}
              placeholder="Origin City"
              placeholderTextColor={tc.color.muted}
            />
          </View>

          <TouchableOpacity style={styles.swapButton} onPress={handleSwap}>
            <Feather name="repeat" size={16} color={tc.color.iris} />
          </TouchableOpacity>

          <View style={[styles.inputWrapper, { alignItems: 'flex-end' }]}>
            <Text style={styles.label}>To</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              {isFetching && <ActivityIndicator size="small" color={tc.color.iris} style={{ marginRight: 8 }} />}
              <TextInput
                style={[styles.input, { textAlign: 'right' }]}
                value={destination}
                onChangeText={setDestination}
                placeholder="Destination"
                placeholderTextColor={tc.color.muted}
                onSubmitEditing={handleSubmit}
                returnKeyType="search"
                autoFocus
                onFocus={() => setShowSuggestions(true)}
              />
            </View>
          </View>
        </View>

        <View style={styles.divider} />

        <TouchableOpacity style={styles.dateRow}>
          <Feather name="calendar" size={16} color={tc.color.muted} />
          <Text style={styles.dateText}>{getTomorrowDateString()}</Text>
        </TouchableOpacity>
      </View>

      {showSuggestions && (
        <View style={styles.suggestions}>
          {displaySuggestions.length === 0 && !isFetching && destination.trim().length > 1 ? (
             <View style={styles.suggestionRow}>
                <Text style={styles.suggestionSubtitle}>No matches found</Text>
             </View>
          ) : (
            displaySuggestions.map((place, i) => (
              <TouchableOpacity key={i} style={styles.suggestionRow} onPress={() => selectPlace(place)}>
                <View style={styles.iconCircle}>
                  <Feather name={place.icon as any} size={18} color={tc.color.ink} />
                </View>
                <View style={styles.suggestionText}>
                  <Text style={styles.suggestionTitle}>{place.title}</Text>
                  <Text style={styles.suggestionSubtitle} numberOfLines={1}>{place.subtitle}</Text>
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: tc.space.md,
    paddingTop: tc.space.md,
    backgroundColor: tc.color.bg,
  },
  card: {
    backgroundColor: tc.color.surface,
    borderRadius: tc.radius.lg,
    padding: tc.space.md,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    zIndex: 2,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  inputWrapper: {
    flex: 1,
  },
  label: {
    fontSize: 12,
    color: tc.color.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  input: {
    fontSize: 22,
    fontWeight: '700',
    color: tc.color.ink,
    height: 32,
    padding: 0,
    minWidth: 100,
  },
  swapButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: tc.color.bg,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: tc.space.sm,
    borderWidth: 1,
    borderColor: tc.color.line,
  },
  divider: {
    height: 1,
    backgroundColor: tc.color.line,
    marginVertical: tc.space.md,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dateText: {
    fontSize: 15,
    fontWeight: '500',
    color: tc.color.ink,
  },
  suggestions: {
    marginTop: tc.space.md,
    backgroundColor: tc.color.surface,
    borderRadius: tc.radius.lg,
    overflow: 'hidden',
  },
  suggestionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: tc.space.md,
    borderBottomWidth: 1,
    borderBottomColor: tc.color.line,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: tc.color.bg,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: tc.space.md,
  },
  suggestionText: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: tc.color.ink,
    marginBottom: 2,
  },
  suggestionSubtitle: {
    fontSize: 13,
    color: tc.color.muted,
  },
});
