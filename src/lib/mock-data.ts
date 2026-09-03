// Static mock data for the NexWise frontend prototype.

export const user = {
  name: "Alex Morgan",
  firstName: "Alex",
  plan: "Premium",
  email: "alex.morgan@gmail.com",
  city: "Bengaluru, India",
  initials: "AM",
};

export const inr = (n: number) =>
  "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });

export const usd = (n: number) =>
  "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/* ------------------------------- dashboard ------------------------------- */

export const savingsByCategory = [
  { label: "Ride", value: 2218, pct: 24, share: 0.72 },
  { label: "Grocery", value: 1437, pct: 15, share: 0.48 },
  { label: "Shopping", value: 941, pct: 12, share: 0.34 },
  { label: "Travel", value: 750, pct: 20, share: 0.26 },
];

export const recentActivity = [
  {
    provider: "Uber Go Sedan",
    detail: "Koramangala → BLR Airport",
    amount: 1890,
    saved: 610,
    time: "9:15 AM",
  },
  {
    provider: "Blinkit Grocery",
    detail: "Delivered • 12 items",
    amount: 2435,
    saved: 465,
    time: "Yesterday",
  },
  {
    provider: "Amazon",
    detail: "Sony WH-CH720N Headphones",
    amount: 8999,
    saved: 1000,
    time: "2 days ago",
  },
  {
    provider: "IndiGo Flight",
    detail: "BLR → DEL • 24 May",
    amount: 12649,
    saved: 1851,
    time: "3 days ago",
  },
];

export const savingsTrend = [
  { label: "May 1", value: 4200 },
  { label: "May 5", value: 6900 },
  { label: "May 8", value: 9100 },
  { label: "May 12", value: 8600 },
  { label: "May 15", value: 13400 },
  { label: "May 19", value: 16200 },
  { label: "May 22", value: 19800 },
  { label: "May 26", value: 24500 },
  { label: "May 29", value: 31240 },
];

export const monthlySavings = [
  { label: "Dec", value: 8420 },
  { label: "Jan", value: 11300 },
  { label: "Feb", value: 14980 },
  { label: "Mar", value: 16240 },
  { label: "Apr", value: 21100 },
  { label: "May", value: 12860 },
];

export const recentIntents = [
  { text: "Ride to Airport", meta: "Compared 8 options", href: "/compare/rides" },
  { text: "Weekly grocery basket", meta: "5 stores compared", href: "/grocery" },
  { text: "MacBook Air 13\" M3", meta: "4 sellers compared", href: "/compare/product" },
];

export const upcomingTrips = [
  {
    title: "Bengaluru → Delhi",
    sub: "IndiGo 6E 2031",
    day: "24",
    month: "MAY",
    meta: "10:05 AM",
  },
  {
    title: "Goa Weekend",
    sub: "Hotel Prime Ocean",
    day: "07",
    month: "JUN",
    meta: "2 Nights",
  },
];

export const recommendedActions = [
  {
    title: "Compare your daily commute",
    sub: "You could save up to ₹230 today",
    cta: "Compare",
    href: "/compare/rides",
  },
  {
    title: "Grocery prices dropped",
    sub: "12 items are now cheaper",
    cta: "View deals",
    href: "/grocery",
  },
  {
    title: "Price watch alert",
    sub: "iPhone 15 hit your target price",
    cta: "View item",
    href: "/price-tracker",
  },
];

/* ------------------------------ product compare --------------------------- */

export type Laptop = {
  id: string;
  name: string;
  sub: string;
  config: string;
  price: number;
  priceLabel: string;
  recommended?: boolean;
  specs: Record<string, string>;
  cost: {
    base: number;
    shipping: string;
    taxes: number;
    warranty: string;
    trueCost: number;
    advantage?: string;
  };
  offers: { card: string; bank: string };
  emi: { noCost: number; low: number };
  seller: { score: number; name: string; type: string };
};

export const laptops: Laptop[] = [
  {
    id: "mba-m3",
    name: 'Apple MacBook Air 13"',
    sub: "M3 (2024)",
    config: "16GB • 512GB • Midnight",
    price: 109900,
    priceLabel: "Lowest TrueCost",
    recommended: true,
    specs: {
      Processor: "Apple M3 chip",
      Memory: "16GB Unified",
      Storage: "512GB SSD",
      Display: '13.6" Liquid Retina',
      "Battery Life": "Up to 18 hours",
      Weight: "1.24 kg",
    },
    cost: {
      base: 104900,
      shipping: "FREE",
      taxes: 6645,
      warranty: "Included",
      trueCost: 116545,
    },
    offers: { card: "5% Cashback", bank: "₹5,000 ICICI Discount" },
    emi: { noCost: 9712, low: 8317 },
    seller: { score: 9.6, name: "Amazon", type: "Trusted Seller" },
  },
  {
    id: "mba-m2",
    name: 'Apple MacBook Air 13"',
    sub: "M2 (2022)",
    config: "16GB • 512GB • Midnight",
    price: 89900,
    priceLabel: "Low TrueCost",
    specs: {
      Processor: "Apple M2 chip",
      Memory: "16GB Unified",
      Storage: "512GB SSD",
      Display: '13.6" Liquid Retina',
      "Battery Life": "Up to 18 hours",
      Weight: "1.24 kg",
    },
    cost: {
      base: 84900,
      shipping: "FREE",
      taxes: 5427,
      warranty: "Included",
      trueCost: 94827,
      advantage: "₹21,718 (7%)",
    },
    offers: { card: "3% Cashback", bank: "₹2,500 SBI Discount" },
    emi: { noCost: 9019, low: 7331 },
    seller: { score: 9.2, name: "Flipkart", type: "Trusted Seller" },
  },
  {
    id: "hp-pavilion",
    name: 'HP Pavilion Plus 14"',
    sub: "(2024)",
    config: "16GB • 512GB • Silver",
    price: 79900,
    priceLabel: "Low TrueCost",
    specs: {
      Processor: "Intel Core Ultra 5 125H",
      Memory: "16GB LPDDR5",
      Storage: "512GB SSD",
      Display: '14" 2.8K OLED',
      "Battery Life": "Up to 12 hours",
      Weight: "1.34 kg",
    },
    cost: {
      base: 74900,
      shipping: "FREE",
      taxes: 4818,
      warranty: "Included",
      trueCost: 84618,
      advantage: "₹10,209 (5%)",
    },
    offers: { card: "3% Instant Off", bank: "₹7,500 HDFC Discount" },
    emi: { noCost: 7982, low: 6519 },
    seller: { score: 8.7, name: "HP Online Store", type: "Official Store" },
  },
  {
    id: "dell-xps",
    name: "Dell XPS 13 Plus",
    sub: "(2024)",
    config: "16GB • 512GB • Graphite",
    price: 129900,
    priceLabel: "Low TrueCost",
    specs: {
      Processor: "Intel Core Ultra 7 155H",
      Memory: "16GB LPDDR5X",
      Storage: "512GB SSD",
      Display: '13.4" 2.8K OLED',
      "Battery Life": "Up to 12 hours",
      Weight: "1.24 kg",
    },
    cost: {
      base: 124900,
      shipping: "FREE",
      taxes: 7819,
      warranty: "Included",
      trueCost: 137719,
      advantage: "₹26,927 (10%)",
    },
    offers: { card: "5% Cashback", bank: "₹5,000 ICICI Discount" },
    emi: { noCost: 11476, low: 9337 },
    seller: { score: 9.4, name: "Dell Store", type: "Official Store" },
  },
];

export const priceHistory = [
  118400, 117200, 119000, 116100, 117400, 114900, 115600, 113200, 114100, 112000,
  113400, 111200, 112600, 110400, 111800, 109900, 110600, 109200, 110100, 108600,
  109900,
].map((v, i) => ({ label: `D${i + 1}`, value: v }));

export const priceHistoryTicks = ["Apr 1", "Apr 15", "Apr 30", "May 15", "May 31", "Jun 15", "Jun 30"];

export const whyWeRecommend = [
  "Best overall performance & efficiency",
  "Lowest TrueCost in its class",
  "Longest battery life",
  "Highest seller trust & reliability",
  "Best resale value after 2 years",
];

export const sellerComparison = [
  { seller: "Amazon", price: 109900, trust: 9.6 },
  { seller: "Flipkart", price: 110400, trust: 9.2 },
  { seller: "Croma", price: 112900, trust: 8.9 },
  { seller: "Vijay Sales", price: 113400, trust: 8.7 },
];

/* --------------------------------- rides --------------------------------- */

export const rides = [
  {
    id: "uber-go",
    provider: "Uber Go",
    sub: "Uber",
    price: 482,
    trueCost: 482,
    rating: 4.6,
    eta: 60,
    pickup: "2 min away",
    score: 9.4,
    recommended: true,
    onTime: 96,
  },
  {
    id: "ola-prime",
    provider: "Ola Prime",
    sub: "Ola",
    price: 519,
    trueCost: 534,
    rating: 4.4,
    eta: 62,
    pickup: "4 min away",
    score: 8.6,
    onTime: 91,
  },
  {
    id: "rapido",
    provider: "Rapido Cab",
    sub: "Rapido",
    price: 441,
    trueCost: 468,
    rating: 4.1,
    eta: 65,
    pickup: "1 min away",
    score: 8.1,
    onTime: 84,
  },
  {
    id: "namma-yatri",
    provider: "Namma Yatri",
    sub: "Namma Yatri",
    price: 462,
    trueCost: 489,
    rating: 4.3,
    eta: 63,
    pickup: "3 min away",
    score: 8.4,
    onTime: 88,
  },
  {
    id: "uber-xl",
    provider: "Uber XL",
    sub: "Uber",
    price: 648,
    trueCost: 648,
    rating: 4.7,
    eta: 58,
    pickup: "5 min away",
    score: 7.9,
    onTime: 97,
  },
];

export const rideReasons = [
  "Best balance of price, ETA & reliability",
  "Highest on-time probability (96%)",
  "Trusted provider with top safety score",
  "Good availability in your area",
];

/* -------------------------------- grocery -------------------------------- */

export const basket = [
  { name: "Amul Gold Milk (1L)", qty: 2, price: 120 },
  { name: "Aashirvaad Atta (2kg)", qty: 1, price: 249 },
  { name: "Fortune Sunflower Oil (1L)", qty: 1, price: 145 },
  { name: "Tata Tea Premium (250g)", qty: 1, price: 160 },
  { name: "India Gate Basmati Rice (1kg)", qty: 1, price: 195 },
  { name: "Toor Dal (1kg)", qty: 1, price: 120 },
  { name: "Surf Excel Matic (2kg)", qty: 1, price: 299 },
  { name: "Colgate Toothpaste (150g)", qty: 2, price: 160 },
];

export const stores = [
  {
    name: "Blinkit",
    rating: 4.4,
    total: 2612,
    save: "₹233 (8%)",
    available: "25 / 28",
    delivery: 29,
    handling: 15,
    platform: 10,
    coupons: -60,
    eta: "14–17 mins",
    best: true,
  },
  {
    name: "Zepto",
    rating: 4.3,
    total: 2649,
    save: "₹201 (7%)",
    available: "27 / 28",
    delivery: 19,
    handling: 15,
    platform: 9,
    coupons: -40,
    eta: "19–22 mins",
  },
  {
    name: "Instamart",
    rating: 4.2,
    total: 2701,
    save: "₹149 (5%)",
    available: "26 / 28",
    delivery: 39,
    handling: 15,
    platform: 10,
    coupons: -30,
    eta: "25–30 mins",
  },
  {
    name: "BigBasket",
    rating: 4.4,
    total: 2845,
    save: "—",
    available: "24 / 28",
    delivery: 0,
    handling: 25,
    platform: 15,
    coupons: -25,
    eta: "60–90 mins",
  },
  {
    name: "More",
    rating: 4.1,
    total: 2910,
    save: "—",
    available: "26 / 28",
    delivery: 49,
    handling: 20,
    platform: 10,
    coupons: -15,
    eta: "45–60 mins",
  },
];

/* --------------------------------- travel -------------------------------- */

export const outboundFlights = [
  { dep: "8:15 AM", arr: "11:35 AM", dur: "3h 20m", stops: "Nonstop", airline: "IndiGo", price: 12649, tag: "Excellent", smart: true },
  { dep: "7:30 AM", arr: "11:00 AM", dur: "3h 30m", stops: "Nonstop", airline: "Vistara", price: 13120, tag: "Very Good" },
  { dep: "9:45 AM", arr: "1:20 PM", dur: "3h 35m", stops: "1 stop", airline: "Air India", price: 10499, tag: "Good", note: "HYD • 45m layover" },
];

export const returnFlights = [
  { dep: "5:30 PM", arr: "8:45 PM", dur: "3h 15m", stops: "Nonstop", airline: "IndiGo", price: 11380, tag: "Excellent", smart: true },
  { dep: "5:00 PM", arr: "8:15 PM", dur: "3h 15m", stops: "Nonstop", airline: "Vistara", price: 11790, tag: "Very Good" },
  { dep: "4:20 PM", arr: "8:50 PM", dur: "4h 30m", stops: "1 stop", airline: "Air India", price: 9360, tag: "Good", note: "BOM • 1h 05m layover" },
];

export const hotels = [
  { name: "Taj Fort Aguada Resort", tag: "Smart Pick", rating: 4.6, reviews: 2248, price: 14900, notes: ["Oceanfront", "Free cancellation May 22", "Breakfast included"] },
  { name: "W Goa, Vagator", tag: "Premium Pick", rating: 4.7, reviews: 1896, price: 18100, notes: ["Beach access", "Free cancellation May 21", "Resort fee included"] },
  { name: "Novotel Candolim", tag: "Budget Pick", rating: 4.2, reviews: 612, price: 11200, notes: ["Rooftop pool", "Free cancellation May 22", "No hidden fees"] },
];

export const budgetBreakdown = [
  { label: "Flights", value: 24029, color: "var(--color-chart-1)" },
  { label: "Hotel (2 nights)", value: 14900, color: "var(--color-chart-3)" },
  { label: "Airport Ride", value: 2980, color: "var(--color-chart-4)" },
  { label: "Taxes & Fees", value: 1270, color: "var(--color-chart-5)" },
];

export const itinerary = [
  { date: "Sat, May 24", rows: [["8:15 AM", "BLR → GOI", "IndiGo 6E 2031 · Nonstop"], ["11:35 AM", "Arrive in Goa", ""]] },
  { date: "May 24 – May 28", rows: [["2 nights stay", "Candolim, Goa", ""]] },
  { date: "Mon, May 28", rows: [["5:30 PM", "GOI → BLR", "IndiGo 6E 456 · Nonstop"], ["8:45 PM", "Arrive in Bengaluru", ""]] },
];

/* -------------------------------- ownership ------------------------------ */

export const ownedItems = [
  { name: "iPhone 15 Pro", brand: "Apple", purchased: "Mar 12, 2025", paid: 134900, value: 112000, saved: 11900, status: "Protected", category: "Electronics" },
  { name: "MacBook Air M2", brand: "Apple", purchased: "Apr 16, 2025", paid: 109900, value: 87000, saved: 15240, status: "Under Warranty", category: "Electronics" },
  { name: "WH-1000XM5", brand: "Sony", purchased: "Apr 3, 2025", paid: 34800, value: 28000, saved: 4560, status: "Price Drop Alert", category: "Accessories" },
  { name: "Air Fryer XXL", brand: "Philips", purchased: "Jan 25, 2025", paid: 19999, value: 15000, saved: 3160, status: "Return Eligible", category: "Appliances" },
  { name: "Galaxy Watch 6", brand: "Samsung", purchased: "Feb 8, 2025", paid: 28999, value: 19500, saved: 2400, status: "Under Warranty", category: "Accessories" },
  { name: "Dyson V12", brand: "Dyson", purchased: "Dec 19, 2024", paid: 47900, value: 33000, saved: 5100, status: "Protected", category: "Appliances" },
];

export const smartAlerts = [
  { title: "Warranty expiring soon", sub: "Apple MacBook Air · Expires in 18 days", cta: "Renew", tone: "positive" as const },
  { title: "Price drop detected", sub: "Sony WH-1000XM5 · ₹3,490 drop · 2h ago", cta: "View", tone: "warning" as const },
  { title: "Return window closing", sub: "Philips Air Fryer · 3 days left to return", cta: "View", tone: "danger" as const },
];

export const resaleTrend = [
  190000, 194000, 191000, 198000, 202000, 199000, 205000, 208000, 206000, 212000,
].map((v, i) => ({ label: `W${i + 1}`, value: v }));

/* ------------------------------ price tracker ---------------------------- */

export const trackedProducts = [
  {
    name: "iPhone 15 (128GB)",
    seller: "Amazon • Electronics",
    price: 69900,
    change: -4000,
    target: 65000,
    progress: 78,
    alert: true,
    history: [78400, 76900, 75200, 74100, 73400, 72100, 71800, 70500, 69900].map((v, i) => ({ label: `W${i + 1}`, value: v })),
  },
  {
    name: "AirPods Pro (2nd Gen)",
    seller: "Flipkart • Audio",
    price: 22900,
    change: -1100,
    target: 21900,
    progress: 88,
    alert: true,
    history: [26900, 26100, 25400, 24900, 24200, 23800, 23400, 23000, 22900].map((v, i) => ({ label: `W${i + 1}`, value: v })),
  },
  {
    name: "Sony WH-1000XM5",
    seller: "Croma • Audio",
    price: 26990,
    change: -3490,
    target: 25000,
    progress: 64,
    alert: false,
    history: [33900, 33100, 32400, 31200, 30500, 29800, 28400, 27500, 26990].map((v, i) => ({ label: `W${i + 1}`, value: v })),
  },
  {
    name: 'LG 55" C4 OLED',
    seller: "Reliance Digital • TV",
    price: 134990,
    change: 2400,
    target: 124900,
    progress: 42,
    alert: true,
    history: [141000, 139500, 137900, 136200, 134100, 132600, 132000, 132590, 134990].map((v, i) => ({ label: `W${i + 1}`, value: v })),
  },
];

/* --------------------------------- agent --------------------------------- */

export const agentSuggestions = [
  "Find me the best laptop under ₹80,000",
  "Compare rides to the airport",
  "Find the cheapest grocery basket",
  "Plan my weekend trip",
  "Find the best flight to Delhi",
];

export const agentThread = [
  {
    role: "user" as const,
    text: "I need to reach the airport tomorrow at 6:30 AM. Find the best option.",
  },
];
