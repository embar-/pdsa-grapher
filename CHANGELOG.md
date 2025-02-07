# Pakeitimai
Lietuviškai surašytus keitimus rasite [PAKEITIMAI.md](PAKEITIMAI.md).

# Changelog
Only the most visible and important changes for the application user are presented here. 
You can view the most detailed change log on the https://github.com/embar-/pdsa-grapher/commits/master/ page.

## Latest
### Fixes
- Add constraint on column choice in File upload tab - make columns "table" mandatory 
  as they are necessary for filters and displays in the Graphic tab
  ([issue#13](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/13)).
- When changing the language or reopening the page, the uploaded PDSA and relationship data does not disappear.

### New features
- Option to choose type neighbors: incoming, outgoing or all ([issue#14](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/14)).
- View incoming and outgoing links from active node to neighbours in different colors.
- Allow selecting tables even if they are forgotten to be described in the PDSA document 
  but were in the relationships document.
- Warnings and errors are displayed in the browser window below the *Submit* button, 
  explaining why the user cannot submit data for the chart.

## v1.2 (2025-01-29)
### Fixes
- Tables with no relations were not visible ([issue#21](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/21)).
- Recompile translation MO files when they are older than the PO files.
- Prevented crashes after removing all nodes (tables).

### New features
- Button to draw all tables at once ([issue#17](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/17)).
- When requesting to show neighbors, display them in a different node color.
- Clicking a node displays detailed information about it, including relations to non-displayed tables.
- Clicking a link displays information about columns what join the tables.
- Ability to indicate in the 'File Upload' card that we have relationship columns.
- Ability to use CSV files as references, in addition to XLSX files ([issue#18](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/18)).
- Updated layout in *Graphic* tab with an option to resize panels.
- Make a directed Graph - display relationships as arrows that 
  show which node is source and which is target.

## v1.0 (2025-01-09)
Changes after forking [Lukas-Vasionis/pdsa-grapher](https://github.com/Lukas-Vasionis/pdsa-grapher).

### Fixes
- Fixed multiple crashes when opening ([issue#23](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/23)).
- Resolved crashes during layout selection ([issue#15](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/15)).

### New features
Main new features include:
- Interface language selection: Lithuanian or English, eliminating the need to run code from a language-specific branch.
- Automatic preselection of sheet names and column names in *File upload* tab 
  for standard PDSA and References files.
- Automatic preselection of up to 10 tables with the most relations to other tables for display.
