import dash_ag_grid as dag
from dash import Dash, html, dcc
import pandas as pd


class ag_tbl_defs:
    def __init__(self, columnDefs, defaultColDef):
        self.columnDefs = [
            {"field": "athlete"},
            {
                "field": "country",
                "filterParams": {
                    "filterOptions": ["contains", "startsWith", "endsWith"],
                    "defaultOption": "startsWith",
                },
            },
            {
                "field": "age",
                "filter": "agNumberColumnFilter",
                "filterParams": {
                    "filterPlaceholder": "Age...",
                    "alwaysShowBothConditions": True,
                    "defaultJoinOperator": "OR",
                },
                "maxWidth": 100,
            },
        ]
        defaultColDef = {
            "flex": 1,
            "minWidth": 150,
            "filter": True,
        }

def make_ag_grid(df, ag_tbl_defs):
    dag.AgGrid(
                 id="filter-options-example-2",
                rowData=df.to_dict("records"),
                columnDefs=ag_tbl_defs.columnDefs,
                columnSize="sizeToFit",
                defaultColDef=ag_tbl_defs.defaultColDef,
                className="header-style-on-filter ag-theme-alpine",
            ),
