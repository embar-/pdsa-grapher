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

    // remember currently selected nodes to restore selection after re-creation
    const oldSelectedNodes = d3.select(graphDiv).selectAll(".node-clicked").nodes()
    const oldSelectedNodesNames = oldSelectedNodes.map(node => d3.select(node).select("title").text());

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

        // Function to create an arrowhead marker
        function createArrowheadMarker(defs, id, viewBox, refX, d) {
            defs.append("marker")
                .attr("id", id)
                .attr("viewBox", viewBox)
                .attr("refX", refX)
                .attr("refY", 0)
                .attr("markerWidth", 12)
                .attr("markerHeight", 12)
                .attr("orient", "auto")
                .attr("markerUnits", "userSpaceOnUse")
                .append("path")
                .attr("d", d)
                .attr("fill", "black");
        }
        // Define arrowhead markers
        const defs = d3.select(svg).append("defs");
        createArrowheadMarker(defs, "arrowhead-start", "20 -10 20 20", 20, "M40,-10L20,0L40,10");
        createArrowheadMarker(defs, "arrowhead-end", "0 -10 20 20", 20, "M0,-10L20,0L0,10");

        // Find background - the first polygon element with fill="white" and stroke="none"
        const polygon = svg.querySelector('polygon[fill="white"][stroke="none"]');
        if (polygon) {
            polygon.remove();  // Remove background
        }

        // Remember orininal viewports
        const originalViewBox = svg.getAttribute("viewBox")
            ? svg.getAttribute("viewBox").split(" ").map(Number)
            : [0, 0, svg.clientWidth, svg.clientHeight];

        // Create layers for edge hit using D3
        const hitboxLayer = svgG.insert("g", ":first-child").attr("class", "hitbox-layer");  // big invisible edges to hit and see tooltips

        /*
        ----------------------------------------
        Mazgai
        ----------------------------------------
         */
        const nodes = d3.select(svg).selectAll("g.node");

        const nodes_map = new Map();
        nodes.each(function () {
            // Extract node data and create map
            const node = d3.select(this);
            const id = node.select("title").text();
            nodes_map.set(id, { id, node });

            // restore selection
            if (id && oldSelectedNodesNames.includes(id)) {
                node.classed("node-clicked", true);
            }

            // Set background color to white (not transparent) to be able to drag later
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

        /*
        ----------------------------------------
        Ryšiai
        ----------------------------------------
         */
        const links = [];
        const edges = d3.select(svg).selectAll("g.edge");
        edges.each(function () {
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
                const sourceCoords = sourceTransform
                    ? sourceTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                    : [0, 0];
                const sourceLeftEdgeX = sourceCoords[0] + sourceBBox.x;
                const sourceRightEdgeX = sourceCoords[0] + sourceBBox.x + sourceBBox.width;
                const sourceOffsetY = Math.min(Math.max(startPoint.y, sourceBBox.y), sourceBBox.y + sourceBBox.height) - sourceCoords[1];
                const sourceY = sourceCoords[1] + sourceOffsetY;

                // Calculate the target node's bounding box edge coordinates
                const targetBBox = targetNode.node.node().getBBox();
                const targetTransform = targetNode.node.attr("transform");
                const targetCoords = targetTransform
                    ? targetTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                    : [0, 0];
                const targetLeftEdgeX = targetCoords[0] + targetBBox.x;
                const targetRightEdgeX = targetCoords[0] + targetBBox.x + targetBBox.width;
                const targetOffsetY = Math.min(Math.max(endPoint.y, targetBBox.y), targetBBox.y + targetBBox.height) - targetCoords[1];
                const targetY = targetCoords[1] + targetOffsetY;

                // Determine which edge is closer for source and target
                const { sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad } = chooseEdgeX(
                    sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX
                );

                // Find position of existing arrows
                let hasMarkerStart = false
                let hasMarkerEnd = false
                const distance = (p1, p2) => Math.sqrt(Math.pow(p1[0] - p2[0], 2) + Math.pow(p1[1] - p2[1], 2));
                const polygonElements = edge.selectAll("polygon").nodes();
                polygonElements.forEach(polygon => {
                    // Determine the position of each polygon
                    const polygonPoints = polygon.getAttribute("points").split(/[ ,]+/).map(Number);
                    const polygonCenter = [
                        polygonPoints.reduce(
                            (sum, val, idx) => idx % 2 === 0 ? sum + val : sum, 0
                        ) / (polygonPoints.length / 2),
                        polygonPoints.reduce(
                            (sum, val, idx) => idx % 2 !== 0 ? sum + val : sum, 0
                        ) / (polygonPoints.length / 2)
                    ];
                    const distToStart = distance(polygonCenter, [startPoint.x, startPoint.y]);
                    const distToEnd = distance(polygonCenter, [endPoint.x, endPoint.y]);
                    if (distToStart < distToEnd) {
                        hasMarkerStart = true;  // Polygon is at the start
                    } else {
                        hasMarkerEnd = true;  // Polygon is at the end
                    }
                });

                // Remove existing paths and polygons
                edge.selectAll(["path", "polygon"]).remove();

                // Copy container with title needed for tooltips
                const hitEdge = edge.clone(true)

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
                    .attr("d", lineGenerator(points))
                    .attr("class", "edge");
                if (hasMarkerStart) {
                    path.attr("marker-start", "url(#arrowhead-start)");
                }
                if (hasMarkerEnd) {
                    path.attr("marker-end", "url(#arrowhead-end)");
                }

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
                    .datum({ title, parentEdge: path }); // Store the parent edge
                hitEdge.node().appendChild(hitPath.node());
                hitboxLayer.node().appendChild(hitEdge.node());  // Move the entire edge group to the hitboxLayer

            }
        });

        // Add click event listener to the hitboxes
        d3.selectAll("path.edge-hitbox").on("click", function (event, d) {
            event.stopPropagation();  // Prevent the SVG click event from firing
            const visiblePath = d3.select(this).datum().parentEdge;  // Get the corresponding visible path

            // Handle the click event for the visible path. For example, you can add a class to highlight the path
            visiblePath.classed("edge-clicked", true);
        });

        function updateEdgeHitPaths() {
            // Update the invisible hitbox path to match the visible path
            d3.selectAll("path.edge-hitbox").each(function() {
                const invisiblePath = d3.select(this);
                const visiblePath = invisiblePath.datum().parentEdge;  // Get the corresponding visible path
                invisiblePath.attr("d", visiblePath.attr("d"));
            });
        }
        updateEdgeHitPaths();


        // Determine which edge is closer for source and target
        function chooseEdgeX(sourceLeftEdgeX, sourceRightEdgeX, targetLeftEdgeX, targetRightEdgeX) {
            let sourceEdgeX, targetEdgeX, sourceEdgeXpad, targetEdgeXpad;
            const pad = 20;
            const viewBox_SideRatio = 10
            const viewBox = svg.getAttribute("viewBox")
                ? svg.getAttribute("viewBox").split(" ").map(Number)
                : [0, 0, svg.clientWidth, svg.clientHeight];
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

                const sourceCoords = sourceTransform
                    ? sourceTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                    : [0, 0];
                const targetCoords = targetTransform
                    ? targetTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                    : [0, 0];

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
        Spustelėjus tuščią vietą grafike
        ----------------------------------------
         */

        // Share variables between graphClick() and nodeDragStartOrClick() to restore original visibility
        let selectedNodes

        function getSelectedNodeNames() {
            const allSelectedNodes = d3.select(svg).selectAll(".node-clicked").nodes()
            return allSelectedNodes.map(node => d3.select(node).select("title").text());
        }

        function dispatchNoNodeClickedEvent() {
            // Trigger a custom event to notify Dash that no node is clicked without interfering with regular click events
            // Don't confuse with dispatchNodeClickedEvent() function (without "No" in middle of name)!
            const customEvent = new CustomEvent("nodeClicked", {
                detail: {
                    clickedNodeId: null,
                    doubleClick: false,
                    nodeCoord: null,
                    selectedNodes: getSelectedNodeNames(),
                },
                bubbles: true
            });
            graphDiv.dispatchEvent(customEvent);
        }

        // Add click event listener to SVG container for empty area clicks
        function graphClick(event) {
            const closest_node = event.target.closest("g.node")
            if (closest_node) {
                const isCtrlPressed = event.ctrlKey || event.metaKey;  // Check if the Ctrl key is pressed
                if (isCtrlPressed) {
                    // Remove "node-clicked-twice" from all nodes
                    nodes.classed("node-clicked-twice", false);
                    // Toggle the "node-clicked" class on the clicked node
                    const node = d3.select(closest_node);
                    dispatchNodeClickedEvent(node);  // notify about node clicked
                    node.classed("node-clicked", !node.classed("node-clicked"));
                    if (node.classed("node-clicked")) {
                        highlightConnectedEdges(node);  // highlight the connected paths when a node is clicked
                    }
                }
            } else {
                // Remove "node-clicked" and "node-clicked-twice" from all nodes
                nodes.classed("node-clicked", false);
                nodes.classed("node-clicked-twice", false);

                // Reset all regular paths
                d3.selectAll("path.edge:not(.edge-hitbox)")
                    .classed("edge-clicked", false)
                    .classed("edge-source-neighbor", false)
                    .classed("edge-target-neighbor", false);

                dispatchNoNodeClickedEvent();
            }
        }
        d3.select(graphDiv).on("click", graphClick);

        /*
        ----------------------------------------
        Pavienių mazgų paspaudimas ir pertempimas
        ----------------------------------------
         */

        // Share variables between nodeDragStartOrClick() and nodeDragMove() to restore original visibility
        let previousSibling
        let nodeMoved = false;

        function getNodeAbsolutePosition(selectedNode) {
            // Return absolute node coordinates in screen: left x, top y, width and height.
            // Note: Node is in svg.g and thus node coordinates is relative to svg.g; svg.g coordinates is relative to svg.
            // This function tested and works with Firefox 135, Chrome 133, Edge 133

            // Get SVG coordinates
            const svgViewBox = svg.getAttribute("viewBox")
                ? svg.getAttribute("viewBox").split(" ").map(Number)
                : [0, 0, svg.clientWidth, svg.clientHeight];
            const svgRect = svg.getBoundingClientRect();

            // Get the transformation matrix of the SVG "g" element
            const gTransformMatrix = svgG.node().getScreenCTM();
            // Extract the scale factors from the transformation matrix. Usually scaleX == scaleY
            const scaleX = gTransformMatrix.a;
            const scaleY = gTransformMatrix.d;

            // Get selected node coordinates
            const nodeBBox = selectedNode.node().getBBox();
            const nodeTransform = selectedNode.attr("transform");
            const nodeCoords = nodeTransform
                ? nodeTransform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                : [0, 0];

            // Calculate the absolute left X coordinate // Kairiojo krašto X koordinatė
            const svgLeftX = svgRect.left + window.scrollX; // left of SVG with compensated webpage scrolling right
            const viewBoxLeftX = ( svgRect.width - svgViewBox[2] * scaleX ) / 2;  // distance between svgLeftX and viewport left side
            const viewBoxShiftX = 0 - svgViewBox[0];
            const nodeLeftInternalX = nodeCoords[0] + nodeBBox.x; // node X coordinate within viewport
            const nodeLeftX = svgLeftX + viewBoxLeftX + (viewBoxShiftX + nodeLeftInternalX) * scaleX;

            // Calculate the absolute top Y coordinate // Viršutinio krašto Y koordinatė
            const svgTopY = svgRect.top + window.scrollY; // top of SVG with compensated webpage scrolling down  // geras tiek FF, tiek Chrome
            const viewBoxTopY =  ( svgRect.height - svgViewBox[3] * scaleY) / 2;  // distanec between svgTopY and viewport top
            const viewBoxShiftY = originalViewBox[3] - svgViewBox[1];
            const nodeTopInternalY =  nodeCoords[1] + nodeBBox.y;  // node Y coordinate within viewport
            const nodeTopY = svgTopY + viewBoxTopY + (viewBoxShiftY + nodeTopInternalY) * scaleY;

            // Size
            const nodeWidth = nodeBBox.width  * scaleX;  // plotis ekrane
            const nodeHeight = nodeBBox.height * scaleY;  // aukštis ekrane

            return {x: nodeLeftX, y: nodeTopY, width: nodeWidth, height: nodeHeight};
        }

        function dispatchNodeClickedEvent(node) {
            // Trigger a custom event to notify Dash without interfering with regular click events
            // Don't confuse with dispatchNoNodeClickedEvent() function (with "No" in middle of name)!
            const customEvent = new CustomEvent("nodeClicked", {
                detail: {
                    clickedNodeId: node.select("title").text(),
                    doubleClick: node.classed("node-clicked-twice"),
                    nodePosition: getNodeAbsolutePosition(node),
                    selectedNodes: getSelectedNodeNames()
                },
                bubbles: true
            });
            graphDiv.dispatchEvent(customEvent);
        }

        function nodeDragStartOrClick(event, d) {
            // This is one function for both code click ar start to drag, because Chrome (and its deviravives like Edge)
            // does not differentiate between them at pressing node, though Firefox can differentiate a bit better.
            // Note: if you press Ctrl, this function will not be called, instead graphClick() is called
            nodeMoved = false;

            // Get the clicked node's data
            const node = d3.select(this);
            const isClickedAgain = (node.classed("node-clicked"))

            // Visibility
            previousSibling = node.node().previousSibling;  // Remember elements order for overlaping.
            node.raise().classed("active", true);  // Move above any other element

            // Nodes to drag
            selectedNodes = d3.select(svg).selectAll(".node-clicked").nodes();
            if (!selectedNodes || !isClickedAgain) {
                // Even if we have selected other nodes, but active node clicked just now, move only active one
                selectedNodes = [node.node()];
            }

            // Highlight the connected paths when a node is clicked
            highlightConnectedEdges(node);
        }

        // Highlight the connected paths
        function highlightConnectedEdges(node) {
            const clickedNodeId = node.select("title").text();
            // Find connected paths
            const connectedEdges = d3.selectAll("path.edge:not(.edge-hitbox)");
            if (connectedEdges) {
                connectedEdges.each(function() {
                    const path = d3.select(this);
                    const pathData = path.datum();
                    // Check if the path is connected to the clicked node
                    const isSource = pathData.source.id === clickedNodeId;
                    const isTarget = pathData.target.id === clickedNodeId;
                    // Highlight connected paths
                    path.classed("edge-source-neighbor", isSource);
                    path.classed("edge-target-neighbor", isTarget);
                })
            };
        }

        function nodeDragMove(event, d) {
            // When sharing the screen via MS Teams and clicking on a node, the Chrome/Edge browsers (but not Firefox)
            // interpreted it as a drag action, thereby blocking the simple mouse click release actions.
            // Therefore, it is necessary to check whether event.dx and event.dy are indeed not zeros.
            if (event.dx || event.dy) {
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
                    if (!nodeMoved) {
                        nodeMoved = true;
                        // notify, that this is not single or double click; e.g. it could help could remove tooltip
                        dispatchNoNodeClickedEvent();
                    }
                });

                updateLinks();

                // updateViewBox();  // updating visible area may be less responsive or slower, too much floating and undesired acceleration
            }
        }

        function nodeDragEnd(event, d) {
            const node = d3.select(this);
            node.classed("active", false);
            if (previousSibling) {
                previousSibling.parentNode.insertBefore(node.node(), previousSibling.nextSibling);
            } else {
                node.node().parentNode.appendChild(node.node());
            }

            if (nodeMoved) {
                // node changed position
                updateViewBox();  // Update viewport
            } else {
                // node did not change position, it was just clicked and released
                const isNodeDoubleClicked = (
                    node.classed("node-clicked") && !node.classed("node-clicked-twice")
                    )
                // Remove "node-clicked" and "node-clicked-twice" from all nodes
                nodes.classed("node-clicked", false);
                nodes.classed("node-clicked-twice", false);
                node.classed("node-clicked-twice", isNodeDoubleClicked);  // double-clicked status
                // Trigger a custom event to notify Dash without interfering with regular click events
                dispatchNodeClickedEvent(node);
                // Set "node-clicked" only to the clicked node
                node.classed("node-clicked", true);
            }
        }

        // Make nodes draggable
        nodes.call(d3.drag()
            // Chrome (not Firefox) needs { passive: true }: otherwise sometimes may lag and show warning:
            // [Violation] Added non-passive event listener to a scroll-blocking 'touchstart' event.
            // Consider marking event handler as 'passive' to make the page more responsive.
            .on("start", nodeDragStartOrClick, { passive: true })
            .on("drag", nodeDragMove, { passive: true })
            .on("end", nodeDragEnd));


        /*
        ----------------------------------------
        Mazguose esančių checkbox nuspaudimas
        ----------------------------------------
         */

        // Select all text elements containing the checkbox character
        const checkboxSymbols0 = ["⬜", "🔲", "☐"];
        const checkboxSymbols1 = ["✅", "☑️", "☑", "🗹", "🟨", "🟩", "🟥", "🟦"];
        d3.selectAll("text").each(function() {
            const textElement = d3.select(this);
            if (checkboxSymbols0.includes(textElement.text())) {
                textElement.attr("class", "checkbox checkbox-unchecked");
            } else if (checkboxSymbols1.includes(textElement.text())) {
                textElement.attr("class", "checkbox checkbox-checked");
            }
        })
        // Function to toggle the checkbox state
        function toggleCheckbox() {
            event.stopImmediatePropagation(); // Stop the event from propagating
            const checkbox = d3.select(this);
            if (checkboxSymbols0.includes(this.textContent)) {
                // Change to checked checkbox
                this.textContent = "🟩";
                checkbox.attr("class", "checkbox checkbox-checked");
            } else if (this.textContent === "🟩") {
                // Change to checked checkbox color
                this.textContent = "🟥";
            } else if (this.textContent === "🟥") {
                // Change to checked checkbox color
                this.textContent = "🟨";
            } else {
                // Change back to unchecked checkbox
                this.textContent = "⬜";
                checkbox.attr("class", "checkbox checkbox-unchecked");
            }

            // dispatch event
            const parent = checkbox.node().parentElement;
            const title_attr = parent.attributes["xlink:title"];
            if (title_attr) {
                const customEvent = new CustomEvent("checkboxClicked", {
                    detail: {
                        clickedCheckboxId: title_attr.value,
                        clickedCheckboxValue: (checkboxSymbols1.includes(this.textContent)),
                        clickedCheckboxSymbol: this.textContent,
                        parentPosition: getNodeAbsolutePosition(d3.select(parent))
                    },
                    bubbles: true
                });
                graphDiv.dispatchEvent(customEvent);
            }
        }
        d3.selectAll(".checkbox")
            .style("pointer-events", "all")  // Ensure the hitbox captures click events
            .on("mousedown", toggleCheckbox);  // .on("click", ...) will work in Firefox, but not work in Chrome


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
                const coords = transform
                    ? transform.match(/translate\(([^)]+)\)/)[1].split(",").map(Number)
                    : [0, 0];
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
        let translateX = 0;  // will update in resetZoom() and zoom()
        let translateY = 0;
        let currentMouseX = 0;  // will update in graphMouseMove()
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

        graphDiv.addEventListener(
            // Mark as non-passive because we call preventDefault() inside zoom(); otherwise we would get error
            // However, marking event handler as 'passive' could make page more responsive.
            "wheel", zoom, { passive: false }
        );

        // Add double-click event listener to reset zoom
        function resetZoom() {
            scale = 1;
            translateX = 0;
            translateY = 0;
            applyTransform();
        }

        function graphDoubleClick(event) {
            // If the double-click target is a node, do not reset zoom
            const closest_node = event.target.closest("g.node")
            if (!closest_node) {
                resetZoom();
            }
        }
        graphDiv.addEventListener("dblclick", graphDoubleClick, { passive: true });


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
        }, { passive: true });

        graphDiv.addEventListener("mouseleave", () => {
            isPanning = false;
            graphDiv.style.cursor = "auto";
        }, { passive: true });

        graphDiv.addEventListener("mouseup", () => {
            isPanning = false;
            graphDiv.style.cursor = "auto";
        });

        function graphMouseMove(event) {
            const rect = graphDiv.getBoundingClientRect();
            currentMouseX = event.clientX - rect.left;
            currentMouseY = event.clientY - rect.top;
            if (!isPanning) return;

            // move entire graph
            // event.preventDefault();
            const x = event.pageX;
            const y = event.pageY;
            const walkX = x - startX;
            const walkY = y - startY;
            panX += walkX;
            panY += walkY;
            translateX += walkX;
            translateY += walkY;
            applyTransform();
            startX = x;
            startY = y;
        }
        graphDiv.addEventListener("mousemove", graphMouseMove, { passive: true });


        /*
        ----------------------------------------
        Klaviatūros paspaudimai
        ----------------------------------------
         */

        function dispatchKeyboardEvent(event) {
            // Trigger event to notify Dash about a key press (Python Dash does not support listening itself)
            const keydownEvent = new CustomEvent("keyPress", {
                detail: {
                    key: event.key,  // name of the pressed key
                    // modifier keys
                    ctrlKey: event.ctrlKey,
                    shiftKey: event.shiftKey,
                    altKey: event.altKey,
                    metaKey: event.metaKey
                },
                bubbles: true
            });
            graphDiv.dispatchEvent(keydownEvent);
        }

       document.addEventListener('keydown', function(event) {
            // listen for keypress events on the entire document but ignore them when the focus is on input fields
            if (document.activeElement === document.body) {
                dispatchKeyboardEvent(event);
            }
        }, { passive: true });

    }).catch(error => {
        graphDiv.innerHTML = "<FONT COLOR=\"red\">Please check DOT syntax. <BR>" + error + "</FONT><>";
        console.error("Error rendering graph:", error);
    });
}
