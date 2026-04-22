import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const BG = "#0f0f23";
const ACCENT = "#00d4aa";
const TEXT = "#e6e6e6";
const DIM = "#8888a0";
const RED = "#ff5555";
const GREEN = "#50fa7b";

const SceneTitle: React.FC<{ text: string; frame: number; fps: number }> = ({
  text,
  frame,
  fps,
}) => {
  const opacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [0, 0.5 * fps], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        top: 60,
        left: 0,
        right: 0,
        textAlign: "center",
        fontSize: 48,
        fontWeight: 700,
        color: ACCENT,
        opacity,
        transform: `translateY(${y}px)`,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {text}
    </div>
  );
};

const TerminalBox: React.FC<{
  children: React.ReactNode;
  frame: number;
  fps: number;
  delay?: number;
}> = ({ children, frame, fps, delay = 0 }) => {
  const progress = spring({
    frame: frame - delay,
    fps,
    config: { damping: 200 },
  });
  const scale = interpolate(progress, [0, 1], [0.95, 1]);
  const opacity = progress;

  return (
    <div
      style={{
        background: "#1a1a2e",
        borderRadius: 12,
        border: "1px solid #2a2a4e",
        padding: "30px 40px",
        fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace',
        fontSize: 28,
        color: TEXT,
        transform: `scale(${scale})`,
        opacity,
        boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        maxWidth: 1100,
        margin: "0 auto",
      }}
    >
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <span style={{ width: 16, height: 16, borderRadius: 8, background: RED }} />
        <span style={{ width: 16, height: 16, borderRadius: 8, background: "#f1fa8c" }} />
        <span style={{ width: 16, height: 16, borderRadius: 8, background: GREEN }} />
      </div>
      {children}
    </div>
  );
};

const Cursor: React.FC<{ frame: number }> = ({ frame }) => {
  const blink = Math.floor(frame / 15) % 2 === 0;
  return (
    <span
      style={{
        display: "inline-block",
        width: 3,
        height: 34,
        background: ACCENT,
        marginLeft: 4,
        verticalAlign: "middle",
        opacity: blink ? 1 : 0,
      }}
    />
  );
};

const Typewriter: React.FC<{
  text: string;
  frame: number;
  fps: number;
  startFrame: number;
  speed?: number;
  color?: string;
}> = ({ text, frame, fps, startFrame, speed = 20, color = TEXT }) => {
  const chars = Math.floor(((frame - startFrame) / fps) * speed);
  const visible = text.slice(0, Math.max(0, chars));
  const done = chars >= text.length;

  return (
    <span style={{ color }}>
      {visible}
      {!done && <Cursor frame={frame} />}
    </span>
  );
};

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene timings
  const SCENE1 = 0; // Title
  const SCENE2 = 150; // Problem
  const SCENE3 = 300; // Solution
  const SCENE4 = 600; // Result
  const SCENE5 = 750; // CTA

  return (
    <AbsoluteFill
      style={{
        background: BG,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* SCENE 1: Title */}
      {frame < SCENE2 && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              fontSize: 96,
              fontWeight: 800,
              color: ACCENT,
              transform: `scale(${spring({ frame, fps, config: { damping: 12 } })})`,
              letterSpacing: -2,
            }}
          >
            youtube-to-kimi
          </div>
          <div
            style={{
              marginTop: 30,
              fontSize: 40,
              color: DIM,
              opacity: interpolate(frame, [30, 60], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            Download & split YouTube videos for AI analysis
          </div>
          <div
            style={{
              marginTop: 20,
              fontSize: 24,
              color: "#555577",
              opacity: interpolate(frame, [60, 90], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {"yt-dlp + ffmpeg stream-copy + <100MB chunks"}
          </div>
        </AbsoluteFill>
      )}

      {/* SCENE 2: Problem */}
      {frame >= SCENE2 && frame < SCENE3 && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <SceneTitle text="The Problem" frame={frame - SCENE2} fps={fps} />
          <div
            style={{
              display: "flex",
              gap: 80,
              alignItems: "center",
              marginTop: 80,
            }}
          >
            <div
              style={{
                textAlign: "center",
                opacity: interpolate(frame - SCENE2, [0, 30], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              <div style={{ fontSize: 120 }}>🔗</div>
              <div style={{ fontSize: 32, color: TEXT, marginTop: 20 }}>
                YouTube URL
              </div>
              <div style={{ fontSize: 24, color: RED, marginTop: 10 }}>
                AI cannot access directly
              </div>
            </div>

            <div
              style={{
                fontSize: 80,
                color: RED,
                opacity: interpolate(frame - SCENE2, [30, 60], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              ✕
            </div>

            <div
              style={{
                textAlign: "center",
                opacity: interpolate(frame - SCENE2, [60, 90], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              <div style={{ fontSize: 120 }}>🤖</div>
              <div style={{ fontSize: 32, color: TEXT, marginTop: 20 }}>
                AI Assistant
              </div>
              <div style={{ fontSize: 24, color: RED, marginTop: 10 }}>
                100MB upload limit
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* SCENE 3: Solution - Terminal */}
      {frame >= SCENE3 && frame < SCENE4 && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <SceneTitle text="The Solution" frame={frame - SCENE3} fps={fps} />
          <div style={{ marginTop: 60, width: "100%" }}>
            <TerminalBox frame={frame - SCENE3} fps={fps} delay={15}>
              <div style={{ marginBottom: 16 }}>
                <span style={{ color: GREEN }}>$</span>{" "}
                <Typewriter
                  text="youtube-to-kimi prepare \"https://youtube.com/watch?v=...\""
                  frame={frame}
                  fps={fps}
                  startFrame={SCENE3 + 45}
                  speed={18}
                />
              </div>

              <div
                style={{
                  marginTop: 24,
                  color: DIM,
                  fontSize: 22,
                  lineHeight: 1.6,
                  opacity: interpolate(frame - SCENE3, [120, 150], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }),
                }}
              >
                <div>
                  <span style={{ color: GREEN }}>✓</span> Downloaded: 325.5 MB
                </div>
                <div>
                  <span style={{ color: GREEN }}>✓</span> Split into 6 chunks
                  (~85MB each)
                </div>
                <div>
                  <span style={{ color: GREEN }}>✓</span> Lossless stream-copy —
                  no quality loss
                </div>
              </div>
            </TerminalBox>
          </div>
        </AbsoluteFill>
      )}

      {/* SCENE 4: Result */}
      {frame >= SCENE4 && frame < SCENE5 && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <SceneTitle text="Ready for AI" frame={frame - SCENE4} fps={fps} />
          <div
            style={{
              marginTop: 60,
              display: "grid",
              gridTemplateColumns: "repeat(3, 280px)",
              gap: 30,
              opacity: interpolate(frame - SCENE4, [0, 30], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {[
              { n: "1", name: "part_000.mp4", size: "67.8 MB" },
              { n: "2", name: "part_001.mp4", size: "65.2 MB" },
              { n: "3", name: "part_002.mp4", size: "64.9 MB" },
              { n: "4", name: "part_003.mp4", size: "62.1 MB" },
              { n: "5", name: "part_004.mp4", size: "59.5 MB" },
              { n: "6", name: "part_005.mp4", size: "6.0 MB" },
            ].map((item, i) => (
              <div
                key={item.n}
                style={{
                  background: "#1a1a2e",
                  borderRadius: 12,
                  padding: "24px 28px",
                  border: "1px solid #2a2a4e",
                  transform: `translateY(${interpolate(
                    frame - SCENE4 - i * 5,
                    [0, 20],
                    [30, 0],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                  )}px)`,
                  opacity: interpolate(
                    frame - SCENE4 - i * 5,
                    [0, 20],
                    [0, 1],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                  ),
                }}
              >
                <div
                  style={{
                    fontSize: 18,
                    color: ACCENT,
                    fontWeight: 700,
                    marginBottom: 8,
                  }}
                >
                  #{item.n}
                </div>
                <div
                  style={{
                    fontSize: 20,
                    color: TEXT,
                    fontFamily: "monospace",
                  }}
                >
                  {item.name}
                </div>
                <div style={{ fontSize: 18, color: GREEN, marginTop: 6 }}>
                  {item.size}
                </div>
              </div>
            ))}
          </div>
          <div
            style={{
              marginTop: 50,
              fontSize: 28,
              color: DIM,
              opacity: interpolate(frame - SCENE4, [90, 120], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            Upload chunks to Kimi sequentially → full video analysis
          </div>
        </AbsoluteFill>
      )}

      {/* SCENE 5: CTA */}
      {frame >= SCENE5 && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              fontSize: 72,
              fontWeight: 800,
              color: ACCENT,
              transform: `scale(${spring({
                frame: frame - SCENE5,
                fps,
                config: { damping: 12 },
              })})`,
            }}
          >
            Get Started
          </div>
          <TerminalBox
            frame={frame - SCENE5}
            fps={fps}
            delay={30}
          >
            <div style={{ fontSize: 24, color: DIM, marginBottom: 12 }}>
              Install with uv:
            </div>
            <div style={{ fontSize: 28, color: TEXT }}>
              <span style={{ color: GREEN }}>$</span> uv tool install
              youtube-to-kimi
            </div>
            <div
              style={{
                marginTop: 30,
                fontSize: 24,
                color: DIM,
                borderTop: "1px solid #2a2a4e",
                paddingTop: 20,
              }}
            >
              github.com/UncertaintyDeterminesYou4ndMe/youtube-to-kimi
            </div>
          </TerminalBox>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
