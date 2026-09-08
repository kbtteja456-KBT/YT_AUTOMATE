import React, { useEffect, useRef, useState } from 'react';

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
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth <= 768 || window.matchMedia('(hover: none) and (pointer: coarse)').matches;
  });

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth <= 768 || window.matchMedia('(hover: none) and (pointer: coarse)').matches;
      setIsMobile(mobile);
    };

    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    // If on mobile/touch screen, do not run heavy 2D canvas animation loops to preserve battery and 60fps scrolling
    if (isMobile) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
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

    // Optimized pulse count for high desktop performance
    const MAX_PULSES = 30;
    const pulses: CircuitPulse[] = [];

    const spawnPulse = (nearMouse = false): CircuitPulse => {
      const color: 'orange' | 'green' = Math.random() > 0.5 ? 'orange' : 'green';

      let x: number;
      let y: number;

      if (nearMouse && mouse.active) {
        const angle = Math.random() * Math.PI * 2;
        const rad = 200 + Math.random() * 400;
        x = mouse.x + Math.cos(angle) * rad;
        y = mouse.y + Math.sin(angle) * rad;
      } else {
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
      const baseSpeed = 2.4 + Math.random() * 2.8;

      return {
        x,
        y,
        vx: dir.vx,
        vy: dir.vy,
        speed: baseSpeed,
        baseSpeed,
        color,
        trail: [],
        maxTrailLength: 18 + Math.floor(Math.random() * 18),
        life: 0,
        maxLife: 90 + Math.floor(Math.random() * 140),
        thickness: 1.6 + Math.random() * 1.4,
        turnCooldown: 15 + Math.floor(Math.random() * 25)
      };
    };

    for (let i = 0; i < MAX_PULSES; i++) {
      pulses.push(spawnPulse());
    }

    let lastFrameTime = performance.now();

    // Animation loop with frame pacing and visibility check
    const render = (time: number) => {
      if (document.hidden) {
        animFrameId = requestAnimationFrame(render);
        return;
      }

      const delta = time - lastFrameTime;
      // Cap render rate to ~60fps (14ms minimum) to protect 120Hz/144Hz monitors from overtaxing
      if (delta < 14) {
        animFrameId = requestAnimationFrame(render);
        return;
      }
      lastFrameTime = time;

      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = 'screen';

      const isCursorActive = mouse.active && (time - mouse.lastMoved < 3000);

      // Draw subtle cursor energy nexus if active
      if (isCursorActive) {
        const auraGrad = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          60
        );
        auraGrad.addColorStop(0, 'rgba(255, 255, 255, 0.35)');
        auraGrad.addColorStop(0.3, 'rgba(245, 158, 11, 0.2)');
        auraGrad.addColorStop(0.65, 'rgba(16, 185, 129, 0.12)');
        auraGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 60, 0, Math.PI * 2);
        ctx.fillStyle = auraGrad;
        ctx.fill();
      }

      for (let i = 0; i < pulses.length; i++) {
        const p = pulses[i];

        p.trail.unshift({ x: p.x, y: p.y });
        if (p.trail.length > p.maxTrailLength) {
          p.trail.pop();
        }

        // --- MAGNETIC CURSOR ATTRACTION LOGIC ---
        if (isCursorActive) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.hypot(dx, dy);

          if (dist > 15 && dist < 700) {
            const pullStrength = Math.min(0.24, 150 / (dist + 80));
            const targetVx = dx / dist;
            const targetVy = dy / dist;

            p.vx += (targetVx - p.vx) * pullStrength;
            p.vy += (targetVy - p.vy) * pullStrength;

            const mag = Math.hypot(p.vx, p.vy);
            if (mag > 0.001) {
              p.vx /= mag;
              p.vy /= mag;
            }

            p.speed = Math.min(7.5, p.speed + 0.18);

            if (dist < 90 && Math.random() < 0.2) {
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              const midX = (p.x + mouse.x) / 2 + (Math.random() - 0.5) * 12;
              const midY = (p.y + mouse.y) / 2 + (Math.random() - 0.5) * 12;
              ctx.lineTo(midX, midY);
              ctx.lineTo(mouse.x, mouse.y);
              ctx.strokeStyle = p.color === 'orange' ? ORANGE_COLORS.spark : GREEN_COLORS.spark;
              ctx.lineWidth = 1;
              ctx.shadowColor = p.color === 'orange' ? ORANGE_COLORS.glow : GREEN_COLORS.glow;
              ctx.shadowBlur = 6;
              ctx.stroke();
            }
          } else if (dist <= 15) {
            const scatterAngle = Math.random() * Math.PI * 2;
            p.vx = Math.cos(scatterAngle);
            p.vy = Math.sin(scatterAngle);
            p.speed = 5.0 + Math.random() * 2.5;
            p.turnCooldown = 20;
          }
        } else {
          p.speed += (p.baseSpeed - p.speed) * 0.04;

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
            p.turnCooldown = 20 + Math.floor(Math.random() * 30);
          }
        }

        // Advance position
        p.x += p.vx * p.speed;
        p.y += p.vy * p.speed;
        p.life++;

        const pal = p.color === 'orange' ? ORANGE_COLORS : GREEN_COLORS;

        // Draw electrical trail with lightweight blur
        if (p.trail.length > 1) {
          ctx.beginPath();
          ctx.moveTo(p.trail[0].x, p.trail[0].y);
          for (let j = 1; j < p.trail.length; j++) {
            ctx.lineTo(p.trail[j].x, p.trail[j].y);
          }

          const lifeRatio = Math.sin((p.life / p.maxLife) * Math.PI);
          const alpha = Math.max(0.12, lifeRatio * 0.85);

          // Outer trail with light blur
          ctx.strokeStyle = pal.trail;
          ctx.lineWidth = p.thickness * (isCursorActive ? 1.2 : 1);
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
          ctx.shadowColor = pal.glow;
          ctx.shadowBlur = 6;
          ctx.globalAlpha = alpha;
          ctx.stroke();

          // Inner white filament
          ctx.beginPath();
          ctx.moveTo(p.trail[0].x, p.trail[0].y);
          const corePoints = Math.min(6, p.trail.length);
          for (let k = 1; k < corePoints; k++) {
            ctx.lineTo(p.trail[k].x, p.trail[k].y);
          }
          ctx.strokeStyle = pal.core;
          ctx.lineWidth = p.thickness * 0.5;
          ctx.shadowBlur = 8;
          ctx.globalAlpha = alpha;
          ctx.stroke();
        }

        // Draw glowing head spark
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.thickness * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = pal.core;
        ctx.shadowColor = pal.glow;
        ctx.shadowBlur = 8;
        ctx.globalAlpha = 1;
        ctx.fill();

        const outOfBounds =
          p.x < -60 || p.x > width + 60 || p.y < -60 || p.y > height + 60;
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
  }, [isMobile]);

  // Mobile gets a zero-overhead subtle CSS glow instead of a 60fps canvas loop
  if (isMobile) {
    return (
      <div
        className="mobile-ambient-glow"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: 1,
          background: 'radial-gradient(ellipse 80% 40% at 50% -10%, rgba(245, 158, 11, 0.08) 0%, transparent 60%)'
        }}
      />
    );
  }

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
        zIndex: 1,
        opacity: 0.9
      }}
    />
  );
};
