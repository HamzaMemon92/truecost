import React from 'react';
import * as Sentry from '@sentry/react-native';
import { ActivityIndicator, LogBox, StyleSheet, View } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import SearchExecutionScreen from './screens/SearchExecutionScreen';
import LocationGate from './screens/LocationGate';
import WelcomeScreen from './screens/WelcomeScreen';
import AuthScreen from './screens/AuthScreen';
import CommerceScreen from './screens/CommerceScreen';
import FoundationHome from './screens/FoundationHome';
import ExploreHub from './screens/ExploreHub';
import GroceryHubScreen from './screens/GroceryHubScreen';
import ShoppingHubScreen from './screens/ShoppingHubScreen';
import { OrbitRail } from './components/OrbitRail';
import { AuthProvider, useAuth } from './auth/AuthContext';
import SmartCartScreen from './screens/SmartCartScreen';
import SubstitutionScreen from './screens/SubstitutionScreen';
import ProductDetailScreen from './screens/ProductDetailScreen';
import FocusedCompareScreen from './screens/FocusedCompareScreen';
import CheckoutHandoffScreen from './screens/CheckoutHandoffScreen';
import ComparisonScreen from './screens/ComparisonScreen';
import DecisionExplanationScreen from './screens/DecisionExplanationScreen';
import PriceTrendsScreen from './screens/PriceTrendsScreen';
import CategoryDecisionScreen from './screens/CategoryDecisionScreen';
import WatchlistScreen from './screens/WatchlistScreen';
import SettingsScreen from './screens/SettingsScreen';
import ActivityScreen from './screens/ActivityScreen';
import ProfileHubScreen from './screens/ProfileHubScreen';
import NotificationsScreen from './screens/NotificationsScreen';
import MobilityScreen from './screens/MobilityScreen';
import TravelScreen from './screens/TravelScreen';
import HotelsScreen from './screens/HotelsScreen';
import DealsScreen from './screens/DealsScreen';
import FinanceScreen from './screens/FinanceScreen';
import DealDetailScreen from './screens/DealDetailScreen';
import MobilityResultsScreen from './screens/MobilityResultsScreen';
import FlightResultsScreen from './screens/FlightResultsScreen';
import HotelResultsScreen from './screens/HotelResultsScreen';
import ComparisonHistoryScreen from './screens/ComparisonHistoryScreen';
import ComparisonHistoryDetailScreen from './screens/ComparisonHistoryDetailScreen';
import SavedListDetailScreen from './screens/SavedListDetailScreen';
import SharedListScreen from './screens/SharedListScreen';
import ProfileEditScreen from './screens/ProfileEditScreen';
import LocationManagementScreen from './screens/LocationManagementScreen';
import PaymentPreferencesScreen from './screens/PaymentPreferencesScreen';
import CartOptimizationScreen from './screens/CartOptimizationScreen';
import ScanCompareScreen from './screens/ScanCompareScreen';
import HelpSupportScreen from './screens/HelpSupportScreen';
import ReportIssueScreen from './screens/ReportIssueScreen';
import PermissionsScreen from './screens/PermissionsScreen';
import AccountSecurityScreen from './screens/AccountSecurityScreen';
import PhoneAuthScreen from './screens/PhoneAuthScreen';
import OtpVerificationScreen from './screens/OtpVerificationScreen';
import PushRegistrationSync from './notifications/PushRegistrationSync';
import ConnectedAccountsScreen from './screens/ConnectedAccountsScreen';
import E2EScraperHarness from './screens/E2EScraperHarness';
import ToastNotification from './components/ToastNotification';
import ErrorBoundary from './components/core/ErrorBoundary';
import { LocationProvider, useUserLocation } from './location/LocationContext';
import { QueryProvider } from './query/QueryClient';
import { SearchHistoryProvider } from './search/SearchHistoryContext';
import { tc } from './design/tokens';
import { ExperienceProvider, useExperience } from './accessibility/ExperienceContext';

const Stack = createNativeStackNavigator();
const EntryStack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();
const theme = { ...DefaultTheme, colors: { ...DefaultTheme.colors, background: tc.color.bg, card: tc.color.surface, text: tc.color.ink, border: tc.color.line, primary: tc.color.iris } };
// Every editable screen uses react-native-safe-area-context. The one remaining
// legacy import lives in the contractually immutable AgentSearchScreen.
LogBox.ignoreLogs(['SafeAreaView has been deprecated and will be removed in a future release']);
Sentry.init({ dsn: process.env.EXPO_PUBLIC_SENTRY_DSN || '', enabled: !!process.env.EXPO_PUBLIC_SENTRY_DSN, sendDefaultPii: false, tracesSampleRate: 0.1 });
const linking: any = { prefixes: ['truecost://'], config: { screens: { SharedList: 'shared-list/:shareToken', ProductDetail: 'product/:productId', Watchlist: 'watchlist', Notifications: 'notifications', E2ETest: 'e2e-test', ScraperCert: 'scraper_cert', MainTabs: { screens: { Home: 'home', Explore: 'explore', Compare: 'compare', Saved: 'saved', Profile: 'profile' } } } } };

function AppTabs() {
  return <Tabs.Navigator initialRouteName="Home" tabBar={props => <OrbitRail {...props} />} screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: tc.color.bg }, lazy: true }}>
    <Tabs.Screen name="Home" component={FoundationHome} />
    <Tabs.Screen name="Explore" component={ExploreHub} />
    <Tabs.Screen name="Compare" component={ExploreHub} />
    <Tabs.Screen name="Saved">{props => <CommerceScreen {...props} kind="saved-items" />}</Tabs.Screen>
    <Tabs.Screen name="Profile" component={ProfileHubScreen} />
  </Tabs.Navigator>;
}

function Entry() {
  const { reduceMotion } = useExperience();
  return <EntryStack.Navigator screenOptions={{ headerShown: false, animation: reduceMotion ? 'none' : 'slide_from_right', contentStyle: { backgroundColor: tc.color.bg } }}>
    <EntryStack.Screen name="Welcome" component={WelcomeScreen} />
    <EntryStack.Screen name="Auth" component={AuthScreen} />
    <EntryStack.Screen name="PhoneAuth" component={PhoneAuthScreen} />
    <EntryStack.Screen name="OtpVerification" component={OtpVerificationScreen} />
    <EntryStack.Screen name="SharedList" component={SharedListScreen} />
    <EntryStack.Screen name="E2ETest" component={E2EScraperHarness} />
    <EntryStack.Screen name="ScraperCert" component={E2EScraperHarness} />
  </EntryStack.Navigator>;
}

function AppNavigator() {
  const { location, ready, setLocation } = useUserLocation();
  const { reduceMotion } = useExperience();
  if (!ready) return <View style={styles.boot}><ActivityIndicator color={tc.color.iris} /></View>;
  if (!location) return <LocationGate onLocationGranted={setLocation} />;
  return <Stack.Navigator screenOptions={{ headerShown: false, animation: reduceMotion ? 'none' : 'slide_from_right', contentStyle: { backgroundColor: tc.color.bg }, freezeOnBlur: true }}>
    <Stack.Screen name="MainTabs" component={AppTabs} />
    <Stack.Screen name="E2ETest" component={E2EScraperHarness} />
    <Stack.Screen name="ScraperCert" component={E2EScraperHarness} />
    <Stack.Screen name="GroceryHub" component={GroceryHubScreen} />
    <Stack.Screen name="ShoppingHub" component={ShoppingHubScreen} />
    <Stack.Screen name="AgentSearch" component={SearchExecutionScreen} />
    <Stack.Screen name="Cart" component={SmartCartScreen} />
    <Stack.Screen name="CartOptimization" component={CartOptimizationScreen} />
    <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
    <Stack.Screen name="FocusedCompare" component={FocusedCompareScreen} />
    <Stack.Screen name="Comparison" component={ComparisonScreen} />
    <Stack.Screen name="DecisionExplanation" component={DecisionExplanationScreen} />
    <Stack.Screen name="PriceTrends" component={PriceTrendsScreen} />
    <Stack.Screen name="Substitutions" component={SubstitutionScreen} />
    <Stack.Screen name="CheckoutHandoff" component={CheckoutHandoffScreen} />
    <Stack.Screen name="CategoryDecision" component={CategoryDecisionScreen} />
    <Stack.Screen name="Mobility" component={MobilityScreen} />
    <Stack.Screen name="Travel" component={TravelScreen} />
    <Stack.Screen name="Hotels" component={HotelsScreen} />
    <Stack.Screen name="Deals" component={DealsScreen} />
    <Stack.Screen name="Finance" component={FinanceScreen} />
    <Stack.Screen name="MobilityResults" component={MobilityResultsScreen} />
    <Stack.Screen name="FlightResults" component={FlightResultsScreen} />
    <Stack.Screen name="HotelResults" component={HotelResultsScreen} />
    <Stack.Screen name="DealDetail" component={DealDetailScreen} />
    <Stack.Screen name="Watchlist" component={WatchlistScreen} />
    <Stack.Screen name="Activity" component={ActivityScreen} />
    <Stack.Screen name="Notifications" component={NotificationsScreen} />
    <Stack.Screen name="ComparisonHistory" component={ComparisonHistoryScreen} />
    <Stack.Screen name="ComparisonHistoryDetail" component={ComparisonHistoryDetailScreen} />
    <Stack.Screen name="SavedLists" component={SavedListDetailScreen} />
    <Stack.Screen name="SharedList" component={SharedListScreen} />
    <Stack.Screen name="ProfileEdit" component={ProfileEditScreen} />
    <Stack.Screen name="LocationManagement" component={LocationManagementScreen} />
    <Stack.Screen name="PaymentPreferences" component={PaymentPreferencesScreen} />
    <Stack.Screen name="Settings" component={SettingsScreen} />
    <Stack.Screen name="ScanCompare" component={ScanCompareScreen} />
    <Stack.Screen name="HelpSupport" component={HelpSupportScreen} />
    <Stack.Screen name="ReportIssue" component={ReportIssueScreen} />
    <Stack.Screen name="Permissions" component={PermissionsScreen} />
    <Stack.Screen name="AccountSecurity" component={AccountSecurityScreen} />
    <Stack.Screen name="ConnectedAccounts" component={ConnectedAccountsScreen} />
  </Stack.Navigator>;
}

function Root() {
  const { session, isGuest, ready } = useAuth();
  if (!ready) return <View style={styles.boot}><ActivityIndicator color={tc.color.iris} /></View>;
  return <QueryProvider key={session?.user_id || (isGuest ? 'guest' : 'signed-out')}><NavigationContainer theme={theme} linking={linking}><StatusBar style="dark" /><ToastNotification />{session ? <PushRegistrationSync /> : null}{session || isGuest ? <AppNavigator /> : <Entry />}</NavigationContainer></QueryProvider>;
}

function AccountScopedProviders() {
  const { session, isGuest } = useAuth();
  const scope = session?.user_id || (isGuest ? 'guest' : 'signed-out');
  return <ExperienceProvider key={`experience:${scope}`}><LocationProvider accountScope={scope}><SearchHistoryProvider key={`search:${scope}`}><Root /></SearchHistoryProvider></LocationProvider></ExperienceProvider>;
}

function App() {
  return <SafeAreaProvider><ErrorBoundary fallbackMessage="TrueCost encountered an unexpected interface error."><AuthProvider><AccountScopedProviders /></AuthProvider></ErrorBoundary></SafeAreaProvider>;
}
export default Sentry.wrap(App);
const styles = StyleSheet.create({ boot: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: tc.color.bg } });
