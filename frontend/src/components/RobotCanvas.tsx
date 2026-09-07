import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

interface RobotCanvasProps {
  className?: string;
}

export const RobotCanvas: React.FC<RobotCanvasProps> = ({ className }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 240;
    const height = container.clientHeight || 260;

    // --- 1. Scene, Camera, Renderer ---
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0.4, 4.4);
    camera.lookAt(0, 0.1, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.appendChild(renderer.domElement);

    // --- 2. Lighting (Crisp titanium white key, warm neutral fill, specular rim, gold accents - NO BLUE/PURPLE) ---
    const ambientLight = new THREE.AmbientLight(0x282c34, 1.4);
    scene.add(ambientLight);

    // Key light (soft neutral white from top-front-left)
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.5);
    keyLight.position.set(2.8, 4.5, 3.8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    keyLight.shadow.bias = -0.001;
    scene.add(keyLight);

    // Fill light (neutral titanium fill from front-right)
    const fillLight = new THREE.DirectionalLight(0xa8a29e, 1.1);
    fillLight.position.set(-2.5, 2.0, 2.5);
    scene.add(fillLight);

    // Rim light (crisp titanium white accent from behind)
    const rimLight = new THREE.DirectionalLight(0xffffff, 1.8);
    rimLight.position.set(0, 3.5, -3.5);
    scene.add(rimLight);

    // Subtle floor bounce light (neutral dark charcoal)
    const bounceLight = new THREE.DirectionalLight(0x20242c, 0.8);
    bounceLight.position.set(0, -2, 1);
    scene.add(bounceLight);

    // --- 3. PBR Materials (White ceramic, metallic silver, dark visor, warm gold glow, YouTube red) ---
    const whiteBodyMat = new THREE.MeshStandardMaterial({
      color: 0xf1f5f9,
      roughness: 0.16,
      metalness: 0.08,
    });

    const silverMetalMat = new THREE.MeshStandardMaterial({
      color: 0xc8d1dc,
      roughness: 0.22,
      metalness: 0.88,
    });

    const darkVisorMat = new THREE.MeshStandardMaterial({
      color: 0x050914,
      roughness: 0.08,
      metalness: 0.92,
    });

    const goldGlowMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
    });

    const eyeGoldMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
    });

    const youtubeRedMat = new THREE.MeshStandardMaterial({
      color: 0xcc0000,
      roughness: 0.25,
      metalness: 0.15,
    });

    const whiteMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
    });

    // --- 4. Build 3D Humanoid Mascot Model Hierarchy ---
    const rootGroup = new THREE.Group();
    rootGroup.position.set(0, -0.05, 0);
    // Facing slightly towards the user at a natural angle (approx 8 degrees to left)
    rootGroup.rotation.y = -0.14;
    scene.add(rootGroup);

    // A. Soft Contact Shadow Plane (Ground)
    const shadowCanvas = document.createElement('canvas');
    shadowCanvas.width = 128;
    shadowCanvas.height = 128;
    const shadowCtx = shadowCanvas.getContext('2d');
    if (shadowCtx) {
      const grad = shadowCtx.createRadialGradient(64, 64, 8, 64, 64, 60);
      grad.addColorStop(0, 'rgba(0, 0, 0, 0.75)');
      grad.addColorStop(0.4, 'rgba(0, 0, 0, 0.45)');
      grad.addColorStop(0.75, 'rgba(0, 0, 0, 0.15)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      shadowCtx.fillStyle = grad;
      shadowCtx.fillRect(0, 0, 128, 128);
    }
    const shadowTexture = new THREE.CanvasTexture(shadowCanvas);
    const shadowPlane = new THREE.Mesh(
      new THREE.PlaneGeometry(2.4, 2.4),
      new THREE.MeshBasicMaterial({
        map: shadowTexture,
        transparent: true,
        depthWrite: false
      })
    );
    shadowPlane.rotation.x = -Math.PI / 2;
    shadowPlane.position.y = -1.48;
    rootGroup.add(shadowPlane);

    // B. Upper Body (Torso, Chest, Head, Arms)
    const upperBodyGroup = new THREE.Group();
    upperBodyGroup.position.y = 0;
    rootGroup.add(upperBodyGroup);

    // Torso (cute rounded egg/pear body)
    const torsoGeo = new THREE.SphereGeometry(0.68, 32, 32);
    torsoGeo.scale(1.0, 1.15, 0.92);
    const torso = new THREE.Mesh(torsoGeo, whiteBodyMat);
    torso.position.y = -0.05;
    torso.castShadow = true;
    upperBodyGroup.add(torso);

    // Neck joint (metallic ring)
    const neckRing = new THREE.Mesh(
      new THREE.CylinderGeometry(0.36, 0.42, 0.12, 32),
      silverMetalMat
    );
    neckRing.position.y = 0.65;
    upperBodyGroup.add(neckRing);

    // Pelvis / waist band (metallic silver ring)
    const waistRing = new THREE.Mesh(
      new THREE.CylinderGeometry(0.56, 0.58, 0.1, 32),
      silverMetalMat
    );
    waistRing.position.y = -0.66;
    upperBodyGroup.add(waistRing);

    // YouTube Chest Emblem: Red Rounded Badge + White Play Triangle
    const chestGroup = new THREE.Group();
    chestGroup.position.set(0, 0.14, 0.61);
    chestGroup.rotation.x = -0.15; // match torso curvature

    // Red rounded box
    const badgeShape = new THREE.Shape();
    const bw = 0.32, bh = 0.22, br = 0.06;
    badgeShape.moveTo(-bw/2 + br, -bh/2);
    badgeShape.lineTo(bw/2 - br, -bh/2);
    badgeShape.quadraticCurveTo(bw/2, -bh/2, bw/2, -bh/2 + br);
    badgeShape.lineTo(bw/2, bh/2 - br);
    badgeShape.quadraticCurveTo(bw/2, bh/2, bw/2 - br, bh/2);
    badgeShape.lineTo(-bw/2 + br, bh/2);
    badgeShape.quadraticCurveTo(-bw/2, bh/2, -bw/2, bh/2 - br);
    badgeShape.lineTo(-bw/2, -bh/2 + br);
    badgeShape.quadraticCurveTo(-bw/2, -bh/2, -bw/2 + br, -bh/2);

    const badgeExtrude = new THREE.ExtrudeGeometry(badgeShape, {
      depth: 0.04,
      bevelEnabled: true,
      bevelSegments: 3,
      steps: 1,
      bevelSize: 0.015,
      bevelThickness: 0.015
    });
    badgeExtrude.center();
    const chestBadge = new THREE.Mesh(badgeExtrude, youtubeRedMat);
    chestBadge.castShadow = true;
    chestGroup.add(chestBadge);

    // White play triangle on chest
    const playShape = new THREE.Shape();
    playShape.moveTo(-0.045, -0.055);
    playShape.lineTo(0.065, 0.0);
    playShape.lineTo(-0.045, 0.055);
    playShape.closePath();
    const playGeo = new THREE.ShapeGeometry(playShape);
    const playMesh = new THREE.Mesh(playGeo, whiteMat);
    playMesh.position.z = 0.04;
    chestGroup.add(playMesh);
    upperBodyGroup.add(chestGroup);

    // C. Head Group (Rotatable, cute helmet, visor, eyes, ears)
    const headGroup = new THREE.Group();
    headGroup.position.set(0, 1.05, 0.02);
    upperBodyGroup.add(headGroup);

    // Outer Helmet (rounded white shell)
    const helmetGeo = new THREE.SphereGeometry(0.68, 32, 32);
    helmetGeo.scale(1.18, 0.98, 1.04);
    const helmet = new THREE.Mesh(helmetGeo, whiteBodyMat);
    helmet.castShadow = true;
    headGroup.add(helmet);

    // Dark Visor Faceplate (glossy dark glass curved screen)
    const visorGeo = new THREE.SphereGeometry(0.58, 32, 24);
    visorGeo.scale(1.08, 0.82, 0.65);
    const visor = new THREE.Mesh(visorGeo, darkVisorMat);
    visor.position.set(0, -0.02, 0.32);
    headGroup.add(visor);

    // Cute Smiling Golden Eyes (arch curves ^ ^)
    const createSmilingEye = (xPos: number) => {
      // Inverted U / arch curve using Torus
      const eyeGeo = new THREE.TorusGeometry(0.08, 0.02, 16, 24, Math.PI * 0.9);
      const eye = new THREE.Mesh(eyeGeo, eyeGoldMat);
      eye.position.set(xPos, 0.06, 0.66);
      eye.rotation.z = Math.PI * 0.05 * (xPos > 0 ? -1 : 1);
      return eye;
    };

    const leftEye = createSmilingEye(-0.21);
    const rightEye = createSmilingEye(0.21);
    headGroup.add(leftEye);
    headGroup.add(rightEye);

    // Cute subtle blush discs on cheeks (soft YouTube ruby glow)
    const blushMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.35,
    });
    const blushGeo = new THREE.CircleGeometry(0.045, 16);
    const leftBlush = new THREE.Mesh(blushGeo, blushMat);
    leftBlush.position.set(-0.31, -0.06, 0.64);
    leftBlush.rotation.y = -0.3;
    const rightBlush = new THREE.Mesh(blushGeo, blushMat);
    rightBlush.position.set(0.31, -0.06, 0.64);
    rightBlush.rotation.y = 0.3;
    headGroup.add(leftBlush);
    headGroup.add(rightBlush);

    // Cute side ears / antennas with metallic ring and cyan accent
    const createEar = (isRight: boolean) => {
      const earGroup = new THREE.Group();
      const sign = isRight ? 1 : -1;
      earGroup.position.set(sign * 0.74, 0.06, 0);
      earGroup.rotation.z = sign * -0.25;

      // Metallic base disc
      const earBase = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.12, 0.08, 24),
        silverMetalMat
      );
      earBase.rotation.z = Math.PI / 2;
      earGroup.add(earBase);

      // White rounded ear cap
      const earCap = new THREE.Mesh(
        new THREE.SphereGeometry(0.11, 16, 16),
        whiteBodyMat
      );
      earCap.position.x = sign * 0.05;
      earGroup.add(earCap);

      // Warm gold accent ring
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.12, 0.016, 12, 24),
        goldGlowMat
      );
      ring.rotation.y = Math.PI / 2;
      ring.position.x = sign * 0.03;
      earGroup.add(ring);

      return earGroup;
    };

    headGroup.add(createEar(false));
    headGroup.add(createEar(true));

    // D. Right Arm: Holding the Futuristic Glowing Sword (Raised)
    const rightArmGroup = new THREE.Group();
    rightArmGroup.position.set(-0.76, 0.45, 0.04);
    upperBodyGroup.add(rightArmGroup);

    // Shoulder joint
    const rShoulder = new THREE.Mesh(new THREE.SphereGeometry(0.16, 20, 20), silverMetalMat);
    rightArmGroup.add(rShoulder);

    // Upper arm (raised upward and forward)
    const rUpperArmGeo = new THREE.CapsuleGeometry(0.12, 0.28, 16, 16);
    const rUpperArm = new THREE.Mesh(rUpperArmGeo, whiteBodyMat);
    rUpperArm.position.set(-0.16, 0.18, 0.12);
    rUpperArm.rotation.set(-0.4, 0.2, -0.6);
    rUpperArm.castShadow = true;
    rightArmGroup.add(rUpperArm);

    // Elbow joint
    const rElbow = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), silverMetalMat);
    rElbow.position.set(-0.28, 0.42, 0.24);
    rightArmGroup.add(rElbow);

    // Forearm pointing up holding sword
    const rForearmGeo = new THREE.CapsuleGeometry(0.11, 0.32, 16, 16);
    const rForearm = new THREE.Mesh(rForearmGeo, whiteBodyMat);
    rForearm.position.set(-0.34, 0.68, 0.34);
    rForearm.rotation.set(-0.2, 0.1, -0.2);
    rForearm.castShadow = true;
    rightArmGroup.add(rForearm);

    // Hand gripping sword hilt
    const rHand = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 16), whiteBodyMat);
    rHand.position.set(-0.38, 0.92, 0.4);
    rightArmGroup.add(rHand);

    // Futuristic Light Sword (Saber)
    const swordGroup = new THREE.Group();
    swordGroup.position.set(-0.38, 0.94, 0.4);
    swordGroup.rotation.set(0.18, 0, -0.22); // subtle heroic tilt

    // Metallic hilt
    const hilt = new THREE.Mesh(
      new THREE.CylinderGeometry(0.045, 0.048, 0.28, 16),
      silverMetalMat
    );
    hilt.position.y = 0.02;
    swordGroup.add(hilt);

    // Warm gold emitter pommel
    const pommel = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.045, 0.04, 16),
      goldGlowMat
    );
    pommel.position.y = -0.13;
    swordGroup.add(pommel);

    // Glowing energy blade (Core white beam + outer translucent warm amber gold halo)
    const bladeCore = new THREE.Mesh(
      new THREE.CylinderGeometry(0.025, 0.025, 0.98, 16),
      new THREE.MeshBasicMaterial({ color: 0xffffff })
    );
    bladeCore.position.y = 0.65;
    swordGroup.add(bladeCore);

    const bladeHalo = new THREE.Mesh(
      new THREE.CylinderGeometry(0.052, 0.052, 1.02, 16),
      new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        transparent: true,
        opacity: 0.65
      })
    );
    bladeHalo.position.y = 0.65;
    swordGroup.add(bladeHalo);

    // Soft local point light from the blade (warm gold glow)
    const swordLight = new THREE.PointLight(0xf59e0b, 1.4, 2.5);
    swordLight.position.set(0, 0.6, 0);
    swordGroup.add(swordLight);

    rightArmGroup.add(swordGroup);

    // E. Left Arm: Relaxed at Side
    const leftArmGroup = new THREE.Group();
    leftArmGroup.position.set(0.76, 0.45, 0.04);
    upperBodyGroup.add(leftArmGroup);

    // Left shoulder
    const lShoulder = new THREE.Mesh(new THREE.SphereGeometry(0.16, 20, 20), silverMetalMat);
    leftArmGroup.add(lShoulder);

    // Left upper arm
    const lUpperArmGeo = new THREE.CapsuleGeometry(0.12, 0.28, 16, 16);
    const lUpperArm = new THREE.Mesh(lUpperArmGeo, whiteBodyMat);
    lUpperArm.position.set(0.12, -0.16, 0.05);
    lUpperArm.rotation.set(0.1, 0, -0.15);
    lUpperArm.castShadow = true;
    leftArmGroup.add(lUpperArm);

    // Left elbow
    const lElbow = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 16), silverMetalMat);
    lElbow.position.set(0.18, -0.38, 0.08);
    leftArmGroup.add(lElbow);

    // Left forearm
    const lForearmGeo = new THREE.CapsuleGeometry(0.105, 0.26, 16, 16);
    const lForearm = new THREE.Mesh(lForearmGeo, whiteBodyMat);
    lForearm.position.set(0.22, -0.58, 0.14);
    lForearm.rotation.set(0.2, 0, -0.1);
    lForearm.castShadow = true;
    leftArmGroup.add(lForearm);

    // Left hand with cute rounded fingers
    const lHand = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 16), whiteBodyMat);
    lHand.position.set(0.24, -0.76, 0.18);
    leftArmGroup.add(lHand);

    // F. Legs & Boots (Standing firmly on the ground)
    const createLeg = (isRight: boolean) => {
      const legGroup = new THREE.Group();
      const sign = isRight ? -1 : 1;
      legGroup.position.set(sign * 0.28, -0.68, 0);

      // Hip joint
      const hip = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 16), silverMetalMat);
      legGroup.add(hip);

      // Thigh
      const thigh = new THREE.Mesh(
        new THREE.CapsuleGeometry(0.13, 0.26, 16, 16),
        whiteBodyMat
      );
      thigh.position.set(0, -0.22, 0);
      thigh.castShadow = true;
      legGroup.add(thigh);

      // Knee joint
      const knee = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), silverMetalMat);
      knee.position.set(0, -0.42, 0.02);
      legGroup.add(knee);

      // Shin / Calf
      const shin = new THREE.Mesh(
        new THREE.CapsuleGeometry(0.125, 0.26, 16, 16),
        whiteBodyMat
      );
      shin.position.set(0, -0.62, 0);
      shin.castShadow = true;
      legGroup.add(shin);

      // Foot / Boot (rounded cute robot shoe with metallic sole)
      const footGroup = new THREE.Group();
      footGroup.position.set(0, -0.74, 0.06);

      // White curved boot
      const bootGeo = new THREE.SphereGeometry(0.17, 24, 24);
      bootGeo.scale(0.9, 0.55, 1.35);
      const boot = new THREE.Mesh(bootGeo, whiteBodyMat);
      boot.position.y = 0.02;
      boot.castShadow = true;
      footGroup.add(boot);

      // Silver metallic sole
      const soleGeo = new THREE.CylinderGeometry(0.16, 0.17, 0.04, 24);
      soleGeo.scale(0.88, 1, 1.3);
      const sole = new THREE.Mesh(soleGeo, silverMetalMat);
      sole.position.set(0, -0.04, 0);
      footGroup.add(sole);

      // Warm gold accent light ring at ankle
      const ankleRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.125, 0.015, 12, 24),
        goldGlowMat
      );
      ankleRing.rotation.x = Math.PI / 2;
      ankleRing.position.y = 0.07;
      footGroup.add(ankleRing);

      legGroup.add(footGroup);
      return legGroup;
    };

    const rightLeg = createLeg(true);
    const leftLeg = createLeg(false);
    rootGroup.add(rightLeg);
    rootGroup.add(leftLeg);

    // Dynamic support for user-supplied /robot.glb:
    // If an external GLB is placed in public/robot.glb, seamlessly render it!
    const gltfLoader = new GLTFLoader();
    gltfLoader.load(
      '/robot.glb',
      (gltf) => {
        upperBodyGroup.visible = false;
        rightLeg.visible = false;
        leftLeg.visible = false;
        const customModel = gltf.scene;
        const bbox = new THREE.Box3().setFromObject(customModel);
        const sz = bbox.getSize(new THREE.Vector3());
        const maxDim = Math.max(sz.x, sz.y, sz.z);
        if (maxDim > 0) {
          const sc = 2.4 / maxDim;
          customModel.scale.set(sc, sc, sc);
        }
        customModel.position.set(0, -1.2, 0);
        rootGroup.add(customModel);
      },
      undefined,
      () => {
        // Fallback: Built-in procedural 3D model renders with zero latency
      }
    );

    // --- 5. Subtle Interactive Controls (Mouse Drag Rotation + Mouse Parallax) ---
    let isMouseDown = false;
    let prevMouseX = 0;
    let targetRotationY = -0.14;
    let targetHeadTiltX = 0;
    let targetHeadTiltY = 0;

    const handlePointerDown = (e: MouseEvent) => {
      isMouseDown = true;
      prevMouseX = e.clientX;
      setIsDragging(true);
    };

    const handlePointerMove = (e: MouseEvent) => {
      // Parallax calculation relative to container center
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      targetHeadTiltY = normX * 0.22;
      targetHeadTiltX = -normY * 0.14;

      if (isMouseDown) {
        const deltaX = e.clientX - prevMouseX;
        prevMouseX = e.clientX;
        targetRotationY += deltaX * 0.012;
      }
    };

    const handlePointerUp = () => {
      isMouseDown = false;
      setIsDragging(false);
    };

    const handlePointerLeave = () => {
      isMouseDown = false;
      setIsDragging(false);
      targetHeadTiltX = 0;
      targetHeadTiltY = 0;
    };

    container.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);
    container.addEventListener('mouseleave', handlePointerLeave);

    // --- 6. Animation Loop (Subtle breathing, head sway, blade pulse, smooth damping) ---
    let animFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animFrameId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Smooth damping for root rotation (user drag)
      rootGroup.rotation.y += (targetRotationY - rootGroup.rotation.y) * 0.1;

      // Gentle breathing idle floating (subtle 2mm up/down)
      upperBodyGroup.position.y = Math.sin(time * 2.0) * 0.025;

      // Smooth head parallax + gentle idle sway
      const idleHeadSway = Math.sin(time * 1.4) * 0.04;
      headGroup.rotation.y += ((targetHeadTiltY + idleHeadSway) - headGroup.rotation.y) * 0.08;
      headGroup.rotation.x += (targetHeadTiltX - headGroup.rotation.x) * 0.08;

      // Gentle sword hum
      swordGroup.rotation.z = -0.22 + Math.sin(time * 2.2) * 0.02;
      swordLight.intensity = 1.0 + Math.sin(time * 3.6) * 0.25;

      renderer.render(scene, camera);
    };

    animate();

    // --- 7. Handle Resize ---
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth || 240;
      const newH = container.clientHeight || 260;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // --- Cleanup on Unmount ---
    return () => {
      cancelAnimationFrame(animFrameId);
      container.removeEventListener('mousedown', handlePointerDown);
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
      container.removeEventListener('mouseleave', handlePointerLeave);
      resizeObserver.disconnect();

      renderer.dispose();
      shadowTexture.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className={`robot-3d-container ${className || ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      title="3D Shorts Autopilot Mascot — Drag to rotate"
      style={{
        width: '230px',
        height: '250px',
        position: 'relative',
        cursor: isDragging ? 'grabbing' : isHovered ? 'grab' : 'default',
        userSelect: 'none',
        touchAction: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    />
  );
};
