AGENTS.md
Project Overview
Build a Python command-line program that manages crafting in Subnautica 2.
The program should:
Accept a list of items the user wants to craft.
Look up the recipes for those items in SUBNAUTICA2CRAFTING.csv.
Resolve recipe dependencies, including recipes that require other craftable items.
Calculate the total raw materials required to craft the requested items.
Compare the required materials against the materials currently stored in SUBNAUTICA2STORAGE.csv.
If enough materials are available, remove the required materials from storage.
If materials are missing, tell the user exactly what is missing and pause crafting until the user confirms that they have gathered the missing materials.
Add gathered materials to storage before continuing.
Complete the crafting process and report the items that were crafted.
Report which materials are currently at 0 in storage.
The program should be designed to be understandable to less experienced Python developers.

Language and Environment
Python version: 3.14.7
Application type: command-line interface (CLI)
Input/output: terminal
Data storage: CSV files
External dependencies should be avoided unless they provide a clear benefit.
Prefer Python's standard library, including the csv module, for CSV processing.

Project Files
The program must read and modify these files:
SUBNAUTICA2CRAFTING.csv
SUBNAUTICA2STORAGE.csv
Do not rename these files unless explicitly instructed.
Do not hard-code recipe or material data into the Python source code when that data belongs in the CSV files.

SUBNAUTICA2CRAFTING.csv contains recipes in the following format:
ITEM,AMOUNT MADE WHEN CRAFTING,RECIPE
STRONG ACID,1,2X NECROLEI BUD
METAL FARM,1, 1X AXUM INGOT, 1X AXUM BACTERIAL CULTURE
HABITAT BUILDER,1, 2X TITANIUM, 1X GLASS, 1X BASIC BATTERY, 1X COPPER WIRE
SUBNAUTICA2STORAGE.csv contains materials and the amount of said material in the following format:
ITEM,QUANTITY
MEDICAL GEL SACK,2
TITANIUM,47
CONDUIT CRYSTAL,8


CSV Requirements
Before implementing CSV-related logic, inspect the existing CSV files and use their actual column names and structure.
Do not assume column names that have not been established by the project files.
The implementation should:
Read both CSV files safely.
Handle missing or empty CSV files gracefully.
Validate required columns before processing.
Preserve existing CSV data when updating quantities.
Write updated data back to the appropriate CSV file.
Avoid corrupting either CSV if an operation fails.
If the CSV structure needs to change, explain why before making the change.

User Interaction
Starting the Crafting List
Prompt the user:
What would you like to craft?
The user enters one item at a time.
Each valid item should be appended to the crafting list.
After each item, ask:
Anything else?
The user ends item entry by typing:
DONE
Input should be treated case-insensitively where appropriate.
For example:
User: advanced wiring kit
Program: Adding 'advanced wiring kit' to crafting list. Anything else?

User: survival multitool
Program: Adding 'survival multitool' to crafting list. Anything else?

User: sonic resonator
Program: Adding 'sonic resonator' to crafting list. Anything else?

User: DONE

Do not begin calculating materials until the user enters DONE.

Item Validation
When the user enters an item:
Normalize the input for comparison.
Check whether the requested item exists in the crafting data.
If it exists, add it to the crafting list.
If it does not exist, display a clear error message.
Do not add invalid items to the crafting list.
Example:
I couldn't find 'laser sword' in the crafting recipes.
Please enter a valid recipe name or type DONE to begin crafting.

The program should not crash because of invalid user input.

Quantities
Users may specify multiple copies of an item.
For example:
glass x2

should mean:
glass
glass

or, preferably, an internal representation equivalent to:
glass: 2

The parser should support reasonable variations such as:
glass x2
glass X2
glass 2

If quantity syntax is ambiguous or invalid, ask the user to re-enter the item rather than guessing.
Unless the recipe data explicitly supports another interpretation, quantities should be positive whole numbers.

Recipe Processing
Direct Recipe Requirements
After the user enters DONE, display the requested crafting list.
Example:
Begin crafting of:
- advanced wiring kit
- survival multitool
- sonic resonator

Then calculate the materials required for the entire crafting list.

Recipe Dependencies
Recipes may require other craftable items.
The program must recursively resolve these dependencies until it reaches raw materials.
For example:
Basic Fins
    -> 2 Rubber

Rubber
    -> 2 Lucifer Rotsack

Therefore:
Basic Fins
    -> 2 Rubber
    -> 4 Lucifer Rotsack

The program must account for the total raw-material cost of all dependencies.
Do not treat an intermediate craftable item as a raw material if that item has its own recipe.
The dependency-resolution logic should:
Support multiple levels of dependencies.
Multiply dependencies correctly when an item is required more than once.
Detect circular dependencies.
Fail gracefully if a circular dependency is found.
Example of an invalid circular dependency:
A -> B
B -> C
C -> A

The program should report the problem instead of recursing indefinitely.

Material Comparison
After calculating the total raw-material requirements, compare them with the quantities in SUBNAUTICA2STORAGE.csv.
For each required material:
required quantity
vs.
stored quantity

Determine whether enough material exists.
If enough materials exist
Proceed with crafting.
Subtract the required quantities from storage.
If materials are missing
Do not modify storage yet.
Display every missing material and the quantity required.
Example:
You are missing some materials!

You are missing:

- 5 COPPER
- 3 LUCIFER ROTSACK

Please gather those materials to proceed.
Have you gathered the materials? (YES or NO)


Missing Material Confirmation
If the user answers NO:
Do not modify storage.
Do not continue crafting.
End the current crafting attempt cleanly.
If the user answers YES:
Ask the user how many of each missing material they gathered, unless the program's intended design has another reliable way to determine the quantities.
Add the gathered quantities to SUBNAUTICA2STORAGE.csv.
Recalculate the storage comparison.
Continue only when enough materials are available.
Do not assume that the user gathered exactly the missing quantity unless this behavior is explicitly implemented and documented.
If the user enters an invalid response, ask them to enter YES or NO.

Storage Updates
Storage should only be modified when the program has confirmed that the required materials are available.
When crafting succeeds:
Subtract all required raw materials from storage.
Save the updated storage data.
Report the crafted items.
If crafting cannot be completed, do not partially consume materials.
The operation should be treated as atomic from the user's perspective:
Either:
    all required materials are available and consumed

or:
    nothing is consumed


Final Output
When crafting completes successfully, display:
Your crafting is complete!

You now have:

- advanced wiring kit
- survival multitool
- sonic resonator

Then display all materials whose quantity in storage is currently 0.
Example:
You need to gather more of the following items:

- TITANIUM
- LUCIFER ROTSACK
- COPPER
- SULFUR

If no materials have a quantity of 0, clearly state that there are currently no depleted materials.
Finish with:
Stay safe out there!


Error Handling
The program must handle invalid input without crashing.
At minimum, handle:
Empty user input.
Unknown recipe names.
Invalid quantities.
Negative quantities.
Zero quantities.
Invalid YES/NO responses.
Missing CSV files.
Empty CSV files.
Malformed CSV data.
Missing required CSV columns.
Materials that exist in recipes but not in storage.
Storage entries with invalid quantities.
Recipes with missing dependencies.
Circular recipe dependencies.
Error messages should explain the problem in language understandable to a less experienced user.
Avoid exposing Python tracebacks to the user during normal operation.

Code Structure
Use a modular structure.
Separate responsibilities where practical.
For example, the project may contain modules or functions responsible for:
Loading crafting data.
Loading storage data.
Saving storage data.
Parsing user input.
Validating recipe names.
Parsing quantities.
Resolving recipe dependencies.
Calculating total material requirements.
Comparing requirements with storage.
Updating storage.
Managing the user interaction loop.
Do not create unnecessary abstractions. Prefer simple, readable functions over excessive classes or design patterns.

Type Hints and Documentation
Use Python type hints throughout the project.
Functions and classes should have basic docstrings explaining:
What they do.
Important parameters.
What they return.
Use descriptive variable and function names.
Prefer readable code over overly compact code.
Avoid unnecessary one-line expressions when they make the logic harder for beginners to understand.

Testing
The project should include tests for important functionality.
At minimum, test:
Loading valid CSV data.
Handling missing CSV files.
Valid recipe lookup.
Invalid recipe lookup.
Parsing item quantities.
Calculating a simple recipe.
Calculating nested recipe dependencies.
Multiplying nested dependencies correctly.
Detecting circular dependencies.
Detecting insufficient materials.
Detecting sufficient materials.
Correctly subtracting materials from storage.
Correctly adding gathered materials to storage.
Identifying materials with a quantity of zero.
Ensuring storage is not modified when crafting cannot proceed.
Tests should not depend on the user's actual storage file.
Use temporary/test data when testing CSV modifications.

Code Quality Rules
Follow these principles:
Keep functions focused on one responsibility.
Avoid duplicated logic.
Prefer explicit, readable code.
Use type hints.
Use basic docstrings.
Keep user-interface logic separate from data-processing logic where practical.
Do not silently ignore errors.
Do not silently modify user data.
Do not hard-code recipe data that belongs in the CSV files.
Do not introduce dependencies without a reason.
Do not make unrelated changes to the project.

Development Workflow
Before modifying code:
Inspect the existing project structure.
Inspect both CSV files and determine their actual schema.
Inspect existing Python code and tests.
Understand existing behavior before replacing it.
Make the smallest reasonable changes necessary to satisfy the requirements.
After modifying code:
Run the relevant tests.
Run the program against representative data.
Verify CSV files are still valid.
Check that successful crafting consumes the correct materials.
Check that unsuccessful crafting does not consume materials.
Review the final diff for unintended changes.
Do not consider a task complete merely because the code runs. Verify that the behavior matches the requirements.

Definition of Done
The project is complete when:
The program runs without crashing during normal use.
Python 3.14.7 is supported.
The program can read SUBNAUTICA2CRAFTING.csv.
The program can read and modify SUBNAUTICA2STORAGE.csv.
Users can enter multiple crafting requests.
Users can enter DONE to begin processing.
Invalid recipe names are handled with clear messages.
Invalid quantities are handled with clear messages.
Recipe dependencies are resolved recursively.
Nested recipe dependencies calculate the correct raw-material requirements.
Circular recipe dependencies are detected.
The program correctly identifies insufficient materials.
The program tells the user exactly which materials are missing and how many are required.
The program can add gathered materials to storage.
The program consumes the correct materials when crafting succeeds.
Storage is not partially consumed when crafting cannot proceed.
The program reports the completed crafting list.
The program reports all materials currently at zero.
Important functionality has automated tests.
The code is modular, readable, and understandable to less experienced Python developers.

