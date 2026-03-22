import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, OrbitControls, Sparkles, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface PDE3DViewerProps {
  solution: number[];
  nx: number;
  ny: number;
  nz: number;
  sliceAxis: 'x' | 'y' | 'z';
  sliceIndex: number;
}

type PointCloudBuffers = {
  backgroundPositions: Float32Array;
  slicePositions: Float32Array;
  sliceColors: Float32Array;
};

function VolumeBounds({
  width,
  height,
  depth,
}: {
  width: number;
  height: number;
  depth: number;
}) {
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(width, height, depth)), [width, height, depth]);

  return (
    <lineSegments geometry={edges}>
      <lineBasicMaterial color="#1e3a8a" transparent opacity={0.4} />
    </lineSegments>
  );
}

function SliceHalo({
  axis,
  index,
  nx,
  ny,
  nz,
}: {
  axis: 'x' | 'y' | 'z';
  index: number;
  nx: number;
  ny: number;
  nz: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const step = 0.44;
  const width = Math.max(nx - 1, 1) * step + step * 0.7;
  const height = Math.max(ny - 1, 1) * step + step * 0.7;
  const depth = Math.max(nz - 1, 1) * step + step * 0.7;

  const { rotation, position, planeWidth, planeHeight } = useMemo(() => {
    if (axis === 'x') {
      return {
        rotation: [0, Math.PI / 2, 0] as [number, number, number],
        position: [((index - (nx - 1) / 2) * step), 0, 0] as [number, number, number],
        planeWidth: depth,
        planeHeight: height,
      };
    }

    if (axis === 'y') {
      return {
        rotation: [Math.PI / 2, 0, 0] as [number, number, number],
        position: [0, ((index - (ny - 1) / 2) * step), 0] as [number, number, number],
        planeWidth: width,
        planeHeight: depth,
      };
    }

    return {
      rotation: [0, 0, 0] as [number, number, number],
      position: [0, 0, ((index - (nz - 1) / 2) * step)] as [number, number, number],
      planeWidth: width,
      planeHeight: height,
    };
  }, [axis, index, nx, ny, nz, step, width, height, depth]);

  useFrame((state) => {
    if (!meshRef.current) {
      return;
    }

    const pulse = 0.14 + (Math.sin(state.clock.elapsedTime * 2.4) + 1) * 0.06;
    const material = meshRef.current.material as THREE.MeshBasicMaterial;
    material.opacity = pulse;
  });

  return (
    <mesh ref={meshRef} position={position} rotation={rotation}>
      <planeGeometry args={[planeWidth, planeHeight]} />
      <meshBasicMaterial color="#38bdf8" transparent opacity={0.18} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
    </mesh>
  );
}

function AmbientOrbs() {
  const positions = useMemo(
    () =>
      Array.from({ length: 10 }, (_, index) => ({
        key: index,
        position: [
          (Math.random() - 0.5) * 10,
          (Math.random() - 0.5) * 8,
          (Math.random() - 0.5) * 10,
        ] as [number, number, number],
        scale: 0.08 + Math.random() * 0.12,
        speed: 1.2 + Math.random() * 1.4,
      })),
    [],
  );

  return (
    <>
      {positions.map((orb) => (
        <Float
          key={orb.key}
          speed={orb.speed}
          rotationIntensity={1.4}
          floatIntensity={1.8}
          position={orb.position}
        >
          <mesh scale={orb.scale}>
            <sphereGeometry args={[1, 10, 10]} />
            <meshBasicMaterial color="#7dd3fc" transparent opacity={0.55} />
          </mesh>
        </Float>
      ))}
    </>
  );
}

function PulseLights() {
  const lightA = useRef<THREE.PointLight>(null);
  const lightB = useRef<THREE.PointLight>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (lightA.current) {
      lightA.current.intensity = 16 + Math.sin(t * 1.3) * 2.4;
    }
    if (lightB.current) {
      lightB.current.intensity = 7 + Math.cos(t * 1.1) * 1.6;
    }
  });

  return (
    <>
      <pointLight ref={lightA} position={[12, 10, 14]} intensity={16} color="#38bdf8" />
      <pointLight ref={lightB} position={[-10, -8, -6]} intensity={7} color="#8b5cf6" />
    </>
  );
}

function buildColor(normalized: number): THREE.Color {
  const color = new THREE.Color();
  color.setHSL((1 - normalized) * 0.72, 0.95, 0.54);
  return color;
}

export default function PDE3DViewer({
  solution,
  nx,
  ny,
  nz,
  sliceAxis,
  sliceIndex,
}: PDE3DViewerProps) {
  const { backgroundPositions, slicePositions, sliceColors } = useMemo<PointCloudBuffers>(() => {
    if (!solution.length || nx <= 0 || ny <= 0 || nz <= 0) {
      return {
        backgroundPositions: new Float32Array(),
        slicePositions: new Float32Array(),
        sliceColors: new Float32Array(),
      };
    }

    const totalPoints = nx * ny * nz;
    const background: number[] = [];
    const highlight: number[] = [];
    const colors: number[] = [];

    let minVal = Infinity;
    let maxVal = -Infinity;

    for (let i = 0; i < Math.min(solution.length, totalPoints); i += 1) {
      minVal = Math.min(minVal, solution[i]);
      maxVal = Math.max(maxVal, solution[i]);
    }

    const range = maxVal - minVal || 1;
    const xOffset = (nx - 1) / 2;
    const yOffset = (ny - 1) / 2;
    const zOffset = (nz - 1) / 2;

    for (let z = 0; z < nz; z += 1) {
      for (let y = 0; y < ny; y += 1) {
        for (let x = 0; x < nx; x += 1) {
          const index = (z * ny + y) * nx + x;
          const value = solution[index] ?? 0;
          const normalized = (value - minVal) / range;
          const px = (x - xOffset) * 0.44;
          const py = (y - yOffset) * 0.44;
          const pz = (z - zOffset) * 0.44;

          const isOnSlice =
            (sliceAxis === 'x' && x === sliceIndex) ||
            (sliceAxis === 'y' && y === sliceIndex) ||
            (sliceAxis === 'z' && z === sliceIndex);

          if (isOnSlice) {
            const color = buildColor(normalized);
            highlight.push(px, py, pz);
            colors.push(color.r, color.g, color.b);
          } else {
            background.push(px, py, pz);
          }
        }
      }
    }

    return {
      backgroundPositions: new Float32Array(background),
      slicePositions: new Float32Array(highlight),
      sliceColors: new Float32Array(colors),
    };
  }, [solution, nx, ny, nz, sliceAxis, sliceIndex]);

  const cameraPosition = useMemo<[number, number, number]>(() => {
    const scale = Math.max(nx, ny, nz) * 0.32;
    return [scale * 1.6, scale * 1.25, scale * 1.8];
  }, [nx, ny, nz]);

  const bounds = useMemo(() => {
    const step = 0.44;
    return {
      width: Math.max(nx - 1, 1) * step + step,
      height: Math.max(ny - 1, 1) * step + step,
      depth: Math.max(nz - 1, 1) * step + step,
    };
  }, [nx, ny, nz]);

  return (
    <div className="relative h-[520px] w-full overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-inner">
      <Canvas camera={{ position: cameraPosition, fov: 42 }} dpr={[1, 2]}>
        <color attach="background" args={['#020617']} />
        <fog attach="fog" args={['#020617', 8, 32]} />
        <ambientLight intensity={0.52} />
        <PulseLights />
        <Stars radius={48} depth={36} count={1800} factor={3.2} saturation={0} fade speed={1.2} />
        <Sparkles count={45} scale={[bounds.width + 2, bounds.height + 2, bounds.depth + 2]} size={2.8} speed={0.32} color="#7dd3fc" opacity={0.24} />
        <AmbientOrbs />
        <Float speed={1.4} rotationIntensity={0.4} floatIntensity={0.5}>
          <VolumeBounds width={bounds.width} height={bounds.height} depth={bounds.depth} />
        </Float>
        <SliceHalo axis={sliceAxis} index={sliceIndex} nx={nx} ny={ny} nz={nz} />

        <points>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={backgroundPositions.length / 3}
              array={backgroundPositions}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            color="#335266"
            size={0.08}
            transparent
            opacity={0.18}
            sizeAttenuation
            depthWrite={false}
          />
        </points>

        <points>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={slicePositions.length / 3}
              array={slicePositions}
              itemSize={3}
            />
            <bufferAttribute
              attach="attributes-color"
              count={sliceColors.length / 3}
              array={sliceColors}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            vertexColors
            size={0.2}
            sizeAttenuation
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

        <OrbitControls enableDamping dampingFactor={0.06} autoRotate={false} />
      </Canvas>

      <div className="pointer-events-none absolute left-4 top-4 rounded-md border border-cyan-500/20 bg-slate-900/70 px-3 py-2 font-mono text-[11px] text-cyan-300 backdrop-blur-sm">
        <p>L-Click: Rotate | R-Click: Pan | Scroll: Zoom</p>
        <p className="mt-1 opacity-80">Volumetric Particle Viewer Active</p>
        <p className="mt-1 opacity-60">Slice glow + ambient field layers enabled</p>
      </div>
    </div>
  );
}
