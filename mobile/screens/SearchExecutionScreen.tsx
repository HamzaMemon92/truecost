import React, { Suspense } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { tc } from '../design/tokens';

const AgentSearchScreen = React.lazy(() => import('./AgentSearchScreen'));

export default function SearchExecutionScreen({ route, navigation }: any) {
  const query = String(route.params?.initialQuery || '').trim();
  const category = String(route.params?.category || 'Grocery');

  return (
    <Suspense fallback={<View style={styles.boot}><ActivityIndicator color={tc.color.iris} /></View>}>
      <AgentSearchScreen key={`${category}:${query}`} route={route} navigation={navigation} />
    </Suspense>
  );
}

const styles = StyleSheet.create({ 
  boot: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: tc.color.surfaceMuted }
});
