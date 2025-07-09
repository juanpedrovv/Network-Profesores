function forceHull(groups) {
    const strength = 1.2; // Increased strength significantly

    function force(alpha) {
        for (const node of force.nodes) {
            for (const group of groups) {
                const isMember = group.members.includes(node.id);

                if (isMember || !group.hullPoints || !group.centroid) continue;

                if (d3.polygonContains(group.hullPoints, [node.x, node.y])) {
                    const vecX = node.x - group.centroid[0];
                    const vecY = node.y - group.centroid[1];
                    const dist = Math.sqrt(vecX * vecX + vecY * vecY) || 1;

                    node.vx += (vecX / dist) * strength * alpha;
                    node.vy += (vecY / dist) * strength * alpha;
                }
            }
        }
    }

    force.initialize = function(nodes) {
        force.nodes = nodes;
    };

    return force;
}

function forceClusterRepulsion(groups) {
    const strength = 5; // Increased strength
    const radius = 1; // Increased minimum distance

    function force(alpha) {
        for (let i = 0; i < groups.length; i++) {
            const groupA = groups[i];
            if (!groupA.centroid) continue;

            for (let j = i + 1; j < groups.length; j++) {
                const groupB = groups[j];
                if (!groupB.centroid) continue;

                const vecX = groupB.centroid[0] - groupA.centroid[0];
                const vecY = groupB.centroid[1] - groupA.centroid[1];
                const dist = Math.sqrt(vecX*vecX + vecY*vecY) || 1;

                if (dist < radius) {
                    const overlap = radius - dist;
                    const forceX = (vecX / dist) * overlap * strength * alpha;
                    const forceY = (vecY / dist) * overlap * strength * alpha;

                    // Apply repulsion to all nodes in each group
                    groupA.members.forEach(memberId => {
                        const node = force.nodes.find(n => n.id === memberId);
                        if (node) {
                            node.vx -= forceX / groupA.members.length;
                            node.vy -= forceY / groupA.members.length;
                        }
                    });

                    groupB.members.forEach(memberId => {
                        const node = force.nodes.find(n => n.id === memberId);
                        if (node) {
                            node.vx += forceX / groupB.members.length;
                            node.vy += forceY / groupB.members.length;
                        }
                    });
                }
            }
        }
    }

    force.initialize = function(nodes) {
        force.nodes = nodes;
    };

    return force;
}

document.addEventListener('DOMContentLoaded', () => {
    const graphContainer = document.getElementById('graph-container');
    const tooltip = document.getElementById('tooltip');
    const groupBySelect = document.getElementById('group-by');
    const degreeFilterCheckboxes = document.querySelectorAll('#degree-filter input[type="checkbox"]');

    const width = graphContainer.clientWidth;
    const height = graphContainer.clientHeight || window.innerHeight * 0.8;

    const simWidth = width * 2;
    const simHeight = height * 2;

    const svg = d3.select(graphContainer).append('svg')
        .attr('width', width)
        .attr('height', height);

    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on('zoom', (event) => {
            container.attr('transform', event.transform);
        });

    svg.call(zoom);

    const container = svg.append('g');

    const legendGroup = svg.append('g')
        .attr('class', 'legend');

    const color = d3.scaleOrdinal(d3.schemeSet3); // More distinct colors
    let simulation;
    let originalGraphData = { nodes: [], groups: [] };

    function renderGraph(graph) {
        // Reset zoom and pan on new data
        const initialTransform = d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5);
        svg.call(zoom.transform, initialTransform);

        container.selectAll('*').remove(); // Clear previous graph elements from container
        legendGroup.selectAll('*').remove(); // Clear previous legend items

        if (!graph.nodes.length) return;

        // Create Legend
        legendGroup.attr('transform', `translate(${width - 300}, 30)`);
        const legendItem = legendGroup.selectAll('.legend-item')
            .data(graph.groups)
            .enter().append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${i * 30})`) // Increased vertical spacing
            .on('mouseover', (event, d_legend) => {
                const groupIndex = graph.groups.findIndex(g => g.name === d_legend.name);

                svg.selectAll('.hull')
                    .transition().duration(200)
                    .style('fill-opacity', h => h.name === d_legend.name ? 0.25 : 0.05)
                    .style('stroke-opacity', h => h.name === d_legend.name ? 0.6 : 0.1);

                svg.selectAll('.node')
                    .transition().duration(200)
                    .style('opacity', n => n.groups.includes(groupIndex) ? 1 : 0.1);
            })
            .on('mouseout', () => {
                svg.selectAll('.hull')
                    .transition().duration(200)
                    .style('fill-opacity', 0.2)
                    .style('stroke-opacity', 0.5);

                svg.selectAll('.node')
                    .transition().duration(200)
                    .style('opacity', 1);
            });

        // Add a background rect for better hover detection
        legendItem.append('rect')
            .attr('width', 300)
            .attr('height', 30) // Increased height to match spacing
            .style('fill', 'transparent');

        legendItem.append('rect')
            .attr('class', 'legend-color-box')
            .attr('width', 20)
            .attr('height', 20)
            .style('fill', (d, i) => color(i));

        legendItem.append('text')
            .attr('class', 'legend-text')
            .attr('x', 30)
            .attr('y', 15)
            .text(d => d.name);


        // Group data processing
        const groupMap = {};
        graph.groups.forEach((group, i) => {
            group.members.forEach(memberId => {
                if (!groupMap[memberId]) {
                    groupMap[memberId] = [];
                }
                groupMap[memberId].push(i);
            });
        });

        graph.nodes.forEach(node => {
            node.groups = groupMap[node.id] || [];
        });

        // Add a scale for node sizes
        const sizeScale = d3.scaleSqrt()
            .domain([0, d3.max(graph.nodes, d => d.research_papers)])
            .range([15, 80]); // Min and max radius size

        simulation = d3.forceSimulation(graph.nodes)
            .force('charge', d3.forceManyBody().strength(-250)) // Reduced charge strength
            .force('collision', d3.forceCollide().radius(d => sizeScale(d.research_papers) + 5)) // Dynamic collision radius
            .force('hull', forceHull(graph.groups))
            .force('cluster', forceClusterRepulsion(graph.groups)); // Add cluster repulsion

        const hullGroup = container.append('g');
        const nodeGroup = container.append('g');

        // Define image patterns
        const defs = container.append('defs');
        graph.nodes.forEach(node => {
            defs.append('pattern')
                .attr('id', `img-${node.id.replace(/\s+/g, '-')}`)
                .attr('height', 1)
                .attr('width', 1)
                .attr('x', '0')
                .attr('y', '0')
                .append('image')
                .attr('xlink:href', node.url_image)
                .attr('height', d => sizeScale(node.research_papers) * 2) // Match the circle diameter
                .attr('width', d => sizeScale(node.research_papers) * 2);  // Match the circle diameter
        });

        const node = nodeGroup.selectAll('.node-group')
            .data(graph.nodes)
            .enter().append('g')
            .attr('class', 'node-group')
            .call(drag(simulation))
            .on('mouseover', (event, d) => {
                tooltip.style.display = 'block';
                tooltip.innerHTML = `
                    <strong>${d.name}</strong><br>
                    Carrera: ${d.normalized_specialization}<br>
                    Universidad: ${d.normalized_university}<br>
                    Investigaciones: ${d.research_papers}
                `;
            })
            .on('mousemove', (event) => {
                tooltip.style.left = `${event.pageX + 10}px`;
                tooltip.style.top = `${event.pageY + 10}px`;
            })
            .on('mouseout', () => {
                tooltip.style.display = 'none';
            });

        node.append('circle')
            .attr('class', 'node')
            .attr('r', d => sizeScale(d.research_papers)) // Dynamic radius
            .style('fill', d => `url(#img-${d.id.replace(/\s+/g, '-')})`);

        node.append('text')
            .attr('class', 'node-label')
            .attr('y', d => -sizeScale(d.research_papers) - 5) // Position above the node circle
            .text(d => d.name);
            
        const hulls = hullGroup.selectAll('.hull')
            .data(graph.groups)
            .enter().append('path')
            .attr('class', 'hull')
            .style('fill', (d, i) => color(i))
            .style('stroke', (d, i) => color(i))
            .on('mouseover', (event, d) => {
                tooltip.style.display = 'block';
                tooltip.innerHTML = `<strong>${d.name}</strong><br>${d.members.length} miembros`;
            })
            .on('mousemove', (event) => {
                tooltip.style.left = `${event.pageX + 10}px`;
                tooltip.style.top = `${event.pageY + 10}px`;
            })
            .on('mouseout', () => {
                tooltip.style.display = 'none';
            });

        simulation.on('tick', () => {
            node.attr('transform', d => `translate(${d.x},${d.y})`);
            
            hulls.attr('d', group => {
                const nodePoints = group.members.map(memberId => {
                    return graph.nodes.find(n => n.id === memberId);
                }).filter(Boolean);

                // Handle single-person groups by drawing a circle
                if (nodePoints.length === 1) {
                    const node = nodePoints[0];
                    const radius = sizeScale(node.research_papers) + 15; // Adjusted radius for single-node hull
                    group.centroid = [node.x, node.y];
                    // Define hull points for force calculations
                    group.hullPoints = [
                        [node.x - radius, node.y], [node.x + radius, node.y],
                        [node.x, node.y - radius], [node.x, node.y + radius]
                    ];
                    // SVG path for a circle
                    return `M ${node.x - radius}, ${node.y} A ${radius},${radius} 0 1,0 ${node.x + radius},${node.y} A ${radius},${radius} 0 1,0 ${node.x - radius},${node.y}`;
                }

                if (nodePoints.length < 2) {
                    delete group.hullPoints;
                    delete group.centroid;
                    return '';
                }

                const points = nodePoints.map(n => [n.x, n.y]);
                const hull = d3.polygonHull(points);

                if (!hull) {
                    delete group.hullPoints;
                    delete group.centroid;
                    return '';
                }

                group.centroid = d3.polygonCentroid(hull);

                const padding = 45; // This can remain constant or be dynamic
                const paddedPoints = hull.map(p => {
                    const angle = Math.atan2(p[1] - group.centroid[1], p[0] - group.centroid[0]);
                    const nodeRadius = sizeScale(graph.nodes.find(n => n.x === p[0] && n.y === p[1])?.research_papers || 0) || 30;
                    const dynamicPadding = nodeRadius + 15;
                    return [p[0] + dynamicPadding * Math.cos(angle), p[1] + dynamicPadding * Math.sin(angle)];
                });

                group.hullPoints = paddedPoints;

                return `M${paddedPoints.join('L')}Z`;
            });
        });
    }

    function drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    function applyFiltersAndRender() {
        const selectedDegrees = Array.from(degreeFilterCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedDegrees.length === 0) {
            renderGraph({ nodes: [], groups: [] });
            return;
        }

        const filteredNodes = originalGraphData.nodes.filter(node =>
            selectedDegrees.includes(node.degree_level)
        );

        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));

        const filteredGroups = originalGraphData.groups
            .map(group => {
                const newMembers = group.members.filter(memberId => filteredNodeIds.has(memberId));
                return { ...group, members: newMembers };
            })
            .filter(group => group.members.length > 0);

        renderGraph({ nodes: filteredNodes, groups: filteredGroups });
    }

    async function fetchDataAndRender(groupBy) {
        const response = await fetch(`/graph-data?groupBy=${groupBy}`);
        originalGraphData = await response.json();
        applyFiltersAndRender();
    }


    groupBySelect.addEventListener('change', () => {
        fetchDataAndRender(groupBySelect.value);
    });

    degreeFilterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', applyFiltersAndRender);
    });

    fetchDataAndRender(groupBySelect.value);
}); 