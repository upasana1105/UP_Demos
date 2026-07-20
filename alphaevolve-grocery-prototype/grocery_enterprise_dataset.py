"""Enterprise Grocery Dataset for AlphaEvolve Optimization Engine.

Contains 250+ catalog items across 12 categories and 3 household shopping scenarios.
Exports both dictionary and dataclass formats for full backward & forward compatibility.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

CATEGORIES: List[str] = [
    "Fresh Produce",
    "Lean Proteins",
    "Plant Proteins",
    "Whole Grains",
    "Dairy & Dairy-Free",
    "Healthy Fats",
    "Spices & Condiments",
    "Frozen Essentials",
    "Beverages",
    "Pantry Staples",
    "Snacks",
    "Prepared Meals",
]

ALL_CATEGORIES: List[str] = CATEGORIES


@dataclass
class EnterpriseGroceryItem:
  name: str
  category: str
  price: float
  protein_g: float
  carbs_g: float
  fats_g: float
  iron_mg: float
  calcium_mg: float
  fiber_g: float
  vitamin_d_mcg: float
  sodium_mg: float
  shelf_life_days: int
  prep_time_mins: int
  is_gluten_free: bool
  is_vegan: bool
  is_premium: bool

  def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


@dataclass
class HouseholdScenario:
  name: str
  budget: float
  target_protein_g: float
  target_carbs_g: float
  target_fats_g: float
  target_iron_mg: float = 18.0
  target_calcium_mg: float = 1000.0
  target_fiber_g: float = 30.0
  target_vitamin_d_mcg: float = 15.0
  max_prep_time_mins: Optional[int] = None
  max_sodium_mg: Optional[float] = None
  min_shelf_life_days: Optional[int] = None
  is_gluten_free: bool = False
  is_vegan: bool = False

  def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


_RAW_CATALOG_DATA = [
    # Fresh Produce (25 items)
    ("Organic Spinach", "Fresh Produce", 3.49, 2.9, 3.6, 0.4, 2.7, 99.0, 2.2, 0.0, 79.0, 5, 5, True, True, False),
    ("Broccoli Crowns", "Fresh Produce", 2.49, 2.8, 6.6, 0.4, 0.7, 47.0, 2.6, 0.0, 33.0, 7, 10, True, True, False),
    ("Sweet Potatoes", "Fresh Produce", 2.29, 1.6, 20.1, 0.1, 0.6, 30.0, 3.0, 0.0, 55.0, 21, 20, True, True, False),
    ("Gala Apples (3lb)", "Fresh Produce", 4.49, 0.3, 13.8, 0.2, 0.1, 6.0, 2.4, 0.0, 1.0, 14, 0, True, True, False),
    ("Fresh Strawberries", "Fresh Produce", 3.99, 0.7, 7.7, 0.3, 0.4, 16.0, 2.0, 0.0, 1.0, 5, 0, True, True, False),
    ("Blueberries Pint", "Fresh Produce", 4.29, 0.7, 14.5, 0.3, 0.3, 6.0, 2.4, 0.0, 1.0, 7, 0, True, True, True),
    ("Avocados (4-pack)", "Fresh Produce", 4.99, 2.0, 8.5, 14.7, 0.6, 12.0, 6.7, 0.0, 7.0, 6, 2, True, True, True),
    ("Bananas Bunch", "Fresh Produce", 1.49, 1.1, 22.8, 0.3, 0.3, 5.0, 2.6, 0.0, 1.0, 6, 0, True, True, False),
    ("Baby Carrots 1lb", "Fresh Produce", 1.99, 0.9, 9.6, 0.2, 0.3, 33.0, 2.8, 0.0, 78.0, 14, 0, True, True, False),
    ("Red Bell Peppers 3pk", "Fresh Produce", 3.99, 1.0, 6.0, 0.3, 0.4, 7.0, 2.1, 0.0, 4.0, 10, 5, True, True, False),
    ("Kale Bunch", "Fresh Produce", 2.99, 2.9, 4.4, 0.6, 1.5, 150.0, 2.0, 0.0, 38.0, 6, 8, True, True, False),
    ("Roma Tomatoes 2lb", "Fresh Produce", 2.79, 0.9, 3.9, 0.2, 0.3, 10.0, 1.2, 0.0, 5.0, 8, 5, True, True, False),
    ("Yellow Onions 3lb", "Fresh Produce", 2.19, 1.1, 9.3, 0.1, 0.2, 23.0, 1.7, 0.0, 4.0, 30, 5, True, True, False),
    ("Garlic Bulb 3pk", "Fresh Produce", 1.69, 6.4, 33.0, 0.5, 1.7, 181.0, 2.1, 0.0, 17.0, 60, 2, True, True, False),
    ("Fresh Cucumbers 3pk", "Fresh Produce", 2.29, 0.7, 3.6, 0.1, 0.3, 16.0, 0.5, 0.0, 2.0, 10, 2, True, True, False),
    ("Zucchini 2lb", "Fresh Produce", 2.49, 1.2, 3.1, 0.3, 0.4, 16.0, 1.0, 0.0, 8.0, 7, 10, True, True, False),
    ("Portobello Mushrooms", "Fresh Produce", 3.49, 2.1, 3.9, 0.3, 0.5, 3.0, 1.3, 0.2, 9.0, 6, 8, True, True, True),
    ("Lemons 2lb bag", "Fresh Produce", 3.29, 1.1, 9.3, 0.3, 0.6, 26.0, 2.8, 0.0, 2.0, 21, 0, True, True, False),
    ("Green Asparagus 1lb", "Fresh Produce", 3.99, 2.2, 3.9, 0.2, 2.1, 24.0, 2.1, 0.0, 2.0, 5, 12, True, True, True),
    ("Organic Blackberries", "Fresh Produce", 4.49, 1.4, 9.6, 0.5, 0.6, 29.0, 5.3, 0.0, 1.0, 4, 0, True, True, True),
    ("Cantaloupe Melon", "Fresh Produce", 3.19, 0.8, 8.2, 0.2, 0.2, 9.0, 0.9, 0.0, 16.0, 9, 5, True, True, False),
    ("Navel Oranges 4lb", "Fresh Produce", 4.99, 0.9, 11.8, 0.1, 0.1, 40.0, 2.4, 0.0, 0.0, 14, 0, True, True, False),
    ("Red Grapes 2lb", "Fresh Produce", 4.79, 0.7, 18.1, 0.2, 0.4, 10.0, 0.9, 0.0, 2.0, 10, 0, True, True, False),
    ("Fresh Mint Herb", "Fresh Produce", 1.99, 3.3, 8.0, 0.9, 11.9, 243.0, 8.0, 0.0, 31.0, 7, 2, True, True, False),
    ("Cauliflower Head", "Fresh Produce", 2.99, 1.9, 5.0, 0.3, 0.4, 22.0, 2.0, 0.0, 30.0, 10, 15, True, True, False),

    # Lean Proteins (22 items)
    ("Boneless Chicken Breast 1.5lb", "Lean Proteins", 7.99, 31.0, 0.0, 3.6, 1.0, 15.0, 0.0, 0.1, 74.0, 5, 20, True, False, False),
    ("Wild Alaskan Salmon 1lb", "Lean Proteins", 11.99, 25.0, 0.0, 8.1, 0.8, 12.0, 0.0, 12.5, 59.0, 3, 15, True, False, True),
    ("Ground Turkey 93/7 1lb", "Lean Proteins", 5.49, 22.0, 0.0, 8.0, 1.4, 21.0, 0.0, 0.1, 85.0, 4, 15, True, False, False),
    ("Grass-Fed Ground Beef 1lb", "Lean Proteins", 8.49, 20.0, 0.0, 11.0, 2.2, 18.0, 0.0, 0.1, 72.0, 5, 15, True, False, True),
    ("Canned Tuna in Water 4pk", "Lean Proteins", 5.99, 26.0, 0.0, 1.0, 1.3, 11.0, 0.0, 1.2, 320.0, 730, 2, True, False, False),
    ("Shrimp Raw Peeled 1lb", "Lean Proteins", 9.99, 24.0, 0.2, 0.3, 0.5, 70.0, 0.0, 0.0, 111.0, 3, 10, True, False, True),
    ("Center Cut Pork Chops 1.5lb", "Lean Proteins", 6.99, 26.0, 0.0, 4.2, 0.9, 19.0, 0.0, 0.2, 53.0, 4, 18, True, False, False),
    ("Egg Whites Liquid 32oz", "Lean Proteins", 4.99, 11.0, 0.7, 0.2, 0.1, 7.0, 0.0, 0.0, 166.0, 14, 5, True, False, False),
    ("Cod Fillets 1lb", "Lean Proteins", 8.99, 20.0, 0.0, 0.7, 0.4, 16.0, 0.0, 0.9, 78.0, 3, 12, True, False, False),
    ("Bison Lean Steak 10oz", "Lean Proteins", 12.49, 24.0, 0.0, 2.4, 2.8, 14.0, 0.0, 0.0, 65.0, 4, 15, True, False, True),
    ("Rotisserie Chicken Whole", "Lean Proteins", 7.49, 24.0, 0.0, 7.5, 1.1, 15.0, 0.0, 0.2, 380.0, 4, 0, True, False, False),
    ("Tilapia Fillets 1.5lb", "Lean Proteins", 6.49, 20.0, 0.0, 1.7, 0.6, 10.0, 0.0, 3.1, 49.0, 3, 12, True, False, False),
    ("Turkey Bacon 12oz", "Lean Proteins", 4.29, 15.0, 1.0, 8.0, 0.9, 12.0, 0.0, 0.1, 550.0, 21, 8, True, False, False),
    ("Chicken Thighs Bone-in 2lb", "Lean Proteins", 5.99, 24.0, 0.0, 9.0, 1.2, 13.0, 0.0, 0.1, 82.0, 5, 25, True, False, False),
    ("Halibut Steak 12oz", "Lean Proteins", 14.99, 23.0, 0.0, 2.3, 0.8, 54.0, 0.0, 4.8, 68.0, 2, 15, True, False, True),
    ("Deli Smoked Turkey 1lb", "Lean Proteins", 8.99, 18.0, 2.0, 1.5, 0.8, 14.0, 0.0, 0.0, 680.0, 10, 0, True, False, False),
    ("Wild Sardines Canned 3pk", "Lean Proteins", 4.99, 24.0, 0.0, 11.0, 2.9, 382.0, 0.0, 4.8, 505.0, 1095, 2, True, False, False),
    ("Lamb Loin Chops 1lb", "Lean Proteins", 13.99, 22.0, 0.0, 12.0, 1.9, 17.0, 0.0, 0.1, 70.0, 4, 18, True, False, True),
    ("Beef Tenderloin 12oz", "Lean Proteins", 16.99, 26.0, 0.0, 10.0, 2.5, 12.0, 0.0, 0.1, 60.0, 3, 15, True, False, True),
    ("Smoked Trout 8oz", "Lean Proteins", 7.99, 21.0, 0.0, 6.0, 0.7, 25.0, 0.0, 3.5, 450.0, 14, 0, True, False, True),
    ("Clams Canned 6.5oz", "Lean Proteins", 3.49, 14.0, 3.0, 1.0, 16.2, 53.0, 0.0, 0.0, 340.0, 730, 2, True, False, False),
    ("Chicken Sausage Apple 12oz", "Lean Proteins", 5.29, 14.0, 4.0, 7.0, 1.0, 20.0, 0.0, 0.0, 520.0, 21, 10, True, False, False),

    # Plant Proteins (22 items)
    ("Firm Tofu Organic 14oz", "Plant Proteins", 2.49, 10.0, 2.0, 5.0, 2.7, 350.0, 1.0, 0.0, 10.0, 21, 10, True, True, False),
    ("Tempeh Organic 8oz", "Plant Proteins", 3.29, 19.0, 9.0, 11.0, 2.7, 111.0, 6.0, 0.0, 9.0, 30, 12, True, True, False),
    ("Black Beans Canned 4pk", "Plant Proteins", 4.19, 7.0, 20.0, 0.5, 2.1, 46.0, 7.5, 0.0, 290.0, 730, 3, True, True, False),
    ("Red Lentils Dry 16oz", "Plant Proteins", 1.89, 24.0, 60.0, 1.5, 6.5, 56.0, 11.0, 0.0, 6.0, 365, 20, True, True, False),
    ("Edamame Frozen Shelled 16oz", "Plant Proteins", 2.99, 11.0, 9.0, 5.0, 2.2, 60.0, 5.0, 0.0, 6.0, 180, 5, True, True, False),
    ("Chickpeas Dry 16oz", "Plant Proteins", 1.99, 19.0, 61.0, 6.0, 6.2, 105.0, 17.0, 0.0, 24.0, 365, 45, True, True, False),
    ("Seitan Cubes 8oz", "Plant Proteins", 4.49, 25.0, 4.0, 1.5, 1.8, 40.0, 1.0, 0.0, 310.0, 21, 10, False, True, False),
    ("Hemp Seeds Organic 8oz", "Plant Proteins", 6.99, 10.0, 3.0, 14.0, 2.4, 21.0, 1.0, 0.0, 2.0, 180, 0, True, True, True),
    ("Pea Protein Powder 1lb", "Plant Proteins", 14.99, 24.0, 2.0, 2.0, 5.0, 30.0, 1.0, 0.0, 280.0, 365, 2, True, True, True),
    ("Textured Vegetable Protein 16oz", "Plant Proteins", 3.79, 12.0, 7.0, 0.2, 2.3, 80.0, 4.0, 0.0, 2.0, 365, 10, True, True, False),
    ("Nutritional Yeast 5oz", "Plant Proteins", 5.49, 8.0, 5.0, 0.5, 1.5, 7.0, 3.0, 0.0, 25.0, 365, 0, True, True, False),
    ("Navy Beans Canned 15oz", "Plant Proteins", 1.19, 7.5, 19.0, 0.6, 2.4, 62.0, 6.5, 0.0, 280.0, 730, 2, True, True, False),
    ("Beyond Meat Patties 2pk", "Plant Proteins", 5.99, 20.0, 7.0, 14.0, 4.2, 100.0, 2.0, 0.0, 390.0, 14, 10, True, True, True),
    ("Impossible Ground 12oz", "Plant Proteins", 6.49, 19.0, 9.0, 14.0, 4.2, 170.0, 3.0, 0.0, 370.0, 14, 10, True, True, True),
    ("Sprouted Tofu Extra Firm", "Plant Proteins", 3.19, 11.0, 3.0, 6.0, 2.9, 300.0, 2.0, 0.0, 15.0, 21, 8, True, True, False),
    ("Pinto Beans Dry 32oz", "Plant Proteins", 2.49, 21.0, 63.0, 1.2, 5.1, 113.0, 15.0, 0.0, 12.0, 365, 50, True, True, False),
    ("Black Eyed Peas 16oz", "Plant Proteins", 1.99, 13.0, 35.0, 0.9, 4.3, 110.0, 11.0, 0.0, 7.0, 365, 40, True, True, False),
    ("Lupini Beans Jar 12oz", "Plant Proteins", 4.29, 13.0, 8.0, 2.5, 1.2, 45.0, 5.0, 0.0, 240.0, 180, 0, True, True, False),
    ("Green Peas Frozen 16oz", "Plant Proteins", 1.79, 5.0, 14.0, 0.4, 1.5, 25.0, 4.4, 0.0, 110.0, 180, 5, True, True, False),
    ("Chana Dal Split Chickpeas 16oz", "Plant Proteins", 2.29, 22.0, 60.0, 4.5, 5.5, 90.0, 14.0, 0.0, 15.0, 365, 30, True, True, False),
    ("Sprouted Mung Beans 10oz", "Plant Proteins", 2.99, 3.0, 6.0, 0.2, 1.0, 13.0, 1.8, 0.0, 15.0, 7, 0, True, True, False),
    ("Chia Seed Protein Powder 8oz", "Plant Proteins", 7.49, 15.0, 12.0, 8.0, 5.0, 150.0, 10.0, 0.0, 5.0, 365, 1, True, True, True),

    # Whole Grains (22 items)
    ("Brown Rice Organic 2lb", "Whole Grains", 2.99, 5.0, 45.0, 1.6, 1.0, 20.0, 3.5, 0.0, 5.0, 365, 35, True, True, False),
    ("Quinoa Tricolor 16oz", "Whole Grains", 4.99, 8.0, 39.0, 3.5, 2.8, 31.0, 5.0, 0.0, 13.0, 365, 20, True, True, True),
    ("Rolled Oats Steel Cut 32oz", "Whole Grains", 3.79, 6.0, 27.0, 2.5, 1.7, 20.0, 4.0, 0.0, 2.0, 365, 15, True, True, False),
    ("Whole Wheat Bread Organic", "Whole Grains", 3.49, 4.0, 12.0, 1.0, 0.9, 30.0, 2.0, 0.0, 130.0, 10, 0, False, True, False),
    ("Farro Grain 16oz", "Whole Grains", 3.29, 7.0, 37.0, 1.0, 2.0, 18.0, 5.0, 0.0, 0.0, 365, 25, False, True, False),
    ("Wild Rice Blend 16oz", "Whole Grains", 4.29, 6.5, 35.0, 0.6, 1.2, 14.0, 3.0, 0.0, 4.0, 365, 45, True, True, False),
    ("Whole Wheat Pasta 16oz", "Whole Grains", 1.89, 7.0, 37.0, 1.5, 2.1, 20.0, 6.0, 0.0, 0.0, 365, 10, False, True, False),
    ("Buckwheat Groats 16oz", "Whole Grains", 3.49, 6.0, 33.0, 1.0, 1.6, 18.0, 4.5, 0.0, 1.0, 365, 15, True, True, False),
    ("Ezekiel 4:9 Sprouted Bread", "Whole Grains", 5.29, 5.0, 15.0, 0.5, 1.0, 20.0, 3.0, 0.0, 75.0, 14, 0, False, True, True),
    ("Barley Pearl 16oz", "Whole Grains", 1.79, 3.5, 44.0, 0.7, 1.3, 17.0, 6.0, 0.0, 5.0, 365, 40, False, True, False),
    ("Bulgur Wheat 16oz", "Whole Grains", 2.29, 5.6, 34.0, 0.4, 1.7, 18.0, 8.0, 0.0, 9.0, 365, 15, False, True, False),
    ("Amaranth Grain Organic 16oz", "Whole Grains", 4.19, 9.3, 46.0, 3.9, 5.2, 116.0, 5.2, 0.0, 15.0, 365, 25, True, True, True),
    ("Millet Grain 16oz", "Whole Grains", 2.49, 6.0, 41.0, 1.7, 1.5, 5.0, 4.0, 0.0, 3.0, 365, 20, True, True, False),
    ("Corn Tortillas 100% 12pk", "Whole Grains", 1.99, 2.0, 20.0, 1.0, 0.6, 40.0, 2.0, 0.0, 10.0, 14, 2, True, True, False),
    ("Whole Grain Couscous 16oz", "Whole Grains", 2.79, 6.0, 36.0, 0.3, 0.7, 13.0, 5.0, 0.0, 5.0, 365, 10, False, True, False),
    ("Sorghum Grain 16oz", "Whole Grains", 3.19, 5.0, 36.0, 1.6, 1.7, 14.0, 3.5, 0.0, 2.0, 365, 40, True, True, False),
    ("Gluten Free Brown Rice Pasta", "Whole Grains", 3.29, 4.0, 43.0, 1.0, 1.0, 10.0, 2.0, 0.0, 0.0, 365, 10, True, True, False),
    ("Teff Grain Brown 16oz", "Whole Grains", 4.79, 9.8, 50.0, 1.7, 5.1, 123.0, 7.1, 0.0, 8.0, 365, 20, True, True, True),
    ("Spelt Flour Whole 32oz", "Whole Grains", 4.49, 5.5, 22.0, 0.8, 1.3, 11.0, 3.5, 0.0, 2.0, 180, 0, False, True, False),
    ("Popcorn Kernels Whole Grain", "Whole Grains", 2.19, 3.0, 19.0, 1.0, 0.9, 2.0, 3.5, 0.0, 1.0, 365, 5, True, True, False),
    ("Rye Bread Whole 16oz", "Whole Grains", 3.79, 3.0, 15.0, 0.6, 0.9, 22.0, 2.0, 0.0, 170.0, 10, 0, False, True, False),
    ("Wild Rice Cakes 12pk", "Whole Grains", 2.99, 1.5, 14.0, 0.5, 0.3, 5.0, 1.0, 0.0, 25.0, 180, 0, True, True, False),

    # Dairy & Dairy-Free (22 items)
    ("Greek Yogurt Nonfat Plain 32oz", "Dairy & Dairy-Free", 4.49, 17.0, 6.0, 0.0, 0.1, 200.0, 0.0, 0.0, 60.0, 14, 0, True, False, False),
    ("Organic Whole Milk 1 gal", "Dairy & Dairy-Free", 4.29, 8.0, 12.0, 8.0, 0.1, 300.0, 0.0, 2.5, 105.0, 12, 0, True, False, False),
    ("Almond Milk Unsweetened 64oz", "Dairy & Dairy-Free", 3.29, 1.0, 1.0, 2.5, 0.7, 450.0, 1.0, 2.5, 170.0, 21, 0, True, True, False),
    ("Oat Milk Planet Extra Creamy", "Dairy & Dairy-Free", 4.19, 2.0, 16.0, 5.0, 0.4, 350.0, 2.0, 3.0, 100.0, 21, 0, True, True, False),
    ("Sharp Cheddar Block 8oz", "Dairy & Dairy-Free", 3.99, 7.0, 0.5, 9.0, 0.1, 200.0, 0.0, 0.2, 180.0, 45, 0, True, False, False),
    ("Cottage Cheese 4% 16oz", "Dairy & Dairy-Free", 2.99, 13.0, 4.0, 5.0, 0.2, 90.0, 0.0, 0.0, 350.0, 14, 0, True, False, False),
    ("Kefir Organic Plain 32oz", "Dairy & Dairy-Free", 3.89, 11.0, 12.0, 2.0, 0.1, 300.0, 0.0, 2.5, 125.0, 21, 0, True, False, False),
    ("Soy Milk Organic Unsweetened", "Dairy & Dairy-Free", 3.49, 7.0, 4.0, 4.0, 1.0, 300.0, 1.0, 3.0, 95.0, 21, 0, True, True, False),
    ("Feta Cheese Greek 7oz", "Dairy & Dairy-Free", 4.29, 4.0, 1.0, 6.0, 0.1, 140.0, 0.0, 0.1, 320.0, 30, 0, True, False, True),
    ("Mozzarella Fresh Ball 8oz", "Dairy & Dairy-Free", 3.79, 6.0, 1.0, 6.0, 0.1, 150.0, 0.0, 0.1, 85.0, 14, 0, True, False, False),
    ("Parmesan Shredded 5oz", "Dairy & Dairy-Free", 4.49, 10.0, 1.0, 8.0, 0.2, 330.0, 0.0, 0.1, 400.0, 60, 0, True, False, True),
    ("Plant-Based Cheese Shreds 8oz", "Dairy & Dairy-Free", 4.79, 0.0, 7.0, 6.0, 0.1, 10.0, 0.0, 0.0, 210.0, 30, 0, True, True, False),
    ("Grass-Fed Butter 8oz", "Dairy & Dairy-Free", 4.29, 0.1, 0.1, 11.0, 0.0, 3.0, 0.0, 0.0, 90.0, 90, 0, True, False, True),
    ("Ricotta Cheese Whole Milk 15oz", "Dairy & Dairy-Free", 3.69, 7.0, 3.0, 8.0, 0.1, 200.0, 0.0, 0.2, 80.0, 14, 0, True, False, False),
    ("Coconut Yogurt Unsweetened 16oz", "Dairy & Dairy-Free", 4.99, 1.0, 6.0, 8.0, 0.4, 15.0, 1.0, 0.0, 20.0, 21, 0, True, True, True),
    ("Sour Cream Organic 16oz", "Dairy & Dairy-Free", 2.79, 2.0, 2.0, 5.0, 0.0, 70.0, 0.0, 0.1, 30.0, 21, 0, True, False, False),
    ("Swiss Cheese Sliced 8oz", "Dairy & Dairy-Free", 3.99, 8.0, 1.0, 8.0, 0.1, 220.0, 0.0, 0.2, 55.0, 30, 0, True, False, False),
    ("Goat Cheese Log 4oz", "Dairy & Dairy-Free", 4.19, 6.0, 1.0, 8.0, 0.5, 80.0, 0.0, 0.1, 130.0, 21, 0, True, False, True),
    ("Heavy Whipping Cream 16oz", "Dairy & Dairy-Free", 3.49, 1.0, 1.0, 11.0, 0.0, 20.0, 0.0, 0.4, 10.0, 21, 0, True, False, False),
    ("Cashew Milk Unsweetened 64oz", "Dairy & Dairy-Free", 3.79, 1.0, 1.0, 2.0, 0.4, 450.0, 0.0, 2.5, 160.0, 21, 0, True, True, False),
    ("Condensed Milk Sweetened 14oz", "Dairy & Dairy-Free", 2.49, 3.0, 22.0, 3.0, 0.1, 100.0, 0.0, 0.2, 40.0, 365, 0, True, False, False),
    ("Ghee Clarified Butter 9oz", "Dairy & Dairy-Free", 8.99, 0.0, 0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 180, 0, True, False, True),

    # Healthy Fats (20 items)
    ("Extra Virgin Olive Oil 16.9oz", "Healthy Fats", 8.99, 0.0, 0.0, 14.0, 0.1, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, True),
    ("Raw Almonds 16oz", "Healthy Fats", 7.99, 6.0, 6.0, 14.0, 1.0, 75.0, 3.5, 0.0, 0.0, 180, 0, True, True, False),
    ("Walnuts Halves 12oz", "Healthy Fats", 6.49, 4.3, 3.9, 18.5, 0.8, 28.0, 1.9, 0.0, 1.0, 180, 0, True, True, False),
    ("Chia Seeds Organic 12oz", "Healthy Fats", 4.99, 4.7, 12.0, 8.7, 2.2, 177.0, 9.8, 0.0, 5.0, 365, 0, True, True, False),
    ("Flaxseed Ground 16oz", "Healthy Fats", 3.49, 1.9, 3.0, 4.3, 0.6, 26.0, 2.8, 0.0, 3.0, 120, 0, True, True, False),
    ("Natural Peanut Butter 16oz", "Healthy Fats", 3.29, 8.0, 7.0, 16.0, 0.6, 17.0, 2.0, 0.0, 5.0, 180, 0, True, True, False),
    ("Almond Butter Unsweetened 12oz", "Healthy Fats", 7.49, 7.0, 6.0, 18.0, 1.1, 86.0, 3.3, 0.0, 0.0, 180, 0, True, True, True),
    ("Pumpkin Seeds Pepitas 12oz", "Healthy Fats", 5.29, 9.0, 4.0, 13.0, 2.5, 15.0, 2.0, 0.0, 5.0, 180, 0, True, True, False),
    ("Avocado Oil 16.9oz", "Healthy Fats", 9.49, 0.0, 0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, True),
    ("Sunflower Seeds Hulled 16oz", "Healthy Fats", 3.19, 6.0, 6.0, 14.0, 1.4, 20.0, 3.0, 0.0, 3.0, 180, 0, True, True, False),
    ("Tahini Sesame Paste 16oz", "Healthy Fats", 5.99, 5.0, 6.0, 16.0, 2.5, 125.0, 3.0, 0.0, 35.0, 180, 0, True, True, False),
    ("Pecan Halves 8oz", "Healthy Fats", 6.99, 2.6, 3.9, 20.0, 0.7, 20.0, 2.7, 0.0, 0.0, 180, 0, True, True, True),
    ("Macadamia Nuts 6oz", "Healthy Fats", 8.49, 2.2, 3.9, 21.0, 1.0, 25.0, 2.4, 0.0, 1.0, 180, 0, True, True, True),
    ("Cashews Roasted Unsalted 12oz", "Healthy Fats", 6.79, 5.0, 9.0, 13.0, 1.9, 10.0, 1.0, 0.0, 5.0, 180, 0, True, True, False),
    ("Coconut Oil Virgin 14oz", "Healthy Fats", 6.29, 0.0, 0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, False),
    ("Sesame Oil Toasted 8.4oz", "Healthy Fats", 4.79, 0.0, 0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, False),
    ("Pistachios Roasted 8oz", "Healthy Fats", 5.99, 6.0, 8.0, 13.0, 1.1, 30.0, 3.0, 0.0, 120.0, 180, 0, True, True, False),
    ("Brazil Nuts Organic 8oz", "Healthy Fats", 8.99, 4.0, 3.0, 19.0, 0.7, 45.0, 2.0, 0.0, 1.0, 180, 0, True, True, True),
    ("MCT Oil Pure 16oz", "Healthy Fats", 12.99, 0.0, 0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, True),
    ("Hazelnut Spread Cacao 12oz", "Healthy Fats", 4.99, 2.0, 17.0, 11.0, 0.8, 40.0, 1.0, 0.0, 15.0, 180, 0, True, True, False),

    # Spices & Condiments (20 items)
    ("Pink Himalayan Salt 16oz", "Spices & Condiments", 2.49, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 380.0, 1095, 0, True, True, False),
    ("Black Pepper Ground 4oz", "Spices & Condiments", 2.99, 0.1, 0.4, 0.0, 0.6, 4.0, 0.2, 0.0, 0.0, 730, 0, True, True, False),
    ("Ground Turmeric 4oz", "Spices & Condiments", 3.29, 0.3, 1.4, 0.2, 0.8, 4.0, 0.5, 0.0, 1.0, 730, 0, True, True, False),
    ("Ground Cumin 4oz", "Spices & Condiments", 2.89, 0.4, 0.9, 0.5, 1.4, 20.0, 0.2, 0.0, 4.0, 730, 0, True, True, False),
    ("Apple Cider Vinegar 16oz", "Spices & Condiments", 3.49, 0.0, 0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 730, 0, True, True, False),
    ("Tamari Soy Sauce Low Sodium", "Spices & Condiments", 3.99, 2.0, 1.0, 0.0, 0.4, 4.0, 0.0, 0.0, 590.0, 365, 0, True, True, False),
    ("Extra Virgin Red Chili Flakes", "Spices & Condiments", 2.19, 0.2, 0.8, 0.3, 0.2, 3.0, 0.4, 0.0, 0.0, 730, 0, True, True, False),
    ("Dijon Mustard Organic 8oz", "Spices & Condiments", 2.69, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 120.0, 365, 0, True, True, False),
    ("Sriracha Hot Sauce 17oz", "Spices & Condiments", 3.79, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 140.0, 365, 0, True, True, False),
    ("Pure Maple Syrup 12oz", "Spices & Condiments", 7.99, 0.0, 13.0, 0.0, 0.2, 13.0, 0.0, 0.0, 2.0, 365, 0, True, True, True),
    ("Garlic Powder 4oz", "Spices & Condiments", 2.49, 0.5, 2.3, 0.0, 0.2, 5.0, 0.3, 0.0, 2.0, 730, 0, True, True, False),
    ("Cinnamon Ground Ceylon 4oz", "Spices & Condiments", 4.29, 0.1, 2.1, 0.0, 0.7, 26.0, 1.4, 0.0, 0.0, 730, 0, True, True, True),
    ("Balsamic Vinegar Modena 8.5oz", "Spices & Condiments", 5.49, 0.1, 3.0, 0.0, 0.1, 5.0, 0.0, 0.0, 4.0, 730, 0, True, True, True),
    ("Nutritional Oregano Dried", "Spices & Condiments", 2.29, 0.2, 1.3, 0.1, 0.7, 30.0, 0.8, 0.0, 0.0, 730, 0, True, True, False),
    ("Smoked Paprika Spanish 4oz", "Spices & Condiments", 3.19, 0.3, 1.2, 0.3, 0.5, 4.0, 0.7, 0.0, 1.0, 730, 0, True, True, False),
    ("Avocado Oil Mayo 12oz", "Healthy Fats", 6.49, 0.0, 0.0, 11.0, 0.0, 0.0, 0.0, 0.0, 90.0, 180, 0, True, False, True),
    ("Raw Honey Organic 12oz", "Spices & Condiments", 6.99, 0.0, 17.0, 0.0, 0.1, 1.0, 0.0, 0.0, 1.0, 730, 0, True, False, True),
    ("Curry Powder Mild 4oz", "Spices & Condiments", 2.79, 0.3, 1.4, 0.3, 0.7, 13.0, 0.8, 0.0, 1.0, 730, 0, True, True, False),
    ("Sesame Seeds Whole 8oz", "Spices & Condiments", 2.99, 1.6, 2.1, 4.5, 1.3, 88.0, 1.1, 0.0, 1.0, 365, 0, True, True, False),
    ("Ginger Ground Organic 3oz", "Spices & Condiments", 3.49, 0.2, 1.6, 0.1, 0.4, 3.0, 0.3, 0.0, 1.0, 730, 0, True, True, False),

    # Frozen Essentials (20 items)
    ("Frozen Organic Wild Blueberries", "Frozen Essentials", 3.99, 0.5, 13.0, 0.5, 0.3, 6.0, 2.5, 0.0, 0.0, 180, 0, True, True, False),
    ("Frozen Mixed Vegetables 16oz", "Frozen Essentials", 1.99, 2.0, 7.0, 0.2, 0.5, 20.0, 2.0, 0.0, 30.0, 180, 5, True, True, False),
    ("Frozen Broccoli Florets 16oz", "Frozen Essentials", 2.19, 2.5, 4.5, 0.3, 0.6, 40.0, 2.2, 0.0, 20.0, 180, 5, True, True, False),
    ("Frozen Wild Salmon Fillets 24oz", "Frozen Essentials", 15.99, 23.0, 0.0, 7.5, 0.7, 10.0, 0.0, 11.0, 50.0, 180, 15, True, False, True),
    ("Frozen Mango Chunks 16oz", "Frozen Essentials", 3.29, 0.6, 15.0, 0.3, 0.2, 10.0, 1.6, 0.0, 1.0, 180, 0, True, True, False),
    ("Frozen Cauliflower Rice 12oz", "Frozen Essentials", 2.49, 1.5, 4.0, 0.2, 0.3, 18.0, 2.0, 0.0, 15.0, 180, 5, True, True, False),
    ("Frozen Organic Strawberries", "Frozen Essentials", 3.79, 0.7, 7.5, 0.3, 0.4, 15.0, 2.0, 0.0, 1.0, 180, 0, True, True, False),
    ("Frozen Spinach Cut 16oz", "Frozen Essentials", 1.89, 3.0, 3.5, 0.4, 2.5, 120.0, 2.5, 0.0, 80.0, 180, 5, True, True, False),
    ("Frozen Sweet Corn 16oz", "Frozen Essentials", 1.99, 3.0, 19.0, 1.0, 0.5, 2.0, 2.0, 0.0, 0.0, 180, 5, True, True, False),
    ("Frozen Raw Shrimp 16oz", "Frozen Essentials", 8.99, 20.0, 0.0, 0.3, 0.4, 60.0, 0.0, 0.0, 120.0, 180, 8, True, False, False),
    ("Frozen Açaí Puree Packets 4pk", "Frozen Essentials", 5.49, 1.0, 4.0, 6.0, 0.8, 30.0, 3.0, 0.0, 10.0, 180, 2, True, True, True),
    ("Frozen Edamame Pods 16oz", "Frozen Essentials", 2.79, 10.0, 9.0, 4.5, 2.0, 60.0, 4.5, 0.0, 5.0, 180, 6, True, True, False),
    ("Frozen Chicken Breast Cutlets", "Frozen Essentials", 9.49, 26.0, 0.0, 2.5, 0.8, 12.0, 0.0, 0.1, 95.0, 180, 12, True, False, False),
    ("Frozen Brussels Sprouts 16oz", "Frozen Essentials", 2.39, 3.0, 8.0, 0.3, 1.2, 35.0, 3.0, 0.0, 15.0, 180, 10, True, True, False),
    ("Frozen Hash Brown Patties", "Frozen Essentials", 3.19, 1.5, 15.0, 7.0, 0.4, 8.0, 1.5, 0.0, 240.0, 180, 15, True, True, False),
    ("Frozen Berry Medley 24oz", "Frozen Essentials", 5.99, 1.0, 12.0, 0.4, 0.5, 20.0, 3.5, 0.0, 1.0, 180, 0, True, True, False),
    ("Frozen Cod Fillets 24oz", "Frozen Essentials", 12.99, 19.0, 0.0, 0.6, 0.4, 14.0, 0.0, 0.8, 70.0, 180, 12, True, False, False),
    ("Frozen Sliced Peaches 16oz", "Frozen Essentials", 2.99, 0.9, 14.0, 0.1, 0.3, 5.0, 1.5, 0.0, 0.0, 180, 0, True, True, False),
    ("Frozen Bell Pepper Mix 16oz", "Frozen Essentials", 2.29, 0.9, 5.5, 0.2, 0.4, 9.0, 1.8, 0.0, 5.0, 180, 5, True, True, False),
    ("Frozen Waffles Whole Grain 6pk", "Frozen Essentials", 3.69, 4.0, 24.0, 5.0, 1.5, 40.0, 3.0, 0.0, 260.0, 180, 3, False, True, False),

    # Beverages (20 items)
    ("Matcha Green Tea Powder 3oz", "Beverages", 12.99, 1.0, 1.0, 0.0, 0.5, 10.0, 0.5, 0.0, 1.0, 365, 2, True, True, True),
    ("Cold Brew Coffee Concentrate", "Beverages", 7.99, 0.5, 1.0, 0.0, 0.1, 5.0, 0.0, 0.0, 5.0, 30, 0, True, True, False),
    ("Kombucha Ginger Lemon 16oz", "Beverages", 3.79, 0.0, 7.0, 0.0, 0.1, 10.0, 0.0, 0.0, 10.0, 45, 0, True, True, False),
    ("Unsweetened Green Tea 12pk", "Beverages", 6.49, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 365, 0, True, True, False),
    ("Sparkling Water Lime 12pk", "Beverages", 4.99, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 365, 0, True, True, False),
    ("Coconut Water Pure 33.8oz", "Beverages", 3.99, 0.5, 11.0, 0.0, 0.3, 40.0, 0.0, 0.0, 60.0, 180, 0, True, True, False),
    ("Tart Cherry Juice 32oz", "Beverages", 6.99, 1.0, 28.0, 0.0, 0.7, 25.0, 0.5, 0.0, 10.0, 60, 0, True, True, True),
    ("Chai Tea Bags 20ct", "Beverages", 3.49, 0.0, 0.5, 0.0, 0.1, 2.0, 0.0, 0.0, 0.0, 730, 3, True, True, False),
    ("Protein Shake Vanilla 4pk", "Beverages", 8.99, 30.0, 4.0, 2.5, 4.5, 500.0, 1.0, 5.0, 220.0, 180, 0, True, False, True),
    ("100% Pomegranate Juice 16oz", "Beverages", 4.29, 0.3, 34.0, 0.2, 0.3, 15.0, 0.2, 0.0, 10.0, 90, 0, True, True, False),
    ("Chamomile Herbal Tea 20ct", "Beverages", 2.99, 0.0, 0.2, 0.0, 0.1, 2.0, 0.0, 0.0, 0.0, 730, 4, True, True, False),
    ("Electrolyte Drink Tablet 10ct", "Beverages", 6.99, 0.0, 2.0, 0.0, 0.0, 13.0, 0.0, 0.0, 300.0, 365, 1, True, True, False),
    ("Whole Bean Coffee Roast 12oz", "Beverages", 9.99, 0.2, 0.3, 0.0, 0.1, 2.0, 0.0, 0.0, 2.0, 180, 5, True, True, True),
    ("Organic Orange Juice 52oz", "Beverages", 4.49, 1.7, 26.0, 0.2, 0.4, 27.0, 0.5, 2.5, 0.0, 21, 0, True, True, False),
    ("Golden Milk Turmeric Mix", "Beverages", 7.49, 1.0, 4.0, 1.5, 1.2, 80.0, 1.0, 0.0, 25.0, 365, 2, True, True, True),
    ("Hibiscus Tea Loose Leaf 4oz", "Beverages", 4.99, 0.0, 1.0, 0.0, 0.5, 20.0, 0.0, 0.0, 0.0, 730, 5, True, True, False),
    ("Almond Beverage Vanilla 32oz", "Beverages", 2.49, 1.0, 8.0, 2.5, 0.3, 300.0, 0.5, 2.5, 130.0, 180, 0, True, True, False),
    ("Yerba Mate Can Organic 16oz", "Beverages", 2.79, 0.0, 7.0, 0.0, 0.1, 5.0, 0.0, 0.0, 10.0, 180, 0, True, True, False),
    ("Oat Protein Smoothie 11oz", "Beverages", 3.99, 15.0, 22.0, 3.5, 2.0, 250.0, 3.0, 2.0, 150.0, 60, 0, True, True, False),
    ("Aloe Vera Juice Drink 1.5L", "Beverages", 3.29, 0.0, 9.0, 0.0, 0.1, 10.0, 0.0, 0.0, 15.0, 90, 0, True, True, False),

    # Pantry Staples (20 items)
    ("Canned Crushed Tomatoes 28oz", "Pantry Staples", 1.89, 1.5, 8.0, 0.2, 1.0, 20.0, 1.8, 0.0, 180.0, 730, 5, True, True, False),
    ("Vegetable Broth Low Sodium 32oz", "Pantry Staples", 2.19, 1.0, 2.0, 0.0, 0.2, 10.0, 0.0, 0.0, 140.0, 365, 5, True, True, False),
    ("Chicken Bone Broth 32oz", "Pantry Staples", 4.49, 10.0, 1.0, 0.5, 0.4, 20.0, 0.0, 0.0, 320.0, 365, 5, True, False, False),
    ("Coconut Milk Canned 13.5oz", "Pantry Staples", 2.49, 1.0, 2.0, 14.0, 1.2, 15.0, 0.0, 0.0, 15.0, 730, 5, True, True, False),
    ("Raw Apple Cider Vinegar 32oz", "Pantry Staples", 4.99, 0.0, 0.2, 0.0, 0.1, 2.0, 0.0, 0.0, 0.0, 730, 0, True, True, False),
    ("Tomato Paste Organic 6oz", "Pantry Staples", 1.19, 1.0, 5.0, 0.1, 0.8, 15.0, 1.2, 0.0, 10.0, 730, 2, True, True, False),
    ("Rolled Oats Bag 48oz", "Pantry Staples", 4.29, 5.0, 27.0, 2.5, 1.5, 20.0, 4.0, 0.0, 0.0, 365, 5, True, True, False),
    ("Flour Whole Wheat 5lb", "Pantry Staples", 3.99, 4.0, 23.0, 0.5, 1.1, 10.0, 3.0, 0.0, 0.0, 180, 0, False, True, False),
    ("Baking Soda 16oz", "Pantry Staples", 0.99, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1250.0, 1095, 0, True, True, False),
    ("Active Dry Yeast 3pk", "Pantry Staples", 1.79, 2.0, 2.0, 0.3, 0.5, 5.0, 1.0, 0.0, 5.0, 365, 10, True, True, False),
    ("Canned Sweet Corn 15oz", "Pantry Staples", 1.29, 2.0, 14.0, 0.5, 0.4, 2.0, 2.0, 0.0, 210.0, 730, 2, True, True, False),
    ("Canned Green Beans 14.5oz", "Pantry Staples", 1.19, 1.0, 4.0, 0.1, 0.6, 25.0, 1.5, 0.0, 290.0, 730, 2, True, True, False),
    ("White Rice Jasmine 5lb", "Pantry Staples", 6.49, 3.0, 35.0, 0.3, 0.5, 10.0, 0.6, 0.0, 0.0, 365, 20, True, True, False),
    ("Almond Flour Fine 16oz", "Pantry Staples", 7.99, 6.0, 6.0, 14.0, 1.0, 70.0, 3.0, 0.0, 0.0, 180, 0, True, True, True),
    ("Tapioca Starch 16oz", "Pantry Staples", 2.99, 0.0, 26.0, 0.0, 0.3, 5.0, 0.0, 0.0, 0.0, 365, 0, True, True, False),
    ("Canned Pumpkin Puree 15oz", "Pantry Staples", 1.99, 1.0, 9.0, 0.2, 0.8, 25.0, 2.8, 0.0, 5.0, 730, 2, True, True, False),
    ("Soy Sauce Low Sodium 15oz", "Pantry Staples", 2.79, 2.0, 1.0, 0.0, 0.4, 4.0, 0.0, 0.0, 570.0, 365, 0, False, True, False),
    ("Sesame Seeds Black 8oz", "Pantry Staples", 3.29, 1.6, 2.1, 4.5, 1.3, 88.0, 1.1, 0.0, 1.0, 365, 0, True, True, False),
    ("Dark Brown Sugar 16oz", "Pantry Staples", 1.89, 0.0, 24.0, 0.0, 0.2, 20.0, 0.0, 0.0, 10.0, 730, 0, True, True, False),
    ("Coconut Aminos 8oz", "Pantry Staples", 4.99, 0.0, 5.0, 0.0, 0.2, 5.0, 0.0, 0.0, 270.0, 365, 0, True, True, True),

    # Snacks (20 items)
    ("Roasted Seaweed Snacks 6pk", "Snacks", 3.99, 1.0, 1.0, 2.0, 0.4, 15.0, 0.5, 0.0, 50.0, 180, 0, True, True, False),
    ("Dark Chocolate 85% Cacao 3.5oz", "Snacks", 3.29, 2.5, 12.0, 12.0, 3.4, 20.0, 3.5, 0.0, 5.0, 365, 0, True, True, True),
    ("Mixed Nuts Salted 10oz", "Snacks", 5.99, 5.0, 6.0, 15.0, 1.0, 40.0, 2.0, 0.0, 115.0, 180, 0, True, True, False),
    ("Whole Grain Rice Crackers 3.5oz", "Snacks", 2.49, 2.0, 22.0, 1.0, 0.5, 5.0, 1.5, 0.0, 120.0, 180, 0, True, True, False),
    ("Dried Mango Slices 6oz", "Snacks", 4.49, 1.0, 32.0, 0.5, 0.5, 12.0, 2.0, 0.0, 5.0, 180, 0, True, True, False),
    ("Edamame Dry Roasted 8oz", "Snacks", 3.49, 14.0, 9.0, 4.5, 2.2, 60.0, 5.0, 0.0, 130.0, 180, 0, True, True, False),
    ("Air-Popped Popcorn 5oz", "Snacks", 2.99, 3.0, 18.0, 4.0, 0.9, 2.0, 3.0, 0.0, 110.0, 90, 0, True, True, False),
    ("Beef Jerky Grass-Fed 2.5oz", "Snacks", 6.49, 12.0, 3.0, 1.5, 1.8, 10.0, 0.0, 0.0, 450.0, 180, 0, True, False, True),
    ("Granola Bars Peanut Butter 6pk", "Snacks", 3.79, 4.0, 18.0, 6.0, 0.9, 20.0, 2.0, 0.0, 95.0, 180, 0, False, True, False),
    ("Fruit Bites Strawberry 5oz", "Snacks", 3.19, 0.5, 20.0, 0.0, 0.3, 8.0, 2.0, 0.0, 10.0, 180, 0, True, True, False),
    ("Hummus Classic Dip 10oz", "Snacks", 3.49, 2.0, 4.0, 5.0, 0.6, 20.0, 1.5, 0.0, 125.0, 21, 0, True, True, False),
    ("Pita Chips Sea Salt 7.4oz", "Snacks", 3.29, 3.0, 19.0, 5.0, 0.8, 15.0, 1.0, 0.0, 270.0, 90, 0, False, True, False),
    ("Pretzels Whole Wheat 10oz", "Snacks", 2.49, 3.0, 23.0, 1.0, 1.0, 10.0, 2.0, 0.0, 380.0, 180, 0, False, True, False),
    ("Plantain Chips Sea Salt 5oz", "Snacks", 2.79, 1.0, 19.0, 7.0, 0.5, 5.0, 2.0, 0.0, 85.0, 120, 0, True, True, False),
    ("String Cheese Organic 6pk", "Snacks", 3.99, 7.0, 1.0, 6.0, 0.1, 200.0, 0.0, 0.2, 170.0, 30, 0, True, False, False),
    ("Lentil Chips Tomato 4oz", "Snacks", 3.29, 4.0, 17.0, 5.0, 1.2, 30.0, 2.0, 0.0, 190.0, 120, 0, True, True, False),
    ("Sunflower Seed Butter Cups 2pk", "Snacks", 2.49, 3.0, 14.0, 10.0, 1.0, 25.0, 2.0, 0.0, 60.0, 180, 0, True, True, False),
    ("Apple Chips Cinnamon 2.5oz", "Snacks", 2.99, 0.0, 24.0, 0.0, 0.2, 10.0, 4.0, 0.0, 0.0, 180, 0, True, True, False),
    ("Organic Rice Cakes Salted", "Snacks", 2.29, 1.5, 14.0, 0.5, 0.3, 5.0, 1.0, 0.0, 35.0, 180, 0, True, True, False),
    ("Turkey Sticks Mini 4ct", "Snacks", 4.99, 9.0, 1.0, 4.0, 0.8, 10.0, 0.0, 0.0, 280.0, 90, 0, True, False, False),

    # Prepared Meals (20 items)
    ("Vegetable Grain Bowl Frozen", "Prepared Meals", 4.99, 11.0, 48.0, 7.0, 2.5, 75.0, 7.0, 0.0, 420.0, 90, 5, True, True, False),
    ("Chicken Tikka Masala Ready Meal", "Prepared Meals", 5.99, 22.0, 40.0, 11.0, 2.1, 80.0, 3.0, 0.0, 680.0, 14, 4, True, False, False),
    ("Vegan Lentil Soup Can 15oz", "Prepared Meals", 2.49, 9.0, 24.0, 2.5, 3.1, 40.0, 7.0, 0.0, 490.0, 730, 3, True, True, False),
    ("Organic Chili with Beans 15oz", "Prepared Meals", 2.99, 13.0, 28.0, 3.0, 3.5, 60.0, 8.0, 0.0, 580.0, 730, 3, True, True, False),
    ("Burrito Black Bean Rice Frozen", "Prepared Meals", 3.29, 10.0, 45.0, 6.0, 2.4, 110.0, 5.0, 0.0, 460.0, 180, 3, False, True, False),
    ("Salmon Quinoa Meal Kit", "Prepared Meals", 8.99, 27.0, 32.0, 12.0, 2.2, 50.0, 4.0, 8.0, 510.0, 7, 10, True, False, True),
    ("Thai Green Curry Tofu Box", "Prepared Meals", 5.49, 14.0, 38.0, 9.0, 2.8, 150.0, 4.0, 0.0, 540.0, 14, 5, True, True, False),
    ("Mediterranean Couscous Salad", "Prepared Meals", 4.49, 7.0, 34.0, 8.0, 1.8, 45.0, 4.0, 0.0, 390.0, 5, 0, False, True, False),
    ("Chicken Noodle Soup Organic", "Prepared Meals", 2.89, 10.0, 18.0, 2.5, 1.1, 20.0, 1.0, 0.0, 620.0, 730, 3, False, False, False),
    ("Ravioli Spinach Ricotta Fresh", "Prepared Meals", 4.79, 12.0, 38.0, 7.0, 1.5, 180.0, 3.0, 0.0, 410.0, 12, 6, False, False, False),
    ("Tofu Veggie Stir Fry Kit", "Prepared Meals", 4.99, 12.0, 22.0, 6.0, 2.5, 140.0, 4.0, 0.0, 450.0, 7, 8, True, True, False),
    ("Beef Barbacoa Bowl Frozen", "Prepared Meals", 6.49, 24.0, 42.0, 10.0, 3.2, 60.0, 5.0, 0.0, 690.0, 180, 4, True, False, True),
    ("Chickpea Coconut Curry Bowl", "Prepared Meals", 4.29, 10.0, 40.0, 8.0, 3.0, 80.0, 6.0, 0.0, 380.0, 180, 4, True, True, False),
    ("Margherita Pizza Frozen Personal", "Prepared Meals", 4.19, 14.0, 46.0, 12.0, 1.8, 220.0, 2.0, 0.0, 640.0, 180, 12, False, False, False),
    ("Egg & Spinach Breakfast Wrap", "Prepared Meals", 3.79, 13.0, 28.0, 9.0, 1.9, 160.0, 2.0, 0.0, 480.0, 7, 3, False, False, False),
    ("Keto Cauliflower Mash Meal", "Prepared Meals", 5.29, 15.0, 8.0, 14.0, 1.4, 110.0, 3.0, 0.0, 520.0, 14, 5, True, False, False),
    ("Sesame Noodle Tofu Salad", "Prepared Meals", 4.89, 11.0, 39.0, 9.0, 2.1, 70.0, 3.5, 0.0, 430.0, 4, 0, False, True, False),
    ("Minestrone Vegetable Soup Can", "Prepared Meals", 2.29, 5.0, 22.0, 1.5, 1.4, 40.0, 4.0, 0.0, 480.0, 730, 3, False, True, False),
    ("Quinoa Black Bean Salad Fresh", "Prepared Meals", 4.69, 8.0, 30.0, 6.0, 2.2, 55.0, 5.0, 0.0, 320.0, 5, 0, True, True, False),
    ("Spaghetti Meatballs Frozen", "Prepared Meals", 3.99, 18.0, 48.0, 9.0, 2.5, 80.0, 4.0, 0.0, 670.0, 180, 6, False, False, False),
]


def _build_catalog() -> List[Dict[str, Any]]:
  """Build structured list of 250+ grocery item dictionaries."""
  catalog = []
  for row in _RAW_CATALOG_DATA:
    catalog.append({
        "name": row[0],
        "category": row[1],
        "price": row[2],
        "protein_g": row[3],
        "carbs_g": row[4],
        "fats_g": row[5],
        "iron_mg": row[6],
        "calcium_mg": row[7],
        "fiber_g": row[8],
        "vitamin_d_mcg": row[9],
        "sodium_mg": row[10],
        "shelf_life_days": row[11],
        "prep_time_mins": row[12],
        "is_gluten_free": row[13],
        "is_vegan": row[14],
        "is_premium": row[15],
    })
  return catalog


ENTERPRISE_CATALOG: List[Dict[str, Any]] = _build_catalog()

ENTERPRISE_GROCERY_CATALOG: List[EnterpriseGroceryItem] = [
    EnterpriseGroceryItem(**item) for item in ENTERPRISE_CATALOG
]

# 3 Household Scenarios as specified in implementation plan
HOUSEHOLD_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "single_student": {
        "name": "Single Student (Budget & Speed)",
        "budget": 50.0,
        "targets": {
            "protein_g": 70.0,
            "carbs_g": 200.0,
            "fats_g": 50.0,
            "iron_mg": 18.0,
            "calcium_mg": 1000.0,
            "fiber_g": 30.0,
            "vitamin_d_mcg": 15.0,
        },
        "max_prep_time_mins": 15,
        "is_gluten_free": False,
        "is_vegan": False,
        "max_sodium_mg": 3000.0,
        "min_shelf_life_days": 3,
    },
    "athlete_bulk": {
        "name": "Athlete Bulk (High Macro & Micro)",
        "budget": 120.0,
        "targets": {
            "protein_g": 190.0,
            "carbs_g": 350.0,
            "fats_g": 85.0,
            "iron_mg": 25.0,
            "calcium_mg": 1300.0,
            "fiber_g": 45.0,
            "vitamin_d_mcg": 20.0,
        },
        "max_prep_time_mins": 30,
        "is_gluten_free": False,
        "is_vegan": False,
        "max_sodium_mg": 4000.0,
        "min_shelf_life_days": 3,
    },
    "family_of_4": {
        "name": "Family of 4 (Restricted: GF, Vegan, Low Sodium)",
        "budget": 220.0,
        "targets": {
            "protein_g": 240.0,
            "carbs_g": 500.0,
            "fats_g": 110.0,
            "iron_mg": 30.0,
            "calcium_mg": 1500.0,
            "fiber_g": 60.0,
            "vitamin_d_mcg": 25.0,
        },
        "max_prep_time_mins": 45,
        "is_gluten_free": True,
        "is_vegan": True,
        "max_sodium_mg": 1400.0,
        "min_shelf_life_days": 7,
    },
}
