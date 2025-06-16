# PDSA graferis

Lietuvišką pilną aprašą rasite [PERSKAITYK.md](PERSKAITYK.md) rinkmenoje.

| ![graferis viz](sample_data/biblioteka_viz.gif) | ![graferis cyto](sample_data/biblioteka_cyto.gif) |
|-------------------------------------------------|---------------------------------------------------|

# PDSA grapher

**Purpose**:
To display selected database tables, their metadata, and relationships, while allowing interactive table dragging.

**Technologies**:
Python 3, Plotly's Dash framework, Polars, Viz.js, D3.js.

**Key features**
- **Interactivity:** Visualize table relationships and drag tables in the graph using the selected drawing engine:
  - **Viz** - Graphviz-based Viz.js powered with D3.js for dragging and other interactivity;
  - **Cytoscape** - for simpler network-like drawing.
- **Table information display**: View detailed metadata, including columns, keys, descriptions, and relations.
- **Multiple file format support**: DBML, JSON, XLSX, XLS, ODS and CSV for data import.


## Table of Contents
- [Source directory structure](#source-directory-structure)
- [Required files for inputs](#required-files-for-inputs)
- [Installation and start](#installation-and-start)
  - [Option 1: regular Python](#option-1-regular-python)
  - [Option 2: run GitHub code via PyCharm](#option-2-run-github-code-via-pycharm)
  - [Option 3: Docker app from local sources](#option-3-docker-app-from-local-sources)
  - [Option 4: Docker image from Docker Hub](#option-4-docker-image-from-docker-hub)
- [Usage](#usage)
  - [File upload](#file-upload)
  - [Graph](#graph)
- [Updates since fork](#updates-since-fork)
- [Known bugs, limitations and requested features](#known-bugs-limitations-and-requested-features)
- [License](#license)


## Source directory structure
The project files are organized in the following directories:

| Directory       | Description                                                                                |
|-----------------|--------------------------------------------------------------------------------------------|
| `assets/`       | Dash custom assets and third-party libraries, see the [assets/README.md](assets/README.md) |
| `grapher_lib/`  | Helper functions library                                                                   |
| `locale/`       | Gettext localization files                                                                 |
| `locale_utils/` | Tools to set Gettext locale and update `locale/` files                                     |
| `sample_data/`  | Example PDSA, references and other related files                                           |

In the main directory, you will find 
the main Python file `main.py`, Docker files and other general files. 

The files are encoded in UTF-8.


## Required files for inputs
To familiarize yourself with the program's capabilities, you can use the files located in the `sample_data/` directory. 
For uploading, you will need:
- either one JSON file (e.g., `biblioteka.json`),
- or one DBML file (e.g., `biblioteka.dbml`),
- or two (or several) separate files (e.g., `biblioteka_pdsa.xlsx` and `biblioteka_refs.csv`):
  - Primary Data Structure Description (liet. Pirminių duomenų struktūros aprašas, PDSA) XLSX file with specific sheets 
    (e.g., `biblioteka_pdsa.xlsx`) or corresponding CSV files (e.g., `biblioteka_pdsa_tables.csv` and `biblioteka_pdsa_columns.csv`):
    - defining the **tables** (e.g., `biblioteka_pdsa.xlsx` sheet `table` or `biblioteka_pdsa_tables.csv` file):
      - table names (expected in `table` column),
      - table descriptions (expected in `comment` column, optional),
      - number of table records (expected in `n_records` column, optional).
    - defining their **columns** (e.g., `biblioteka_pdsa.xlsx` sheet `table` or `biblioteka_pdsa_columns.csv`):
      - table names (expected in `table` column),
      - column names (expected in `column` column),
      - column descriptions (expected in `comment` column, optional),
      - primary key indication (expected in `is_primary` column, optional),
      - column data types etc.
  - **References** XLSX or CSV file containing information about edges (relations between tables). 
    App requires columns that hold the names of the source table and target table, 
    columns holding info about source column and target column are optional.

The names of the XLSX sheets and the names of the sheet columns can be anything - you can choose what each column means 
in the program. However, if they are found with default names, assignments will be automatic.


## Installation and start
Choose one option to install dependencies and run the program: either regular Python or Docker.

**Note:** The app was tested on Python 3.10 and 3.12 versions.

**Note:** The program has been tested on Firefox 135, Chrome 133, Edge 133 browsers.

### Option 1: regular Python
1. Open a terminal application and navigate to the source code directory.
2. Create a virtual environment:
   `python -m venv .venv`
3. Activate the virtual environment.
   
   Using Linux or macOS:
   `source .venv/bin/activate`

   Using Windows:
   `.venv\Scripts\activate`

4. Install required libraries:
  `pip install -r requirements.txt`
5. Run the application:
  `python main.py`
6. Open the link that appears in the terminal, usually http://127.0.0.1:8050/pdsa_grapher/


### Option 2: run GitHub code via PyCharm
1. Open PyCharm on your computer and choose to create a new project using version control: 

   1. either on the Welcome screen, click on "Get from VCS" or "Clone Repository",

   2. either in other project go `File` > `Project from Version Control`.

2. In the pop-up window, enter GIT the Repository URL: `https://github.com/embar-/pdsa-grapher.git`
3. Select a directory on your local machine where you want the project to be cloned.
4. Click the "Clone" button to start cloning the repository. PyCharm will automatically propose 
   to create a virtual environment and install dependencies from `requirements.txt`.
5. Once PyCharm opens the project, run `main.py`. You may need indicate the virtual environment at the first run.

### Option 3: Docker app from local sources
Alternatively, you can run program using Docker by using local source code:
1. Ensure _Docker_ service is running on your computer.
2. Open a terminal application and navigate to the source code directory
  (ensure `docker-compose.yml` is located there).
3. Build (if not yet) and run the Docker container:
  `docker-compose up`
4. Open your browser and go to http://localhost:8080/pdsa_grapher/

### Option 4: Docker image from Docker Hub
Alternatively, you can run program from _Docker Hub_ image [mindaubar/grapher-app](https://hub.docker.com/r/mindaubar/grapher-app):
1. Ensure _Docker_ service is running on your computer.
2. Open a terminal application, here get the _Docker_ container and run it 
  (service exposed on 80 port, so you need bind ports):
  `docker run mindaubar/grapher-app:latest`
3. Open your browser and go to http://localhost:8080/pdsa_grapher/

**Note:** This image may not be up-to-date.


## Usage
You can select the **English interface** language at the top right corner.

The app is composed of two **tabs**: *File upload* and *Graph* visualization. Always start with the *File upload* tab.

### File upload
- After opening the link, upload at least one [required file](#required-files-for-inputs) into the respective fields:
  - On the _left_ panel, upload PDSA (in XLSX or CSV format), JSON, or DBML files that define the structure of 
    **database tables and columns**.
  - On the _right_ panel, upload the file describing the **references** (if references were found automatically 
     within JSON or DBML uploaded on the left side, a separate upload on the right is not necessary).
- Specify which **sheets** and **columns** hold the information about database; 
  at least one panel must be filled, but analysis will be most useful if both panels are filled:
  - On the _left_ panel, choose which sheet has _information on tables_ and which sheet has _information on columns_.
    - Then, pick the meanings of the sheet columns (if selected automatically, verify them).
    - Optionally, you can choose the sheet columns you want to see below the chart.
  - On the _right_ panel, choose _References_ columns that hold the names of source table and target table.
- Press **Submit** button to process input information and passes it to the _Graph_ tab.

### Graph
The *Graph* tab visualize the information that you submitted in dashboard. 
Page layout:
- The right side displays filters that define what and how to display:
  - The top bar holds instructions.
  - Set your drawing engine and layout.
    - The default **Viz** engine displays tables in the graph with their columns in rows.
      - The classic Graphviz **dot** layout is more suitable for viewing hierarchies.
      - For free table arrangement in space, we recommend Graphviz **fdp**.
    - The old Cytoscape engine is suitable if you do not need to display columns and if there are
      few tables (with many tables, the browser may freeze).
  - Select tables to graph or add list of tables to graph (comma separated).
  - Checkbox `Get neighbors` lets you display all tables that connect to your selection tables.  
- The left side displays network of your tables. You can drag tables, and double-click to see 
  more detailed information in a pop-up.
- The bottom part displays detailed information:
  - Info about columns of selected tables (usually PDSA sheet 'columns')
  - Info on displayed tables (usually PDSA sheet 'tables')

You can change selection of drawable tables using keyboard depending on which ones are selected in the chart by mouse:
- `Delete` - to remove selected tables,
- `Enter` - to keep only selected tables,
- `P` or `+` - to append selected tables (e.g. displayed neighbors).


## Updates since fork
This fork of [Lukas-Vasionis/pdsa-grapher](https://github.com/Lukas-Vasionis/pdsa-grapher)
contains bug fixes and new features, with the most important ones listed below.
See more detailed changes in [CHANGELOG.md](CHANGELOG.md) file and in
[GitHub commit log](https://github.com/embar-/pdsa-grapher/commits/master/) page.

### Fixes
- Resolved crashes when opening ([issue#23](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/23)), 
  during layout selection ([issue#15](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/15)).
- Prevented crashes after removing all nodes (tables).
- Tables with no relations were not visible ([issue#21](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/21)).

### New features
Main new features include:
- Ability to use CSV files as references, in addition to XLSX files ([issue#18](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/18)).
- Ability to import JSON (JavaScript Object Notation) and DBML (Database Markup Language) files.
- Interface language selection: Lithuanian or English, eliminating the need to run code from a language-specific branch.
- Automatic preselection of sheet names and column names in *File upload* tab 
  for standard PDSA and References files.
- The new default Viz engine for graph drawing (as an alternative to Cytoscape).
  Using the Viz engine, the ability to edit intermediate Graphviz DOT syntax.
- Automatic preselection of up to 10 tables.
- Button to draw all tables at once ([issue#17](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/17)).
- Clicking a node displays detailed information about it, including relations to non-displayed tables.
- Option to choose type neighbors: incoming, outgoing or all ([issue#14](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/14)).
- View incoming and outgoing links from active node to neighbours in different colors.
- Ability to mark columns with colors in checkboxes (e.g., for inclusion into the prototype table).
- Ability to use keyboard keys to change table selection.

## Known bugs, limitations and requested features
- Limitation: If there are tables with the same names in different schemas within the database, they will be 
  considered as the same table; to avoid confusion, either analyze tables from different schemas 
  separately or rename them (e.g., by adding the schema as a prefix).
- Limitation: You may not be able to upload excessively large files; in such cases, pressing F12 in your browser may show 
  "QuotaExceededError", "413 Request Entity Too Large", or "Failed to load resource: the server responded with status 413".
  In such cases, try working in a new browser tab, or remove unnecessary sheets and columns from the data being uploaded.
- Internal Dash Cytoscape bug: When using the Cyto engine, the pop-up about the connection may appear in the wrong place, although 
  explanations are displayed correctly when clicking on a node.
- Requested feature: The ability to edit connections between tables (often they are missing).
- Requested feature: Analyze SQL commands of views and draw their structure.
- See also other ideas in https://github.com/Lukas-Vasionis/pdsa-grapher/issues

## License
Project is distributed under MIT license, see `LICENSE` file.
