"""Grocery catalog dataset and test scenarios for AlphaEvolve prototype."""

from typing import NamedTuple


class GroceryItem(NamedTuple):
  name: str
  price: float  # Price in USD
  nutrition_score: float  # 1.0 to 10.0 scale
  category: str  # vegetable, fruit, protein, grain, dairy, snack


# 30 Everyday Grocery Items Catalog
GROCERY_CATALOG: list[GroceryItem] = [
    # Vegetables
    GroceryItem("Organic Spinach", 3.49, 9.5, "vegetable"),
    GroceryItem("Broccoli Crowns", 2.49, 9.0, "vegetable"),
    GroceryItem("Carrots (2lb bag)", 1.99, 8.5, "vegetable"),
    GroceryItem("Bell Peppers (3-pack)", 3.99, 8.0, "vegetable"),
    GroceryItem("Sweet Potatoes", 2.29, 8.5, "vegetable"),
    # Fruits
    GroceryItem("Bananas (bunch)", 1.49, 7.5, "fruit"),
    GroceryItem("Gala Apples (3lb bag)", 4.49, 8.0, "fruit"),
    GroceryItem("Fresh Strawberries", 3.99, 8.5, "fruit"),
    GroceryItem("Blueberries (pint)", 4.29, 9.0, "fruit"),
    GroceryItem("Oranges (4lb bag)", 4.99, 8.0, "fruit"),
    # Proteins
    GroceryItem("Boneless Chicken Breast (1.5lb)", 7.99, 9.0, "protein"),
    GroceryItem("Wild Salmon Fillet (1lb)", 11.99, 9.5, "protein"),
    GroceryItem("Organic Eggs (dozen)", 3.99, 8.5, "protein"),
    GroceryItem("Firm Tofu (14oz)", 2.49, 8.0, "protein"),
    GroceryItem("Black Beans (can)", 1.19, 8.0, "protein"),
    # Grains
    GroceryItem("Whole Wheat Bread", 3.29, 7.0, "grain"),
    GroceryItem("Brown Rice (2lb)", 2.99, 7.5, "grain"),
    GroceryItem("Rolled Oats (32oz)", 3.79, 8.5, "grain"),
    GroceryItem("Quinoa (16oz)", 4.99, 9.0, "grain"),
    GroceryItem("Whole Wheat Pasta", 1.89, 7.0, "grain"),
    # Dairy & Alternatives
    GroceryItem("Greek Yogurt (32oz)", 4.49, 8.5, "dairy"),
    GroceryItem("Whole Milk (1 gal)", 3.79, 7.5, "dairy"),
    GroceryItem("Cheddar Cheese Block", 3.99, 6.5, "dairy"),
    GroceryItem("Almond Milk (64oz)", 3.29, 7.0, "dairy"),
    GroceryItem("Cottage Cheese", 2.99, 8.0, "dairy"),
    # Snacks & Treats
    GroceryItem("Dark Chocolate Bar", 2.99, 5.0, "snack"),
    GroceryItem("Roasted Almonds (8oz)", 5.99, 7.5, "snack"),
    GroceryItem("Potato Chips", 3.49, 2.0, "snack"),
    GroceryItem("Granola Bars (6-pack)", 3.79, 5.5, "snack"),
    GroceryItem("Pretzels", 2.49, 3.0, "snack"),
]

ALL_CATEGORIES: list[str] = [
    "vegetable",
    "fruit",
    "protein",
    "grain",
    "dairy",
    "snack",
]


class ShoppingScenario(NamedTuple):
  name: str
  budget: float
  target_diversity_min_per_category: int


DEFAULT_SCENARIO = ShoppingScenario(
    name="Weekly Smart Household Budget ($45)",
    budget=45.0,
    target_diversity_min_per_category=1,
)

