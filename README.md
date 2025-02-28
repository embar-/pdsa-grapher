# PDSA graferis

Lietuvišką pilną aprašą rasite [PERSKAITYK.md](PERSKAITYK.md) rinkmenoje.

| ![graferis viz](sample_data/biblioteka_viz.gif) | ![graferis cyto](sample_data/biblioteka_cyto.gif) |
|---------------------------------------------------|-------------------------------------------------|

# PDSA grapher

**Purpose**:
This program allows displaying and selecting database table relationships, as well as 
displaying metadata of those tables, with the added feature of interactively dragging 
the tables displayed in the graph.

**Technologies**:
Python 3, Plotly's Dash framework, Polars, Viz.js, D3.js.

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
  - [Graphic](#graphic)
- [Updates since fork](#updates-since-fork)
- [Known bugs and required features](#known-bugs-and-required-features)
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
- or two separate files (e.g., `biblioteka_pdsa.xlsx` and `biblioteka_refs.csv`):
  - PDSA **xlsx** file containing information about nodes (tables). The app expects this file to have at least two sheets:
    - One sheet defining the **tables**:
      - table names (expected in `table` column),
      - table descriptions (expected in `comment` column, optional),
      - number of table records (expected in `n_records` column, optional).
    - One sheet defining their **columns**:
      - table names (expected in `table` column),
      - column names (expected in `column` column),
      - column descriptions (expected in `comment` column, optional),
      - primary key indication (expected in `is_primary` column, optional),
      - column data types etc.
  - References **xlsx** or **csv** file containing information about edges (relations between tables). 
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
  `docker run -p 8080:80 mindaubar/grapher-app:latest`
3. Open your browser and go to http://localhost:8080/pdsa_grapher/

**Note:** This image may not be up-to-date.


## Usage
You can select the **English interface** language at the top right corner.

The app is composed of two **tabs**: *File upload* and *Graphic* visualization. Always start with the *File upload* tab.

### File upload
- After opening the link, upload the required PDSA and references files in the displayed fields.
- Specify which sheets and columns hold the information about database:
  - On the left _PDSA_ panel, choose which sheet holds information on tables and columns.
    Then, pick the columns that you want to see in the dashboard.  
  - On the right _References_ panel, choose which columns that hold the names of source table and target table.
- Press **Submit** button to process input information and passes it to the _Graphic_ tab.

### Graphic
The *Graphic* tab visualize the information that you submitted in dashboard. 
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

**Note:** The app was tested on Firefox, Chrome, Edge browsers.

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


## Known bugs and required features
- When using the Cyto engine, the pop-up about the connection may appear in the wrong place, although 
  explanations are displayed correctly when clicking on a node. This is an internal Dash Cytoscape bug.
- The ability to edit connections between tables (often they are missing).
- Analyze SQL commands of views and draw their structure.
- See also other ideas in https://github.com/Lukas-Vasionis/pdsa-grapher/issues

## License
Project is distributed under MIT license, see `LICENSE` file.
