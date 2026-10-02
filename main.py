"""Subnautica 2 crafting manager.

A beginner-friendly command-line program for calculating crafting requirements
and safely updating the player's material storage.
"""

from __future__ import annotations

import csv
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

CRAFTING_FILE = Path("SUBNAUTICA2CRAFTING.csv")
STORAGE_FILE = Path("SUBNAUTICA2STORAGE.csv")

CRAFTING_COLUMNS = ["ITEM", "AMOUNT MADE WHEN CRAFTED", "RECIPE COMPONENTS"]
STORAGE_COLUMNS = ["ITEM", "QUANTITY"]


class CraftingError(Exception):
    """Raised when crafting data or a crafting operation is invalid."""


def normalize_name(name: str) -> str:
    """Normalize an item name for case-insensitive comparisons."""
    return " ".join(name.strip().upper().split())


def parse_positive_integer(value: str) -> int:
    """Return a positive integer or raise CraftingError."""
    try:
        number = int(value)
    except ValueError as exc:
        raise CraftingError("Quantity must be a whole number.") from exc

    if number <= 0:
        raise CraftingError("Quantity must be greater than zero.")

    return number


def load_csv(path: Path, required_columns: List[str]) -> List[dict]:
    """Load a CSV file and validate its required columns."""
    if not path.exists():
        raise CraftingError(f"CSV file not found: {path}")

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise CraftingError(f"{path} is empty.")

            missing = [column for column in required_columns
                       if column not in reader.fieldnames]
            if missing:
                raise CraftingError(
                    f"{path} is missing required column(s): {', '.join(missing)}."
                )

            rows = list(reader)
    except OSError as exc:
        raise CraftingError(f"Could not read {path}: {exc}") from exc
    except csv.Error as exc:
        raise CraftingError(f"Could not read malformed CSV data in {path}: {exc}") from exc

    return rows


def load_recipes(path: Path = CRAFTING_FILE) -> Dict[str, Tuple[int, List[Tuple[str, int]]]]:
    """Load recipes.

    Returns a mapping of normalized item name to:
    (amount produced, [(ingredient name, ingredient quantity), ...]).
    """
    rows = load_csv(path, CRAFTING_COLUMNS)
    recipes: Dict[str, Tuple[int, List[Tuple[str, int]]]] = {}

    for row in rows:
        item = normalize_name(row["ITEM"])
        if not item:
            raise CraftingError("A crafting recipe has an empty ITEM value.")

        try:
            amount_made = parse_positive_integer(row["AMOUNT MADE WHEN CRAFTED"])
        except CraftingError as exc:
            raise CraftingError(
                f"Recipe '{item}' has an invalid amount made: "
                f"{row['AMOUNT MADE WHEN CRAFTED']!r}."
            ) from exc

        ingredients = parse_recipe_components(row["RECIPE COMPONENTS"], item)
        recipes[item] = (amount_made, ingredients)

    return recipes


def parse_recipe_components(recipe_text: str, recipe_name: str = "") -> List[Tuple[str, int]]:
    """Parse a recipe such as '2X TITANIUM, 1X GLASS'."""
    recipe_text = recipe_text.strip()

    if not recipe_text:
        raise CraftingError(f"Recipe '{recipe_name}' has no ingredients.")

    ingredients: List[Tuple[str, int]] = []

    for part in recipe_text.split(","):
        part = part.strip()
        match = re.fullmatch(r"(\d+)\s*[xX]\s*(.+)", part)
        if not match:
            raise CraftingError(
                f"Invalid ingredient '{part}' in recipe '{recipe_name}'."
            )

        quantity = int(match.group(1))
        name = normalize_name(match.group(2))

        if quantity <= 0 or not name:
            raise CraftingError(
                f"Invalid ingredient '{part}' in recipe '{recipe_name}'."
            )

        ingredients.append((name, quantity))

    return ingredients


def load_storage(path: Path = STORAGE_FILE) -> Dict[str, int]:
    """Load storage quantities from the storage CSV."""
    rows = load_csv(path, STORAGE_COLUMNS)
    storage: Dict[str, int] = {}

    for row in rows:
        item = normalize_name(row["ITEM"])
        if not item:
            raise CraftingError("Storage contains an empty ITEM value.")

        try:
            quantity = int(row["QUANTITY"])
        except ValueError as exc:
            raise CraftingError(
                f"Storage quantity for '{item}' is not a valid whole number."
            ) from exc

        if quantity < 0:
            raise CraftingError(
                f"Storage quantity for '{item}' cannot be negative."
            )

        storage[item] = quantity

    return storage


def resolve_raw_materials(
    item: str,
    quantity: int,
    recipes: Dict[str, Tuple[int, List[Tuple[str, int]]]],
    active_path: Tuple[str, ...] = (),
) -> Counter:
    """Recursively convert a craftable item into raw-material requirements."""
    item = normalize_name(item)

    if item in active_path:
        cycle = " -> ".join((*active_path, item))
        raise CraftingError(f"Circular recipe dependency detected: {cycle}")

    if item not in recipes:
        return Counter({item: quantity})

    amount_made, ingredients = recipes[item]
    crafts_needed = (quantity + amount_made - 1) // amount_made

    requirements = Counter()

    for ingredient, ingredient_quantity in ingredients:
        requirements.update(
            resolve_raw_materials(
                ingredient,
                crafts_needed * ingredient_quantity,
                recipes,
                (*active_path, item),
            )
        )

    return requirements


def calculate_requirements(
    crafting_list: Counter,
    recipes: Dict[str, Tuple[int, List[Tuple[str, int]]]],
) -> Counter:
    """Calculate total raw materials for all requested items."""
    requirements = Counter()

    for item, quantity in crafting_list.items():
        requirements.update(resolve_raw_materials(item, quantity, recipes))

    return requirements


def compare_storage(
    requirements: Counter, storage: Dict[str, int]
) -> Dict[str, int]:
    """Return only the materials for which storage is insufficient."""
    missing = {}

    for material, required in requirements.items():
        available = storage.get(material, 0)
        if available < required:
            missing[material] = required - available

    return missing


def save_storage(storage: Dict[str, int], path: Path = STORAGE_FILE) -> None:
    """Safely replace the storage CSV with updated quantities."""
    if not path.exists():
        raise CraftingError(f"CSV file not found: {path}")

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if fieldnames is None or any(column not in fieldnames for column in STORAGE_COLUMNS):
            raise CraftingError(f"{path} does not contain the required storage columns.")

        for row in rows:
            item = normalize_name(row["ITEM"])
            if item in storage:
                row["QUANTITY"] = str(storage[item])

        # Write to a temporary file first. Only replace the original after
        # the complete new file has been written successfully.
        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        temp_path.replace(path)

    except OSError as exc:
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise CraftingError(f"Could not safely update {path}: {exc}") from exc


def add_materials_to_storage(
    gathered: Dict[str, int], storage: Dict[str, int]
) -> None:
    """Add gathered materials to the in-memory storage."""
    for material, quantity in gathered.items():
        storage[material] = storage.get(material, 0) + quantity


def subtract_requirements(
    requirements: Counter, storage: Dict[str, int]
) -> Dict[str, int]:
    """Return a new storage state after consuming requirements.

    This does not mutate the original storage unless all requirements can be met.
    """
    missing = compare_storage(requirements, storage)
    if missing:
        raise CraftingError("Cannot consume materials because some are missing.")

    updated = storage.copy()
    for material, required in requirements.items():
        updated[material] -= required

    return updated


def parse_crafting_input(text: str, recipes: Dict[str, Tuple[int, List[Tuple[str, int]]]]) -> Tuple[str, int]:
    """Parse an item name with an optional positive quantity.

    Supported examples:
        glass
        glass x2
        glass X2
        glass 2
    """
    text = " ".join(text.strip().split())
    if not text:
        raise CraftingError("Please enter an item name.")

    match = re.fullmatch(r"(.+?)\s+[xX]?(\d+)", text)
    if match:
        name = normalize_name(match.group(1))
        quantity = parse_positive_integer(match.group(2))
    else:
        name = normalize_name(text)
        quantity = 1

    if name not in recipes:
        raise CraftingError(
            f"I couldn't find '{name}' in the crafting recipes."
        )

    return name, quantity


def display_requirements(requirements: Counter) -> None:
    """Display calculated raw-material requirements."""
    print("\nRaw materials required:")
    for material, quantity in sorted(requirements.items()):
        print(f"- {material}: {quantity}")


def gather_missing_materials(
    missing: Dict[str, int],
    storage: Dict[str, int],
    storage_path: Path,
) -> bool:
    """Ask the user for gathered quantities and update storage.

    Returns True if the user chose to continue, otherwise False.
    """
    print("\nYou are missing some materials!\n")
    print("You are missing:")
    for material, quantity in sorted(missing.items()):
        print(f"- {quantity} {material}")

    while True:
        answer = input("\nHave you gathered the materials? (YES or NO): ").strip().upper()

        if answer == "NO":
            return False

        if answer != "YES":
            print("Please enter YES or NO.")
            continue

        gathered: Dict[str, int] = {}

        for material, required_missing in sorted(missing.items()):
            while True:
                value = input(
                    f"How many {material} did you gather? "
                    f"(At least {required_missing}): "
                ).strip()

                try:
                    quantity = parse_positive_integer(value)
                except CraftingError as exc:
                    print(exc)
                    continue

                gathered[material] = quantity
                break

        add_materials_to_storage(gathered, storage)
        save_storage(storage, storage_path)
        return True


def print_zero_materials(storage: Dict[str, int]) -> None:
    """Display all stored materials whose quantity is exactly zero."""
    zero_items = sorted(item for item, quantity in storage.items() if quantity == 0)

    print("\nYou need to gather more of the following items:")
    if zero_items:
        for item in zero_items:
            print(f"- {item}")
    else:
        print("There are currently no depleted materials.")


def run(
    crafting_path: Path = CRAFTING_FILE,
    storage_path: Path = STORAGE_FILE,
) -> None:
    """Run the interactive crafting program."""
    try:
        recipes = load_recipes(crafting_path)
        storage = load_storage(storage_path)
    except CraftingError as exc:
        print(f"Error: {exc}")
        return

    crafting_list: Counter = Counter()

    print("Subnautica 2 Crafting Manager")
    print("-----------------------------")

    while True:
        text = input("\nWhat would you like to craft? ").strip()

        if text.upper() == "DONE":
            break

        try:
            item, quantity = parse_crafting_input(text, recipes)
        except CraftingError as exc:
            print(exc)
            print("Please enter a valid recipe name or type DONE to begin crafting.")
            continue

        crafting_list[item] += quantity
        print(
            f"Adding '{item}' x{quantity} to crafting list. Anything else?"
        )

    if not crafting_list:
        print("No items were selected. Crafting cancelled.")
        return

    print("\nBegin crafting of:")
    for item, quantity in crafting_list.items():
        if quantity == 1:
            print(f"- {item}")
        else:
            print(f"- {item} x{quantity}")

    try:
        requirements = calculate_requirements(crafting_list, recipes)
    except CraftingError as exc:
        print(f"\nError while calculating materials: {exc}")
        return

    display_requirements(requirements)

    missing = compare_storage(requirements, storage)

    if missing:
        if not gather_missing_materials(missing, storage, storage_path):
            print("Crafting cancelled. Your storage was not consumed.")
            return

        missing = compare_storage(requirements, storage)
        if missing:
            print("\nYou still do not have enough materials.")
            for material, quantity in sorted(missing.items()):
                print(f"- {quantity} more {material}")
            print("Crafting cancelled. No materials were consumed.")
            return

    try:
        updated_storage = subtract_requirements(requirements, storage)
        save_storage(updated_storage, storage_path)
        storage = updated_storage
    except CraftingError as exc:
        print(f"Error: {exc}")
        return

    print("\nYour crafting is complete!")
    print("\nYou now have:")
    for item, quantity in crafting_list.items():
        if quantity == 1:
            print(f"- {item}")
        else:
            print(f"- {item} x{quantity}")

    print_zero_materials(storage)
    print("\nStay safe out there!")


if __name__ == "__main__":
    run()
