/*
Funkcija, valdanti Python Dash ir renderPdsaDotViaViz.js sąveiką.
Pastaroji renderPdsaDotViaViz.js f-ja Graphviz DOT sintaksę atvaizduoja kaip SVG paveiksliuką, kurio mazgus galima judinti.


Priklausomybės (jas galite sudėti "assets" kataloge):
    1. d3 iš https://d3js.org/d3.v7.min.js
    2. viz-standalone.js iš
        https://unpkg.com/@viz-js/viz@3.11.0/lib/viz-standalone.js
        arba
        https://github.com/mdaines/viz-js/releases/download/release-viz-3.11.0/viz-standalone.js
    3. renderPdsaDotViaViz.js


Python Dash programoje įterpkite:
app.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='runRenderFunction'),
    Input("graphviz-dot", "value"),  # Graphviz DOT sintaksė kaip tekstas
)
*/
/*
(c) 2025 Mindaugas B.
This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.

*/

window.onload = function() {
        // Ensure dash_clientside.callbacks is initialized
        window.dash_clientside = Object.assign({}, window.dash_clientside, {clientside: {}});

        window.dash_clientside.clientside.runRenderFunction = function(dot) {
            const chartId = 'graphviz-chart'
            const chart = document.getElementById(chartId)
            if (chart) {
                // Create SVG and interact with its elements
                renderPdsaDotViaViz(dot, chartId);

                // Add event listener to know when a node is clicked
                chart.addEventListener('nodeClicked', function (event) {
                    const storeData = {
                        type: 'nodeClicked',
                        id: event.detail.clickedNodeId
                    };
                    dash_clientside.set_props('viz-clicked-node-store', { data: storeData });
                });
            }
            return window.dash_clientside.no_update;
        };

        window.dash_clientside.clientside.saveSVG = function() {
            // Save SVG to disk
            const svgElement = document.querySelector('#graphviz-chart svg');
            if (svgElement) {
                // Get the current date and time for download name
                const now = new Date();
                const formattedDateTime = now.toISOString().replace(/T/, '_').replace(/:/g, '').split('.')[0];

                // Extract SVG content
                const svgData = new XMLSerializer().serializeToString(svgElement);
                const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });

                // Prepare for download
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `pdsa-grapher viz ${formattedDateTime}.svg`;
                document.body.appendChild(a);

                // Download
                a.click();

                // Clean-up
                document.body.removeChild(a);
            }
        };

};
