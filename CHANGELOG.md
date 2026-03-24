# ChangeLog

## [0.2.3] - 19-03-2026
### Added
 - Reaction load outputs added.
 - Residual check added.
 - FieldOutput class added for storing results

### Changed
 - Reaction loads head() print added to solver.py __main__
 - gui and plot logic updated to handle new FieldOutput class.

### Fixed
 - Rogue print statement in plot.py removed
 - Better alignment with PEP8 
 - Unused code deleted or commented out

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
