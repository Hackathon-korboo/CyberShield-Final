/**
 * CYBERSHIELD AI 2.0 — PERSISTENT PROCEDURAL 3D ROBOTIC JELLYFISH BACKGROUND
 * Implementation Standard: Medusa JF-4 Autonomous Field Simulator Architecture
 * 
 * Non-Negotiable Properties:
 * 1. Single WebGL Renderer & Scene mounted ONCE at application root level.
 * 2. Uninterrupted continuous rotation around vertical Y axis.
 * 3. Natural procedural robotic tentacle kinematics (hierarchical vertebrae joints).
 * 4. Translucent glass-like bell with metallic/ceramic mechanical armature.
 * 5. Aqua (#46c9bf) & Coral (#ff5a3c) sensor nodes and reactor core.
 * 6. Continuous idle animation (NEVER departs, NEVER teardown, NEVER disappears).
 * 7. Zero interference with foreground interactive UI (pointer-events: none).
 */

(function () {
  'use strict';

  // Prevent multiple initializations across script reloads or internal navigations
  if (window.__CYBERSHIELD_JELLYFISH_ACTIVE__) {
    console.log('[ThreeJS] Persistent robotic jellyfish already initialized at root.');
    return;
  }
  window.__CYBERSHIELD_JELLYFISH_ACTIVE__ = true;

  // Scene globals
  let scene, camera, renderer, canvas;
  let jellyfishGroup, bellGroup, coreGroup;
  let tentacles = [];
  let sensoryFilaments = [];
  let oralRibbons = [];
  let coreReactorLight, rimNodes = [];
  let animationFrameId = null;
  let clock;
  let isReducedMotion = false;

  // Check reduced motion preference
  if (window.matchMedia) {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    isReducedMotion = motionQuery.matches;
    motionQuery.addEventListener('change', (e) => {
      isReducedMotion = e.matches;
    });
  }

  function init() {
    canvas = document.getElementById('jellyfish-canvas');
    if (!canvas) {
      console.warn('[ThreeJS] #jellyfish-canvas not found in DOM.');
      return;
    }

    if (typeof THREE === 'undefined') {
      console.error('[ThreeJS] Three.js library not loaded.');
      return;
    }

    clock = new THREE.Clock();

    // 1. Scene setup
    scene = new THREE.Scene();

    // 2. Camera setup
    const aspect = window.innerWidth / window.innerHeight;
    camera = new THREE.PerspectiveCamera(42, aspect, 0.1, 100);
    // Position camera to view the jellyfish gracefully centered/slightly upper
    camera.position.set(0, -0.4, 9.2);
    camera.lookAt(0, -0.6, 0);

    // 3. WebGL Renderer
    renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    // 4. Lighting Rig
    setupLighting();

    // 5. Build Procedural Robotic Jellyfish Model
    buildRoboticJellyfish();

    // 6. Event listeners
    window.addEventListener('resize', onWindowResize, { passive: true });

    // 7. Start persistent animation loop
    animate();
    console.log('[ThreeJS] Persistent 3D Robotic Jellyfish Background successfully mounted.');
  }

  function setupLighting() {
    // Pale marine ambient light
    const ambientLight = new THREE.AmbientLight(0xe8f7f6, 0.85);
    scene.add(ambientLight);

    // Key directional light (top-front-right crisp sheen)
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
    keyLight.position.set(5, 8, 6);
    scene.add(keyLight);

    // Fill directional light (soft cool marine fill from left)
    const fillLight = new THREE.DirectionalLight(0x46c9bf, 0.6);
    fillLight.position.set(-6, -2, 4);
    scene.add(fillLight);

    // Rim light from rear-bottom
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.7);
    rimLight.position.set(0, -5, -6);
    scene.add(rimLight);

    // Core point light (aqua reactor glow)
    coreReactorLight = new THREE.PointLight(0x46c9bf, 2.0, 12);
    coreReactorLight.position.set(0, 0.3, 0);
    scene.add(coreReactorLight);

    // Accent point light (coral warning frequency)
    const coralAccentLight = new THREE.PointLight(0xff5a3c, 1.2, 8);
    coralAccentLight.position.set(0, -1.2, 0);
    scene.add(coralAccentLight);
  }

  function buildRoboticJellyfish() {
    jellyfishGroup = new THREE.Group();
    jellyfishGroup.position.set(0, 0.2, 0);
    scene.add(jellyfishGroup);

    // -------------------------------------------------------------------------
    // A. Outer Translucent Glass-Like Bell
    // -------------------------------------------------------------------------
    bellGroup = new THREE.Group();
    jellyfishGroup.add(bellGroup);

    // Dome geometry: half sphere scaled to an umbrella bell curvature
    const bellRadius = 2.4;
    const bellGeo = new THREE.SphereGeometry(bellRadius, 48, 24, 0, Math.PI * 2, 0, Math.PI * 0.44);
    
    // Glass-like physical material with aqua tint
    const bellMat = new THREE.MeshPhysicalMaterial({
      color: 0x5cd3ca,
      emissive: 0x0e3a3d,
      emissiveIntensity: 0.15,
      roughness: 0.12,
      metalness: 0.08,
      transmission: 0.82,
      thickness: 0.45,
      transparent: true,
      opacity: 0.68,
      side: THREE.DoubleSide,
      depthWrite: false
    });

    const bellMesh = new THREE.Mesh(bellGeo, bellMat);
    bellMesh.scale.set(1.0, 0.78, 1.0);
    bellGroup.add(bellMesh);

    // Fine wireframe ribbing overlay for mechanical engineering aesthetic
    const ribGeo = new THREE.SphereGeometry(bellRadius * 1.002, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.44);
    const ribMat = new THREE.MeshBasicMaterial({
      color: 0x46c9bf,
      wireframe: true,
      transparent: true,
      opacity: 0.22
    });
    const ribMesh = new THREE.Mesh(ribGeo, ribMat);
    ribMesh.scale.copy(bellMesh.scale);
    bellGroup.add(ribMesh);

    // -------------------------------------------------------------------------
    // B. Titanium Bell Rim & Armature
    // -------------------------------------------------------------------------
    const rimRadius = bellRadius * Math.sin(Math.PI * 0.44); // ~2.35
    const rimY = -bellRadius * Math.cos(Math.PI * 0.44) * 0.78; // base of dome
    
    // Main structural torus rim
    const rimGeo = new THREE.TorusGeometry(rimRadius, 0.055, 16, 64);
    const darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x0e3a3d,
      metalness: 0.88,
      roughness: 0.22
    });
    const rimMesh = new THREE.Mesh(rimGeo, darkMetalMat);
    rimMesh.rotation.x = Math.PI / 2;
    rimMesh.position.y = rimY;
    bellGroup.add(rimMesh);

    // Inner mechanical bevel ring
    const innerRimGeo = new THREE.TorusGeometry(rimRadius * 0.88, 0.035, 12, 48);
    const innerRimMesh = new THREE.Mesh(innerRimGeo, darkMetalMat);
    innerRimMesh.rotation.x = Math.PI / 2;
    innerRimMesh.position.y = rimY + 0.15;
    bellGroup.add(innerRimMesh);

    // 12 Radial Ceramic-Metallic Struts connecting Center Hub to Rim
    const strutCount = 12;
    const strutMat = new THREE.MeshStandardMaterial({
      color: 0xd3e8e7,
      metalness: 0.75,
      roughness: 0.3
    });
    
    for (let i = 0; i < strutCount; i++) {
      const angle = (i / strutCount) * Math.PI * 2;
      const strutLength = rimRadius - 0.45;
      const strutGeo = new THREE.CylinderGeometry(0.025, 0.035, strutLength, 8);
      const strut = new THREE.Mesh(strutGeo, strutMat);
      
      strut.position.set(
        Math.cos(angle) * (strutLength / 2 + 0.45),
        rimY + 0.3,
        Math.sin(angle) * (strutLength / 2 + 0.45)
      );
      strut.rotation.z = Math.PI / 2;
      strut.rotation.y = -angle;
      strut.rotation.x = 0.15;
      bellGroup.add(strut);
    }

    // -------------------------------------------------------------------------
    // C. Optical Sensor Nodes (Aqua & Coral Alternating)
    // -------------------------------------------------------------------------
    const sensorCount = 12;
    const coralSensorMat = new THREE.MeshStandardMaterial({
      color: 0xff5a3c,
      emissive: 0xff5a3c,
      emissiveIntensity: 0.85,
      roughness: 0.2
    });
    const aquaSensorMat = new THREE.MeshStandardMaterial({
      color: 0x46c9bf,
      emissive: 0x0f9d8a,
      emissiveIntensity: 0.85,
      roughness: 0.2
    });

    for (let i = 0; i < sensorCount; i++) {
      const angle = (i / sensorCount) * Math.PI * 2;
      const isCoral = i % 2 === 0;
      const sensorGeo = new THREE.SphereGeometry(0.07, 16, 16);
      const sensorMesh = new THREE.Mesh(sensorGeo, isCoral ? coralSensorMat : aquaSensorMat);
      sensorMesh.position.set(
        Math.cos(angle) * rimRadius,
        rimY,
        Math.sin(angle) * rimRadius
      );
      bellGroup.add(sensorMesh);
      rimNodes.push({ mesh: sensorMesh, baseAngle: angle, isCoral: isCoral });
    }

    // -------------------------------------------------------------------------
    // D. Central Mechanical Core & Reactor Housing
    // -------------------------------------------------------------------------
    coreGroup = new THREE.Group();
    coreGroup.position.set(0, rimY + 0.4, 0);
    jellyfishGroup.add(coreGroup);

    // Multi-tiered titanium hub
    const hubGeo = new THREE.CylinderGeometry(0.55, 0.65, 0.4, 24);
    const hubMesh = new THREE.Mesh(hubGeo, darkMetalMat);
    coreGroup.add(hubMesh);

    const hubRingGeo = new THREE.TorusGeometry(0.68, 0.04, 12, 32);
    const hubRing = new THREE.Mesh(hubRingGeo, darkMetalMat);
    hubRing.rotation.x = Math.PI / 2;
    coreGroup.add(hubRing);

    // Glowing central reactor sphere
    const reactorGeo = new THREE.SphereGeometry(0.32, 24, 24);
    const reactorMat = new THREE.MeshStandardMaterial({
      color: 0x46c9bf,
      emissive: 0x0f9d8a,
      emissiveIntensity: 1.2,
      roughness: 0.15
    });
    const reactorMesh = new THREE.Mesh(reactorGeo, reactorMat);
    reactorMesh.position.y = 0.25;
    coreGroup.add(reactorMesh);

    // Floating gyro stabilizer ring around reactor
    const gyroGeo = new THREE.TorusGeometry(0.42, 0.02, 8, 32);
    const gyroMat = new THREE.MeshStandardMaterial({
      color: 0xff5a3c,
      emissive: 0xff5a3c,
      emissiveIntensity: 0.4,
      metalness: 0.9,
      roughness: 0.2
    });
    const gyroMesh = new THREE.Mesh(gyroGeo, gyroMat);
    gyroMesh.position.y = 0.25;
    gyroMesh.rotation.x = 0.4;
    gyroMesh.name = 'gyroRing';
    coreGroup.add(gyroMesh);

    // -------------------------------------------------------------------------
    // E. 8 Primary Articulated Robotic Tentacles
    // -------------------------------------------------------------------------
    // Each tentacle is an articulated hierarchical chain of vertebrae
    const tentacleCount = 8;
    const vertebraePerTentacle = 16;
    const vertebraLength = 0.24;

    const vertebraMat = new THREE.MeshStandardMaterial({
      color: 0x5d8284,
      metalness: 0.8,
      roughness: 0.3
    });
    const jointMat = new THREE.MeshStandardMaterial({
      color: 0x46c9bf,
      emissive: 0x0f9d8a,
      emissiveIntensity: 0.35,
      roughness: 0.2
    });

    for (let t = 0; t < tentacleCount; t++) {
      const tentacleAngle = (t / tentacleCount) * Math.PI * 2;
      const rootRadius = rimRadius * 0.72;
      const rootX = Math.cos(tentacleAngle) * rootRadius;
      const rootZ = Math.sin(tentacleAngle) * rootRadius;

      const tentacleChain = [];
      let parentObj = coreGroup;

      // Base mount swivel
      const baseMount = new THREE.Group();
      baseMount.position.set(rootX, -0.2, rootZ);
      coreGroup.add(baseMount);
      parentObj = baseMount;

      for (let v = 0; v < vertebraePerTentacle; v++) {
        const segGroup = new THREE.Group();
        segGroup.position.set(0, -vertebraLength, 0);

        // Cylindrical segment
        const taper = 1.0 - (v / vertebraePerTentacle) * 0.55;
        const segGeo = new THREE.CylinderGeometry(0.045 * taper, 0.038 * taper, vertebraLength * 0.85, 8);
        const segMesh = new THREE.Mesh(segGeo, vertebraMat);
        segMesh.position.y = vertebraLength * 0.42;
        segGroup.add(segMesh);

        // Articulation joint sphere
        const jointGeo = new THREE.SphereGeometry(0.05 * taper, 12, 12);
        const jointMesh = new THREE.Mesh(jointGeo, v % 3 === 0 ? jointMat : vertebraMat);
        jointMesh.position.y = 0;
        segGroup.add(jointMesh);

        parentObj.add(segGroup);
        parentObj = segGroup;
        tentacleChain.push(segGroup);
      }

      tentacles.push({
        baseAngle: tentacleAngle,
        chain: tentacleChain,
        speedOffset: t * 0.65,
        freq: 1.8 + (t % 3) * 0.2
      });
    }

    // -------------------------------------------------------------------------
    // F. 16 Secondary Fine Sensory Filaments
    // -------------------------------------------------------------------------
    // Procedural wavy spline curves descending downwards
    const filamentCount = 16;
    const filamentMat = new THREE.LineBasicMaterial({
      color: 0x46c9bf,
      transparent: true,
      opacity: 0.45,
      linewidth: 1
    });

    for (let f = 0; f < filamentCount; f++) {
      const angle = (f / filamentCount) * Math.PI * 2;
      const rad = rimRadius * 0.94;
      const points = [];
      const numPoints = 24;
      const totalLen = 4.8;

      for (let p = 0; p < numPoints; p++) {
        const y = - (p / (numPoints - 1)) * totalLen;
        points.push(new THREE.Vector3(Math.cos(angle) * rad, rimY + y, Math.sin(angle) * rad));
      }

      const curve = new THREE.CatmullRomCurve3(points);
      const filGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(36));
      const filLine = new THREE.Line(filGeo, filamentMat);
      jellyfishGroup.add(filLine);

      sensoryFilaments.push({
        line: filLine,
        baseAngle: angle,
        baseRad: rad,
        baseY: rimY,
        totalLen: totalLen,
        pointsCount: numPoints,
        phase: f * 0.4
      });
    }

    // -------------------------------------------------------------------------
    // G. 4 Central Undulating Oral Ribbon Arms
    // -------------------------------------------------------------------------
    const ribbonMat = new THREE.MeshPhysicalMaterial({
      color: 0x46c9bf,
      emissive: 0x0e3a3d,
      emissiveIntensity: 0.2,
      transmission: 0.75,
      transparent: true,
      opacity: 0.48,
      roughness: 0.2,
      side: THREE.DoubleSide,
      depthWrite: false
    });

    for (let r = 0; r < 4; r++) {
      const angle = (r / 4) * Math.PI * 2;
      const ribbonGeo = new THREE.PlaneGeometry(0.38, 4.2, 4, 32);
      const ribbonMesh = new THREE.Mesh(ribbonGeo, ribbonMat);
      ribbonMesh.position.set(Math.cos(angle) * 0.25, -2.1, Math.sin(angle) * 0.25);
      ribbonMesh.rotation.y = angle;
      coreGroup.add(ribbonMesh);

      oralRibbons.push({
        mesh: ribbonMesh,
        angle: angle,
        geo: ribbonGeo,
        origPos: ribbonGeo.attributes.position.clone()
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 6. Continuous Idle Animation Engine
  // ---------------------------------------------------------------------------
  function animate() {
    animationFrameId = requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const time = clock.getElapsedTime() * (isReducedMotion ? 0.4 : 1.0);

    if (!jellyfishGroup) return;

    // 1. Continuous vertical rotation (Never stops)
    jellyfishGroup.rotation.y += (isReducedMotion ? 0.0015 : 0.0035);

    // 2. Gentle vertical floating bob
    jellyfishGroup.position.y = 0.2 + Math.sin(time * 0.85) * 0.22;
    jellyfishGroup.rotation.z = Math.sin(time * 0.4) * 0.04;
    jellyfishGroup.rotation.x = Math.cos(time * 0.35) * 0.03;

    // 3. Subtle bell breathing / rhythmic contraction
    const breath = Math.sin(time * 1.5);
    const scaleXZ = 1.0 + breath * 0.038;
    const scaleY = 1.0 - breath * 0.024;
    if (bellGroup) {
      bellGroup.scale.set(scaleXZ, scaleY, scaleXZ);
    }

    // 4. Gyro ring rotation inside core
    const gyro = coreGroup?.getObjectByName('gyroRing');
    if (gyro) {
      gyro.rotation.z += 0.02;
      gyro.rotation.x = 0.3 + Math.sin(time * 2.0) * 0.15;
    }

    // 5. Reactor light pulsing
    if (coreReactorLight) {
      coreReactorLight.intensity = 1.8 + Math.sin(time * 3.0) * 0.5;
    }

    // 6. Kinematic robotic tentacle waves
    for (let t = 0; t < tentacles.length; t++) {
      const tent = tentacles[t];
      const chain = tent.chain;
      const count = chain.length;

      for (let v = 0; v < count; v++) {
        const seg = chain[v];
        const vRatio = v / count;
        // Cumulative wave displacement
        const waveAngle = Math.sin(time * tent.freq - v * 0.38 + tent.speedOffset);
        const waveSide = Math.cos(time * 1.2 - v * 0.28 + tent.speedOffset);
        
        // Progressively amplify bend towards the tip
        const amp = 0.05 + vRatio * 0.14;
        seg.rotation.z = waveAngle * amp;
        seg.rotation.x = waveSide * (amp * 0.6);
      }
    }

    // 7. Undulating Oral Ribbon Vertices
    for (let r = 0; r < oralRibbons.length; r++) {
      const rib = oralRibbons[r];
      const posAttr = rib.geo.attributes.position;
      const orig = rib.origPos;
      const vertexCount = posAttr.count;

      for (let i = 0; i < vertexCount; i++) {
        const yVal = orig.getY(i);
        const depthFactor = Math.abs(yVal) / 4.2;
        const wave = Math.sin(time * 2.2 + yVal * 1.6 + rib.angle) * 0.18 * depthFactor;
        posAttr.setZ(i, wave);
        posAttr.setX(i, orig.getX(i) + Math.cos(time * 1.5 + yVal) * 0.06 * depthFactor);
      }
      posAttr.needsUpdate = true;
    }

    // 8. Trailing Sensory Filaments Animation
    for (let f = 0; f < sensoryFilaments.length; f++) {
      const fil = sensoryFilaments[f];
      const positions = fil.line.geometry.attributes.position;
      const count = positions.count;

      for (let i = 0; i < count; i++) {
        const tPct = i / (count - 1);
        const y = fil.baseY - tPct * fil.totalLen;
        const waveX = Math.sin(time * 1.6 - tPct * 4.0 + fil.phase) * 0.16 * tPct;
        const waveZ = Math.cos(time * 1.4 - tPct * 3.5 + fil.phase) * 0.16 * tPct;

        positions.setXYZ(
          i,
          Math.cos(fil.baseAngle) * fil.baseRad + waveX,
          y,
          Math.sin(fil.baseAngle) * fil.baseRad + waveZ
        );
      }
      positions.needsUpdate = true;
    }

    // Render frame
    renderer.render(scene, camera);
  }

  function onWindowResize() {
    if (!renderer || !camera) return;
    const width = window.innerWidth;
    const height = window.innerHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  }

  // Self-initialize once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
