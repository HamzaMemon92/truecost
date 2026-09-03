import React, { useState } from 'react';
import { View, TextInput, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { tc } from '../../design/tokens';
import { Category } from '../../utils/IntentEngine';

interface UniversalInputProps {
  onSearch: (query: string) => void;
  category: Category | 'All';
  isLoading: boolean;
}

export default function UniversalInput({ onSearch, category, isLoading }: UniversalInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const isFoodOrGrocery = category === 'Food' || category === 'Grocery';
  
  // Logical Fix: Don't hardcode BTM Layout. In a real app, this would use reverse geocoding.
  const locationLabel = "Current Location";

  return (
    <View style={styles.container}>
      {isFoodOrGrocery && (
        <View style={styles.locationHeader}>
          <Feather name="map-pin" size={14} color={tc.color.iris} />
          <Text style={styles.locationText}>Deliver to <Text style={styles.locationBold}>{locationLabel}</Text></Text>
          <Feather name="chevron-down" size={14} color={tc.color.iris} />
        </View>
      )}

      <View style={styles.searchBar}>
        <Feather name="search" size={20} color={tc.color.muted} style={styles.icon} />
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder={category === 'All' ? 'Search anything (flights, cabs, groceries...)' : `Search ${category}...`}
          placeholderTextColor={tc.color.muted}
          onSubmitEditing={handleSubmit}
          returnKeyType="search"
          autoFocus={category === 'All'}
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => setQuery('')} style={styles.clear}>
            <Feather name="x" size={16} color={tc.color.muted} />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: tc.space.md,
    paddingTop: tc.space.sm,
    backgroundColor: tc.color.bg,
  },
  locationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: tc.space.sm,
    gap: 4,
  },
  locationText: {
    fontSize: 13,
    color: tc.color.ink,
  },
  locationBold: {
    fontWeight: '700',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tc.color.surface,
    height: 52,
    borderRadius: tc.radius.pill,
    paddingHorizontal: tc.space.md,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
  },
  icon: {
    marginRight: tc.space.sm,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: tc.color.ink,
    height: '100%',
  },
  clear: {
    padding: 4,
  },
});
