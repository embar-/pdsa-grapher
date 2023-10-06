# Grapher
### For english version, choose branch "grapher_english".
The following program is an App made on Plotly's Dash framework. The App lets you display and filter relationships between tables of your database as well as display the metadata of those tables.
Note: The app was tested on Chrome browser.

![Screenshot of the App](https://github.com/Lukas-Vasionis/pdsa-grapher/assets/47796376/a6f2f675-4e88-463b-b46e-952e46da5078)


# Required files (inputs):
* PDSA **xlsx** file - information about nodes (in this case, tables). The App presumes that file has at least two sheets:
  * One defining the tables (their names, id's, descriptions etc.)
  * One defining their columns (table name, dtype, null counts, descriptions etc.)
* Užklausa **xlsx** file - information about edges (relations between tables). Currently, app only requires to mark the columns that hold the names of source table and target table 

# Usage
### Before execution:
* Install required libraries
* Run `python app_tabs.py` in the terminal
* Open the link that appears in the terminal

### After execution :

The app is composed of two tabs: File upload and Dashboard (Grapher). Always start with the tab of File upload.
* File upload
  * After the link is open, upload the required files in the displayed fields.
  * Mark which sheets/columns hold the information
    * On the left (PDSA panel), choose which sheet holds information on tables and columns. Then, pick the columns that you want to see in the dashboard.  
    * On the right (Užklausa panel), choose which columns that hold the names of source table and target table.
  * **Always click** `Submit` - it summarizes the info that you filled in and passes it to the Grapher tab

* Visualization (Grapher)
  * In the grapher tab you'll find the panel to display the information that you submitted
  * Page layout:
    *   The top bar holds instructions in Lithuanian for each side
    *   The left side displays network of your tables
    *   The right side displays filters that define what and how to display:
      * Set your layout - options for node arrangement in the graph
      * Select tables to graph, Add list of tables to graph (comma separated) - ways to declare tables to display. The selections are added up and send to the graph
      * Button `Get neighbors` - lets you add all tables that connect to your selection tables.  
      * Get info about columns of selected tables (PDSA sheet 'columns')
      * Button `Info on tables displayed in network (PDSA sheet 'tables')`
      
# Required features:
* <del>Make input definition more simple - create Graphic User Interface for inputs</del>
* <del>Add requirements.txt</del>
* <del>Add dummy data</del>
* Option to display of columns what join the tables
* Make a directed Graph - display relationships as arrows that show which node is source and which is arrow
* Add constraint on column choice in File upload tab - make columns "table" and "column" mandatory as they are necessary for filters and displays in the Grapher tab.  
* Deploy program to server so users with no programming knowledge could use it
