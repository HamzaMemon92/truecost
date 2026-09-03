import type { ComponentProps } from 'react';
import type { Feather } from '@expo/vector-icons';
import { CATEGORY_DEFINITIONS } from './providerManifest.generated';

export type TrueCostCategory = {
  id: string;
  name: string;
  engineCategory: string;
  family: 'everyday' | 'products' | 'travel' | 'money' | 'services';
  icon: ComponentProps<typeof Feather>['name'];
  route?: string;
  mode: 'search' | 'decision';
  requiresLocation: boolean;
  description: string;
  prompts: string[];
  capability: 'provider_observations' | 'deterministic_estimate' | 'development_preview' | 'persisted_offers';
};

const PRESENTATION: Record<string, Pick<TrueCostCategory, 'icon' | 'route' | 'mode' | 'prompts'>> = {
  grocery: { icon: 'shopping-cart', route: 'GroceryHub', mode: 'search', prompts: ['weekly grocery basket', 'milk and breakfast items', 'fresh fruit'] },
  food: { icon: 'coffee', mode: 'search', prompts: ['dinner near me', 'family meal', 'healthy lunch'] },
  pharmacy: { icon: 'plus-circle', mode: 'search', prompts: ['wellness essentials', 'personal care', 'medicine search'] },
  shopping: { icon: 'shopping-bag', route: 'ShoppingHub', mode: 'search', prompts: ['phone under my budget', 'wireless headphones', 'running shoes'] },
  mobility: { icon: 'navigation', route: 'Mobility', mode: 'decision', prompts: ['ride to the airport', 'schedule a ride', 'compare ride classes'] },
  travel: { icon: 'send', route: 'Travel', mode: 'decision', prompts: ['round-trip flight', 'flexible travel dates', 'one-way flight'] },
  hotels: { icon: 'home', route: 'Hotels', mode: 'decision', prompts: ['stay near my destination', 'refundable hotel', 'family-friendly stay'] },
  deals: { icon: 'tag', route: 'Deals', mode: 'decision', prompts: ['cashback offers', 'expiring offers', 'payment discounts'] },
  finance: { icon: 'credit-card', route: 'Finance', mode: 'decision', prompts: ['best payment method', 'card benefits', 'UPI offers'] },
  services: { icon: 'briefcase', mode: 'search', prompts: ['team productivity tool', 'design collaboration service', 'work software'] },
};

export const CATEGORY_CATALOG: TrueCostCategory[] = CATEGORY_DEFINITIONS.map(category => ({
  id: category.id,
  name: category.name,
  engineCategory: category.engine_category,
  family: category.family,
  requiresLocation: category.requires_location,
  description: category.description,
  capability: category.capability,
  ...PRESENTATION[category.id],
}));

export const PROFILE_CATEGORY_NAMES = CATEGORY_CATALOG.map(item => item.name);
export const categoryByName = (value?: string) => CATEGORY_CATALOG.find(item => item.name === value || item.engineCategory === value) || CATEGORY_CATALOG[0];
export const categoryById = (value: string) => CATEGORY_CATALOG.find(item => item.id === value);
