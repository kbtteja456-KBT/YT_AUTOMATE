import React, { useEffect, useRef } from 'react';

interface TrailPoint {
  x: number;
  y: number;
}

interface CircuitPulse {
  x: number;
  y: number;
  vx: number;
  vy: number;
  speed: number;
  baseSpeed: number;
  color: 'orange' | 'green';
  trail: TrailPoint[];
  maxTrailLength: number;
  life: number;
  maxLife: number;
  thickness: number;
  turnCooldown: number;
}

export const CircuitStormCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mouse tracking for cursor storm attraction
    const mouse = {
      x: -1000,
      y: -1000,
      active: false,
      lastMoved: 0
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      mouse.active = true;
      mouse.lastMoved = performance.now();
    };

    const handleMouseLeave = () => {
      mouse.active = false;
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('resize', handleResize);

    // Color definitions (Electric Amber Orange & Radiant Emerald Green)
    const ORANGE_COLORS = {
      core: '#ffffff',
      glow: '#fbbf24',
      trail: '#f59e0b',
      spark: 'rgba(251, 191, 36, 0.8)'
    };

    const GREEN_COLORS = {
      core: '#ffffff',
      glow: '#34d399',
      trail: '#10b981',
      spark: 'rgba(52, 211, 153, 0.8)'
    };

    const MAX_PULSES = 60;
    const pulses: CircuitPulse[] = [];

    const spawnPulse = (nearMouse = false): CircuitPulse => {
      const color: 'orange' | 'green' = Math.random() > 0.5 ? 'orange' : 'green';

      let x: number;
      let y: number;

      if (nearMouse && mouse.active) {
        // Spawn scattered in proximity to cursor
        const angle = Math.random() * Math.PI * 2;
        const rad = 200 + Math.random() * 400;
        x = mouse.x + Math.cos(angle) * rad;
        y = mouse.y + Math.sin(angle) * rad;
      } else {
        // Spawn from edges or random field position
        const edge = Math.random();
        if (edge < 0.25) {
          x = -20;
          y = Math.random() * height;
        } else if (edge < 0.5) {
          x = width + 20;
          y = Math.random() * height;
        } else if (edge < 0.75) {
          x = Math.random() * width;
          y = -20;
        } else {
          x = Math.random() * width;
          y = height + 20;
        }
      }

      // Initial direction (orthogonal or angled)
      const dirs = [
        { vx: 1, vy: 0 },
        { vx: -1, vy: 0 },
        { vx: 0, vy: 1 },
        { vx: 0, vy: -1 },
        { vx: 0.707, vy: 0.707 },
        { vx: -0.707, vy: 0.707 },
        { vx: 0.707, vy: -0.707 },
        { vx: -0.707, vy: -0.707 }
      ];
      const dir = dirs[Math.floor(Math.random() * dirs.length)];
      const baseSpeed = 2.8 + Math.random() * 3.5;

      return {
        x,
        y,
        vx: dir.vx,
        vy: dir.vy,
        speed: baseSpeed,
        baseSpeed,
        color,
        trail: [],
        maxTrailLength: 22 + Math.floor(Math.random() * 26),
        life: 0,
        maxLife: 100 + Math.floor(Math.random() * 160),
        thickness: 1.8 + Math.random() * 1.8,
        turnCooldown: 15 + Math.floor(Math.random() * 30)
      };
    };

    for (let i = 0; i < MAX_PULSES; i++) {
      pulses.push(spawnPulse());
    }

    // Animation loop
    const render = (time: number) => {
      ctx.clearRect(0, 0, width, height);

      // Additive blending for electric plasma storm glow
      ctx.globalCompositeOperation = 'screen';

      const isCursorActive = mouse.active && (time - mouse.lastMoved < 3000);

      // Draw subtle cursor energy nexus if active
      if (isCursorActive) {
        // Dual-color electric pulse ring around cursor
        const auraGrad = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          65
        );
        auraGrad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
        auraGrad.addColorStop(0.3, 'rgba(245, 158, 11, 0.25)');
        auraGrad.addColorStop(0.65, 'rgba(16, 185, 129, 0.18)');
        auraGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 65, 0, Math.PI * 2);
        ctx.fillStyle = auraGrad;
        ctx.fill();
      }

      for (let i = 0; i < pulses.length; i++) {
        const p = pulses[i];

        // Store trail point
        p.trail.unshift({ x: p.x, y: p.y });
        if (p.trail.length > p.maxTrailLength) {
          p.trail.pop();
        }

        // --- MAGNETIC CURSOR ATTRACTION LOGIC ---
        if (isCursorActive) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.hypot(dx, dy);

          if (dist > 15 && dist < 850) {
            // Magnetic steering force toward cursor
            const pullStrength = Math.min(0.28, 180 / (dist + 80));
            const targetVx = dx / dist;
            const targetVy = dy / dist;

            // Interpolate velocity vector toward cursor
            p.vx += (targetVx - p.vx) * pullStrength;
            p.vy += (targetVy - p.vy) * pullStrength;

            // Re-normalize direction vector
            const mag = Math.hypot(p.vx, p.vy);
            if (mag > 0.001) {
              p.vx /= mag;
              p.vy /= mag;
            }

            // Accelerate as pulses storm towards the cursor
            p.speed = Math.min(8.8, p.speed + 0.22);

            // Draw micro lightning arc when close to cursor
            if (dist < 110 && Math.random() < 0.25) {
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              const midX = (p.x + mouse.x) / 2 + (Math.random() - 0.5) * 16;
              const midY = (p.y + mouse.y) / 2 + (Math.random() - 0.5) * 16;
              ctx.lineTo(midX, midY);
              ctx.lineTo(mouse.x, mouse.y);
              ctx.strokeStyle = p.color === 'orange' ? ORANGE_COLORS.spark : GREEN_COLORS.spark;
              ctx.lineWidth = 1.2;
              ctx.shadowColor = p.color === 'orange' ? ORANGE_COLORS.glow : GREEN_COLORS.glow;
              ctx.shadowBlur = 8;
              ctx.stroke();
            }
          } else if (dist <= 15) {
            // Slingshot / orbital discharge around cursor
            const scatterAngle = Math.random() * Math.PI * 2;
            p.vx = Math.cos(scatterAngle);
            p.vy = Math.sin(scatterAngle);
            p.speed = 5.5 + Math.random() * 3.5;
            p.turnCooldown = 25;
          }
        } else {
          // Decay back to base speed when cursor idle
          p.speed += (p.baseSpeed - p.speed) * 0.04;

          // Motherboard circuit 90-degree orthogonal turns
          p.turnCooldown--;
          if (p.turnCooldown <= 0 && Math.random() < 0.1) {
            if (Math.abs(p.vx) > 0.1 && Math.abs(p.vy) < 0.1) {
              p.vx = 0;
              p.vy = Math.random() > 0.5 ? 1 : -1;
            } else if (Math.abs(p.vy) > 0.1 && Math.abs(p.vx) < 0.1) {
              p.vy = 0;
              p.vx = Math.random() > 0.5 ? 1 : -1;
            } else {
              if (Math.random() > 0.5) {
                p.vx = p.vx > 0 ? 1 : -1;
                p.vy = 0;
              } else {
                p.vx = 0;
                p.vy = p.vy > 0 ? 1 : -1;
              }
            }
            p.turnCooldown = 20 + Math.floor(Math.random() * 35);
          }
        }

        // Advance position
        p.x += p.vx * p.speed;
        p.y += p.vy * p.speed;
        p.life++;

        // Palette selection
        const pal = p.color === 'orange' ? ORANGE_COLORS : GREEN_COLORS;

        // Draw electrical trail
        if (p.trail.length > 1) {
          ctx.beginPath();
          ctx.moveTo(p.trail[0].x, p.trail[0].y);
          for (let j = 1; j < p.trail.length; j++) {
            ctx.lineTo(p.trail[j].x, p.trail[j].y);
          }

          const lifeRatio = Math.sin((p.life / p.maxLife) * Math.PI);
          const alpha = Math.max(0.12, lifeRatio * 0.9);

          // Outer glowing lightning trail
          ctx.strokeStyle = pal.trail;
          ctx.lineWidth = p.thickness * (isCursorActive ? 1.3 : 1);
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
          ctx.shadowColor = pal.glow;
          ctx.shadowBlur = 12;
          ctx.globalAlpha = alpha;
          ctx.stroke();

          // Intense white-hot inner energy filament
          ctx.beginPath();
          ctx.moveTo(p.trail[0].x, p.trail[0].y);
          const corePoints = Math.min(8, p.trail.length);
          for (let k = 1; k < corePoints; k++) {
            ctx.lineTo(p.trail[k].x, p.trail[k].y);
          }
          ctx.strokeStyle = pal.core;
          ctx.lineWidth = p.thickness * 0.55;
          ctx.shadowBlur = 16;
          ctx.globalAlpha = alpha;
          ctx.stroke();
        }

        // Draw glowing head spark / energy bolt tip
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.thickness * 1.6, 0, Math.PI * 2);
        ctx.fillStyle = pal.core;
        ctx.shadowColor = pal.glow;
        ctx.shadowBlur = 18;
        ctx.globalAlpha = 1;
        ctx.fill();

        // Respawn if pulse expired or drifted out of bounds
        const outOfBounds =
          p.x < -80 || p.x > width + 80 || p.y < -80 || p.y > height + 80;
        if (p.life >= p.maxLife || outOfBounds) {
          pulses[i] = spawnPulse(isCursorActive);
        }
      }

      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';

      animFrameId = requestAnimationFrame(render);
    };

    animFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 1, // Layered above the background image, underneath cards & controls
        opacity: 0.9
      }}
    />
  );
};
