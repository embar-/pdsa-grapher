# Grapher
The following program is an App made on Plotly's Dash framework. The App lets you to display and filter relationships between tables of your database in the network graph as well as display the info on tables.
Note: The app was tested on Chrome browser.

# Requred files (inputs):
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

The app is composed of two tabs: File upload and Dashborad (Grapher). Always start with the tab of File upload.
* File upload
  * After the link is open, upload the required files in the displayed fields.
  * Mark which sheets/columns hold the information
    * On the left (PDSA panel), choose, which sheet hold information on tables and columns. Then, pick the columns that you want to see in the dashboard.  
    * On the right (Užklausa panel), choose, which columns that hold the names of source table and target table.
  * **Always click** `Submit` - it summarizes the info that you filled in and passes it to the Grapher tab

* Visualisation (Grapher)
  * In the grapher tab you'll find the panel to display the information that you submitted
  * Page layout:
    *   The top bar holds instructions in Lithuanian for each side
    *   The left side displays network of your tables
    *   The right side displays filters that define what and how to display:
      * Set your layout - options for node arrangement in the graph
      * Select tables to graph, Add list of tables to graph (comma separated) - ways to declare tables to display. The selections are added up and send to the graph
      * Button `Get neighbours` - lets you add all tables that connect to your selection tables.  
      * Get info about columns of selected tables (PDSA sheet 'columns')
      * Button `Info on tables displayed in network (PDSA sheet 'tables')`
      
# Reikalingi update:
* <del>Kadangi norim duot šį scriptą naudoti PDSA vadybininkams, jam reikia sukurti GUI</del>
* Sukurti galimybę grafoje atvaizduoti stulpelius, kurie jungia lenteles
* Grafą paversti į "directed graph". Kitaip tariant, pridėti rodykles, nurodančias kas jungtyje yra source ir target
* Uždėt apribojimą ant stuleplių pasirinkimo tab'e "failų įkelimas". Čia, būtina palikti stulpelius "table" ir "column", nes jie yra naudojami grapher tab'o filtruose. Jei šie stulpeliai yra pašalinami tab'e "failų įkelimas", "grapher" tab'e lentelių informacijos nebeatvaizduosi.  
* Deploy'int programa, informacijos vadibininkams prieinamu budu
