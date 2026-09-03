export type Category = 'Grocery' | 'Mobility' | 'Shopping' | 'Food' | 'Pharmacy' | 'Travel' | 'Finance' | 'Productivity';

// Elite local intent detection using regex heuristics
export class IntentEngine {
  static detectCategory(query: string): Category | null {
    const q = query.toLowerCase();

    // 1. Travel
    if (/flight|ticket|delhi|mumbai|bangalore|goa|airport to|to airport|airlines/i.test(q)) {
      if (/(cab|taxi|uber|ola) to airport/i.test(q)) return 'Mobility';
      return 'Travel';
    }

    // 2. Mobility
    if (/cab|taxi|ride|auto|bike|uber|ola|rapido|namma yatri|drop|pickup/i.test(q)) {
      return 'Mobility';
    }

    // 3. Food
    if (/pizza|burger|biryani|dosa|restaurant|zomato|swiggy|hungry|order food/i.test(q)) {
      return 'Food';
    }

    // 4. Pharmacy
    if (/medicine|tablet|syrup|paracetamol|dolo|crocin|fever|cough|1mg|pharmeasy/i.test(q)) {
      return 'Pharmacy';
    }

    // 5. Finance
    if (/loan|insurance|credit card|emi|term plan|policy|bank/i.test(q)) {
      return 'Finance';
    }

    // 6. Productivity
    if (/notion|figma|slack|canva|software|subscription|plan/i.test(q)) {
      return 'Productivity';
    }

    // 7. Grocery
    if (/milk|bread|eggs|vegetables|fruits|zepto|blinkit|instamart|bigbasket|grocery/i.test(q)) {
      return 'Grocery';
    }

    // 8. Shopping (Catch-all for typical e-commerce terms)
    if (/phone|iphone|laptop|shoes|shirt|headphones|watch|amazon|flipkart|meesho|myntra/i.test(q)) {
      return 'Shopping';
    }

    // Default: return null to let the current active category handle it
    return null;
  }
}
