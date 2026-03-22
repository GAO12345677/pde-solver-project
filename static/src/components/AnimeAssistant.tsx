import { useEffect, useMemo, useState } from 'react';

export type AssistantMood = 'idle' | 'happy' | 'thinking' | 'angry' | 'shy';

interface AnimeAssistantProps {
  mood?: AssistantMood;
  message?: string;
  className?: string;
}

interface BubbleParticle {
  id: number;
  left: number;
  top: number;
  size: number;
  delay: number;
  duration: number;
  opacity: number;
  drift: number;
  color: string;
  borderColor: string;
  shadowColor: string;
}

const BASE_URL = import.meta.env.BASE_URL || '/';
const FRAME_PATHS = Array.from(
  { length: 17 },
  (_, index) => `${BASE_URL}assistant/idle-lite/frame_${String(index).padStart(3, '0')}.png`,
);

const MOOD_BUBBLE: Record<AssistantMood, string> = {
  idle: 'border-sky-100 bg-white/95 text-slate-700',
  happy: 'border-emerald-100 bg-emerald-50/95 text-emerald-900',
  thinking: 'border-amber-100 bg-amber-50/95 text-amber-900',
  angry: 'border-rose-100 bg-rose-50/95 text-rose-900',
  shy: 'border-pink-100 bg-pink-50/95 text-pink-900',
};

const MOOD_GLOW: Record<AssistantMood, string> = {
  idle: 'from-cyan-400/18 via-blue-500/8 to-transparent',
  happy: 'from-emerald-300/25 via-cyan-300/12 to-transparent',
  thinking: 'from-amber-300/22 via-slate-300/10 to-transparent',
  angry: 'from-rose-400/20 via-orange-300/10 to-transparent',
  shy: 'from-pink-300/25 via-rose-200/10 to-transparent',
};

const MOOD_FILTER: Record<AssistantMood, string> = {
  idle: 'saturate(1)',
  happy: 'saturate(1.08) brightness(1.01)',
  thinking: 'saturate(0.98) brightness(0.99)',
  angry: 'saturate(1.06) hue-rotate(-4deg)',
  shy: 'saturate(1.03) brightness(1.02)',
};

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

const BUBBLE_PALETTE = [
  {
    color: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.92), rgba(250,204,21,0.72) 58%, rgba(234,179,8,0.68) 100%)',
    borderColor: 'rgba(254,240,138,0.95)',
    shadowColor: 'rgba(234,179,8,0.32)',
  },
  {
    color: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.92), rgba(59,130,246,0.72) 58%, rgba(37,99,235,0.68) 100%)',
    borderColor: 'rgba(191,219,254,0.95)',
    shadowColor: 'rgba(59,130,246,0.3)',
  },
  {
    color: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.92), rgba(248,113,113,0.72) 58%, rgba(220,38,38,0.68) 100%)',
    borderColor: 'rgba(254,202,202,0.95)',
    shadowColor: 'rgba(239,68,68,0.28)',
  },
  {
    color: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.7), rgba(71,85,105,0.7) 58%, rgba(15,23,42,0.74) 100%)',
    borderColor: 'rgba(203,213,225,0.72)',
    shadowColor: 'rgba(15,23,42,0.24)',
  },
] as const;

export default function AnimeAssistant({
  mood = 'idle',
  message,
  className = '',
}: AnimeAssistantProps) {
  const [showMessage, setShowMessage] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [clicked, setClicked] = useState(false);
  const [particles, setParticles] = useState<BubbleParticle[]>([]);
  const [playBurst, setPlayBurst] = useState(false);
  const [burstFrameIndex, setBurstFrameIndex] = useState(0);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setMousePos({
        x: event.clientX / window.innerWidth - 0.5,
        y: event.clientY / window.innerHeight - 0.5,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    const spawnAt = (clientX: number, clientY: number, count: number) => {
      const xPercent = clamp((clientX / window.innerWidth) * 100, 4, 96);
      const yPercent = clamp((clientY / window.innerHeight) * 100, 6, 94);
      const burst = Array.from({ length: count }, (_, index) => {
        const palette = BUBBLE_PALETTE[Math.floor(Math.random() * BUBBLE_PALETTE.length)];
        return {
          id: Date.now() + index + Math.round(Math.random() * 1000),
          left: xPercent + (Math.random() - 0.5) * 4,
          top: yPercent + (Math.random() - 0.5) * 3,
          size: 8 + Math.random() * 12,
          delay: index * 0.03,
          duration: 4.2 + Math.random() * 0.8,
          opacity: 0.42 + Math.random() * 0.28,
          drift: (Math.random() - 0.5) * 70,
          color: palette.color,
          borderColor: palette.borderColor,
          shadowColor: palette.shadowColor,
        };
      });

      setParticles((current) => [...current, ...burst]);
      window.setTimeout(() => {
        setParticles((current) => current.filter((particle) => !burst.some((item) => item.id === particle.id)));
      }, 5000);
    };

    const handleGlobalClick = (event: MouseEvent) => {
      spawnAt(event.clientX, event.clientY, 8);
    };

    window.addEventListener('click', handleGlobalClick);
    return () => window.removeEventListener('click', handleGlobalClick);
  }, []);

  useEffect(() => {
    if (!message) {
      return undefined;
    }

    setShowMessage(true);
    const timer = window.setTimeout(() => setShowMessage(false), 4200);
    return () => window.clearTimeout(timer);
  }, [message]);

  const idleFrameIndex = Math.floor(FRAME_PATHS.length / 2);
  const frameIndex = playBurst ? burstFrameIndex : idleFrameIndex;
  const currentFrame = FRAME_PATHS[frameIndex] || FRAME_PATHS[idleFrameIndex] || FRAME_PATHS[0] || '';

  useEffect(() => {
    if (!playBurst) {
      setBurstFrameIndex(0);
      return undefined;
    }

    setBurstFrameIndex(0);
    const sequence = [0, 2, 4, 6, 8, 10, 12, 14, 16];
    let step = 0;
    const timer = window.setInterval(() => {
      step += 1;
      if (step >= sequence.length) {
        window.clearInterval(timer);
        return;
      }
      setBurstFrameIndex(sequence[step]);
    }, 95);

    return () => window.clearInterval(timer);
  }, [playBurst]);

  const floatTransform = useMemo(() => {
    const translateX = mousePos.x * 8;
    const translateY = mousePos.y * 4;
    return `translate3d(${translateX}px, ${translateY}px, 0)`;
  }, [mousePos]);

  const handleClick = () => {
    setClicked(true);
    window.setTimeout(() => setClicked(false), 420);
    setPlayBurst(true);
    window.setTimeout(() => setPlayBurst(false), 980);
  };

  return (
    <>
      <div className="pointer-events-none fixed inset-0 z-[39] hidden overflow-hidden md:block">
        {particles.map((particle) => (
          <span
            key={particle.id}
            className="absolute rounded-full border backdrop-blur-[1px]"
            style={{
              left: `${particle.left}%`,
              top: `${particle.top}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animation: `assistant-bubble-rise ${particle.duration}s ease-out forwards`,
              animationDelay: `${particle.delay}s`,
              ['--bubble-drift' as string]: `${particle.drift}px`,
              background: particle.color,
              borderColor: particle.borderColor,
              boxShadow: `0 0 14px ${particle.shadowColor}`,
              opacity: particle.opacity,
            }}
          />
        ))}
      </div>
      <div className={`pointer-events-none fixed bottom-0 right-2 z-40 hidden select-none md:block xl:right-4 ${className}`}>
      <style>{`
        @keyframes assistant-idle-float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        @keyframes assistant-pop {
          0% { transform: scale(1) rotate(0deg); }
          35% { transform: scale(1.05) rotate(-1.4deg); }
          70% { transform: scale(0.985) rotate(1deg); }
          100% { transform: scale(1) rotate(0deg); }
        }
        @keyframes assistant-bubble-rise {
          0% {
            transform: translate3d(0, 0, 0) scale(0.65);
            opacity: 0;
          }
          15% {
            opacity: 0.95;
          }
          100% {
            transform: translate3d(var(--bubble-drift), -120px, 0) scale(1.12);
            opacity: 0;
          }
        }
      `}</style>

      <div
        className={`pointer-events-none absolute -top-5 right-28 max-w-[280px] origin-bottom-right transition-all duration-300 ${
          showMessage ? 'translate-y-0 scale-100 opacity-100' : 'translate-y-4 scale-95 opacity-0'
        }`}
      >
        <div className={`relative rounded-[24px] border px-4 py-3 text-sm leading-6 shadow-[0_18px_45px_rgba(15,23,42,0.18)] backdrop-blur-md ${MOOD_BUBBLE[mood]}`}>
          <div className="whitespace-pre-wrap font-medium">{message}</div>
          <div className="absolute bottom-[-9px] right-9 h-5 w-5 rotate-45 border-b border-r border-inherit bg-inherit" />
        </div>
      </div>

      <div
        className="pointer-events-auto relative h-[430px] w-[300px] cursor-pointer overflow-visible transition-transform duration-500 hover:-translate-y-2 xl:h-[560px] xl:w-[390px]"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={handleClick}
      >
        <div className={`absolute inset-x-2 bottom-10 h-24 rounded-full bg-gradient-to-r ${MOOD_GLOW[mood]} blur-3xl transition-opacity duration-500 ${hovered ? 'opacity-100' : 'opacity-70'}`} />
        <div className="absolute inset-x-14 bottom-3 h-8 rounded-full bg-slate-900/15 blur-xl" />
        <div className="absolute right-10 top-16 h-20 w-20 rounded-full bg-white/25 blur-2xl" />

        <div
          className="absolute bottom-0 right-0 h-full w-full origin-bottom-right"
          style={{
            transform: `perspective(900px) rotateY(${mousePos.x * 8}deg) rotateX(${mousePos.y * -5}deg) ${floatTransform} ${hovered ? 'scale(1.03)' : 'scale(1)'}`,
            transition: 'transform 180ms ease-out',
            animation: `${clicked ? 'assistant-pop 420ms ease-out 1,' : ''} assistant-idle-float 4.2s ease-in-out infinite`,
            filter: MOOD_FILTER[mood],
          }}
        >
          {currentFrame ? (
            <img
              src={currentFrame}
              alt="assistant idle animation"
              className="h-full w-full object-contain object-bottom-right drop-shadow-[0_28px_48px_rgba(15,23,42,0.3)]"
              draggable={false}
            />
          ) : (
            <div className="flex h-full w-full items-end justify-end">
              <div className="rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm text-slate-500 shadow-lg">
                Assistant frames not found.
              </div>
            </div>
          )}

          {(mood === 'thinking' || mood === 'angry') && (
            <div className={`absolute right-8 top-14 rounded-full px-2 py-1 text-[11px] font-bold shadow-lg ${mood === 'thinking' ? 'bg-white/90 text-slate-600' : 'bg-rose-100 text-rose-700'}`}>
              {mood === 'thinking' ? '...' : '#'}
            </div>
          )}

          {(mood === 'happy' || mood === 'shy') && (
            <>
              <div className="pointer-events-none absolute left-[37%] top-[35%] h-7 w-12 rounded-full bg-rose-300/32 blur-xl" />
              <div className="pointer-events-none absolute left-[56%] top-[35%] h-7 w-12 rounded-full bg-rose-300/32 blur-xl" />
            </>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
