import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Sparkles, Stars } from '@react-three/drei';
import * as THREE from 'three';

type ScenePage = 'home' | 'question' | 'solve' | 'results' | 'finance' | 'llm-config';

function pageAccent(page: ScenePage) {
  switch (page) {
    case 'solve':
      return { primary: '#38bdf8', secondary: '#818cf8', tertiary: '#e0f2fe' };
    case 'results':
      return { primary: '#22c55e', secondary: '#14b8a6', tertiary: '#dcfce7' };
    case 'finance':
      return { primary: '#f59e0b', secondary: '#ef4444', tertiary: '#fef3c7' };
    case 'llm-config':
      return { primary: '#a855f7', secondary: '#ec4899', tertiary: '#fae8ff' };
    case 'question':
      return { primary: '#0ea5e9', secondary: '#06b6d4', tertiary: '#cffafe' };
    case 'home':
    default:
      return { primary: '#2563eb', secondary: '#8b5cf6', tertiary: '#dbeafe' };
  }
}

function FloatingNodes({
  primary,
  secondary,
}: {
  primary: string;
  secondary: string;
}) {
  const nodes = useMemo(
    () =>
      Array.from({ length: 18 }, (_, index) => ({
        key: index,
        position: [
          (Math.random() - 0.5) * 16,
          (Math.random() - 0.5) * 9,
          (Math.random() - 0.5) * 10,
        ] as [number, number, number],
        scale: 0.06 + Math.random() * 0.16,
        speed: 0.7 + Math.random() * 1.3,
        color: index % 2 === 0 ? primary : secondary,
      })),
    [primary, secondary],
  );

  return (
    <>
      {nodes.map((node) => (
        <Float
          key={node.key}
          speed={node.speed}
          rotationIntensity={1.2}
          floatIntensity={1.6}
          position={node.position}
        >
          <mesh scale={node.scale}>
            <sphereGeometry args={[1, 12, 12]} />
            <meshBasicMaterial color={node.color} transparent opacity={0.72} />
          </mesh>
        </Float>
      ))}
    </>
  );
}

function RibbonWave({
  color,
  offset,
  amplitude,
  mouse,
}: {
  color: string;
  offset: number;
  amplitude: number;
  mouse: { x: number; y: number };
}) {
  const geometry = useMemo(() => new THREE.BufferGeometry(), []);
  const material = useMemo(
    () =>
      new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.34,
      }),
    [color],
  );
  const points = useMemo(() => new Float32Array(180 * 3), []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    for (let i = 0; i < 180; i += 1) {
      const x = (i / 179) * 18 - 9;
      const y =
        Math.sin(i * 0.14 + t * 1.15 + offset) * amplitude +
        Math.cos(t * 0.7 + offset) * 0.35 +
        mouse.y * 1.2;
      const z = Math.cos(i * 0.1 + t * 0.86 + offset) * 0.9 + mouse.x * 1.4;
      points[i * 3] = x;
      points[i * 3 + 1] = y;
      points[i * 3 + 2] = z;
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(points, 3));
    geometry.attributes.position.needsUpdate = true;
  });

  return <line geometry={geometry} material={material} />;
}

function MouseField({
  primary,
  secondary,
  tertiary,
  mouse,
}: {
  primary: string;
  secondary: string;
  tertiary: string;
  mouse: { x: number; y: number };
}) {
  const groupRef = useRef<THREE.Group | null>(null);

  useFrame(() => {
    if (!groupRef.current) {
      return;
    }
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, mouse.x * 0.45, 0.05);
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, mouse.y * 0.18, 0.05);
    groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, mouse.x * 0.55, 0.05);
    groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, mouse.y * 0.35, 0.05);
  });

  return (
    <group ref={groupRef}>
      <RibbonWave color={primary} offset={0} amplitude={0.68} mouse={mouse} />
      <RibbonWave color={secondary} offset={1.8} amplitude={0.96} mouse={mouse} />
      <RibbonWave color={tertiary} offset={3.1} amplitude={0.42} mouse={mouse} />
      <FloatingNodes primary={primary} secondary={secondary} />
    </group>
  );
}

export default function GlobalSceneBackdrop({ page }: { page: ScenePage }) {
  const accent = pageAccent(page);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setMouse({
        x: (event.clientX / window.innerWidth) * 2 - 1,
        y: (event.clientY / window.innerHeight) * 2 - 1,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className="absolute inset-0 opacity-100"
        style={{
          background: `
            radial-gradient(circle at 18% 12%, ${accent.tertiary} 0%, rgba(255,255,255,0) 30%),
            radial-gradient(circle at 84% 18%, ${accent.primary}26 0%, rgba(255,255,255,0) 26%),
            radial-gradient(circle at 78% 72%, ${accent.secondary}24 0%, rgba(255,255,255,0) 28%),
            radial-gradient(circle at 22% 76%, ${accent.primary}18 0%, rgba(255,255,255,0) 24%),
            linear-gradient(180deg, rgba(248,250,252,0.96) 0%, rgba(241,245,249,0.76) 48%, rgba(248,250,252,0.96) 100%)
          `,
        }}
      />
      <div className="absolute inset-0">
        <Canvas camera={{ position: [0, 0, 9.5], fov: 42 }}>
          <color attach="background" args={['#f8fbff']} />
          <fog attach="fog" args={['#f8fbff', 10, 20]} />
          <ambientLight intensity={0.72} />
          <pointLight position={[6, 4, 5]} intensity={8} color={accent.primary} />
          <pointLight position={[-5, -1, 4]} intensity={5} color={accent.secondary} />
          <Stars radius={32} depth={18} count={1100} factor={2.5} saturation={0} fade speed={0.7} />
          <Sparkles count={54} scale={[16, 8, 10]} size={3.8} speed={0.24} color={accent.primary} opacity={0.24} />
          <MouseField primary={accent.primary} secondary={accent.secondary} tertiary={accent.tertiary} mouse={mouse} />
        </Canvas>
      </div>
      <div className="absolute left-[8%] top-[14%] h-72 w-72 rounded-full bg-white/35 blur-3xl" />
      <div className="absolute right-[6%] top-[36%] h-80 w-80 rounded-full bg-white/25 blur-3xl" />
      <div className="absolute bottom-[8%] left-[28%] h-64 w-64 rounded-full bg-white/20 blur-3xl" />
    </div>
  );
}
