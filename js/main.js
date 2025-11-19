let camera, scene, renderer, loader, light1, light2, controls, model;

init();
animate();

function init() {

    let url = (document.URL.split('?')[1] || "example/test_complete.obj");

    loader = new Loader(url, 1024, 20);
    loader.start(function(elements) {
        for (let element of elements) {
            if (element !== undefined) {
                try {
                    model.manageElement(element);
                } catch(e) {
                    if (e.type === "custom") {
                        document.getElementById('errormessage').innerHTML = e;
                    } else {
                        throw e;
                    }
                }
            }
        }

        colorizeModel(model, "byHeight");    // random per-face colors
    });

    camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.0001, 1000);
    camera.position.z = 3;

    scene = new THREE.Scene();

    model = new Model(url);
    scene.add(model);

    light1 = new THREE.AmbientLight(0x999999);
    scene.add(light1);

    light2 = new THREE.DirectionalLight(0xffffff, 1.0);
    light2.position.set(0.0, 1.0, 0.0);
    scene.add(light2);

    renderer = new THREE.WebGLRenderer({antialias: true});
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    window.addEventListener('resize', onWindowResize, false);
    controls = new THREE.OrbitControls(camera, renderer.domElement);

}

function animate() {

    requestAnimationFrame(animate);
    controls.update();
    document.getElementById('progressbar').value = Math.floor(100 * loader.percentage()) || 0;
    document.getElementById('percentage').innerHTML = Math.floor(100 * loader.percentage()) / 100 + "%";
    renderer.render(scene, camera);

}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize( window.innerWidth, window.innerHeight );
}

// colorizeModel(meshRoot, mode)
// mode: "random" | "byHeight" (you can add more modes)
function colorizeModel(meshRoot, mode = "random") {

    meshRoot.traverse((child) => {
        if (!child.isMesh) return;

        // Ensure BufferGeometry
        let geom = child.geometry;
        if (!geom.isBufferGeometry) return;

        // Convert to non-indexed so every triangle has its own unique vertices
        // (this lets us color faces independently)
        if (geom.index) {
            geom = geom.toNonIndexed(); // returns a new BufferGeometry
            child.geometry = geom;
        }

        const posAttr = geom.attributes.position;
        const vertexCount = posAttr.count; // number of vertices (3 per triangle)

        // Create color attribute (r,g,b) per vertex
        const colors = new Float32Array(vertexCount * 3);

        // Helper: set color rgb into colors array for vertex i
        function setVertexColor(idx, color) {
            colors[3 * idx + 0] = color.r;
            colors[3 * idx + 1] = color.g;
            colors[3 * idx + 2] = color.b;
        }

        // Helper: create THREE.Color from HSL or hex quickly
        const tmpColor = new THREE.Color();

        // If mode is byHeight we need min/max z to map heights
        let minZ = Infinity, maxZ = -Infinity;
        if (mode === "byHeight") {
            for (let i = 0; i < vertexCount; i++) {
                const z = posAttr.getZ(i);
                if (z < minZ) minZ = z;
                if (z > maxZ) maxZ = z;
            }
            // avoid zero range
            if (minZ === maxZ) { minZ -= 0.5; maxZ += 0.5; }
        }

        // For each triangle (3 vertices), compute a color and assign to 3 verts
        for (let tri = 0; tri < vertexCount; tri += 3) {

            let color;
            if (mode === "random") {
                // random bright color
                tmpColor.setHSL(Math.random(), 0.7, 0.5);
                color = tmpColor.clone();

            } else if (mode === "byHeight") {
                // compute average z for this triangle
                const z0 = posAttr.getZ(tri + 0);
                const z1 = posAttr.getZ(tri + 1);
                const z2 = posAttr.getZ(tri + 2);
                const avgZ = (z0 + z1 + z2) / 3;
                const t = (avgZ - minZ) / (maxZ - minZ); // 0..1
                // map t to color (e.g., blue at bottom, green mid, red top)
                tmpColor.setHSL((1 - t) * 0.6, 0.8, 0.5); // hue sweep
                color = tmpColor.clone();

            } else {
                // default: gray
                color = new THREE.Color(0.8, 0.8, 0.8);
            }

            // set the same color to the 3 vertices of the triangle
            setVertexColor(tri + 0, color);
            setVertexColor(tri + 1, color);
            setVertexColor(tri + 2, color);
        }

        // Assign the color attribute to geometry
        geom.setAttribute('color', new THREE.BufferAttribute(colors, 3, false));

        // Replace material with one that uses vertexColors
        // Keep existing material properties like shininess by cloning or customizing
        const baseMat = child.material && child.material.isMaterial ? child.material : new THREE.MeshPhongMaterial();
        const mat = new THREE.MeshPhongMaterial({
            vertexColors: true,
            flatShading: true,      // show flat faces (set false for smooth shading)
            side: baseMat.side || THREE.FrontSide,
            shininess: baseMat.shininess !== undefined ? baseMat.shininess : 30
        });

        child.material = mat;
    });
}
