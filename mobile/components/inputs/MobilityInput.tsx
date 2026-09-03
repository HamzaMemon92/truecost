import React, { useState, useEffect } from 'react';
import { View, TextInput, StyleSheet, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { tc } from '../../design/tokens';
import type { UserLocation } from '../../screens/LocationGate';

interface MobilityInputProps {
  onSearch: (pickup: string, dropoff: string) => void;
  isLoading: boolean;
  userLocation?: UserLocation;
}

interface Place {
  icon: string;
  title: string;
  subtitle: string;
}

const SAVED_PLACES: Place[] = [
  { icon: 'home', title: 'Home', subtitle: 'Saved Location' },
  { icon: 'briefcase', title: 'Work', subtitle: 'Saved Location' },
  { icon: 'map', title: 'Airport', subtitle: 'City Airport' },
];

export default function MobilityInput({ onSearch, isLoading, userLocation }: MobilityInputProps) {
  const [pickup, setPickup] = useState('Current Location');
  const [dropoff, setDropoff] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [liveSuggestions, setLiveSuggestions] = useState<Place[]>([]);
  const [isFetching, setIsFetching] = useState(false);

  // Debounced Live Autocomplete using OpenStreetMap (Photon API)
  useEffect(() => {
    if (!dropoff.trim() || dropoff.trim().length < 2) {
      setLiveSuggestions([]);
      setIsFetching(false);
      return;
    }

    setIsFetching(true);
    const timeout = setTimeout(async () => {
      try {
        // Use user location to bias search results (e.g., searching "rail" in Surat suggests Surat places)
        const lat = userLocation?.latitude ?? 21.1702; // Default to Surat if missing
        const lon = userLocation?.longitude ?? 72.8311;
        
        const res = await fetch(
          `https://photon.komoot.io/api/?q=${encodeURIComponent(dropoff.trim())}&lat=${lat}&lon=${lon}&limit=5`
        );
        const data = await res.json();
        
        if (data && data.features) {
          const parsed = data.features.map((f: any) => {
            const p = f.properties;
            const subtitleParts = [p.street, p.district, p.city, p.state].filter(Boolean);
            return {
              icon: 'map-pin',
              title: p.name || p.city || p.street || 'Unknown Location',
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
    }, 400); // 400ms debounce to prevent spamming the API

    return () => clearTimeout(timeout);
  }, [dropoff, userLocation]);

  const handleSubmit = () => {
    if (dropoff.trim()) {
      setShowSuggestions(false);
      onSearch(pickup, dropoff);
    }
  };

  const selectPlace = (place: Place) => {
    setDropoff(place.title);
    setShowSuggestions(false);
    onSearch(pickup, place.title);
  };

  const displaySuggestions = dropoff.trim().length > 1 ? liveSuggestions : SAVED_PLACES;

  return (
    <View style={styles.container}>
      <View style={styles.inputCard}>
        {/* Visual Timeline (Uber style) */}
        <View style={styles.timeline}>
          <View style={styles.dot} />
          <View style={styles.line} />
          <View style={styles.square} />
        </View>

        {/* Inputs */}
        <View style={styles.fields}>
          <View style={styles.fieldRow}>
            <TextInput
              style={[styles.input, styles.pickupInput]}
              value={pickup}
              onChangeText={setPickup}
              placeholder="Pickup Location"
              placeholderTextColor={tc.color.muted}
            />
          </View>
          <View style={styles.divider} />
          <View style={styles.fieldRow}>
            <TextInput
              style={styles.input}
              value={dropoff}
              onChangeText={setDropoff}
              placeholder="Where to?"
              placeholderTextColor={tc.color.muted}
              autoFocus
              onFocus={() => setShowSuggestions(true)}
              onSubmitEditing={handleSubmit}
              returnKeyType="search"
            />
            {isFetching && (
              <ActivityIndicator size="small" color={tc.color.iris} style={styles.loader} />
            )}
          </View>
        </View>
      </View>

      {showSuggestions && (
        <View style={styles.suggestions}>
          {displaySuggestions.length === 0 && !isFetching && dropoff.trim().length > 1 ? (
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
  inputCard: {
    flexDirection: 'row',
    backgroundColor: tc.color.surface,
    borderRadius: tc.radius.lg,
    padding: tc.space.sm,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
  },
  timeline: {
    width: 32,
    alignItems: 'center',
    paddingVertical: 18,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: tc.color.muted,
  },
  line: {
    width: 1,
    flex: 1,
    backgroundColor: tc.color.line,
    marginVertical: 4,
  },
  square: {
    width: 8,
    height: 8,
    backgroundColor: tc.color.iris,
  },
  fields: {
    flex: 1,
  },
  fieldRow: {
    height: 44,
    justifyContent: 'center',
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: tc.color.ink,
    fontWeight: '500',
    height: '100%',
  },
  pickupInput: {
    color: tc.color.muted,
  },
  loader: {
    marginLeft: tc.space.sm,
  },
  divider: {
    height: 1,
    backgroundColor: tc.color.line,
    marginLeft: -32,
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
