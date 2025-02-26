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

// Dependencies expected to be in parent functions (e.g. via Python Dash), thus below are just references
// import * as d3 from "https://d3js.org/d3.v7.min.js";
// import * as Viz from "https://unpkg.com/@viz-js/viz@3.11.0/lib/viz-standalone.js";

function renderPdsaDotViaViz(dot, graphDivId) {
/*
Graphviz DOT syntax is rendered as an SVG image with movable nodes.
It is adapted for drawing database table structures, where a node is an HTML table.

Inputs:
- dot - DOT syntax text
- graphDivId - HTML DIV object ID
*/
    const graphDiv = document.getElementById(graphDivId);
    if (!graphDiv) {
        console.error(`Cannot find HTML DIV with id ${graphDivId}.`);
        return;
    }
    Viz.instance().then(function(viz) {
        graphDiv.innerHTML = ''; // Clear the existing graph
        if (!dot) {
            // Can not render SVG from empty DOT code"
            return;
        }
        // Rendering static SVG from DOT code via Viz
        const svgString = viz.renderString(dot, { format: "svg" });
        const parser = new DOMParser();
        const svg = parser.parseFromString(svgString, "image/svg+xml").documentElement;
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        graphDiv.appendChild(svg);
        const svgG = d3.select(svg).select("g")

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
            .attr("markerUnits", "userSpaceOnUse")
            .append("path")
            .attr("d", "M0,-10L20,0L0,10")
            .attr("fill", "black");

        // Find background - the first polygon element with fill="white" and stroke="none"
        const polygon = svg.querySelector('polygon[fill="white"][stroke="none"]');
        if (polygon) {
            polygon.remove();  // Remove background
        }

        // Remember orininal viewports
        const originalViewBox = svg.getAttribute("viewBox") ? (
            svg.getAttribute("viewBox").split(" ").map(Number)
        ) : (
            [0, 0, svg.clientWidth, svg.clientHeight]
        );
        const origBBox = svgG.node().getBBox();

        /*
        ----------------------------------------
        Mazgai
        ----------------------------------------
         */
        const nodes = d3.select(svg).selectAll("g.node");

        // Set background color to white (not transparent) to be able to drag later
        nodes.each(function() {
            const node = d3.select(this);
            const bbox = node.node().getBBox();
            if (!node.select("ellipse").empty()) {
                // If "ellipse" exists, add a white "ellipse" as background
                node.insert("ellipse", ":first-child")
                    .attr("cx", bbox.x + bbox.width / 2)
                    .attr("cy", bbox.y + bbox.height / 2)
                    .attr("rx", bbox.width / 2)
                    .attr("ry", bbox.height / 2)
                    .attr("fill", "white");
            } else {
                // add a white "rect" as background
                node.insert("rect", ":first-child")
                    .attr("x", bbox.x)
                    .attr("y", bbox.y)
                    .attr("width", bbox.width)
                    .attr("height", bbox.height)
                    .attr("fill", "white");
            }
        });


        // Extract node data and create map
        const nodes_map = new Map();
        d3.select(svg).selectAll("g.node").each(function () {
            const node = d3.select(this);
            const id = node.select("title").text();
            nodes_map.set(id, { id, node });
        });


        /*
        ----------------------------------------
        Ryšiai
        ----------------------------------------
         */
        const links = [];
        d3.select(svg).selectAll("g.edge").each(function () {
            const edge = d3.select(this);
            const title = edge.select("title").text();
            const [sourceId, targetId] = title.split("->").map(s => s.trim());
            const [sourceId1, sourceId2] = sourceId.split(":").map(s => s.trim());
            const [targetId1, targetId2] = targetId.split(":").map(s => s.trim());
            const sourceNode = nodes_map.get(sourceId1) ? nodes_map.get(sourceId1) : nodes_map.get(sourceId);
            const targetNode = nodes_map.get(targetId1) ? nodes_map.get(targetId1) : nodes_map.get(targetId);

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
                const sourceOffsetY = Math.min(Math.max(startPoint.y, sourceBBox.y), sourceBBox.y + sourceBBox.height) - sourceCoords[1];
                const sourceY = sourceCoords[1] + sourceOffsetY;

                // Calculate the target node's bounding box edge coordinates
                const targetBBox = targetNode.node.node().getBBox();
                const targetTransform = targetNode.node.attr("transform");
                const targetCoords = targetTransform ? targetTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const targetLeftEdgeX = targetCoords[0] + targetBBox.x;
                const targetRightEdgeX = targetCoords[0] + targetBBox.x + targetBBox.width;
                const targetOffsetY = Math.min(Math.max(endPoint.y, targetBBox.y), targetBBox.y + targetBBox.height) - targetCoords[1];
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
                    .attr("d", lineGenerator(points))
                    .attr("class", "edge");

                const link_data = {
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
                };
                path.datum(link_data);

                // Append to list of all links
                links.push(link_data);

                // Create an invisible path behind the visible path
                const hitPath = path.clone(true)
                    .classed("edge-hitbox", true)
                    .attr("stroke", "transparent") // Make the hitbox invisible
                    .style("stroke-width", 15) // Increase the stroke width for the hitbox
                    .style("pointer-events", "all") // Ensure the hitbox captures click events
                    .lower(); // Move the hitbox behind the visible path

                // Add the hitbox to the DOM
                path.node().parentNode.insertBefore(hitPath.node(), path.node());
            }
        });

        // Add click event listener to the hitboxes
        d3.selectAll("path.edge-hitbox").on("click", function (event, d) {
            // Prevent the SVG click event from firing
            event.stopPropagation();

            // Get the corresponding visible path
            const visiblePath = d3.select(this.nextSibling);

            // Handle the click event for the visible path. For example, you can add a class to highlight the path
            visiblePath.classed("edge-clicked", true);
        });

        function updateEdgeHitPaths() {
            // Update the invisible hitbox path to match the visible path
            d3.selectAll("path.edge-hitbox").each(function() {
                const invisiblePath = d3.select(this);
                const visiblePath = d3.select(this.nextSibling);
                invisiblePath.attr("d", visiblePath.attr("d"));
            });
        }
        updateEdgeHitPaths();

        function raiseLinks() {
            // Select all edges and re-append them to move to the upper layer
            // FIXME: Does not take visible effect
            d3.selectAll("path.edge").each(function() {
                this.parentNode.appendChild(this);
            });
        }
        raiseLinks();

        // Determine which edge is closer for source and target
        function chooseEdgeX(sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX) {
            let sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad;
            const pad = 20;
            const viewBox_SideRatio = 10
            const viewBox = svg.getAttribute("viewBox") ? (
                svg.getAttribute("viewBox").split(" ").map(Number)
            ): (
                [0, 0, svg.clientWidth, svg.clientHeight]
            );
            const viewBoxWidth = viewBox[2] - viewBox[0];
            const viewBoxSide = viewBoxWidth / viewBox_SideRatio;

            if (targetRightEdgeX + pad < sourceLeftEdgeX) {
                // Target is to the right of the source
                sourceEdgeX = sourceLeftEdgeX;
                targetEdgeX = targetRightEdgeX;
                sourceEdgeXpad = sourceEdgeX - pad;
                targetEdgeXpad = targetEdgeX + pad;
            } else if (sourceRightEdgeX + pad < targetLeftEdgeX) {
                // Source is to the right of the target
                sourceEdgeX = sourceRightEdgeX;
                targetEdgeX = targetLeftEdgeX;
                sourceEdgeXpad = sourceEdgeX + pad;
                targetEdgeXpad = targetEdgeX - pad;
            } else {
                // Check if edges are at side of the viewBox width from the left or right
                const isSourceLeftClose = sourceLeftEdgeX <= viewBox[0] + viewBoxSide;
                const isTargetLeftClose = targetLeftEdgeX <= viewBox[0] + viewBoxSide;
                const isSourceRightClose = sourceRightEdgeX >= viewBox[0] + (viewBox_SideRatio - 1) * viewBoxSide;
                const isTargetRightClose = targetRightEdgeX >= viewBox[0] + (viewBox_SideRatio - 1) * viewBoxSide;

                // If either the source or target node is close to the left or right side,
                // prioritize that side for positioning the edge. This is because sides
                // typically have more space and are less likely to be obstructed by other objects or lines.
                if (isSourceLeftClose || isTargetLeftClose) {
                    sourceEdgeX = sourceLeftEdgeX;
                    targetEdgeX = targetLeftEdgeX;
                } else if (isSourceRightClose || isTargetRightClose) {
                    sourceEdgeX = sourceRightEdgeX;
                    targetEdgeX = targetRightEdgeX;
                } else {
                    // Neither the source nor target node is close to the left or right side.
                    // Since both nodes are more centrally located, determine the closest edges based on distance
                    const leftDistance = Math.abs(targetLeftEdgeX - sourceLeftEdgeX);
                    const rightDistance = Math.abs(targetRightEdgeX - sourceRightEdgeX);

                    if (leftDistance < rightDistance) {
                        sourceEdgeX = sourceLeftEdgeX;
                        targetEdgeX = targetLeftEdgeX;
                    } else {
                        sourceEdgeX = sourceRightEdgeX;
                        targetEdgeX = targetRightEdgeX;
                    }
                }

                // Calculate padded coordinates with double padding if necessary
                const edgeXpad = (sourceEdgeX === sourceLeftEdgeX && targetEdgeX === targetLeftEdgeX)
                    ? Math.min(sourceEdgeX, targetEdgeX) - pad * 2
                    : Math.max(sourceEdgeX, targetEdgeX) + pad * 2;

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

                link.path.attr("d", lineGenerator(points))
            });
            updateEdgeHitPaths();
        }


        /*
        ----------------------------------------
        Spustelėjus mazgą
        ----------------------------------------
         */

        function getNodeAbsolutePosition(selectedNode) {
            // Return absolute node coordinates in screen: left x, top y, width and height.
            // Note: Node is in svg.g and thus node coordinates is relative to svg.g; svg.g coordinates is relative to svg.

            // Get SVG coordinates
            const svgViewBox = svg.getAttribute("viewBox") ? svg.getAttribute("viewBox").split(" ").map(Number) : [0, 0, svg.clientWidth, svg.clientHeight];
            const svgRect = svg.getBoundingClientRect();

            // Get SVG.g coordinates
            const gBBox = svgG.node().getBBox();
            // Get the transformation matrix of the "g" element
            const gTransformMatrix = svgG.node().getCTM();
            // Extract the scale factors from the transformation matrix. Usually scaleX == scaleY
            const scaleX = gTransformMatrix.a;
            const scaleY = gTransformMatrix.d;

            // Get selected node coordinates
            const nodeBBox = selectedNode.node().getBBox();
            const nodeTransform = selectedNode.attr("transform");
            const nodeCoords = nodeTransform ? nodeTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];

            // Calculate the absolute left X coordinate // Kairiojo krašto X koordinatė
            const svgLeftX = svgRect.left + window.scrollX; // left of SVG with compensated webpage scrolling right
            const gLeftX = ( svgRect.width - gBBox.width * scaleX ) / 2;
            const nodeLeftInternalX = nodeCoords[0] + nodeBBox.x - gBBox.x;
            const nodeLeftX = svgLeftX + gLeftX + nodeLeftInternalX * scaleX;
            // const viewBoxShiftX = // FIXME: look deeper for more accurate adjustment

            // Calculate the absolute top Y coordinate // Viršutinio krašto Y koordinatė
            const svgTopY = svgRect.top + window.scrollY; // top of SVG with compensated webpage scrolling down
            const gTopY =  ( svgRect.height - gBBox.height * scaleY) / 2; // top of SVG root "g" object, with few pixel error
            const viewBoxShiftY = originalViewBox[3] - svgViewBox[1] + origBBox.y + origBBox.height;  // FIXME: look deeper for more accurate adjustment
            const nodeTopInternalY =  nodeCoords[1] + nodeBBox.y;
            const nodeTopY = svgTopY + gTopY + (viewBoxShiftY + nodeTopInternalY) * scaleY;

            //const svgBotY = svgRect.bottom + window.scrollY; // bottom of SVG with compensated webpage scrolling down
            //const gBotY = - ( svgRect.height - gBBox.height * scaleY) / 2; // bottom of SVG root "g" object

            // Dydis
            const nodeWidth = nodeBBox.width  * scaleX;  // plotis ekrane
            const nodeHeight = nodeBBox.height * scaleY;  // aukštis ekrane
            return {x: nodeLeftX, y: nodeTopY, width: nodeWidth, height: nodeHeight};
        }

        // Add an event listener to the nodes that will highlight the connected paths when a node is clicked
        d3.select(svg).selectAll("g.node").on("click", function(event, d) {
            // Prevent the SVG click event from firing
            event.stopPropagation();

            // Get the clicked node's data
            const node = d3.select(this);
            const clickedNodeId = node.select("title").text();

            // Check if the Ctrl key is pressed
            const isCtrlPressed = event.ctrlKey || event.metaKey;

            if (isCtrlPressed) {
                // Toggle the "node-clicked" class on the clicked node
                node.classed("node-clicked", !node.classed("node-clicked"));
            } else {
                // Set "node-clicked" only to the clicked node
                d3.select(svg).selectAll("g.node").classed("node-clicked", false);
                node.classed("node-clicked", true);
            }

            // Trigger a custom event to notify Dash without interfering with regular click events
            const customEvent = new CustomEvent("nodeClicked", {
                detail: {
                    clickedNodeId: clickedNodeId,
                    doubleClick: false,
                    nodePosition: getNodeAbsolutePosition(node)
                },
                bubbles: true
            });
            graphDiv.dispatchEvent(customEvent);

            // Find connected paths
            d3.selectAll("path.edge:not(.edge-hitbox)").each(function() {
                const path = d3.select(this);
                const pathData = path.datum();
                // Check if the path is connected to the clicked node
                const isSource = pathData.source.id === clickedNodeId;
                const isTarget = pathData.target.id === clickedNodeId;
                // Highlight connected paths
                path.classed("edge-source-neighbor", isSource);
                path.classed("edge-target-neighbor", isTarget);
            });
        });

        function dispatchNoNodeClickedEvent() {
            // Trigger a custom event to notify Dash that no node is clicked without interfering with regular click events
            const customEvent = new CustomEvent("nodeClicked", {
                detail: { clickedNodeId: null, doubleClick: false, nodeCoord: null},
                bubbles: true
            });
            graphDiv.dispatchEvent(customEvent);
        }

        // Add click event listener to SVG container for empty area clicks
        d3.select(graphDiv).on("click", function(event) {
            if (!event.target.closest("g.node")) {
                // Remove "node-clicked" from all nodes
                d3.select(svg).selectAll("g.node").classed("node-clicked", false);

                // Reset all regular paths
                d3.selectAll("path.edge:not(.edge-hitbox)")
                    .classed("edge-clicked", false)
                    .classed("edge-source-neighbor", false)
                    .classed("edge-target-neighbor", false);

                dispatchNoNodeClickedEvent();
            }
        });


        /*
        ----------------------------------------
        Pavienių mazgų pertempimas
        ----------------------------------------
         */

        // Share variables between dragstarted() and dragended() to restore original visibility
        let previousSibling
        let selectedNodes

        function dragstarted(event) {
            const node = d3.select(this);
            previousSibling = node.node().previousSibling;
            node.raise().classed("active", true);

            selectedNodes = d3.select(svg).selectAll(".node-clicked").nodes();
            if (!selectedNodes || !node.classed("node-clicked")) {
                selectedNodes = [node.node()];
                dispatchNoNodeClickedEvent();
            }
        }

        function dragged(event, d) {
            selectedNodes.forEach(node => {
                const d3Node = d3.select(node);
                let transform = d3Node.attr("transform");
                if (!transform) {
                    transform = "translate(0,0)";
                    d3Node.attr("transform", transform);
                }
                const translate = transform.match(/translate\(([^)]+)\)/);
                const coords = translate ? translate[1].split(",").map(Number) : [0, 0];
                const newX = isNaN(coords[0]) ? 0 : coords[0] + event.dx;
                const newY = isNaN(coords[1]) ? 0 : coords[1] + event.dy;
                d3Node.attr("transform", `translate(${newX},${newY})`);
            });

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

        // Make nodes draggable
        nodes.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));


        /*
        ----------------------------------------
        Matomos srities atnaujinimas po mazgų pertempimo
        ----------------------------------------
         */

        function updateViewBox() {
            const allElements = d3.selectAll("g.node, path.edge");
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

            allElements.each(function() {
                const elem = d3.select(this);
                const bbox = elem.node().getBBox();
                const transform = elem.attr("transform");
                const coords = transform ? transform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number) : [0, 0];
                const x = coords[0] + bbox.x;
                const y = originalViewBox[3] + coords[1] + bbox.y;
                const width = bbox.width;
                const height = bbox.height;
                const pad = 20

                minX = Math.min(x - pad, minX);
                minY = Math.min(y - pad, minY);
                maxX = Math.max(x + width + pad, maxX);
                maxY = Math.max(y + height + pad, maxY);
            });

            const viewBoxWidth = maxX - minX;
            const viewBoxHeight = maxY - minY;
            const viewBox = `${minX} ${minY} ${viewBoxWidth} ${viewBoxHeight}`;
            d3.select(svg).attr("viewBox", viewBox);

            dispatchNoNodeClickedEvent();
        }
        // Pradžioje pakeistos linijos galėjo išeiti už pradinių ribų, tad atnaujinti ribas
        updateViewBox();


        /*
        ----------------------------------------
        Priartinimas bei atitolinimas
        ----------------------------------------
         */

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

        graphDiv.addEventListener("dblclick", function(event) {
            // If the double-click target is a node, do not reset zoom
            const closest_node = event.target.closest(".node")
            if (closest_node) {
                // Trigger a custom event to notify Dash without interfering with regular click events
                const clickedNode = d3.select(closest_node)
                const clickedNodeId = clickedNode.select("title").text();
                const customEvent = new CustomEvent("nodeClicked", {
                    detail: {
                        clickedNodeId: clickedNodeId,
                        doubleClick: true,
                        nodePosition: getNodeAbsolutePosition(clickedNode)
                    },
                    bubbles: true
                });
                graphDiv.dispatchEvent(customEvent);
                return;
            }
            resetZoom();
        });


        /*
        ----------------------------------------
        Viso grafiko pertempimas
        ----------------------------------------
         */

        // Add panning functionality
        let isPanning = false;
        let startX = 0;
        let startY = 0;
        let panX = 0;
        let panY = 0;

        graphDiv.addEventListener("mousedown", (e) => {
            isPanning = true;
            startX = e.pageX;
            startY = e.pageY;
            graphDiv.style.cursor = "grabbing"; // Change cursor to grabbing
        });

        graphDiv.addEventListener("mouseleave", () => {
            isPanning = false;
            graphDiv.style.cursor = "auto";
        });

        graphDiv.addEventListener("mouseup", () => {
            isPanning = false;
            graphDiv.style.cursor = "auto";
        });

        graphDiv.addEventListener("mousemove", (e) => {
            if (!isPanning) return;
            e.preventDefault();
            const x = e.pageX;
            const y = e.pageY;
            const walkX = x - startX;
            const walkY = y - startY;
            panX += walkX;
            panY += walkY;
            translateX += walkX;
            translateY += walkY;
            applyTransform();
            startX = x;
            startY = y;
        });

    }).catch(error => {
        graphDiv.innerHTML = "<FONT COLOR=\"red\">Please check DOT syntax. <BR>" + error + "</FONT><>";
        console.error("Error rendering graph:", error);
    });
}
