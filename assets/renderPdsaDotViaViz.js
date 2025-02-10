/*
Graphviz DOT sintaksę atvaizduoja kaip SVG paveiksliuką, kurio mazgus galima judinti. 
Pritaikyta braižyti duombazės lentelių struktūras, kur mazgas yra HTML lentelė.
Kiti įrankiai paprastai atvaizduoja DOT kaip statišką paveiksliuką arba pritaikyti taškiniams mazgams.

Ypatybės:
* Jungties aukštis nuo mazgo centro išlaikomas pastovus net judinant mazgą, tad
  ryšių linijos visada jungia tuos pačius duombazės stulpelius (HTML eilutes).
* Linijos kaskart perpiešiamos iš naujo patobulinant Viz linijų išlenkimą bei išdėstymą 
  (tačiau nei vienas sprendimas neprilygsta kompiuteryje įdiegtos Graphviz galimybėms).

Priklausomybės:
    1. d3 iš https://d3js.org/d3.v7.min.js
    2. viz-standalone.js iš
        https://unpkg.com/@viz-js/viz@3.11.0/lib/viz-standalone.js
        arba
        https://github.com/mdaines/viz-js/releases/download/release-viz-3.11.0/viz-standalone.js

*/
/*
(c) 2025 Mindaugas B.
This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
*/

function renderPdsaDotViaViz(dot, graphDiv) {


    // const dot = textarea.value;

    Viz.instance().then(function(viz) {
        graphDiv.innerHTML = ''; // Clear the existing graph
        if (!dot) {
            console.log("Can not render graph from empty DOT code");
            return;
        }
        console.log("Rendering graph from DOT code");
        const svgString = viz.renderString(dot, { format: "svg" });
        const parser = new DOMParser();
        const svg = parser.parseFromString(svgString, "image/svg+xml").documentElement;
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        graphDiv.appendChild(svg);

        // Define arrowhead marker
        const defs = d3.select(svg).append("defs");
        defs.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -10 20 20")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 12)
            .attr("markerHeight", 12)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-10L20,0L0,10")
            .attr("fill", "black");


        // Share variable between dragstarted() and dragended() to restore original visibility
        let previousSibling

        const nodes = d3.select(svg).selectAll("g.node");

        // Set background color to white (not transparent) to be able to drag later
        nodes.each(function() {
            const node = d3.select(this);
            const bbox = node.node().getBBox();
            if (!node.select("ellipse").empty()) {
                // If "ellipse" exists, add a white "ellipse" as background
                // console.log("ellipse:", node)
                node.insert("ellipse", ":first-child")
                    .attr("cx", bbox.x + bbox.width / 2)
                    .attr("cy", bbox.y + bbox.height / 2)
                    .attr("rx", bbox.width / 2)
                    .attr("ry", bbox.height / 2)
                    .attr("fill", "white");
            } else {
                // add a white "rect" as background
                // console.log("rect:", node)
                node.insert("rect", ":first-child")
                    .attr("x", bbox.x)
                    .attr("y", bbox.y)
                    .attr("width", bbox.width)
                    .attr("height", bbox.height)
                    .attr("fill", "white");
            }
        });


        // Make nodes draggable
        nodes.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
        // console.log("Nodes:", nodes)


        // Extract node and edge data
        const nodes2 = new Map();
        const links = [];


        d3.select(svg).selectAll("g.node").each(function () {
            const node = d3.select(this);
            const id = node.select("title").text();
            nodes2.set(id, { id, node });
        });
        // console.log("Nodes2:", nodes2)

        // Ryšiai
        d3.select(svg).selectAll("g.edge").each(function () {
            const edge = d3.select(this);
            const title = edge.select("title").text();
            const [sourceId, targetId] = title.split("->").map(s => s.trim());
            const [sourceId1, sourceId2] = sourceId.split(":").map(s => s.trim());
            const [targetId1, targetId2] = targetId.split(":").map(s => s.trim());
            const sourceNode = nodes2.get(sourceId1) ? nodes2.get(sourceId1) : nodes2.get(sourceId);
            const targetNode = nodes2.get(targetId1) ? nodes2.get(targetId1) : nodes2.get(targetId);
            // console.log(title, sourceId, sourceNode, targetId, targetNode);
            if (sourceNode && targetNode) {
                // Extract coordinates from the existing path
                const pathElement = edge.select("path").node();
                const pathLength = pathElement.getTotalLength();
                const startPoint = pathElement.getPointAtLength(0);
                const endPoint = pathElement.getPointAtLength(pathLength);

                // Calculate and store the offsets
                const sourceBBox = sourceNode.node.node().getBBox();
                const sourceTransform = sourceNode.node.attr("transform");
                const sourceCoords = sourceTransform ? sourceTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const sourceLeftEdgeX = sourceCoords[0] + sourceBBox.x;
                const sourceRightEdgeX = sourceCoords[0] + sourceBBox.x + sourceBBox.width;
                const sourceOffsetY = startPoint.y - sourceCoords[1];
                const sourceY = sourceCoords[1] + sourceOffsetY;

                // Calculate the target node's bounding box edge coordinates
                const targetBBox = targetNode.node.node().getBBox();
                const targetTransform = targetNode.node.attr("transform");
                const targetCoords = targetTransform ? targetTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const targetLeftEdgeX = targetCoords[0] + targetBBox.x;
                const targetRightEdgeX = targetCoords[0] + targetBBox.x + targetBBox.width;
                const targetOffsetY = endPoint.y - targetCoords[1];
                const targetY = targetCoords[1] + targetOffsetY;

                // Determine which edge is closer for source and target
                const { sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad } = chooseEdgeX(
                    sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX
                );

                // Remove existing paths and polygons
                edge.selectAll(["path", "polygon"]).remove();

                // Add spline path with arrowhead
                const lineGenerator = d3.line()
                    .curve(d3.curveBasis)
                    .x(d => d[0])
                    .y(d => d[1]);
                const points = [
                    [sourceEdgeX, sourceY],
                    [sourceEdgeXpad, sourceY],
                    [targetEdgeXpad, targetY],
                    [targetEdgeX, targetY]
                ];

                const path = edge.append("path")
                    .attr("stroke-width", 1)
                    .attr("stroke", "black")
                    .attr("fill", "none")
                    .attr("marker-end", "url(#arrowhead)")
                    .attr("d", lineGenerator(points));

                // Append to list of all links
                links.push({
                    title,
                    source: sourceNode,
                    target: targetNode,
                    path,
                    sourceLeftEdgeX,
                    sourceRightEdgeX,
                    sourceOffsetY,
                    targetLeftEdgeX,
                    targetRightEdgeX,
                    targetOffsetY
                });
            }
        });
        // console.log("Links:", links)

        function raiseLinks() {
            // Select all edges and re-append them to move to the upper layer
            d3.selectAll("path.edge").each(function () {
                this.parentNode.appendChild(this);
            });
        }

        // Determine which edge is closer for source and target
        function chooseEdgeX(sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX) {
            let sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad;
            const pad = 20;

            if (targetRightEdgeX + pad < sourceLeftEdgeX) {
                sourceEdgeX = sourceLeftEdgeX;
                targetEdgeX = targetRightEdgeX;
                sourceEdgeXpad = sourceEdgeX - pad;
                targetEdgeXpad = targetEdgeX + pad;
            } else if (sourceRightEdgeX + pad < targetLeftEdgeX) {
                sourceEdgeX = sourceRightEdgeX;
                targetEdgeX = targetLeftEdgeX;
                sourceEdgeXpad = sourceEdgeX + pad;
                targetEdgeXpad = targetEdgeX - pad;
            } else if (Math.abs(targetLeftEdgeX - sourceLeftEdgeX) < Math.abs(targetRightEdgeX - sourceRightEdgeX)) {
                sourceEdgeX = sourceLeftEdgeX;
                targetEdgeX = targetLeftEdgeX;
                const edgeXpad = Math.min(sourceEdgeX, targetEdgeX) - pad * 2;
                sourceEdgeXpad = edgeXpad;
                targetEdgeXpad = edgeXpad;
            } else {
                sourceEdgeX = sourceRightEdgeX;
                targetEdgeX = targetRightEdgeX;
                const edgeXpad = Math.max(sourceEdgeX, targetEdgeX) + pad * 2;
                sourceEdgeXpad = edgeXpad;
                targetEdgeXpad = edgeXpad;
            }

            return { sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad };
        }

        function updateLinks() {
            links.forEach(link => {
                const sourceTransform = link.source.node.attr("transform");
                const targetTransform = link.target.node.attr("transform");

                const sourceCoords = sourceTransform ? sourceTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const targetCoords = targetTransform ? targetTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];

                const sourceLeftEdgeX = sourceCoords[0] + link.sourceLeftEdgeX;
                const sourceRightEdgeX = sourceCoords[0] + link.sourceRightEdgeX;
                const sourceY = sourceCoords[1] + link.sourceOffsetY;
                const targetLeftEdgeX = targetCoords[0] + link.targetLeftEdgeX;
                const targetRightEdgeX = targetCoords[0] + link.targetRightEdgeX;
                const targetY = targetCoords[1] + link.targetOffsetY;

                const { sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad } = chooseEdgeX(
                    sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX
                );

                const lineGenerator = d3.line()
                    .curve(d3.curveBasis)
                    .x(d => d[0])
                    .y(d => d[1]);

                const points = [
                    [sourceEdgeX, sourceY],
                    [sourceEdgeXpad, sourceY],
                    [targetEdgeXpad, targetY],
                    [targetEdgeX, targetY]
                ];

                link
                    .path.attr("d", lineGenerator(points));
            });
        }

        // Set initial positions of the links
        updateLinks();
        raiseLinks()

        function dragstarted(event, d) {
            const node = d3.select(this);
            previousSibling = node.node().previousSibling;
            node.raise().classed("active", true);
        }

        function dragged(event, d) {
            const node = d3.select(this);
            let transform = node.attr("transform");
            if (!transform) {
                transform = "translate(0,0)";
                node.attr("transform", transform);
            }
            const translate = transform.match(/translate\(([^)]+)\)/);
            const coords = translate ? translate[1].split(",").map(Number) : [0, 0];
            const newX = isNaN(coords[0]) ? 0 : coords[0] + event.dx;
            const newY = isNaN(coords[1]) ? 0 : coords[1] + event.dy;
            node.attr("transform", `translate(${newX},${newY})`);
            updateLinks();
        }

        function dragended(event, d) {
            const node = d3.select(this);
            node.classed("active", false);
            if (previousSibling) {
                previousSibling.parentNode.insertBefore(node.node(), previousSibling.nextSibling);
            } else {
                node.node().parentNode.appendChild(node.node());
            }
            updateViewBox();
        }


        const originalViewBox = svg.getAttribute("viewBox") ? svg.getAttribute("viewBox").split(" ").map(Number) : [0, 0, svg.clientWidth, svg.clientHeight];
        // console.log("originalViewBox:", originalViewBox)

        function updateViewBox() {
            const allNodes = d3.select(svg).selectAll("g.node");
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            // current_view_box = svg.getAttribute("viewBox")
            // console.log("current_view_box:", current_view_box)

            allNodes.each(function() {
                const node = d3.select(this);
                const bbox = node.node().getBBox();
                const transform = node.attr("transform");
                const coords = transform ? transform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const x = coords[0] + bbox.x;
                const y = originalViewBox[3] + coords[1] + bbox.y;
                const width = bbox.width;
                const height = bbox.height;
                pad = 30

                if (x < minX) minX = x - pad;
                if (y < minY) minY = y - pad;
                if (x + width > maxX) maxX = x + width + pad;
                if (y + height > maxY) maxY = y + height + pad;

                /*
                console.log(
                    node.select("title").text(),
                    "x:", coords[0], x,
                    "y:", coords[1], y,
                    "bbox:", bbox,
                    "viewbox:", [minX, minY, maxX, maxY]
                )
                 */
            });

            minX = Math.min(minX, originalViewBox[0]);
            minY = Math.min(minY, originalViewBox[1]);
            maxX = Math.max(maxX, originalViewBox[0] + originalViewBox[2]);
            maxY = Math.max(maxY, originalViewBox[1] + originalViewBox[3]);

            const viewBoxWidth = maxX - minX;
            const viewBoxHeight = maxY - minY;
            const viewBox = `${minX} ${minY} ${viewBoxWidth} ${viewBoxHeight}`;
            // console.log("viewBox:", viewBox);
            d3.select(svg).attr("viewBox", viewBox);
        }


        // Define zoom behavior
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let currentMouseX = 0;
        let currentMouseY = 0;

        function applyTransform() {
            svg.setAttribute("transform", `translate(${translateX}, ${translateY}) scale(${scale})`);
        }

        function zoom(event) {
            event.preventDefault();
            const factor = event.deltaY < 0 ? 1.25 : 0.8;
            const rect = graphDiv.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const point = [currentMouseX - centerX, currentMouseY - centerY];

            const dx = (point[0] - translateX) * (factor - 1);
            const dy = (point[1] - translateY) * (factor - 1);
            scale *= factor;
            translateX -= dx;
            translateY -= dy;
            applyTransform();
        }

        graphDiv.addEventListener("wheel", function(event) {
            event.preventDefault();
            zoom(event);
        });

        graphDiv.addEventListener("mousemove", function(event) {
            const rect = graphDiv.getBoundingClientRect();
            currentMouseX = event.clientX - rect.left;
            currentMouseY = event.clientY - rect.top;
        });

        // Add double-click event listener to reset zoom
        function resetZoom() {
            scale = 1;
            translateX = 0;
            translateY = 0;
            applyTransform();
        }

        graphDiv.addEventListener("dblclick", function() {
            resetZoom();
        });


    }).catch(error => {
        graphDiv.innerHTML = "<FONT COLOR=\"red\">Please check DOT syntax. <BR>" + error + "</FONT><>";
        console.error("Error rendering graph:", error);
    });
}
