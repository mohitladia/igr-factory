import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

// ==========================================
// Types
// ==========================================
type WordTiming = {text: string; start: number; end: number};
type NodeItem = {label: string; detail?: string; color?: string};
type StepItem = {label: string; detail?: string};
type Beat = {
  id: string;
  type: string;
  title: string;
  spoken_text: string;
  visual_action?: string;
  duration_frames: number;
  audio_file?: string;
  audio_duration_seconds?: number;
  word_timings?: WordTiming[];
  asset_file?: string;
  nodes?: NodeItem[];
  connections?: number[][];
  steps?: StepItem[];
  accent_words?: string[];
  metric?: string;
};
type Plan = {
  title: string;
  topic: string;
  topic_family?: string;
  teaching_format?: string;
  platform?: 'reel' | 'shorts' | string;
  cover_file?: string;
  fps: number;
  width: number;
  height: number;
  total_duration_frames: number;
  beats: Beat[];
};
type Props = {plan: Plan};

// ==========================================
// Design Tokens & Palette (@backendlore benchmark)
// ==========================================
const C = {
  bg: '#070707',
  cardBg: 'rgba(16, 18, 22, 0.94)',
  cardBorder: 'rgba(255, 255, 255, 0.09)',
  gold: '#FF9F2A',
  goldGlow: 'rgba(255, 159, 42, 0.32)',
  green: '#3CEB8B',
  greenGlow: 'rgba(60, 235, 139, 0.28)',
  blue: '#58A6FF',
  blueGlow: 'rgba(88, 166, 255, 0.32)',
  purple: '#A78BFA',
  red: '#FF4D4D',
  white: '#F7F8FA',
  muted: '#8B949E',
  mutedLight: '#C9D1D9',
};

const FONT_SERIF = "'Fraunces', 'Lora', 'Georgia', serif";
const FONT_MONO = "'JetBrains Mono', 'SF Mono', Consolas, monospace";
const FONT_SANS = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const normalizeTopic = (topic: string) => topic.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const isTwoSumTopic = (topic: string) => normalizeTopic(topic).includes('two sum');
const isRagTopic = (topic: string) => {
  const normalized = normalizeTopic(topic);
  return /(^| )rag( |$)/.test(normalized) || normalized.includes('retrieval augmented generation');
};
const isScalingTopic = (topic: string) => {
  const normalized = normalizeTopic(topic);
  return normalized === 'scaling' || normalized.includes('horizontal scaling') || normalized.includes('vertical scaling');
};

// ==========================================
// Typography Helpers
// ==========================================
const EditorialText: React.FC<{
  text: string;
  fontSize?: number;
  color?: string;
  accentColor?: string;
  style?: React.CSSProperties;
}> = ({text, fontSize = 54, color = C.white, accentColor = C.gold, style}) => {
  const parts = text.split(/(\*[^*]+\*)/g);
  return (
    <span
      style={{
        fontFamily: FONT_SERIF,
        fontSize,
        lineHeight: 1.15,
        color,
        letterSpacing: -0.5,
        ...style,
      }}
    >
      {parts.map((part, i) => {
        if (part.startsWith('*') && part.endsWith('*')) {
          const content = part.slice(1, -1);
          return (
            <span
              key={i}
              style={{
                fontStyle: 'italic',
                color: accentColor,
                fontWeight: 700,
                textShadow: `0 0 25px ${accentColor}44`,
                margin: '0 4px',
              }}
            >
              {content}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
};

// ==========================================
// Canvas Spotlight Backdrop
// ==========================================
const BenchmarkBackdrop: React.FC<{frame: number}> = ({frame}) => {
  const pulse = 0.08 + 0.03 * Math.sin(frame / 24);
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      {/* Central warm spotlight */}
      <div
        style={{
          position: 'absolute',
          top: '40%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 900,
          height: 900,
          borderRadius: 9999,
          background: `radial-gradient(circle, rgba(255,159,42,${pulse}) 0%, rgba(255,100,20,0.02) 48%, transparent 75%)`,
          filter: 'blur(90px)',
          pointerEvents: 'none',
        }}
      />
      {/* Soft dark vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.75) 100%)',
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

// ==========================================
// 1. Hook Screen (Benchmark 1:1)
// ==========================================
const InterviewHookCard: React.FC<{
  topic: string;
  beat: Beat;
  frame: number;
}> = ({topic, beat, frame}) => {
  const cardEnter = interpolate(frame, [0, 14], [0, 1], clamp);
  const badgeEnter = interpolate(frame, [6, 20], [0, 1], clamp);
  const statEnter = interpolate(frame, [14, 28], [0, 1], clamp);

  const topicLower = topic.toLowerCase();
  const isKafka = topicLower.includes('kafka');
  const isTwoSum = isTwoSumTopic(topic);
  const isScaling = isScalingTopic(topic);

  const question = isKafka
    ? 'Kafka itna *fast* kaise hai, jab woh har message *disk* pe likhta hai?'
    : isTwoSum
      ? '*O(n²)* se *O(n)* kaise laaye, bina array sort kare?'
      : isScaling
        ? '10 Lakh users aane par server *BADA* kyun nahi karte, *NAYE* servers kyun lagate hain?'
        : beat.spoken_text
          ? beat.spoken_text.replace(/[!.?]+$/, '') + '?'
          : `*${topic}* internal working aur real architecture kya hai?`;

  const statNumber = isKafka
    ? '7,000,000,000,000'
    : isTwoSum
      ? 'O(n) Time · O(n) Space'
      : isScaling
        ? '10,000,000'
        : beat.metric || topic.toUpperCase();

  const statSub = isKafka
    ? "messages a day · LinkedIn's Kafka, 2019"
    : isTwoSum
      ? 'Optimal HashMap Approach · LeetCode #1'
      : isScaling
        ? 'concurrent users · Zero Downtime Architecture'
        : `${topic.toUpperCase()} · ${beat.metric || 'CORE CONCEPTS'}`;

  const pillTag = isKafka
    ? 'sab disk pe?'
    : isTwoSum
      ? 'brute force fail?'
      : isScaling
        ? 'vertical fail?'
        : (beat.accent_words && beat.accent_words[0]) || 'interview question';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 240,
        paddingLeft: 64,
        paddingRight: 64,
      }}
    >
      {/* Top Floating Interview Question Card */}
      <div
        style={{
          width: '100%',
          maxWidth: 950,
          borderRadius: 24,
          padding: '36px 44px',
          background: C.cardBg,
          border: '1px solid rgba(255, 255, 255, 0.11)',
          boxShadow: '0 24px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(255, 159, 42, 0.06)',
          backdropFilter: 'blur(20px)',
          opacity: cardEnter,
          transform: `translateY(${(1 - cardEnter) * 35}px)`,
        }}
      >
        <div
          style={{
            fontFamily: FONT_SANS,
            fontSize: 20,
            color: '#8A94A6',
            letterSpacing: 1.5,
            marginBottom: 16,
            fontWeight: 600,
          }}
        >
          Interview mein poocha
        </div>
        <EditorialText text={question} fontSize={46} color={C.white} accentColor={C.green} />
      </div>

      {/* Center Topic Badge + Question Tag */}
      <div
        style={{
          marginTop: 100,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          opacity: badgeEnter,
          transform: `scale(${0.9 + badgeEnter * 0.1})`,
        }}
      >
        <div style={{position: 'relative'}}>
          <div
            style={{
              width: 170,
              height: 170,
              borderRadius: 36,
              background: '#FFFFFF',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 50px rgba(255, 255, 255, 0.25), 0 0 90px rgba(255, 159, 42, 0.25)',
            }}
          >
            {isKafka ? (
              <svg width="84" height="84" viewBox="0 0 24 24" fill="none">
                <circle cx="6" cy="12" r="3" fill="#0A0A0A" />
                <circle cx="18" cy="6" r="3" fill="#0A0A0A" />
                <circle cx="18" cy="18" r="3" fill="#0A0A0A" />
                <line x1="8.5" y1="10.5" x2="15.5" y2="7.5" stroke="#0A0A0A" strokeWidth="2.5" />
                <line x1="8.5" y1="13.5" x2="15.5" y2="16.5" stroke="#0A0A0A" strokeWidth="2.5" />
              </svg>
            ) : (
              <svg width="84" height="84" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="7" height="7" rx="2" fill="#0A0A0A" />
                <rect x="14" y="3" width="7" height="7" rx="2" fill="#0A0A0A" />
                <rect x="3" y="14" width="7" height="7" rx="2" fill="#0A0A0A" />
                <path d="M14 17.5H21M17.5 14V21" stroke="#0A0A0A" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            )}
            <div
              style={{
                fontFamily: FONT_SANS,
                fontSize: 18,
                fontWeight: 900,
                color: '#0A0A0A',
                letterSpacing: 1,
                marginTop: 4,
              }}
            >
              {topic.toLowerCase().slice(0, 10)}
            </div>
          </div>

          <div
            style={{
              position: 'absolute',
              top: 10,
              right: -130,
              padding: '8px 18px',
              borderRadius: 999,
              border: `1.5px solid ${C.red}`,
              background: 'rgba(255, 77, 77, 0.15)',
              color: '#FF6B6B',
              fontFamily: FONT_MONO,
              fontSize: 18,
              fontWeight: 600,
            }}
          >
            {pillTag}
          </div>
        </div>

        {/* Large Scale Metric Number + Phase B Multi-Phase Stamp */}
        <div
          style={{
            marginTop: 55,
            textAlign: 'center',
            opacity: statEnter,
            transform: `translateY(${(1 - statEnter) * 20}px)`,
          }}
        >
          <div
            style={{
              fontFamily: FONT_SANS,
              fontSize: 64,
              fontWeight: 900,
              color: C.gold,
              letterSpacing: -1,
              textShadow: '0 0 45px rgba(255, 159, 42, 0.4)',
            }}
          >
            {statNumber}
          </div>
          <div
            style={{
              fontFamily: FONT_SANS,
              fontSize: 22,
              color: C.muted,
              marginTop: 10,
              fontWeight: 500,
            }}
          >
            {statSub}
          </div>

          {frame >= 85 && (
            <div
              style={{
                marginTop: 28,
                display: 'inline-block',
                padding: '14px 36px',
                borderRadius: 16,
                background: 'rgba(14, 8, 10, 0.96)',
                border: `3px solid ${C.red}`,
                boxShadow: `0 16px 50px rgba(0,0,0,0.9), 0 0 40px ${C.red}`,
                transform: `rotate(-3deg) scale(${interpolate(frame, [85, 100], [1.6, 1], clamp)})`,
              }}
            >
              <span style={{fontFamily: FONT_MONO, fontSize: 28, fontWeight: 900, color: C.red, letterSpacing: 2}}>
                ✕ NAIVE TRAP → {pillTag.toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 2. Sequential Log Stream Diagram (Kafka Benchmark 1:1)
// ==========================================
const LogStreamDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const cursorBlink = Math.floor(frame / 12) % 2 === 0;

  const logEntries = [
    {tag: 'order_placed', offset: 0, color: C.gold},
    {tag: 'payment_done', offset: 1, color: C.green},
    {tag: 'order_delivered', offset: 2, color: C.purple},
    {tag: 'order_placed', offset: 3, color: C.gold},
    {tag: 'payment_done', offset: 4, color: C.green},
    {tag: 'order_delivered', offset: 5, color: C.purple},
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 180,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 65}}>
        <EditorialText text="Kafka = *distributed log*" fontSize={62} color={C.white} accentColor={C.gold} />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 160,
          position: 'relative',
          marginBottom: 60,
          opacity: enter,
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: '20%',
            right: '20%',
            height: 2,
            background: 'rgba(255, 255, 255, 0.18)',
            top: '50%',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: `${20 + ((frame * 1.2) % 60)}%`,
            top: '50%',
            width: 8,
            height: 8,
            borderRadius: 99,
            background: C.gold,
            transform: 'translate(-50%, -50%)',
            boxShadow: `0 0 14px ${C.gold}`,
          }}
        />

        <div
          style={{
            padding: '16px 36px',
            borderRadius: 16,
            background: C.cardBg,
            border: `1.5px solid ${C.gold}88`,
            textAlign: 'center',
            zIndex: 2,
          }}
        >
          <div style={{fontFamily: FONT_SANS, color: C.white, fontSize: 24, fontWeight: 700}}>Producer</div>
          <div style={{fontFamily: FONT_MONO, color: C.gold, fontSize: 16, marginTop: 4}}>writes →</div>
        </div>

        <div
          style={{
            padding: '16px 36px',
            borderRadius: 16,
            background: C.cardBg,
            border: `1.5px solid ${C.blue}88`,
            textAlign: 'center',
            zIndex: 2,
          }}
        >
          <div style={{fontFamily: FONT_SANS, color: C.white, fontSize: 24, fontWeight: 700}}>Consumer</div>
          <div style={{fontFamily: FONT_MONO, color: C.blue, fontSize: 16, marginTop: 4}}>reads in order</div>
        </div>
      </div>

      <div
        style={{
          fontFamily: FONT_MONO,
          color: C.gold,
          fontSize: 20,
          marginBottom: 26,
          opacity: enter,
          letterSpacing: 0.5,
        }}
      >
        append only · new messages only at the end →
      </div>

      <div
        style={{
          width: 960,
          height: 120,
          borderRadius: 18,
          background: 'rgba(12, 14, 18, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          gap: 16,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {logEntries.map((item, i) => (
          <div
            key={i}
            style={{
              minWidth: 140,
              height: 80,
              borderRadius: 14,
              border: `1.5px solid ${item.color}88`,
              background: 'rgba(18, 20, 26, 0.95)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              padding: '0 14px',
              boxShadow: `0 0 20px ${item.color}15`,
            }}
          >
            <div style={{fontFamily: FONT_MONO, color: item.color, fontSize: 13, fontWeight: 600}}>
              {item.tag}
            </div>
            <div style={{fontFamily: FONT_MONO, color: C.white, fontSize: 22, fontWeight: 800, marginTop: 4}}>
              {item.offset}
            </div>
          </div>
        ))}

        <div
          style={{
            width: 4,
            height: 70,
            background: C.green,
            opacity: cursorBlink ? 1 : 0.2,
            borderRadius: 2,
            boxShadow: `0 0 12px ${C.green}`,
          }}
        />
      </div>

      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 23,
          color: C.mutedLight,
          marginTop: 35,
          opacity: enter,
        }}
      >
        har message ka number ={' '}
        <span style={{color: C.gold, fontWeight: 700}}>
          offset 0 · 1 · 2 · 3 · 4 · 5 _
        </span>
      </div>

      <div
        style={{
          width: 900,
          display: 'flex',
          justifyContent: 'space-around',
          marginTop: 65,
          opacity: enter,
        }}
      >
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 14,
            border: `1.5px solid ${C.purple}`,
            background: C.cardBg,
            fontFamily: FONT_MONO,
            fontSize: 20,
            color: C.purple,
            fontWeight: 700,
          }}
        >
          Analytics offset 1
        </div>
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 14,
            border: `1.5px solid ${C.blue}`,
            background: C.cardBg,
            fontFamily: FONT_MONO,
            fontSize: 20,
            color: C.blue,
            fontWeight: 700,
          }}
        >
          Notification offset 3
        </div>
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 14,
            border: `1.5px solid ${C.green}`,
            background: C.cardBg,
            fontFamily: FONT_MONO,
            fontSize: 20,
            color: C.green,
            fontWeight: 700,
          }}
        >
          Payment offset 5
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 3. Partition Lanes Diagram (Kafka Benchmark 1:1)
// ==========================================
const PartitionLanesDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const lanes = [
    {machine: 'machine 1', name: 'P0', color: C.gold, border: C.gold},
    {machine: 'machine 2', name: 'P1', color: C.green, border: C.green},
    {machine: 'machine 3', name: 'P2', color: C.blue, border: C.blue},
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 180,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 25}}>
        <EditorialText text="Topic orders → *3 partitions*" fontSize={60} color={C.white} accentColor={C.gold} />
      </div>

      <div
        style={{
          fontFamily: FONT_MONO,
          color: C.green,
          fontSize: 22,
          marginBottom: 60,
          opacity: enter,
          fontWeight: 600,
        }}
      >
        producers write in parallel →
      </div>

      <div style={{width: 940, display: 'flex', flexDirection: 'column', gap: 24, opacity: enter}}>
        {lanes.map((lane, idx) => {
          const laneEnter = interpolate(frame, [idx * 6, idx * 6 + 12], [0, 1], clamp);
          return (
            <div
              key={lane.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                opacity: laneEnter,
                transform: `translateX(${(1 - laneEnter) * 30}px)`,
              }}
            >
              <div
                style={{
                  width: 140,
                  height: 90,
                  borderRadius: 18,
                  border: `1.5px solid ${lane.border}`,
                  background: C.cardBg,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 0 25px ${lane.border}22`,
                }}
              >
                <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted}}>{lane.machine}</div>
                <div style={{fontFamily: FONT_MONO, fontSize: 32, fontWeight: 900, color: lane.color}}>
                  {lane.name}
                </div>
              </div>

              <div
                style={{
                  flex: 1,
                  height: 90,
                  borderRadius: 18,
                  background: 'rgba(12, 14, 18, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 18px',
                  gap: 16,
                }}
              >
                <div
                  style={{
                    padding: '12px 22px',
                    borderRadius: 12,
                    border: `1.5px solid ${lane.color}88`,
                    background: 'rgba(18, 20, 26, 0.95)',
                    fontFamily: FONT_MONO,
                    fontSize: 18,
                    color: C.white,
                  }}
                >
                  #1042 <span style={{color: lane.color, fontWeight: 700}}>msg_{idx}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: 65,
          padding: '16px 36px',
          borderRadius: 999,
          border: `1.5px solid ${C.gold}`,
          background: 'rgba(255, 159, 42, 0.08)',
          fontFamily: FONT_MONO,
          fontSize: 22,
          color: C.white,
          opacity: enter,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <span style={{color: C.gold}}>key = order_1042</span>
        <span style={{color: C.muted}}>→</span>
        <span style={{color: C.muted}}>hash</span>
        <span style={{color: C.muted}}>→</span>
        <span style={{color: C.green, fontWeight: 800}}>always P1</span>
      </div>

      <div
        style={{
          marginTop: 26,
          fontFamily: FONT_MONO,
          fontSize: 22,
          color: C.mutedLight,
          opacity: enter,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <span>placed → paid → delivered</span>
        <span style={{color: C.green, fontWeight: 900}}>✔</span>
      </div>
    </div>
  );
};

// ==========================================
// 4. DSA Two Sum: Problem & Array Diagram
// ==========================================
const DSAArrayTapeDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const array = [
    {val: 2, idx: 0, highlight: true},
    {val: 7, idx: 1, highlight: true},
    {val: 11, idx: 2, highlight: false},
    {val: 15, idx: 3, highlight: false},
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 180,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 30}}>
        <EditorialText text="Two Sum: *The Array Problem*" fontSize={60} color={C.white} accentColor={C.gold} />
      </div>

      {/* Target Badge */}
      <div
        style={{
          padding: '12px 32px',
          borderRadius: 999,
          border: `1.5px solid ${C.gold}`,
          background: 'rgba(255, 159, 42, 0.12)',
          fontFamily: FONT_MONO,
          fontSize: 26,
          fontWeight: 800,
          color: C.gold,
          marginBottom: 55,
          opacity: enter,
          boxShadow: `0 0 30px ${C.goldGlow}`,
        }}
      >
        TARGET = 9
      </div>

      {/* Array Cards */}
      <div style={{display: 'flex', gap: 24, marginBottom: 60, opacity: enter}}>
        {array.map((item, i) => {
          const itemEnter = interpolate(frame, [i * 5, i * 5 + 12], [0, 1], clamp);
          return (
            <div
              key={i}
              style={{
                width: 150,
                height: 150,
                borderRadius: 24,
                border: `2px solid ${item.highlight ? C.green : 'rgba(255,255,255,0.12)'}`,
                background: item.highlight ? 'rgba(60, 235, 139, 0.14)' : C.cardBg,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: item.highlight ? `0 0 40px ${C.greenGlow}` : 'none',
                opacity: itemEnter,
                transform: `scale(${0.9 + itemEnter * 0.1})`,
              }}
            >
              <div style={{fontFamily: FONT_MONO, fontSize: 16, color: C.muted}}>index {item.idx}</div>
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 52,
                  fontWeight: 900,
                  color: item.highlight ? C.green : C.white,
                  marginTop: 6,
                }}
              >
                {item.val}
              </div>
            </div>
          );
        })}
      </div>

      {/* Goal Callout */}
      <div
        style={{
          width: 860,
          padding: '24px 34px',
          borderRadius: 20,
          border: '1px solid rgba(255,255,255,0.1)',
          background: C.cardBg,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 16,
          opacity: enter,
        }}
      >
        <span style={{fontFamily: FONT_MONO, fontSize: 24, color: C.white}}>
          2 + 7 = <span style={{color: C.gold, fontWeight: 800}}>9</span>
        </span>
        <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.green, fontWeight: 700}}>
          → Return indices [0, 1] ✔
        </span>
      </div>
    </div>
  );
};

// ==========================================
// 5. DSA HashMap & Complement Formula Diagram
// ==========================================
const DSAHashMapDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 180,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 35}}>
        <EditorialText text="One-Pass *HashMap Lookup*" fontSize={60} color={C.white} accentColor={C.gold} />
      </div>

      {/* Formula Pill */}
      <div
        style={{
          padding: '18px 40px',
          borderRadius: 999,
          border: `2px solid ${C.gold}`,
          background: 'rgba(255, 159, 42, 0.1)',
          fontFamily: FONT_MONO,
          fontSize: 26,
          fontWeight: 800,
          color: C.white,
          marginBottom: 50,
          opacity: enter,
          display: 'flex',
          gap: 12,
        }}
      >
        <span>complement</span> = <span style={{color: C.gold}}>target</span> −{' '}
        <span style={{color: C.blue}}>nums[i]</span>
      </div>

      {/* HashMap Table Card */}
      <div
        style={{
          width: 860,
          borderRadius: 24,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          background: C.cardBg,
          padding: '34px 44px',
          opacity: enter,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 20}}>
          <div style={{fontFamily: FONT_MONO, fontSize: 20, color: C.muted, fontWeight: 700}}>
            HASHMAP (Key: Value → Val: Index)
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 18, color: C.green}}>O(1) average lookup</div>
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
          <div
            style={{
              padding: '18px 24px',
              borderRadius: 14,
              border: `1.5px solid ${C.blue}88`,
              background: 'rgba(88, 166, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: FONT_MONO,
              fontSize: 24,
            }}
          >
            <span style={{color: C.white}}>Key: 2</span>
            <span style={{color: C.blue}}>stored at index 0</span>
          </div>

          <div
            style={{
              padding: '18px 24px',
              borderRadius: 14,
              border: `2px solid ${C.green}`,
              background: 'rgba(60, 235, 139, 0.14)',
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: FONT_MONO,
              fontSize: 24,
              boxShadow: `0 0 30px ${C.greenGlow}`,
            }}
          >
            <span style={{color: C.white}}>Next: 7 → Need complement 2</span>
            <span style={{color: C.green, fontWeight: 800}}>MATCH FOUND! [0, 1] ✔</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 6. Comparison Screen (Dynamic Multi-Topic Battle)
// ==========================================
const EditorialComparison: React.FC<{beat: Beat; frame: number; topic?: string}> = ({beat, frame, topic = ''}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const barProgress = interpolate(frame, [10, 45], [0, 1], clamp);
  const pulse = 0.85 + 0.15 * Math.sin(frame / 6);

  const topicLower = (topic || '').toLowerCase();
  const isScaling =
    isScalingTopic(topic) ||
    beat.id === 'vertical_limits';
  const isAnagram = topicLower.includes('anagram');
  const isDSA =
    topicLower.includes('two sum') ||
    isAnagram ||
    (beat.spoken_text || '').toLowerCase().includes('brute') ||
    (beat.spoken_text || '').toLowerCase().includes('o of n') ||
    (beat.title || '').toLowerCase().includes('brute');

  const n0 = beat.nodes && beat.nodes[0];
  const n1 = beat.nodes && beat.nodes[1];
  const n2 = beat.nodes && beat.nodes[2];

  const titleText = isScaling
    ? 'Architecture: *Vertical vs Horizontal*'
    : isAnagram
      ? 'Complexity: *Sorting vs 26-Bucket Array*'
      : isDSA
        ? 'Complexity: *Brute Force vs HashMap*'
        : `*${beat.title || 'Naive vs Optimized'}*`;

  const card1Title = n0?.label
    ? n0.label.toUpperCase()
    : isScaling
      ? 'VERTICAL SCALING'
      : isAnagram
        ? 'NAIVE: SORT STRINGS'
        : 'NAIVE BOTTLENECK';
  const card1Big = isScaling
    ? 'SPOF'
    : isAnagram
      ? 'O(N log N)'
      : isDSA
        ? 'O(n²)'
        : (n2?.label ? n2.label.toUpperCase().slice(0, 12) : 'CRASH ✕');
  const card1Sub =
    n0?.detail ||
    (isScaling
      ? 'Single huge server. Expensive hardware ceiling & 100% outage risk!'
      : isAnagram
        ? 'Sorting both strings takes O(N log N) time & modifies input. REJECTED!'
        : 'High latency, overload & expensive bottleneck under scale.');

  const card2Title = n1?.label
    ? n1.label.toUpperCase()
    : isScaling
      ? 'HORIZONTAL SCALING'
      : isAnagram
        ? 'OPTIMAL: 26 BUCKETS'
        : 'PRODUCTION ENGINE';
  const card2Big = isScaling
    ? '99.999%'
    : isAnagram
      ? 'O(N)'
      : isDSA
        ? 'O(n)'
        : (beat.metric ? beat.metric.slice(0, 12) : 'SCALABLE ✔');
  const card2Sub =
    n1?.detail ||
    (isScaling
      ? 'Pool of commodity servers. Infinite linear scale & Zero Downtime!'
      : isAnagram
        ? 'Single pass with 26-size integer array. O(N) time & O(1) space!'
        : 'Low-latency indexing, high throughput & zero bottleneck.');

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 185,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 44}}>
        <EditorialText text={titleText} fontSize={54} color={C.white} accentColor={C.gold} />
      </div>

      <div style={{width: 920, display: 'flex', gap: 28, opacity: enter}}>
        {/* Left Red Bottleneck Card */}
        <div
          style={{
            flex: 1,
            padding: '34px 28px',
            borderRadius: 24,
            background: C.cardBg,
            border: `2px solid ${C.red}AA`,
            boxShadow: `0 0 40px rgba(255, 77, 77, ${0.15 * pulse})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 999,
              background: 'rgba(255, 77, 77, 0.14)',
              border: `1px solid ${C.red}`,
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: C.red,
              fontWeight: 800,
            }}
          >
            ✕ {card1Title}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 54, fontWeight: 900, color: C.red, margin: '22px 0'}}>
            {card1Big}
          </div>
          <div style={{fontFamily: FONT_SANS, fontSize: 21, color: C.mutedLight, textAlign: 'center', lineHeight: 1.45}}>
            {card1Sub}
          </div>
          {/* Animated Overload Meter */}
          <div
            style={{
              width: '100%',
              height: 12,
              borderRadius: 99,
              background: 'rgba(255,255,255,0.08)',
              marginTop: 26,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${barProgress * 92}%`,
                height: '100%',
                background: C.red,
                boxShadow: `0 0 14px ${C.red}`,
              }}
            />
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.red, marginTop: 10, fontWeight: 700}}>
            LATENCY / COST: 92% OVERLOAD
          </div>
        </div>

        {/* Right Green Optimized Card */}
        <div
          style={{
            flex: 1,
            padding: '34px 28px',
            borderRadius: 24,
            background: C.cardBg,
            border: `2px solid ${C.green}`,
            boxShadow: `0 0 45px ${C.greenGlow}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 999,
              background: 'rgba(63, 185, 80, 0.14)',
              border: `1px solid ${C.green}`,
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: C.green,
              fontWeight: 800,
            }}
          >
            ✔ {card2Title}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 54, fontWeight: 900, color: C.green, margin: '22px 0'}}>
            {card2Big}
          </div>
          <div style={{fontFamily: FONT_SANS, fontSize: 21, color: C.white, textAlign: 'center', lineHeight: 1.45}}>
            {card2Sub}
          </div>
          {/* Animated Fast Efficiency Meter */}
          <div
            style={{
              width: '100%',
              height: 12,
              borderRadius: 99,
              background: 'rgba(255,255,255,0.08)',
              marginTop: 26,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${barProgress * 18}%`,
                height: '100%',
                background: C.green,
                boxShadow: `0 0 14px ${C.green}`,
              }}
            />
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, marginTop: 10, fontWeight: 700}}>
            LATENCY: 2s INSTANT RESPONSE ✔
          </div>
        </div>
      </div>

      {beat.metric && (
        <div
          style={{
            marginTop: 38,
            padding: '14px 32px',
            borderRadius: 16,
            border: `1.5px solid ${C.gold}`,
            background: 'rgba(255, 159, 42, 0.1)',
            fontFamily: FONT_MONO,
            fontSize: 20,
            color: C.gold,
            fontWeight: 800,
            opacity: enter,
          }}
        >
          THIS IS CALLED: {beat.metric}
        </div>
      )}
    </div>
  );
};

// ==========================================
// 6b. Horizontal Scaling & Load Balancer Diagram (System Design Benchmark)
// ==========================================
const HorizontalScalingDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const isCrashed = beat.id === 'fault_tolerance' || (beat.title || '').toLowerCase().includes('downtime');
  const isStateless = beat.id === 'stateless' || (beat.title || '').toLowerCase().includes('stateless');

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 160,
      }}
    >
      <div style={{opacity: enter, textAlign: 'center', marginBottom: 25}}>
        <EditorialText
          text={isStateless ? 'Stateless *Worker Tier*' : isCrashed ? 'Auto-Healing · *Zero Downtime*' : 'Horizontal *Load Balancing*'}
          fontSize={56}
          color={C.white}
          accentColor={isCrashed ? C.red : C.gold}
        />
      </div>

      {/* Top Client Traffic Pill */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '12px 28px',
          borderRadius: 999,
          border: '1px solid rgba(255, 255, 255, 0.15)',
          background: C.cardBg,
          fontFamily: FONT_MONO,
          fontSize: 18,
          color: C.muted,
          marginBottom: 30,
          opacity: enter,
        }}
      >
        <span style={{color: C.green, fontWeight: 700}}>● 100,000 req/s</span>
        <span>→ Incoming Client Requests</span>
      </div>

      {/* Load Balancer Box */}
      <div
        style={{
          width: 860,
          padding: '20px 32px',
          borderRadius: 20,
          border: `2px solid ${C.gold}`,
          background: 'rgba(255, 159, 42, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: `0 0 35px ${C.gold}22`,
          marginBottom: 40,
          opacity: enter,
        }}
      >
        <div>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.gold, letterSpacing: 1.5}}>REVERSE PROXY</div>
          <div style={{fontFamily: FONT_SANS, fontSize: 26, fontWeight: 800, color: C.white}}>Load Balancer (Nginx / ALB)</div>
        </div>
        <div style={{fontFamily: FONT_MONO, fontSize: 16, color: C.gold, textAlign: 'right'}}>
          Algorithm: <span style={{color: C.white, fontWeight: 700}}>Round Robin</span>
          <div style={{fontSize: 13, color: C.muted, marginTop: 4}}>
            {isCrashed ? 'Traffic rerouted 50% / 50%' : 'Distributed 33% / 33% / 33%'}
          </div>
        </div>
      </div>

      {/* 3 Horizontal Server Instances */}
      <div style={{width: 860, display: 'flex', gap: 20, marginBottom: 35, opacity: enter}}>
        {/* Server 1 */}
        <div
          style={{
            flex: 1,
            borderRadius: 18,
            padding: '24px 20px',
            border: `1.5px solid ${C.blue}88`,
            background: C.cardBg,
            boxShadow: `0 0 25px ${C.blue}18`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted}}>INSTANCE 1</div>
          <div style={{fontFamily: FONT_SANS, fontSize: 22, fontWeight: 700, color: C.white, marginTop: 4}}>Server A</div>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, marginTop: 12, fontWeight: 600}}>
            ● Healthy ({isCrashed ? '50K req/s' : '33K req/s'})
          </div>
        </div>

        {/* Server 2 - Can be crashed during fault tolerance beat */}
        <div
          style={{
            flex: 1,
            borderRadius: 18,
            padding: '24px 20px',
            border: isCrashed ? `2px solid ${C.red}` : `1.5px solid ${C.blue}88`,
            background: isCrashed ? 'rgba(255, 77, 77, 0.12)' : C.cardBg,
            boxShadow: isCrashed ? `0 0 35px ${C.red}33` : `0 0 25px ${C.blue}18`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: isCrashed ? C.red : C.muted}}>
            {isCrashed ? 'CRASHED ✖' : 'INSTANCE 2'}
          </div>
          <div style={{fontFamily: FONT_SANS, fontSize: 22, fontWeight: 700, color: isCrashed ? '#FF6B6B' : C.white, marginTop: 4}}>
            Server B
          </div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 14,
              color: isCrashed ? C.red : C.green,
              marginTop: 12,
              fontWeight: 700,
            }}
          >
            {isCrashed ? '✖ Health Check Fail' : '● Healthy (33K req/s)'}
          </div>
        </div>

        {/* Server 3 */}
        <div
          style={{
            flex: 1,
            borderRadius: 18,
            padding: '24px 20px',
            border: `1.5px solid ${C.blue}88`,
            background: C.cardBg,
            boxShadow: `0 0 25px ${C.blue}18`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted}}>INSTANCE 3</div>
          <div style={{fontFamily: FONT_SANS, fontSize: 22, fontWeight: 700, color: C.white, marginTop: 4}}>Server C</div>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, marginTop: 12, fontWeight: 600}}>
            ● Healthy ({isCrashed ? '50K req/s' : '33K req/s'})
          </div>
        </div>
      </div>

      {/* Shared Stateless Data Tier */}
      <div
        style={{
          width: 860,
          padding: '20px 32px',
          borderRadius: 20,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(12, 14, 18, 0.95)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: enter,
        }}
      >
        <div style={{display: 'flex', gap: 24, alignItems: 'center'}}>
          <div
            style={{
              padding: '10px 18px',
              borderRadius: 12,
              border: `1.5px solid ${C.purple}`,
              background: 'rgba(188, 140, 255, 0.1)',
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: C.purple,
              fontWeight: 700,
            }}
          >
            Redis Session Store
          </div>
          <div
            style={{
              padding: '10px 18px',
              borderRadius: 12,
              border: `1.5px solid ${C.green}`,
              background: 'rgba(63, 185, 80, 0.1)',
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: C.green,
              fontWeight: 700,
            }}
          >
            Database Cluster
          </div>
        </div>
        <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.gold, fontWeight: 600}}>
          Stateless = Zero Session Loss ✔
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 6A. 1:1 @backendlore RAG Interactive Motion Graphics Engine
// ==========================================
const RAGStepperBar: React.FC<{activeStep: 0 | 1 | 2; frame: number}> = ({activeStep, frame}) => {
  const steps = [
    {letter: 'R', name: 'RETRIEVAL'},
    {letter: 'A', name: 'AUGMENTED'},
    {letter: 'G', name: 'GENERATION'},
  ];
  const dotPulse = 0.6 + 0.4 * Math.sin(frame / 5);

  return (
    <div style={{width: 900, marginBottom: 28, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 20px',
          borderRadius: 999,
          background: 'rgba(14, 18, 24, 0.92)',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        {steps.map((st, idx) => {
          const isActive = idx === activeStep;
          const isDone = idx < activeStep;
          const color = isActive ? C.green : isDone ? C.blue : C.muted;
          return (
            <React.Fragment key={st.letter}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '8px 20px',
                  borderRadius: 999,
                  background: isActive ? 'rgba(63, 185, 80, 0.16)' : 'transparent',
                  border: isActive ? `1.5px solid ${C.green}` : '1px solid transparent',
                  boxShadow: isActive ? `0 0 24px ${C.greenGlow}` : 'none',
                }}
              >
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 999,
                    border: `2px solid ${color}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: FONT_MONO,
                    fontSize: 17,
                    fontWeight: 900,
                    color,
                  }}
                >
                  {st.letter}
                </div>
                <span
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 17,
                    fontWeight: 800,
                    letterSpacing: 1.5,
                    color: isActive ? C.white : color,
                  }}
                >
                  {st.name}
                </span>
              </div>
              {idx < 2 && (
                <div
                  style={{
                    flex: 1,
                    height: 2,
                    margin: '0 10px',
                    borderTop: `2px dashed ${idx < activeStep ? C.green : 'rgba(255,255,255,0.18)'}`,
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
      {/* Animated vertical indicator dots under active step */}
      <div style={{display: 'flex', flexDirection: 'column', gap: 5, marginTop: 8, opacity: dotPulse}}>
        <div style={{width: 7, height: 7, borderRadius: 99, background: C.green}} />
        <div style={{width: 7, height: 7, borderRadius: 99, background: C.green}} />
      </div>
    </div>
  );
};

const RAGInteractiveDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 12], [0, 1], clamp);

  // BEAT 1: HOOK (500-Page PDF Stack -> 500-Cell Matrix + "497 X PADHE HI NAHI" Neon Stamp)
  if (beat.id === 'hook' || beat.type === 'kinetic_title') {
    const showMatrix = frame >= 80;
    const stampScale = interpolate(frame, [95, 112], [2.2, 1], clamp);
    const stampOpacity = interpolate(frame, [92, 106], [0, 1], clamp);
    const typedLen = Math.min(48, Math.floor(frame * 1.1));
    const promptStr = '500 page ki PDF, aur ChatGPT ka jawab 2s mein?!'.slice(0, typedLen);

    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 170,
          paddingLeft: 56,
          paddingRight: 56,
        }}
      >
        {/* Top Chat Bubble */}
        <div
          style={{
            width: 880,
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            padding: '20px 28px',
            borderRadius: 22,
            background: 'rgba(18, 22, 30, 0.95)',
            border: '1.5px solid rgba(255,255,255,0.14)',
            boxShadow: '0 16px 40px rgba(0,0,0,0.7)',
            marginBottom: 42,
            opacity: enter,
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 999,
              background: 'rgba(88, 166, 255, 0.16)',
              border: `1.5px solid ${C.blue}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: FONT_MONO,
              fontSize: 22,
              color: C.blue,
              fontWeight: 900,
            }}
          >
            Q
          </div>
          <div>
            <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.muted, letterSpacing: 1.5}}>
              INTERVIEWER NE POOCHA
            </div>
            <div style={{fontFamily: FONT_SANS, fontSize: 28, fontWeight: 800, color: C.white, marginTop: 4}}>
              {promptStr}
              <span style={{color: C.gold}}>|</span>
            </div>
          </div>
        </div>

        {!showMatrix ? (
          /* Phase A: 3D Layered 500-Page Biology PDF Stack */
          <div
            style={{
              position: 'relative',
              width: 420,
              height: 520,
              marginTop: 20,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {[3, 2, 1, 0].map((layer) => {
              const floatY = Math.sin((frame + layer * 10) / 10) * 6;
              return (
                <div
                  key={layer}
                  style={{
                    position: 'absolute',
                    width: 310,
                    height: 410,
                    borderRadius: 22,
                    background: layer === 0 ? 'rgba(22, 27, 36, 0.96)' : 'rgba(18, 22, 30, 0.6)',
                    border: layer === 0 ? `2px solid ${C.blue}` : '1.5px solid rgba(255,255,255,0.14)',
                    boxShadow: layer === 0 ? `0 24px 60px rgba(0,0,0,0.85), 0 0 40px ${C.blueGlow}` : 'none',
                    transform: `translate(${layer * 16}px, ${-layer * 14 + floatY}px)`,
                    padding: 28,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.blue, letterSpacing: 2, fontWeight: 800}}>
                    📄 BIOLOGY_NOTES.PDF
                  </div>
                  <div>
                    {[0, 1, 2, 3, 4, 5].map((ln) => (
                      <div
                        key={ln}
                        style={{
                          height: 8,
                          width: `${85 - (ln % 3) * 18}%`,
                          borderRadius: 99,
                          background: 'rgba(255,255,255,0.14)',
                          marginBottom: 14,
                        }}
                      />
                    ))}
                  </div>
                  <div style={{fontFamily: FONT_MONO, fontSize: 16, color: C.muted}}>PAGE 1 .. 500</div>
                </div>
              );
            })}
            <div
              style={{
                position: 'absolute',
                bottom: -70,
                textAlign: 'center',
              }}
            >
              <div style={{fontFamily: FONT_MONO, fontSize: 72, fontWeight: 900, color: C.white, lineHeight: 1}}>
                500
              </div>
              <div style={{fontFamily: FONT_MONO, fontSize: 20, color: C.gold, letterSpacing: 3, marginTop: 6}}>
                PAGES PDF
              </div>
            </div>
          </div>
        ) : (
          /* Phase B: 500-Page Matrix Grid + Giant Neon Red "497 X PADHE HI NAHI" Stamp */
          <div style={{position: 'relative', width: 860, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div
              style={{
                padding: '10px 26px',
                borderRadius: 999,
                border: '1.5px solid rgba(255,255,255,0.2)',
                background: 'rgba(15,18,24,0.95)',
                fontFamily: FONT_MONO,
                fontSize: 18,
                color: C.white,
                fontWeight: 800,
                marginBottom: 22,
              }}
            >
              📄 POORI PDF · 500 PAGES
            </div>

            {/* 20 x 15 Grid representing 500 pages (only 3 green, rest red!) */}
            <div
              style={{
                width: 780,
                display: 'grid',
                gridTemplateColumns: 'repeat(25, 1fr)',
                gap: 6,
                padding: 24,
                borderRadius: 22,
                background: 'rgba(12, 14, 18, 0.92)',
                border: '1px solid rgba(255, 77, 77, 0.3)',
              }}
            >
              {Array.from({length: 300}).map((_, idx) => {
                const isRead = idx === 112 || idx === 113 || idx === 114;
                return (
                  <div
                    key={idx}
                    style={{
                      height: 22,
                      borderRadius: 4,
                      background: isRead ? C.green : 'rgba(255, 77, 77, 0.28)',
                      border: isRead ? `2px solid ${C.white}` : '1px solid rgba(255, 77, 77, 0.45)',
                      boxShadow: isRead ? `0 0 16px ${C.green}` : 'none',
                    }}
                  />
                );
              })}
            </div>

            {/* Giant Tilted Neon Red Stamp */}
            <div
              style={{
                position: 'absolute',
                top: '42%',
                padding: '22px 46px',
                borderRadius: 20,
                background: 'rgba(14, 8, 10, 0.96)',
                border: `4px solid ${C.red}`,
                boxShadow: `0 20px 70px rgba(0,0,0,0.95), 0 0 55px ${C.red}`,
                transform: `rotate(-5deg) scale(${stampScale})`,
                opacity: stampOpacity,
              }}
            >
              <span
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 52,
                  fontWeight: 900,
                  color: C.red,
                  letterSpacing: 3,
                  textShadow: `0 0 24px ${C.red}`,
                }}
              >
                497 ✕ PADHE HI NAHI
              </span>
            </div>

            <div
              style={{
                marginTop: 26,
                fontFamily: FONT_MONO,
                fontSize: 22,
                color: C.green,
                fontWeight: 800,
              }}
            >
              ✔ SIRF 3 SAHI PAGES PADHE → JAWAB IN 2 SECONDS!
            </div>
          </div>
        )}
      </div>
    );
  }

  // BEAT 2: PROBLEM (OVERLOAD Banner -> BADA AI 300/500 Context Window Grid + Cost/Time Counters)
  if (beat.id === 'problem' || beat.type === 'comparison') {
    const showGrid = frame >= 85;
    const pulse = 0.8 + 0.2 * Math.sin(frame / 4);

    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 175,
          paddingLeft: 56,
          paddingRight: 56,
        }}
      >
        {!showGrid ? (
          /* Phase A: Neon Red OVERLOAD Warning + Caution Tape + Overwhelmed AI */
          <div style={{width: 880, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div
              style={{
                padding: '8px 22px',
                borderRadius: 999,
                border: `1.5px solid ${C.red}`,
                background: 'rgba(255, 77, 77, 0.14)',
                fontFamily: FONT_MONO,
                fontSize: 16,
                color: C.red,
                fontWeight: 800,
                marginBottom: 18,
              }}
            >
              ● PROBLEM
            </div>

            <div
              style={{
                fontFamily: FONT_SANS,
                fontSize: 96,
                fontWeight: 900,
                color: C.red,
                letterSpacing: 4,
                textShadow: `0 0 45px ${C.red}`,
                transform: `scale(${0.96 + 0.04 * pulse})`,
                marginBottom: 30,
              }}
            >
              OVERLOAD 🤯
            </div>

            {/* Central Overwhelmed AI Bot Circle + Caution Stripes */}
            <div
              style={{
                position: 'relative',
                width: 860,
                height: 360,
                borderRadius: 28,
                background: 'rgba(16, 18, 24, 0.92)',
                border: `2px solid ${C.red}66`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
              }}
            >
              {/* Diagonal Warning Bars */}
              <div
                style={{
                  width: '110%',
                  height: 28,
                  background: 'repeating-linear-gradient(45deg, #D99B26, #D99B26 20px, #111 20px, #111 40px)',
                  transform: 'rotate(-6deg)',
                  marginBottom: 28,
                }}
              />
              <div
                style={{
                  width: 140,
                  height: 140,
                  borderRadius: 999,
                  background: 'rgba(255, 77, 77, 0.16)',
                  border: `3px solid ${C.red}`,
                  boxShadow: `0 0 40px ${C.red}`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{fontSize: 54}}>🤖</span>
                <span style={{fontFamily: FONT_MONO, fontSize: 16, color: C.white, fontWeight: 800}}>AI LIMIT</span>
              </div>
              <div
                style={{
                  width: '110%',
                  height: 28,
                  background: 'repeating-linear-gradient(45deg, #D99B26, #D99B26 20px, #111 20px, #111 40px)',
                  transform: 'rotate(5deg)',
                  marginTop: 28,
                }}
              />
            </div>

            <div style={{fontFamily: FONT_SANS, fontSize: 28, fontWeight: 800, color: C.white, marginTop: 32}}>
              <span style={{color: C.red}}>500 pages</span> · AI ek baar mein itna padh hi nahi paata!
            </div>
          </div>
        ) : (
          /* Phase B: BADA AI Context Window Box (300/500 inside, +200 overflow outside, 12s & ₹30 cost) */
          <div style={{width: 880, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div
              style={{
                width: '100%',
                borderRadius: 24,
                padding: '26px 32px',
                background: 'rgba(14, 20, 24, 0.96)',
                border: `2px solid ${C.green}`,
                boxShadow: `0 0 40px ${C.greenGlow}`,
              }}
            >
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18}}>
                <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.white, fontWeight: 800}}>
                  ● BADA AI · CONTEXT WINDOW
                </span>
                <span style={{fontFamily: FONT_MONO, fontSize: 26, color: C.gold, fontWeight: 900}}>
                  300 / 500 PAGES
                </span>
              </div>

              {/* 30 Green Page Icons Inside Context Window */}
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: 10}}>
                {Array.from({length: 30}).map((_, i) => (
                  <div
                    key={i}
                    style={{
                      height: 44,
                      borderRadius: 8,
                      background: 'rgba(63, 185, 80, 0.14)',
                      border: `1.5px solid ${C.green}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily: FONT_MONO,
                      fontSize: 13,
                      color: C.green,
                      fontWeight: 700,
                    }}
                  >
                    P.{i + 1}
                  </div>
                ))}
              </div>
            </div>

            {/* +200 Overflowing Red Pages Outside Box */}
            <div
              style={{
                width: 840,
                marginTop: 14,
                padding: '14px 24px',
                borderRadius: 16,
                background: 'rgba(255, 77, 77, 0.12)',
                border: `1.5px dashed ${C.red}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{fontFamily: FONT_MONO, fontSize: 18, color: C.red, fontWeight: 800}}>
                ✕ +200 PAGES ANDAR NAHI AAYE (TRUNCATED!)
              </span>
              <span style={{fontFamily: FONT_MONO, fontSize: 16, color: C.mutedLight}}>301 .. 500 DROPPED</span>
            </div>

            {/* Time (12s) and Money (₹30) Penalty Boxes */}
            <div style={{width: 880, display: 'flex', gap: 24, marginTop: 24}}>
              <div
                style={{
                  flex: 1,
                  padding: '20px 28px',
                  borderRadius: 18,
                  background: 'rgba(255, 77, 77, 0.1)',
                  border: `2px solid ${C.red}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{fontFamily: FONT_MONO, fontSize: 18, color: C.mutedLight}}>TIME PER QUERY</span>
                <span style={{fontFamily: FONT_MONO, fontSize: 38, fontWeight: 900, color: C.red}}>⏱ 12s</span>
              </div>
              <div
                style={{
                  flex: 1,
                  padding: '20px 28px',
                  borderRadius: 18,
                  background: 'rgba(255, 77, 77, 0.1)',
                  border: `2px solid ${C.red}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{fontFamily: FONT_MONO, fontSize: 18, color: C.mutedLight}}>COST PER QUERY</span>
                <span style={{fontFamily: FONT_MONO, fontSize: 38, fontWeight: 900, color: C.red}}>₹ ₹30</span>
              </div>
            </div>

            {/* THIS IS CALLED: Context window badge */}
            <div
              style={{
                marginTop: 28,
                padding: '16px 38px',
                borderRadius: 18,
                background: 'rgba(255, 159, 42, 0.12)',
                border: `2px solid ${C.gold}`,
                textAlign: 'center',
              }}
            >
              <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted, letterSpacing: 2}}>THIS IS CALLED</div>
              <div style={{fontFamily: FONT_SANS, fontSize: 32, fontWeight: 900, color: C.gold, marginTop: 4}}>
                Context window 🧠
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // BEAT 3: CHUNKS & EMBEDDINGS (Phase A: 24 Chunks Grid ✂ -> Phase B: 6 Vector Embedding Cards [x, y])
  if (beat.id === 'embeddings' || beat.type === 'architecture_build') {
    const showEmbeddings = frame >= 95;
    const chunkCards = [
      {page: 'P. 12', title: 'Cell', vec: '[4, 1]', match: false},
      {page: 'P. 45', title: 'Enzymes', vec: '[2, 2]', match: false},
      {page: 'P. 211', title: 'Photosynthesis: intro', vec: '[9, 8]', match: true},
      {page: 'P. 212', title: 'Photosynthesis: dhoop + paani', vec: '[9, 9]', match: true},
      {page: 'P. 213', title: 'Photosynthesis: diagram', vec: '[8, 9]', match: true},
      {page: 'P. 340', title: 'Genetics', vec: '[1, 5]', match: false},
    ];

    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 155,
          paddingLeft: 56,
          paddingRight: 56,
        }}
      >
        <RAGStepperBar activeStep={0} frame={frame} />

        {!showEmbeddings ? (
          /* Phase A: 24 Dashed Green Chunks Grid + "Chunks ✂" Callout */
          <div style={{width: 880, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, width: '100%'}}>
              {Array.from({length: 16}).map((_, idx) => {
                const cEnter = interpolate(frame, [idx * 2, idx * 2 + 12], [0, 1], clamp);
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '16px 14px',
                      borderRadius: 12,
                      background: 'rgba(14, 24, 20, 0.92)',
                      border: `1.5px dashed ${C.green}`,
                      opacity: cEnter,
                      transform: `scale(${0.9 + cEnter * 0.1})`,
                    }}
                  >
                    <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, fontWeight: 800}}>
                      CHUNK {idx + 1}
                    </div>
                    <div
                      style={{
                        height: 6,
                        width: '80%',
                        background: 'rgba(63, 185, 80, 0.35)',
                        borderRadius: 99,
                        marginTop: 8,
                      }}
                    />
                    <div
                      style={{
                        height: 6,
                        width: '55%',
                        background: 'rgba(63, 185, 80, 0.25)',
                        borderRadius: 99,
                        marginTop: 6,
                      }}
                    />
                  </div>
                );
              })}
            </div>

            <div
              style={{
                marginTop: 26,
                padding: '10px 28px',
                borderRadius: 999,
                border: '1px solid rgba(255,255,255,0.2)',
                background: 'rgba(16, 20, 26, 0.95)',
                fontFamily: FONT_MONO,
                fontSize: 20,
                color: C.white,
                fontWeight: 800,
              }}
            >
              📄 500 PAGES → ✂ 2,000 CHUNKS
            </div>

            <div
              style={{
                marginTop: 24,
                padding: '18px 44px',
                borderRadius: 20,
                background: 'rgba(63, 185, 80, 0.12)',
                border: `2px solid ${C.green}`,
                textAlign: 'center',
              }}
            >
              <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted, letterSpacing: 2}}>THIS IS CALLED</div>
              <div style={{fontFamily: FONT_SANS, fontSize: 34, fontWeight: 900, color: C.green, marginTop: 4}}>
                Chunks ✂
              </div>
            </div>
          </div>
        ) : (
          /* Phase B: AI MODEL converts Chunks to Vector Coordinates [4,1], [9,8], [9,9] */
          <div style={{width: 900, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div
              style={{
                padding: '12px 32px',
                borderRadius: 16,
                background: 'rgba(88, 166, 255, 0.16)',
                border: `2px solid ${C.blue}`,
                boxShadow: `0 0 30px ${C.blueGlow}`,
                fontFamily: FONT_MONO,
                fontSize: 22,
                color: C.white,
                fontWeight: 900,
                marginBottom: 24,
              }}
            >
              🤖 AI EMBEDDING MODEL
            </div>

            <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, width: '100%'}}>
              {chunkCards.map((c, idx) => (
                <div
                  key={c.page}
                  style={{
                    padding: '20px 20px',
                    borderRadius: 18,
                    background: c.match ? 'rgba(63, 185, 80, 0.12)' : 'rgba(18, 22, 30, 0.95)',
                    border: `2px solid ${c.match ? C.green : C.blue}AA`,
                    boxShadow: c.match ? `0 0 28px ${C.greenGlow}` : 'none',
                  }}
                >
                  <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.muted}}>{c.page}</div>
                  <div style={{fontFamily: FONT_SANS, fontSize: 20, fontWeight: 800, color: C.white, marginTop: 4}}>
                    {c.title}
                  </div>
                  <div
                    style={{
                      marginTop: 14,
                      display: 'inline-block',
                      padding: '6px 14px',
                      borderRadius: 10,
                      background: 'rgba(0,0,0,0.55)',
                      border: `1.5px solid ${c.match ? C.green : C.blue}`,
                      fontFamily: FONT_MONO,
                      fontSize: 22,
                      fontWeight: 900,
                      color: c.match ? C.green : C.blue,
                    }}
                  >
                    {c.vec}
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                marginTop: 22,
                padding: '10px 26px',
                borderRadius: 999,
                border: `1.5px solid ${C.green}`,
                background: 'rgba(63, 185, 80, 0.1)',
                fontFamily: FONT_MONO,
                fontSize: 17,
                color: C.green,
                fontWeight: 800,
              }}
            >
              ● EK JAISA TOPIC = MILTE-JULTE NUMBERS ([9,8] & [9,9])
            </div>

            <div
              style={{
                marginTop: 20,
                padding: '16px 42px',
                borderRadius: 20,
                background: 'rgba(63, 185, 80, 0.14)',
                border: `2px solid ${C.green}`,
                textAlign: 'center',
              }}
            >
              <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted, letterSpacing: 2}}>THIS IS CALLED</div>
              <div style={{fontFamily: FONT_SANS, fontSize: 34, fontWeight: 900, color: C.green, marginTop: 2}}>
                Embedding
              </div>
              <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.mutedLight, marginTop: 4}}>
                chunk ka matlab = numbers
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // BEAT 4: RETRIEVAL (Query [9,8] + Live PAAS vs DOOR Comparison + 3D Vector Database Cylinder)
  if (beat.id === 'retrieval' || beat.type === 'data_flow') {
    const showMatch = frame >= 45;
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 155,
          paddingLeft: 56,
          paddingRight: 56,
        }}
      >
        <RAGStepperBar activeStep={0} frame={frame} />

        {/* Query -> AI Model -> [9, 8] Row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            marginBottom: 24,
            opacity: enter,
          }}
        >
          <div
            style={{
              padding: '14px 24px',
              borderRadius: 16,
              background: 'rgba(255, 159, 42, 0.14)',
              border: `2px solid ${C.gold}`,
              fontFamily: FONT_SANS,
              fontSize: 22,
              fontWeight: 800,
              color: C.gold,
            }}
          >
            ? Photosynthesis kya hai?
          </div>
          <span style={{fontFamily: FONT_MONO, fontSize: 24, color: C.muted}}>──►</span>
          <div
            style={{
              padding: '14px 22px',
              borderRadius: 16,
              background: 'rgba(88, 166, 255, 0.16)',
              border: `2px solid ${C.blue}`,
              fontFamily: FONT_MONO,
              fontSize: 20,
              fontWeight: 800,
              color: C.white,
            }}
          >
            🤖 AI MODEL
          </div>
          <span style={{fontFamily: FONT_MONO, fontSize: 24, color: C.green}}>──►</span>
          <div
            style={{
              padding: '14px 22px',
              borderRadius: 16,
              background: 'rgba(63, 185, 80, 0.18)',
              border: `2px solid ${C.green}`,
              boxShadow: `0 0 24px ${C.greenGlow}`,
              fontFamily: FONT_MONO,
              fontSize: 26,
              fontWeight: 900,
              color: C.green,
            }}
          >
            [9, 8]
          </div>
        </div>

        {/* Live Similarity Comparison Rows (PAAS ✔ vs DOOR ✕) */}
        {showMatch && (
          <div style={{width: 840, display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 28}}>
            <div
              style={{
                padding: '16px 26px',
                borderRadius: 16,
                background: 'rgba(63, 185, 80, 0.14)',
                border: `2px solid ${C.green}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.white, fontWeight: 800}}>
                [9, 8] vs [9, 9] · <span style={{color: C.mutedLight}}>P.212 PHOTOSYNTHESIS</span>
              </span>
              <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.green, fontWeight: 900}}>PAAS ✔</span>
            </div>

            <div
              style={{
                padding: '16px 26px',
                borderRadius: 16,
                background: 'rgba(255, 77, 77, 0.12)',
                border: `2px solid ${C.red}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.white, fontWeight: 800}}>
                [9, 8] vs [1, 5] · <span style={{color: C.mutedLight}}>P.340 GENETICS</span>
              </span>
              <span style={{fontFamily: FONT_MONO, fontSize: 22, color: C.red, fontWeight: 900}}>DOOR ✕</span>
            </div>
          </div>
        )}

        {/* 3D Glowing Vector Database Cylinder */}
        <div
          style={{
            width: 520,
            borderRadius: '40px / 24px',
            padding: '28px 32px',
            background: 'linear-gradient(180deg, rgba(24, 42, 78, 0.92) 0%, rgba(12, 20, 38, 0.98) 100%)',
            border: `2.5px solid ${C.blue}`,
            boxShadow: `0 20px 60px rgba(0,0,0,0.85), 0 0 50px ${C.blueGlow}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              width: '100%',
              paddingBottom: 14,
              marginBottom: 18,
              borderBottom: `1.5px solid ${C.blue}66`,
              textAlign: 'center',
              fontFamily: FONT_MONO,
              fontSize: 20,
              fontWeight: 900,
              color: C.white,
              letterSpacing: 2,
            }}
          >
            🛢 VECTOR DATABASE
          </div>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, width: '100%'}}>
            {['[4, 1]', '[2, 2]', '[9, 8]', '[9, 9]', '[8, 9]', '[1, 5]'].map((v) => {
              const hit = v === '[9, 8]' || v === '[9, 9]' || v === '[8, 9]';
              return (
                <div
                  key={v}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 10,
                    background: hit ? 'rgba(63, 185, 80, 0.22)' : 'rgba(0,0,0,0.45)',
                    border: `1.5px solid ${hit ? C.green : C.blue}`,
                    fontFamily: FONT_MONO,
                    fontSize: 19,
                    fontWeight: 800,
                    color: hit ? C.green : C.mutedLight,
                    textAlign: 'center',
                  }}
                >
                  {v}
                </div>
              );
            })}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.blue, marginTop: 16, fontWeight: 700}}>
            ~ 2,000 CHUNKS INDEXED · TOP 3 RETRIEVED ✔
          </div>
        </div>
      </div>
    );
  }

  // BEAT 5: AUGMENTED + GENERATION (Dhoondho -> Jodo -> Likho)
  const activeStep: 0 | 1 | 2 = frame < 55 ? 0 : frame < 120 ? 1 : 2;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 155,
        paddingLeft: 56,
        paddingRight: 56,
      }}
    >
      <RAGStepperBar activeStep={activeStep} frame={frame} />

      <div style={{width: 880, display: 'flex', flexDirection: 'column', gap: 20}}>
        {/* 1. R = RETRIEVAL (Dhoondho) */}
        <div
          style={{
            padding: '22px 28px',
            borderRadius: 20,
            background: C.cardBg,
            border: `2px solid ${C.green}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.green, fontWeight: 800}}>
              1. RETRIEVAL (DHOONDHO)
            </div>
            <div style={{fontFamily: FONT_SANS, fontSize: 25, fontWeight: 800, color: C.white, marginTop: 4}}>
              Top 3 Relevant Chunks Extracted
            </div>
          </div>
          <div style={{display: 'flex', gap: 10}}>
            {['P.211 [9,8]', 'P.212 [9,9]', 'P.213 [8,9]'].map((p) => (
              <span
                key={p}
                style={{
                  padding: '8px 14px',
                  borderRadius: 10,
                  background: 'rgba(63, 185, 80, 0.16)',
                  border: `1.5px solid ${C.green}`,
                  fontFamily: FONT_MONO,
                  fontSize: 16,
                  color: C.green,
                  fontWeight: 800,
                }}
              >
                {p}
              </span>
            ))}
          </div>
        </div>

        {/* 2. A = AUGMENTED (Jodo) */}
        <div
          style={{
            padding: '22px 28px',
            borderRadius: 20,
            background: C.cardBg,
            border: `2px solid ${C.gold}`,
            boxShadow: activeStep === 1 ? `0 0 35px ${C.goldGlow}` : 'none',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.gold, fontWeight: 800}}>
              2. AUGMENTED (JODO)
            </div>
            <div style={{fontFamily: FONT_SANS, fontSize: 25, fontWeight: 800, color: C.white, marginTop: 4}}>
              Sawal + 3 Pages Combined in Prompt
            </div>
          </div>
          <div
            style={{
              padding: '10px 18px',
              borderRadius: 12,
              background: 'rgba(255, 159, 42, 0.15)',
              border: `1.5px solid ${C.gold}`,
              fontFamily: FONT_MONO,
              fontSize: 17,
              color: C.gold,
              fontWeight: 800,
            }}
          >
            QUERY + 3 CHUNKS
          </div>
        </div>

        {/* 3. G = GENERATION (Likho) */}
        <div
          style={{
            padding: '24px 28px',
            borderRadius: 20,
            background: C.cardBg,
            border: `2px solid ${C.blue}`,
            boxShadow: activeStep === 2 ? `0 0 40px ${C.blueGlow}` : 'none',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{fontFamily: FONT_MONO, fontSize: 15, color: C.blue, fontWeight: 800}}>
              3. GENERATION (LIKHO)
            </div>
            <div style={{fontFamily: FONT_SANS, fontSize: 25, fontWeight: 800, color: C.white, marginTop: 4}}>
              AI Writes Exact Answer From 3 Pages Only!
            </div>
          </div>
          <div
            style={{
              padding: '10px 20px',
              borderRadius: 12,
              background: 'rgba(63, 185, 80, 0.2)',
              border: `2px solid ${C.green}`,
              fontFamily: FONT_MONO,
              fontSize: 20,
              color: C.green,
              fontWeight: 900,
            }}
          >
            ⚡ 2 SEC ✔
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: 28,
          padding: '14px 36px',
          borderRadius: 999,
          background: 'rgba(63, 185, 80, 0.14)',
          border: `2px solid ${C.green}`,
          fontFamily: FONT_MONO,
          fontSize: 20,
          color: C.white,
          fontWeight: 900,
        }}
      >
        DHOONDHO (R) · JODO (A) · LIKHO (G) = R·A·G ✔
      </div>
    </div>
  );
};

// ==========================================
// ==========================================
// 6A-1. DSA Anagram Interactive Diagram (LeetCode 242)
// ==========================================
const DSAAnagramDiagram: React.FC<{beat: Beat; frame: number}> = ({beat, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const scanProgress = interpolate(frame, [10, 80], [0, 7], clamp);
  const activeCharIdx = Math.min(6, Math.floor(scanProgress));

  const sChars = ['a', 'n', 'a', 'g', 'r', 'a', 'm'];
  const tChars = ['n', 'a', 'g', 'a', 'r', 'a', 'm'];

  const letterBuckets = [
    {char: "'a'", sCount: 3, tCount: 3, finalCount: 0},
    {char: "'g'", sCount: 1, tCount: 1, finalCount: 0},
    {char: "'m'", sCount: 1, tCount: 1, finalCount: 0},
    {char: "'n'", sCount: 1, tCount: 1, finalCount: 0},
    {char: "'r'", sCount: 1, tCount: 1, finalCount: 0},
  ];

  const isDryRun = beat.id === 'dry_run' || beat.id === 'zero_check' || beat.type === 'data_flow';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 160,
        paddingLeft: 56,
        paddingRight: 56,
      }}
    >
      {/* Top Badge */}
      <div
        style={{
          padding: '8px 22px',
          borderRadius: 999,
          background: 'rgba(88, 166, 255, 0.14)',
          border: `1.5px solid ${C.blue}`,
          fontFamily: FONT_MONO,
          fontSize: 14,
          fontWeight: 800,
          color: C.blue,
          marginBottom: 16,
          opacity: enter,
        }}
      >
        LEETCODE 242 · 26-BUCKET SCALE
      </div>

      {/* Main Beat Title */}
      <div style={{textAlign: 'center', marginBottom: 24, opacity: enter}}>
        <EditorialText text={`*${beat.title || 'Valid Anagram'}*`} fontSize={46} color={C.white} accentColor={C.gold} />
      </div>

      {/* String S Strip */}
      <div
        style={{
          width: 880,
          padding: '16px 24px',
          borderRadius: 20,
          background: 'rgba(20, 26, 36, 0.94)',
          border: `1.5px solid ${C.gold}88`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 14,
          opacity: enter,
        }}
      >
        <div style={{fontFamily: FONT_MONO, fontSize: 18, fontWeight: 900, color: C.gold}}>
          String s =
        </div>
        <div style={{display: 'flex', gap: 10}}>
          {sChars.map((ch, i) => {
            const isScanning = isDryRun && i === activeCharIdx;
            const isDone = isDryRun && i < activeCharIdx;
            return (
              <div
                key={i}
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 12,
                  background: isScanning ? C.gold : isDone ? 'rgba(255, 159, 42, 0.2)' : 'rgba(255,255,255,0.06)',
                  border: `2px solid ${isScanning ? '#FFF' : isDone ? C.gold : 'rgba(255,255,255,0.15)'}`,
                  boxShadow: isScanning ? `0 0 20px ${C.gold}` : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: FONT_MONO,
                  fontSize: 24,
                  fontWeight: 900,
                  color: isScanning ? '#000' : C.white,
                  transform: `scale(${isScanning ? 1.15 : 1})`,
                }}
              >
                {ch}
              </div>
            );
          })}
        </div>
        <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, fontWeight: 800}}>
          +1 COUNT
        </div>
      </div>

      {/* String T Strip */}
      <div
        style={{
          width: 880,
          padding: '16px 24px',
          borderRadius: 20,
          background: 'rgba(20, 26, 36, 0.94)',
          border: `1.5px solid ${C.blue}88`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
          opacity: enter,
        }}
      >
        <div style={{fontFamily: FONT_MONO, fontSize: 18, fontWeight: 900, color: C.blue}}>
          String t =
        </div>
        <div style={{display: 'flex', gap: 10}}>
          {tChars.map((ch, i) => {
            const isScanning = isDryRun && i === activeCharIdx;
            const isDone = isDryRun && i < activeCharIdx;
            return (
              <div
                key={i}
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 12,
                  background: isScanning ? C.blue : isDone ? 'rgba(88, 166, 255, 0.2)' : 'rgba(255,255,255,0.06)',
                  border: `2px solid ${isScanning ? '#FFF' : isDone ? C.blue : 'rgba(255,255,255,0.15)'}`,
                  boxShadow: isScanning ? `0 0 20px ${C.blue}` : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: FONT_MONO,
                  fontSize: 24,
                  fontWeight: 900,
                  color: isScanning ? '#000' : C.white,
                  transform: `scale(${isScanning ? 1.15 : 1})`,
                }}
              >
                {ch}
              </div>
            );
          })}
        </div>
        <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.red, fontWeight: 800}}>
          -1 COUNT
        </div>
      </div>

      {/* 26-Bucket Alphabet Array Display */}
      <div
        style={{
          width: 880,
          padding: '24px 28px',
          borderRadius: 22,
          background: 'rgba(14, 18, 24, 0.96)',
          border: `2px solid ${C.cardBorder}`,
          boxShadow: '0 16px 50px rgba(0,0,0,0.7)',
          opacity: enter,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div style={{display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted, letterSpacing: 1.5, fontWeight: 800}}>
            INT[26] FREQUENCY SCALE (INDEX: CHAR - 'A')
          </div>
          <div
            style={{
              padding: '4px 12px',
              borderRadius: 8,
              background: 'rgba(60, 235, 139, 0.15)',
              border: `1px solid ${C.green}`,
              fontFamily: FONT_MONO,
              fontSize: 12,
              fontWeight: 800,
              color: C.green,
            }}
          >
            SPACE: O(1) CONSTANT
          </div>
        </div>

        {/* 5 Buckets of Active Letters + Others indicator */}
        <div style={{display: 'flex', gap: 14, width: '100%', justifyContent: 'center'}}>
          {letterBuckets.map((bucket) => {
            const isSettled = frame > 40;
            return (
              <div
                key={bucket.char}
                style={{
                  flex: 1,
                  padding: '14px 10px',
                  borderRadius: 16,
                  background: 'rgba(255,255,255,0.03)',
                  border: `1.5px solid ${C.green}88`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <div style={{fontFamily: FONT_MONO, fontSize: 15, fontWeight: 900, color: C.gold}}>
                  {bucket.char}
                </div>
                <div style={{fontFamily: FONT_MONO, fontSize: 12, color: C.muted}}>
                  +{bucket.sCount} -{bucket.tCount}
                </div>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: isSettled ? 'rgba(60, 235, 139, 0.2)' : 'rgba(255,255,255,0.06)',
                    border: `1.5px solid ${isSettled ? C.green : 'rgba(255,255,255,0.2)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: FONT_MONO,
                    fontSize: 20,
                    fontWeight: 900,
                    color: isSettled ? C.green : C.white,
                  }}
                >
                  {bucket.finalCount}
                </div>
                <div style={{fontFamily: FONT_MONO, fontSize: 11, color: C.green, fontWeight: 700}}>
                  ✔ ZERO
                </div>
              </div>
            );
          })}
          <div
            style={{
              flex: 1,
              padding: '14px 10px',
              borderRadius: 16,
              background: 'rgba(255,255,255,0.02)',
              border: '1.5px dashed rgba(255,255,255,0.15)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
            }}
          >
            <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted}}>OTHER 21</div>
            <div style={{fontFamily: FONT_MONO, fontSize: 20, fontWeight: 900, color: C.muted}}>0</div>
            <div style={{fontFamily: FONT_MONO, fontSize: 11, color: C.muted}}>UNTOUCHED</div>
          </div>
        </div>

        {/* Live Balance / Result Banner */}
        <div
          style={{
            width: '100%',
            padding: '12px 18px',
            borderRadius: 14,
            background: 'rgba(60, 235, 139, 0.12)',
            border: `1.5px solid ${C.green}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{fontFamily: FONT_MONO, fontSize: 14, fontWeight: 800, color: C.white}}>
            ⚖ SCALE VERIFICATION:
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 15, fontWeight: 900, color: C.green}}>
            ALL 26 BUCKETS == 0 → RETURN TRUE ✔
          </div>
        </div>
      </div>

      {/* Bottom "THIS IS CALLED" Concept Callout Box */}
      <div
        style={{
          marginTop: 22,
          padding: '14px 38px',
          borderRadius: 18,
          background: 'rgba(255, 159, 42, 0.12)',
          border: `2px solid ${C.gold}`,
          textAlign: 'center',
          opacity: enter,
        }}
      >
        <div style={{fontFamily: FONT_MONO, fontSize: 12, color: C.muted, letterSpacing: 2}}>THIS IS CALLED</div>
        <div style={{fontFamily: FONT_SANS, fontSize: 26, fontWeight: 900, color: C.gold, marginTop: 2}}>
          {(beat.accent_words && beat.accent_words[0]) || beat.metric || '26-BUCKET FREQUENCY CANCEL'}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 6A-2. Consistent Hashing Diagram
// ==========================================
const ConsistentHashingDiagram: React.FC<{beat: Beat; topic: string; frame: number}> = ({beat, topic, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const nodes = beat.nodes && beat.nodes.length > 0 ? beat.nodes : [];
  const items = nodes.length > 0 ? nodes : [
    {label: 'Key Hash', detail: 'Incoming object hash token', color: C.gold},
    {label: 'Hash Ring', detail: '0° to 360° circular space', color: C.blue},
    {label: 'Target Node', detail: 'Clockwise next server', color: C.green},
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 155,
        paddingLeft: 56,
        paddingRight: 56,
      }}
    >
      <div
        style={{
          padding: '8px 22px',
          borderRadius: 999,
          background: 'rgba(255, 159, 42, 0.14)',
          border: `1.5px solid ${C.gold}`,
          fontFamily: FONT_MONO,
          fontSize: 14,
          fontWeight: 800,
          color: C.gold,
          marginBottom: 16,
          opacity: enter,
        }}
      >
        DISTRIBUTED SYSTEMS · CONSISTENT HASHING
      </div>

      <div style={{textAlign: 'center', marginBottom: 18, opacity: enter}}>
        <EditorialText text={`*${beat.title || topic}*`} fontSize={46} color={C.white} accentColor={C.gold} />
      </div>

      <div
        style={{
          position: 'relative',
          width: 300,
          height: 300,
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: enter,
        }}
      >
        <svg width="300" height="300" viewBox="0 0 300 300">
          <circle cx="150" cy="150" r="110" fill="rgba(16, 22, 32, 0.85)" stroke={C.blue} strokeWidth="4" strokeDasharray="10 6" />
          <circle
            cx="150"
            cy="150"
            r="110"
            fill="none"
            stroke={C.green}
            strokeWidth="6"
            strokeDasharray={`${interpolate(frame % 90, [0, 89], [20, 240], clamp)} 700`}
            strokeLinecap="round"
            transform="rotate(-90 150 150)"
          />
          <circle cx="150" cy="40" r="16" fill={C.gold} />
          <text x="150" y="45" textAnchor="middle" fill="#000" fontSize="12" fontWeight="900" fontFamily="monospace">S1</text>
          <circle cx="245" cy="205" r="16" fill={C.green} />
          <text x="245" y="210" textAnchor="middle" fill="#000" fontSize="12" fontWeight="900" fontFamily="monospace">S2</text>
          <circle cx="55" cy="205" r="16" fill={C.blue} />
          <text x="55" y="210" textAnchor="middle" fill="#000" fontSize="12" fontWeight="900" fontFamily="monospace">S3</text>
          {(() => {
            const angle = ((frame * 3) % 360) * (Math.PI / 180);
            const kx = 150 + 110 * Math.cos(angle - Math.PI / 2);
            const ky = 150 + 110 * Math.sin(angle - Math.PI / 2);
            return <circle cx={kx} cy={ky} r="9" fill="#FFFFFF" stroke={C.green} strokeWidth="4" />;
          })()}
        </svg>
        <div style={{position: 'absolute', textAlign: 'center'}}>
          <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.muted}}>HASH RING</div>
          <div style={{fontFamily: FONT_MONO, fontSize: 22, fontWeight: 900, color: C.green}}>0° — 360°</div>
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.gold, marginTop: 2}}>CLOCKWISE ↻</div>
        </div>
      </div>

      <div style={{width: 880, display: 'flex', flexDirection: 'column', gap: 10, opacity: enter}}>
        {items.slice(0, 2).map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: '14px 20px',
              borderRadius: 14,
              background: C.cardBg,
              border: `1.5px solid ${item.color || C.cardBorder}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{fontFamily: FONT_MONO, fontSize: 13, color: item.color || C.gold, fontWeight: 800}}>{item.label}</div>
              <div style={{fontFamily: FONT_SANS, fontSize: 16, color: C.mutedLight, marginTop: 2}}>{item.detail}</div>
            </div>
            <div style={{fontFamily: FONT_MONO, fontSize: 14, color: C.green, fontWeight: 800}}>HASHED ✔</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ==========================================
// 6A-3. Rate Limiting Diagram
// ==========================================
const RateLimitingDiagram: React.FC<{beat: Beat; topic: string; frame: number}> = ({beat, topic, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const items = beat.nodes && beat.nodes.length > 0 ? beat.nodes : [
    {label: 'Incoming Traffic', detail: 'Burst requests at scale', color: C.gold},
    {label: 'Token Bucket', detail: 'Refilled at constant rate', color: C.blue},
    {label: 'Traffic Gate', detail: 'Allow 200 or Block 429', color: C.green},
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 155,
        paddingLeft: 56,
        paddingRight: 56,
      }}
    >
      <div
        style={{
          padding: '8px 22px',
          borderRadius: 999,
          background: 'rgba(255, 77, 77, 0.14)',
          border: `1.5px solid ${C.red}`,
          fontFamily: FONT_MONO,
          fontSize: 14,
          fontWeight: 800,
          color: C.red,
          marginBottom: 16,
          opacity: enter,
        }}
      >
        API INFRASTRUCTURE · RATE LIMITING
      </div>

      <div style={{textAlign: 'center', marginBottom: 20, opacity: enter}}>
        <EditorialText text={`*${beat.title || topic}*`} fontSize={46} color={C.white} accentColor={C.gold} />
      </div>

      <div
        style={{
          width: 880,
          padding: '24px 28px',
          marginBottom: 20,
          borderRadius: 22,
          background: 'rgba(14, 18, 26, 0.94)',
          border: `2px solid ${C.gold}88`,
          boxShadow: `0 12px 40px rgba(0,0,0,0.6), 0 0 35px ${C.goldGlow}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          opacity: enter,
        }}
      >
        <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.muted, letterSpacing: 1.5}}>
            {(items[0]?.label || 'BURST TRAFFIC').toUpperCase().slice(0, 20)}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 22, fontWeight: 900, color: C.white}}>
            ⚡ {(items[0]?.detail || beat.metric || 'HIGH SCALE').slice(0, 22)}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: 13, color: C.gold}}>API Gatekeeper</div>
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '12px 22px',
            borderRadius: 16,
            background: 'rgba(255,255,255,0.04)',
            border: `1.5px solid ${C.blue}88`,
          }}
        >
          <div style={{fontFamily: FONT_MONO, fontSize: 12, color: C.blue, fontWeight: 800, marginBottom: 8}}>
            {(items[1]?.label || 'TOKEN BUCKET').toUpperCase()}
          </div>
          <div style={{display: 'flex', gap: 10}}>
            {[0, 1, 2, 3, 4].map((slot) => {
              const activeTokens = 5 - Math.floor((frame % 90) / 18);
              const hasToken = slot < activeTokens;
              return (
                <div
                  key={slot}
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: '50%',
                    background: hasToken ? C.gold : 'rgba(255,255,255,0.08)',
                    border: `2px solid ${hasToken ? '#FFF' : 'rgba(255,255,255,0.2)'}`,
                    boxShadow: hasToken ? `0 0 14px ${C.gold}` : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: FONT_MONO,
                    fontSize: 13,
                    fontWeight: 900,
                    color: hasToken ? '#000' : C.muted,
                  }}
                >
                  {hasToken ? 'T' : '·'}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end'}}>
          <div
            style={{
              padding: '6px 14px',
              borderRadius: 99,
              background: 'rgba(63, 185, 80, 0.16)',
              border: `1.5px solid ${C.green}`,
              fontFamily: FONT_MONO,
              fontSize: 13,
              fontWeight: 800,
              color: C.green,
            }}
          >
            ✔ ALLOWED → 200 OK
          </div>
          <div
            style={{
              padding: '6px 14px',
              borderRadius: 99,
              background: 'rgba(255, 77, 77, 0.16)',
              border: `1.5px solid ${C.red}`,
              fontFamily: FONT_MONO,
              fontSize: 13,
              fontWeight: 800,
              color: C.red,
            }}
          >
            ✕ REJECTED → 429
          </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 6B. Universal Dynamic Topic Diagram (Any New Topic)
// ==========================================
const UniversalTopicDiagram: React.FC<{beat: Beat; topic: string; frame: number}> = ({beat, topic, frame}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const nodes = beat.nodes && beat.nodes.length > 0 ? beat.nodes : [];
  const steps = beat.steps && beat.steps.length > 0 ? beat.steps : [];
  const items =
    nodes.length > 0
      ? nodes.map((n, i) => ({
          tag: `STAGE 0${i + 1}`,
          label: n.label,
          detail: n.detail || 'Core production stage',
          color: n.color || (i === 0 ? C.gold : i === 1 ? C.blue : C.green),
        }))
      : steps.length > 0
        ? steps.map((s, i) => ({
            tag: `STEP 0${i + 1}`,
            label: s.label,
            detail: s.detail || 'Sequential execution flow',
            color: i === 0 ? C.gold : i === 1 ? C.blue : C.green,
          }))
        : [
            {tag: 'STAGE 01', label: `${topic} Input`, detail: 'Incoming request payload', color: C.gold},
            {tag: 'STAGE 02', label: `${beat.title || topic}`, detail: 'Core engine execution', color: C.blue},
            {tag: 'STAGE 03', label: 'Verified Output', detail: 'Low-latency response', color: C.green},
          ];

  const activeStage = Math.min(items.length - 1, Math.floor(frame / 45));
  const calloutConcept = (beat.accent_words && beat.accent_words[0]) || beat.metric || beat.title || topic;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 155,
        paddingLeft: 56,
        paddingRight: 56,
      }}
    >
      {/* Interactive Top Stage Stepper */}
      <div
        style={{
          width: 880,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 20px',
          borderRadius: 999,
          background: 'rgba(14, 18, 24, 0.92)',
          border: '1px solid rgba(255,255,255,0.1)',
          marginBottom: 24,
          opacity: enter,
        }}
      >
        {items.slice(0, 3).map((it, idx) => {
          const isAct = idx === activeStage;
          return (
            <React.Fragment key={it.tag}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 18px',
                  borderRadius: 999,
                  background: isAct ? `${it.color}22` : 'transparent',
                  border: isAct ? `1.5px solid ${it.color}` : '1px solid transparent',
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 999,
                    border: `2px solid ${it.color}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: FONT_MONO,
                    fontSize: 14,
                    fontWeight: 900,
                    color: it.color,
                  }}
                >
                  {idx + 1}
                </div>
                <span style={{fontFamily: FONT_MONO, fontSize: 15, fontWeight: 800, color: isAct ? C.white : C.muted}}>
                  {it.label.slice(0, 18).toUpperCase()}
                </span>
              </div>
              {idx < Math.min(2, items.length - 1) && (
                <div style={{flex: 1, height: 2, margin: '0 8px', borderTop: '2px dashed rgba(255,255,255,0.2)'}} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Main Beat Title */}
      <div style={{textAlign: 'center', marginBottom: 24, opacity: enter}}>
        <EditorialText text={`*${beat.title || topic}*`} fontSize={48} color={C.white} accentColor={C.gold} />
      </div>

      {/* Dynamic Interactive Cards Stack with Live Flow Connectors */}
      <div style={{width: 880, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, opacity: enter}}>
        {items.slice(0, 3).map((item, idx) => {
          const itemEnter = interpolate(frame, [idx * 6, idx * 6 + 14], [0, 1], clamp);
          const isFocused = idx === activeStage;
          return (
            <React.Fragment key={`${item.label}-${idx}`}>
              <div
                style={{
                  width: '100%',
                  borderRadius: 20,
                  padding: '22px 30px',
                  border: `2px solid ${isFocused ? item.color : `${item.color}66`}`,
                  background: isFocused ? 'rgba(20, 26, 36, 0.96)' : C.cardBg,
                  boxShadow: isFocused ? `0 12px 40px rgba(0,0,0,0.8), 0 0 34px ${item.color}33` : 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: itemEnter,
                  transform: `translateY(${(1 - itemEnter) * 20}px) scale(${isFocused ? 1.015 : 1})`,
                }}
              >
                <div>
                  <div
                    style={{fontFamily: FONT_MONO, fontSize: 13, color: item.color, letterSpacing: 1.5, fontWeight: 800}}
                  >
                    {item.tag}
                  </div>
                  <div style={{fontFamily: FONT_SANS, fontSize: 27, fontWeight: 800, color: C.white, marginTop: 4}}>
                    {item.label}
                  </div>
                  <div style={{fontFamily: FONT_SANS, fontSize: 18, color: C.mutedLight, marginTop: 4}}>
                    {item.detail}
                  </div>
                </div>
                <div
                  style={{
                    padding: '10px 18px',
                    borderRadius: 12,
                    background: `${item.color}18`,
                    border: `1.5px solid ${item.color}`,
                    fontFamily: FONT_MONO,
                    fontSize: 15,
                    color: item.color,
                    fontWeight: 800,
                  }}
                >
                  {isFocused ? '⚡ EXECUTING' : 'READY ✔'}
                </div>
              </div>
              {idx < Math.min(2, items.length - 1) && (
                <div style={{fontFamily: FONT_MONO, fontSize: 18, color: C.green, fontWeight: 900, lineHeight: 1}}>
                  ▼
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Bottom "THIS IS CALLED" Concept Callout Box */}
      <div
        style={{
          marginTop: 24,
          padding: '14px 38px',
          borderRadius: 18,
          background: 'rgba(255, 159, 42, 0.12)',
          border: `2px solid ${C.gold}`,
          textAlign: 'center',
          opacity: enter,
        }}
      >
        <div style={{fontFamily: FONT_MONO, fontSize: 12, color: C.muted, letterSpacing: 2}}>THIS IS CALLED</div>
        <div style={{fontFamily: FONT_SANS, fontSize: 28, fontWeight: 900, color: C.gold, marginTop: 2}}>
          {calloutConcept}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 7. Cheat Sheet Outro Card (Benchmark 1:1)
// ==========================================
const CheatsheetOutroCard: React.FC<{topic: string; beat: Beat; frame: number; platform?: 'reel' | 'shorts' | string}> = ({
  topic,
  beat,
  frame,
  platform = 'reel',
}) => {
  const enter = interpolate(frame, [0, 14], [0, 1], clamp);
  const buttonPulse = 1 + 0.04 * Math.sin(frame / 10);
  const isShorts = platform === 'shorts';

  const isTwoSum = isTwoSumTopic(topic);
  const isAnagram = topic.toLowerCase().includes('anagram');
  const isScaling = isScalingTopic(topic);
  const isKafka = topic.toLowerCase().includes('kafka');
  const dynamicBullets =
    beat.nodes && beat.nodes.length > 0
      ? beat.nodes.map((n) => `${n.label.toLowerCase()} (${(n.detail || '').toLowerCase()})`).join(' · ')
      : `${topic.toLowerCase()} · algorithm · complexity · trade-offs`;
  const bulletText = isAnagram
    ? 's = "anagram" · t = "nagaram" · 26 frequency buckets · time O(n) · space O(1) · optimal'
    : isTwoSum
      ? 'array · hashmap · complement · two pointers · time O(n) · space O(n)'
      : isScaling
        ? 'load balancer · round robin · commodity servers · zero downtime · stateless'
        : isKafka
          ? 'log · partitions · disk · page cache · zero copy · retention · replication'
          : dynamicBullets;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 75px',
      }}
    >
      {/* Golden Cheatsheet Card */}
      <div
        style={{
          width: 580,
          borderRadius: 28,
          padding: '42px 46px',
          background: 'rgba(18, 20, 24, 0.96)',
          border: `2px solid ${C.gold}`,
          boxShadow: `0 24px 80px rgba(0,0,0,0.85), 0 0 60px ${C.goldGlow}`,
          opacity: enter,
          transform: `scale(${0.92 + enter * 0.08})`,
        }}
      >
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 18,
            color: C.gold,
            fontWeight: 700,
            letterSpacing: 1,
            marginBottom: 12,
          }}
        >
          PDF · interview notes
        </div>

        <div
          style={{
            fontFamily: FONT_SERIF,
            fontSize: 68,
            fontStyle: 'italic',
            fontWeight: 800,
            color: C.gold,
            lineHeight: 1.05,
          }}
        >
          {topic}
        </div>

        <div style={{display: 'flex', gap: 10, margin: '24px 0'}}>
          {[0, 1, 2, 3, 4].map((idx) => (
            <div
              key={idx}
              style={{
                flex: 1,
                height: 10,
                borderRadius: 99,
                background: idx === 4 ? C.green : 'rgba(255, 255, 255, 0.14)',
                boxShadow: idx === 4 ? `0 0 10px ${C.green}` : 'none',
              }}
            />
          ))}
        </div>

        <div
          style={{
            fontFamily: FONT_SANS,
            fontSize: 20,
            color: C.mutedLight,
            lineHeight: 1.8,
            marginTop: 18,
          }}
        >
          {bulletText}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            fontFamily: FONT_SANS,
            fontSize: 16,
            color: C.mutedLight,
            marginTop: 32,
            fontWeight: 700,
          }}
        >
          <Img
            src={staticFile('branding/channel_avatar.jpg')}
            style={{
              width: 34,
              height: 34,
              borderRadius: '50%',
              border: `1.5px solid ${C.green}`,
              objectFit: 'cover',
            }}
          />
          <span>
            {isShorts ? '@ConceptFirstWithMohit · YouTube Shorts' : '@conceptfirstwithmohit · Concept First'}
          </span>
        </div>
      </div>

      {/* Platform-Aware CTA Button (+ Follow for Reels | ▶ Subscribe for YouTube Shorts) */}
      <div
        style={{
          marginTop: 45,
          padding: '18px 65px',
          borderRadius: 999,
          background: isShorts ? '#FF0033' : C.gold,
          color: isShorts ? '#FFFFFF' : '#0A0A0A',
          fontFamily: FONT_SANS,
          fontSize: 28,
          fontWeight: 900,
          letterSpacing: 0.5,
          boxShadow: isShorts ? '0 12px 45px rgba(255, 0, 51, 0.45)' : `0 12px 40px ${C.goldGlow}`,
          transform: `scale(${buttonPulse})`,
          opacity: enter,
        }}
      >
        {isShorts ? '▶ Subscribe' : '+ Follow'}
      </div>

      {/* Platform-Aware Comment / Pinned Comment Bar */}
      <div
        style={{
          marginTop: 32,
          width: 580,
          padding: '16px 26px',
          borderRadius: 999,
          background: 'rgba(255, 255, 255, 0.06)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isShorts ? 'center' : 'flex-start',
          gap: 14,
          opacity: enter,
        }}
      >
        {isShorts ? (
          <>
            <span style={{fontFamily: FONT_SANS, fontSize: 18, color: C.gold, fontWeight: 700}}>
              📌 Pinned Comment:
            </span>
            <span style={{fontFamily: FONT_MONO, fontSize: 18, color: C.white, fontWeight: 800}}>
              FREE {topic.toUpperCase()} PDF NOTES
            </span>
          </>
        ) : (
          <>
            <span style={{fontFamily: FONT_SANS, fontSize: 18, color: C.muted}}>Add a comment...</span>
            <span style={{fontFamily: FONT_MONO, fontSize: 19, color: C.white, fontWeight: 800}}>
              {topic.toUpperCase().replace(/\s+/g, '')}
            </span>
          </>
        )}
      </div>
    </div>
  );
};

// ==========================================
// Minimalist Editorial Caption Overlay (Safe Zone with Spring Physics)
// ==========================================
const BenchmarkCaption: React.FC<{beat: Beat; frame: number; fps: number}> = ({beat, frame, fps}) => {
  const words = beat.word_timings || [];
  if (words.length === 0) return null;

  const seconds = frame / fps;
  let active = words.findIndex((w) => seconds >= w.start && seconds < w.end);
  if (active < 0) {
    const next = words.findIndex((w) => w.start > seconds);
    active = next >= 0 ? next : Math.max(0, words.length - 1);
  }
  const first = Math.floor(active / 4) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        left: 80,
        right: 80,
        bottom: 220,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: 14,
        padding: '16px 28px',
        borderRadius: 22,
        background: 'rgba(7, 7, 7, 0.88)',
        border: '1.5px solid rgba(255, 255, 255, 0.12)',
        backdropFilter: 'blur(16px)',
        boxShadow: '0 12px 35px rgba(0, 0, 0, 0.65)',
        zIndex: 50,
      }}
    >
      {words.slice(first, first + 4).map((word, i) => {
        const isActive = first + i === active;
        const wordStartFrame = Math.round(word.start * fps);
        const wordAge = Math.max(0, frame - wordStartFrame);
        const springBounce = isActive
          ? spring({
              frame: wordAge,
              fps,
              config: { damping: 10, stiffness: 240, mass: 0.5 },
            })
          : 0;
        const scale = isActive ? 1 + springBounce * 0.14 : 1;

        return (
          <span
            key={`${first + i}-${word.start}`}
            style={{
              fontFamily: FONT_SANS,
              fontSize: 35,
              fontWeight: 900,
              color: isActive ? C.gold : C.white,
              opacity: isActive ? 1 : 0.65,
              textShadow: isActive
                ? `0 0 24px ${C.goldGlow}, 0 2px 10px rgba(0,0,0,0.8)`
                : '0 2px 8px rgba(0,0,0,0.6)',
              transform: `scale(${scale})`,
              display: 'inline-block',
              transition: 'color 0.1s ease',
            }}
          >
            {word.text}
          </span>
        );
      })}
    </div>
  );
};

// ==========================================
// Main Visual Beat Router
// ==========================================
const BenchmarkVisualContent: React.FC<{beat: Beat; frame: number; plan: Plan}> = ({beat, frame, plan}) => {
  const topicLower = plan.topic.toLowerCase();
  const isTwoSum = isTwoSumTopic(plan.topic);
  const isAnagram = topicLower.includes('anagram');
  const isKafka = topicLower.includes('kafka');
  const isRAG = isRagTopic(plan.topic);
  const isScaling = isScalingTopic(plan.topic) && topicLower.includes('scaling');
  const isRateLimit = /\b(rate limit|rate limiter|token bucket|leaky bucket)\b/i.test(topicLower);
  const isConsistentHashing = /\b(consistent hash|hash ring)\b/i.test(topicLower);

  // 1. Summary / Outro
  if (beat.type === 'summary' || beat.id === 'summary') {
    return <CheatsheetOutroCard topic={plan.topic} beat={beat} frame={frame} platform={plan.platform} />;
  }

  // 2. RAG Interactive Motion Graphics Engine (1:1 @backendlore benchmark)
  if (isRAG) {
    return <RAGInteractiveDiagram beat={beat} frame={frame} />;
  }

  // 3. Hook Beat (for non-RAG topics)
  if (beat.id === 'hook' || beat.type === 'kinetic_title') {
    return <InterviewHookCard topic={plan.topic} beat={beat} frame={frame} />;
  }

  // 4. Rate Limiting beats
  if (isRateLimit) {
    if (beat.type === 'comparison') {
      return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
    }
    return <RateLimitingDiagram beat={beat} topic={plan.topic} frame={frame} />;
  }

  // 5. Consistent Hashing beats
  if (isConsistentHashing) {
    if (beat.type === 'comparison') {
      return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
    }
    return <ConsistentHashingDiagram beat={beat} topic={plan.topic} frame={frame} />;
  }

  // 6. Scaling beats
  if (isScaling) {
    if (beat.type === 'comparison' || beat.id === 'vertical_limits') {
      return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
    }
    return <HorizontalScalingDiagram beat={beat} frame={frame} />;
  }

  // 7. Anagram specific beats (LeetCode 242)
  if (isAnagram) {
    if (beat.id === 'naive_trap' || beat.type === 'comparison') {
      return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
    }
    return <DSAAnagramDiagram beat={beat} frame={frame} />;
  }

  // 8. Two Sum specific beats (only for Two Sum problem)
  if (isTwoSum) {
    if (beat.id === 'problem' || beat.type === 'concept_visual') {
      return <DSAArrayTapeDiagram beat={beat} frame={frame} />;
    }
    if (beat.id === 'hashmap' || beat.type === 'architecture_build') {
      return <DSAHashMapDiagram beat={beat} frame={frame} />;
    }
    if (beat.id === 'baseline' || beat.id === 'complexity' || beat.type === 'comparison') {
      return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
    }
    if (beat.id === 'idea' || beat.type === 'metric_callout') {
      return <DSAHashMapDiagram beat={beat} frame={frame} />;
    }
    if (beat.id === 'dryrun' || beat.type === 'data_flow') {
      return <DSAArrayTapeDiagram beat={beat} frame={frame} />;
    }
    return <DSAArrayTapeDiagram beat={beat} frame={frame} />;
  }

  // 9. Kafka / Messaging beats
  if (isKafka) {
    if (beat.id.includes('partition') || beat.type === 'architecture_build') {
      return <PartitionLanesDiagram beat={beat} frame={frame} />;
    }
    return <LogStreamDiagram beat={beat} frame={frame} />;
  }

  // 10. Universal fallback for ANY new topic
  if (beat.type === 'comparison') {
    return <EditorialComparison beat={beat} frame={frame} topic={plan.topic} />;
  }
  return <UniversalTopicDiagram beat={beat} topic={plan.topic} frame={frame} />;
};

// ==========================================
// Single Beat Scene
// ==========================================
const BenchmarkBeatScene: React.FC<{beat: Beat; plan: Plan; beatIndex: number; totalBeats: number}> = ({
  beat,
  plan,
  beatIndex,
  totalBeats,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const opacity = beatIndex === 0 ? 1 : interpolate(frame, [0, 8], [0, 1], clamp);
  const progressPct = Math.min(
    100,
    ((beatIndex + Math.min(1, frame / Math.max(1, durationInFrames))) / Math.max(1, totalBeats)) * 100
  );

  const isHook = beat.id === 'hook' || beat.type === 'kinetic_title';
  const isProblem = beat.id === 'problem' || beat.type === 'comparison' || beat.id === 'vertical_limits';
  const badgeColor = isHook ? C.blue : isProblem ? C.red : C.green;
  const badgeLabel = isHook
    ? '● INTERVIEW QUESTION'
    : isProblem
      ? '● PROBLEM'
      : `● SOLUTION · ${plan.topic.toUpperCase().slice(0, 18)}`;

  return (
    <AbsoluteFill style={{background: C.bg, opacity}}>
      <BenchmarkBackdrop frame={frame} />

      {/* Render AI-generated supporting image when beat.asset_file is present */}
      {beat.asset_file ? (
        <>
          <Img
            src={staticFile(beat.asset_file)}
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: 0.14,
              filter: 'blur(10px) saturate(1.2)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              right: 56,
              bottom: 340,
              width: 240,
              height: 150,
              borderRadius: 18,
              overflow: 'hidden',
              border: `1.5px solid ${C.gold}88`,
              boxShadow: '0 12px 35px rgba(0,0,0,0.75)',
              zIndex: 35,
            }}
          >
            <Img
              src={staticFile(beat.asset_file)}
              style={{width: '100%', height: '100%', objectFit: 'cover'}}
            />
          </div>
        </>
      ) : null}

      <BenchmarkVisualContent beat={beat} frame={frame} plan={plan} />

      {/* @backendlore Benchmark Top Chrome Header + Progress Bar + Status Pill */}
      <div
        style={{
          position: 'absolute',
          top: 48,
          left: 56,
          right: 56,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          zIndex: 40,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              fontFamily: FONT_MONO,
              fontSize: 18,
              fontWeight: 800,
              letterSpacing: 3,
              color: C.white,
            }}
          >
            <Img
              src={staticFile('branding/channel_avatar.jpg')}
              style={{
                width: 30,
                height: 30,
                borderRadius: '50%',
                border: `1.5px solid ${C.green}`,
                objectFit: 'cover',
              }}
            />
            <span>{plan.platform === 'shorts' ? '▶ CONCEPT FIRST' : 'CONCEPT FIRST'}</span>
          </div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 15,
              letterSpacing: 1.5,
              color: C.mutedLight,
              fontWeight: 700,
            }}
          >
            @conceptfirstwithmohit · {(plan.topic_family || 'SYSTEM DESIGN').replace('_', ' ').toUpperCase()}
          </div>
        </div>

        {/* Full-Width Progress Track */}
        <div
          style={{
            width: '100%',
            height: 4,
            borderRadius: 99,
            background: 'rgba(255, 255, 255, 0.14)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progressPct}%`,
              height: '100%',
              background: C.white,
              boxShadow: '0 0 12px rgba(255,255,255,0.8)',
            }}
          />
        </div>

        {/* Status Pill Badge */}
        <div>
          <span
            style={{
              display: 'inline-block',
              padding: '6px 16px',
              borderRadius: 999,
              background: `${badgeColor}18`,
              border: `1.5px solid ${badgeColor}88`,
              fontFamily: FONT_MONO,
              fontSize: 13,
              fontWeight: 800,
              letterSpacing: 1.5,
              color: badgeColor,
            }}
          >
            {badgeLabel}
          </span>
        </div>
      </div>

      {/* Minimal Subtitles */}
      <BenchmarkCaption beat={beat} frame={frame} fps={fps} />
    </AbsoluteFill>
  );
};

// ==========================================
// Root Universal Reel Exporter
// ==========================================
export const UniversalReel: React.FC<Props> = ({plan}) => {
  let cursor = 0;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..900;1,9..144,400..900&family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;600;700;800;900&display=swap');
      `}</style>

      {/* Ambient background music loop with voice-friendly volume */}
      <Audio src={staticFile('audio/bg_ambient.mp3')} volume={0.08} loop />

      {/* 1-Frame Cover Poster Frame Injection for 100% Automatic YouTube/Instagram Thumbnail */}
      {plan.cover_file ? (
        <Sequence from={0} durationInFrames={1}>
          <Img
            src={staticFile(plan.cover_file)}
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              zIndex: 999,
            }}
          />
        </Sequence>
      ) : null}

      {plan.beats.map((beat, idx) => {
        const from = cursor;
        const duration = Math.max(20, Number(beat.duration_frames || 90));
        cursor += duration;
        const isSummary = beat.id === 'summary' || beat.type === 'summary';
        const isProblem =
          beat.id === 'problem' ||
          beat.type === 'comparison' ||
          beat.id === 'vertical_limits' ||
          (beat.id === 'hook' && isRagTopic(plan.topic));

        return (
          <Sequence key={beat.id} from={from} durationInFrames={duration}>
            <BenchmarkBeatScene beat={beat} plan={plan} beatIndex={idx} totalBeats={plan.beats.length} />
            {beat.audio_file ? <Audio src={staticFile(beat.audio_file)} /> : null}
            {/* Subtle transition whoosh on scene changes */}
            {idx > 0 ? <Audio src={staticFile('audio/sfx_whoosh.wav')} volume={0.22} /> : null}
            {/* Timed accent SFX synced with visual stamps/callouts */}
            {isSummary ? (
              <Sequence from={8} durationInFrames={Math.max(10, duration - 8)}>
                <Audio src={staticFile('audio/sfx_chime.wav')} volume={0.28} />
              </Sequence>
            ) : isProblem ? (
              <Sequence from={18} durationInFrames={Math.max(10, duration - 18)}>
                <Audio src={staticFile('audio/sfx_stamp.wav')} volume={0.25} />
              </Sequence>
            ) : (
              <Sequence from={16} durationInFrames={Math.max(10, duration - 16)}>
                <Audio src={staticFile('audio/sfx_pop.wav')} volume={0.22} />
              </Sequence>
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
