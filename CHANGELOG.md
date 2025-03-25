# Pakeitimai
Lietuviškai surašytus keitimus rasite [PAKEITIMAI.md](PAKEITIMAI.md).

# Changelog
Only the most visible and important changes for the application user are presented here. 
You can view the most detailed change log on the https://github.com/embar-/pdsa-grapher/commits/master/ page.

## Latest
### Fixes
- Viz: When sharing the screen via MS Teams and clicking on a node, the Chrome/Edge browsers (but not Firefox) 
  interpreted it as a drag action, thereby blocking the simple mouse click release actions.
- Ensure proper column renaming by pre-renaming conflicting ones when the user swaps column names or uses the 
  same column repeatedly for different purposes.
- Checkboxes are sensitive to clicks throughout the entire context menu length, not just clicks on the text.
### New features
- Viz: Option to show checkboxes near columns for coloring.
- When selecting tables from manual input, ignore case sensitivity and consider wildcard characters like "*" and "?".
- Ability to sort the content of preview tables in the 'File Upload' tab (previously only worked in the 'Graph' tab).
- Ability to filter the content of preview tables in the 'Graph' tab.
- Ability to copy drawn tables with quotation marks (").
- The ability to export all tables (including their columns and references) to JSON, not just the displayed ones.
- The user at PDSA can select the column by which tables are filtered for the initial display in the chart 
  (PDSA does not have a separate column for this, but a separate column is available when importing the exported JSON).
### Other changes
- When copying a list of tables, write the tables on a new line (this does not affect the insertion at 
  'Add list of tables to graph', as the new line is automatically changed to a space here).

## v2.0.7 (2025-03-13)
### Fixes
- Fix filtering tables at "Get info about columns of selected tables".

## v2.0.6 (2025-03-13)
### Fixes
- Specific message in Graph tab at the start of work if no tables are automatically drawn.
### Other changes
- Revert "Viz: Update viewport during move of table" (cab276a).
- Requirements versions update (e.g. for fast DBML parsing).

## v2.0.5 (2025-03-12)
### Fixes
- Viz: do not crash when adding columns based on references if PDSA is not uploaded and there is no 'column' column 
  (fix commit#ded0f85).
- memory-uploaded-pdsa and memory-uploaded-refs memory storage_type='memory' (instead of storage_type='session')
  might help avoid errors due to memory limitations on the browser page.
- Viz: Update viewport during move of table.
### New features
- Show the number of tables depicted in the drawing.
- Show a message in Graph tab at the start of work if not all tables are automatically drawn.

## v2.0.4 (2025-03-07)
### Fixes
- Allow importing an XLSX file that contains at empty sheet among non-empty sheets.
- Sometimes a Lithuanian text document (e.g., JSON) with UTF-8 encoding is mistakenly detected as Windows-1252.
- JSON reading with empty columns.

## v2.0.3 (2025-03-06)
### Fixes
- Viz: Reorder columns by keys before adding the "…" marker (otherwise, if the primary key column is all nulls, 
  such reordering might move the "…" marker to the beginning).
- Avoid having the tooltip appear outside the visible area of the page.
- Allow selecting the tooltip header as text, as dragging is not implemented.
### New features
- Viz: Trim long table and column descriptions in the graph - full descriptions can still be seen by double-clicking.
### Other changes
- Rename PDSA panel into generic and more understandable "Database tables and columns".

## v2.0.2 (2025-03-04)
### Fixes
- Viz: Show columns that are mentioned in references but are not described in the PDSA (or there are discrepancies).
- Viz: Properly arrange arrows on lines of both directions.
### New features
- The ability to upload multiple documents (e.g., CSV) at once as different sheets.
- Allow the user to select only non-empty PDSA columns for information in the graph itself.

## v2.0.1 (2025-03-03)
### Fixes
- Do not crash when the DBML column type is Enum.
- Do not crash when converting already analyzed DBML content to a polars dataframe upon receiving unexpected values.
- While importing JSON and DBML, it is still necessary to check whether the last upload was in the PDSA field, 
  even when relationships have already been imported previously.

## v2.0.0 (2025-02-28)
### Fixes
- Showing neighbors, display the connections between those neighbors.
- Do not crash when there is no data in the selected PDSA sheet.
### New features
- The new default Viz engine for graph drawing (as an alternative to Cytoscape).
- Using the Viz engine, the ability to edit intermediate Graphviz DOT syntax.
- Ability for the user to specify columns instead of requiring them to be named with standard names.
- Option to select a references sheet (if there are more than 1).
- Allow draw only from the references document or PDSA; then just warn if either one is missing.
- Option to exclude PDSA tables that have metadata indicating they contain no records (rows).
- Ability to import JSON (JavaScript Object Notation) and DBML (Database Markup Language) files.
- Ability to export drawn tables and their data to JSON.
### Other changes
- The startup script has been renamed from `app_tabs.py` to `main.py`.
- Use `polars` instead of `pandas`.

## v1.3 (2025-02-10)
### Fixes
- Add constraint on column choice in File upload tab - make columns "table" mandatory 
  as they are necessary for filters and displays in the Graph tab
  ([issue#13](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/13)).
- When changing the language or reopening the page, the uploaded PDSA and relationship data does not disappear.
### New features
- Option to choose type neighbors: incoming, outgoing or all ([issue#14](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/14)).
- View incoming and outgoing links from active node to neighbours in different colors.
- Allow selecting tables even if they are forgotten to be described in the PDSA document 
  but were in the relationships document.
- Warnings and errors are displayed in the browser window below the *Submit* button, 
  explaining why the user cannot submit data for the chart.
- Option to display labels above active connections (checkbox through ☰ menu).
- Option to copy drawn tables (selection through ☰ menu).
- Option to copy the list of tables that the user has chosen to view column info.
- New sample data that allows for a more comprehensive evaluation of the tool's capabilities.

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
- Updated layout in *Graph* tab with an option to resize panels.
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
