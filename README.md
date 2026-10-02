# Subnautica 2 Crafting Manager

A beginner-friendly Python CLI for managing crafting recipes and material storage.

## Files

- `main.py` — application code.
- `test_main.py` — automated tests.
- `SUBNAUTICA2CRAFTING.csv` — your recipe data.
- `SUBNAUTICA2STORAGE.csv` — your current material storage.

The CSV files are intentionally not included because the program should use your
actual game data.

## CSV formats

Crafting:

```csv
ITEM,AMOUNT MADE WHEN CRAFTING,RECIPE
STRONG ACID,1,2X NECROLEI BUD
METAL FARM,1,1X AXUM INGOT, 1X AXUM BACTERIAL CULTURE
HABITAT BUILDER,1,2X TITANIUM, 1X GLASS, 1X BASIC BATTERY, 1X COPPER WIRE
```

Storage:

```csv
ITEM,QUANTITY
MEDICAL GEL SACK,2
TITANIUM,47
CONDUIT CRYSTAL,8
```

## Run

Use Python 3.14.7:

```bash
python main.py
```

The program asks for crafting requests until you enter `DONE`.

Examples:

```text
glass
glass x2
glass X2
glass 2
DONE
```

## Tests

The tests use temporary data and do not modify your real storage file.

If `pytest` is installed:

```bash
python -m pytest
```

## Important behavior

- Recipe names are matched case-insensitively.
- Recipe dependencies are resolved recursively.
- Circular dependencies are detected.
- Missing materials are reported before storage is consumed.
- Gathered materials can be added to storage.
- Storage is only replaced after a complete successful update.
- Materials at quantity `0` are reported after successful crafting.
