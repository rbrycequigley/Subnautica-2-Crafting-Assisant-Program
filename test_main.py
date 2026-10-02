"""Tests for the Subnautica 2 crafting manager."""

import csv

import pytest

from main import (
    CraftingError,
    calculate_requirements,
    compare_storage,
    load_recipes,
    parse_crafting_input,
    parse_recipe,
    resolve_raw_materials,
    save_storage,
)


def test_parse_recipe():
    assert parse_recipe("2X TITANIUM, 1X GLASS") == [
        ("TITANIUM", 2),
        ("GLASS", 1),
    ]


def test_valid_recipe_lookup():
    recipes = {
        "GLASS": (1, [("QUARTZ", 2)]),
    }
    assert parse_crafting_input("glass", recipes) == ("GLASS", 1)


def test_invalid_recipe_lookup():
    recipes = {"GLASS": (1, [("QUARTZ", 2)])}

    with pytest.raises(CraftingError):
        parse_crafting_input("laser sword", recipes)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("glass x2", ("GLASS", 2)),
        ("glass X2", ("GLASS", 2)),
        ("glass 2", ("GLASS", 2)),
    ],
)
def test_parse_quantities(text, expected):
    recipes = {"GLASS": (1, [("QUARTZ", 2)])}
    assert parse_crafting_input(text, recipes) == expected


def test_simple_recipe():
    recipes = {"GLASS": (1, [("QUARTZ", 2)])}
    result = calculate_requirements({"GLASS": 3}, recipes)
    assert result == {"QUARTZ": 6}


def test_nested_dependencies():
    recipes = {
        "BASIC FINS": (1, [("RUBBER", 2)]),
        "RUBBER": (1, [("LUCIFER ROTSACK", 2)]),
    }
    result = resolve_raw_materials("BASIC FINS", 1, recipes)
    assert result == {"LUCIFER ROTSACK": 4}


def test_craft_output_amount_is_accounted_for():
    recipes = {
        "BATTERY": (2, [("COPPER", 1)]),
    }
    result = resolve_raw_materials("BATTERY", 3, recipes)
    assert result == {"COPPER": 2}


def test_circular_dependency():
    recipes = {
        "A": (1, [("B", 1)]),
        "B": (1, [("C", 1)]),
        "C": (1, [("A", 1)]),
    }

    with pytest.raises(CraftingError, match="Circular"):
        resolve_raw_materials("A", 1, recipes)


def test_insufficient_materials():
    requirements = {"COPPER": 5}
    storage = {"COPPER": 2}
    assert compare_storage(requirements, storage) == {"COPPER": 3}


def test_sufficient_materials():
    requirements = {"COPPER": 5}
    storage = {"COPPER": 8}
    assert compare_storage(requirements, storage) == {}


def test_missing_material_not_in_storage():
    requirements = {"COPPER": 5}
    storage = {}
    assert compare_storage(requirements, storage) == {"COPPER": 5}


def test_load_valid_csv(tmp_path):
    crafting = tmp_path / "crafting.csv"
    crafting.write_text(
        "ITEM,AMOUNT MADE WHEN CRAFTING,RECIPE\n"
        "GLASS,1,2X QUARTZ\n",
        encoding="utf-8",
    )

    recipes = load_recipes(crafting)
    assert recipes["GLASS"] == (1, [("QUARTZ", 2)])


def test_missing_csv():
    with pytest.raises(CraftingError):
        load_recipes("/this/file/does/not/exist.csv")


def test_save_storage(tmp_path):
    storage_file = tmp_path / "storage.csv"
    storage_file.write_text(
        "ITEM,QUANTITY\n"
        "COPPER,10\n"
        "TITANIUM,5\n",
        encoding="utf-8",
    )

    save_storage({"COPPER": 4, "TITANIUM": 5}, storage_file)

    with storage_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {"ITEM": "COPPER", "QUANTITY": "4"},
        {"ITEM": "TITANIUM", "QUANTITY": "5"},
    ]
