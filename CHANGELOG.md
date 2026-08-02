# ChangeLog

## [0.2.3] - 02-08-2026
### Added
 - Reaction load outputs added.
 - Residual check added. Note this check is not yet meaningful, see item 3 in docs/todo.md.
 - FieldOutputs class added for storing results, using Abaqus field output names
   (U, RF, S, SP, SM).
 - docs/ expanded: worked_example.md, data_structures.md, roadmap.md and todo.md added,
   theory.md rewritten.
 - examples/worked_example.inp added, a two element patch test used by the worked example.
 - Documentation site added, MkDocs Material built and published by
   .github/workflows/docs.yml.
 - LICENSE added and declared in pyproject.toml.

### Changed
 - Reaction loads head() print added to solver.py __main__
 - gui and plot logic updated to handle new FieldOutputs class.
 - Set and material names are now lowercased at parse time and matched
   case-insensitively, as Abaqus does. Repeated set names now accumulate into one set
   rather than the last definition replacing the earlier ones.
 - Test model fixtures regenerated to match the new set handling.
 - Equations in docs written as unicode in code blocks rather than LaTeX, so they render
   anywhere markdown does.

### Fixed
 - Rogue print statement in plot.py removed
 - Better alignment with PEP8 
 - Unused code deleted or commented out. progress_bar.py deleted, unused os import
   removed from model.py.
 - Plot results no longer fails. plot.py and gui.py were still reading solver attributes
   that the FieldOutputs refactor removed.
 - plot.py no longer decrements element connectivity in place on the model, which
   corrupted it on every plot and failed on the second.

### Known issues
 - test_stress_inplane_3 fails, 162.3 against an expected 162.5. Narrowed from 160.5 by
   the set name fix above but not closed, cause not yet identified. See item 2 in
   docs/todo.md.

## [0.2.2] - 18-03-2026
### Added
 - Partial pivot function added to direct_solver.

### Changed
 - solver.py and direct_solver.py refactored, with greater alignment with PEP.
 - Print statements to gui log updated.
 - Homogeneous correction moved to dedicated function.
 - Unused code removed.

### Fixed
 - Potential bug relating to data types when solving with direct_solver.py (float64).
___
## [0.2.1] - 14-03-2026
### Added
 - stdout replaced with custom function to enable print statements to be passed to gui.
 - Solver run as thread to enable live logging of print statements.
 - Traceback added to gui to provide detailed exception info.
 - Scollbar added to gui log

### Changed
 - Log print statements updated.
 - File paths handled by pathlib.
 - Unused code removed.

### Fixed
 NA
___
## [0.2.0] - 11-03-2026
### Added
 - keywords.md and theory.md add to docs/.
 - Active mask added to model.py to map nodes with active dof.
 - Solver use active mask to reduce stiffness matrix to improve performance.

### Changed
 - pandas replaced with numpy for iterative tasks to improve performance.
 - Code structure updated.
 - pyproject added.
 - unitest replaced with pytest.
 - README.md updated.

### Fixed
 - General typos.
___
## [0.1.0] - 03-10-2024
### Added
 - Option for direct solver, direct_solver.py.

### Changed
 NA

### Fixed
 NA
___
## [0.0.1] - 07-03-2023 
### Added
 - First release.

### Changed
 NA

### Fixed
 NA
