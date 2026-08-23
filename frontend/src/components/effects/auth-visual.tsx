"use client";

import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
} from "framer-motion";
import {
  useEffect,
  useRef,
  type MouseEvent,
} from "react";

export function AuthVisual() {
  const containerRef = useRef<HTMLDivElement>(null);

  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);

  const smoothX = useSpring(pointerX, {
    stiffness: 62,
    damping: 18,
    mass: 0.9,
  });

  const smoothY = useSpring(pointerY, {
    stiffness: 62,
    damping: 18,
    mass: 0.9,
  });

  const rotateY = useTransform(
    smoothX,
    [-1, 1],
    [-13, 13]
  );

  const rotateX = useTransform(
    smoothY,
    [-1, 1],
    [10, -10]
  );

  const translateX = useTransform(
    smoothX,
    [-1, 1],
    [-16, 16]
  );

  const translateY = useTransform(
    smoothY,
    [-1, 1],
    [-12, 12]
  );

  function handlePointerMove(
    event: MouseEvent<HTMLDivElement>
  ) {
    const bounds =
      containerRef.current?.getBoundingClientRect();

    if (!bounds) {
      return;
    }

    const normalizedX =
      ((event.clientX - bounds.left) /
        bounds.width) *
        2 -
      1;

    const normalizedY =
      ((event.clientY - bounds.top) /
        bounds.height) *
        2 -
      1;

    pointerX.set(normalizedX);
    pointerY.set(normalizedY);
  }

  function handlePointerLeave() {
    pointerX.set(0);
    pointerY.set(0);
  }

  useEffect(() => {
    function handleDeviceOrientation(
      event: DeviceOrientationEvent
    ) {
      if (
        event.gamma === null ||
        event.beta === null
      ) {
        return;
      }

      pointerX.set(
        Math.max(-1, Math.min(1, event.gamma / 35))
      );

      pointerY.set(
        Math.max(
          -1,
          Math.min(1, (event.beta - 45) / 35)
        )
      );
    }

    window.addEventListener(
      "deviceorientation",
      handleDeviceOrientation
    );

    return () => {
      window.removeEventListener(
        "deviceorientation",
        handleDeviceOrientation
      );
    };
  }, [pointerX, pointerY]);

  return (
    <div
      ref={containerRef}
      className="auth-visual"
      aria-hidden="true"
      onMouseMove={handlePointerMove}
      onMouseLeave={handlePointerLeave}
    >
      <div className="auth-visual__grid" />
      <div className="auth-visual__veil" />
      <div className="auth-visual__scanline" />
      <div className="auth-visual__noise" />

      <motion.div
        className="intelligence-core-scene"
        style={{
          rotateX,
          rotateY,
          x: translateX,
          y: translateY,
        }}
      >
        <motion.div
          className="intelligence-core-glow intelligence-core-glow--violet"
          animate={{
            x: [-24, 32, -24],
            y: [16, -25, 16],
            scale: [0.92, 1.08, 0.92],
            opacity: [0.32, 0.58, 0.32],
          }}
          transition={{
            duration: 8.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="intelligence-core-glow intelligence-core-glow--rose"
          animate={{
            x: [30, -22, 30],
            y: [-20, 24, -20],
            scale: [1.05, 0.88, 1.05],
            opacity: [0.16, 0.34, 0.16],
          }}
          transition={{
            duration: 10.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="intelligence-orbit intelligence-orbit--outer"
          animate={{
            rotate: 360,
            rotateX: [65, 72, 65],
          }}
          transition={{
            rotate: {
              duration: 28,
              repeat: Infinity,
              ease: "linear",
            },
            rotateX: {
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
            },
          }}
        >
          <span className="intelligence-orbit__node intelligence-orbit__node--one" />
          <span className="intelligence-orbit__node intelligence-orbit__node--two" />
        </motion.div>

        <motion.div
          className="intelligence-orbit intelligence-orbit--middle"
          animate={{
            rotate: -360,
            rotateY: [66, 76, 66],
          }}
          transition={{
            rotate: {
              duration: 19,
              repeat: Infinity,
              ease: "linear",
            },
            rotateY: {
              duration: 7,
              repeat: Infinity,
              ease: "easeInOut",
            },
          }}
        >
          <span className="intelligence-orbit__node intelligence-orbit__node--three" />
        </motion.div>

        <motion.div
          className="intelligence-orbit intelligence-orbit--inner"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "linear",
          }}
        />

        <motion.div
          className="intelligence-shell"
          animate={{
            y: [-8, 11, -8],
            rotateZ: [-1.4, 2.2, -1.4],
            scale: [0.985, 1.018, 0.985],
            borderRadius: [
              "45% 55% 50% 50% / 48% 44% 56% 52%",
              "54% 46% 43% 57% / 55% 48% 52% 45%",
              "47% 53% 57% 43% / 44% 55% 45% 56%",
              "45% 55% 50% 50% / 48% 44% 56% 52%",
            ],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <motion.div
            className="intelligence-shell__metal"
            animate={{
              backgroundPosition: [
                "0% 15%",
                "100% 70%",
                "20% 100%",
                "0% 15%",
              ],
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="intelligence-shell__refraction"
            animate={{
              rotate: [0, 360],
              scale: [0.9, 1.08, 0.9],
            }}
            transition={{
              rotate: {
                duration: 24,
                repeat: Infinity,
                ease: "linear",
              },
              scale: {
                duration: 7,
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
          />

          <motion.div
            className="intelligence-shell__energy"
            animate={{
              rotate: [0, -360],
              x: [-10, 14, -10],
              y: [8, -12, 8],
            }}
            transition={{
              rotate: {
                duration: 26,
                repeat: Infinity,
                ease: "linear",
              },
              x: {
                duration: 7,
                repeat: Infinity,
                ease: "easeInOut",
              },
              y: {
                duration: 8,
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
          />

          <div className="intelligence-shell__highlight" />
          <div className="intelligence-shell__shadow" />

          <motion.div
            className="intelligence-core"
            animate={{
              scale: [0.84, 1.08, 0.84],
              opacity: [0.58, 1, 0.58],
            }}
            transition={{
              duration: 3.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <span className="intelligence-core__point" />
          </motion.div>
        </motion.div>

        <motion.div
          className="intelligence-particle intelligence-particle--one"
          animate={{
            x: [-14, 22, -14],
            y: [-12, 28, -12],
            scale: [0.78, 1.08, 0.78],
          }}
          transition={{
            duration: 6.4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="intelligence-particle intelligence-particle--two"
          animate={{
            x: [15, -24, 15],
            y: [24, -18, 24],
            scale: [1.05, 0.76, 1.05],
          }}
          transition={{
            duration: 7.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="intelligence-particle intelligence-particle--three"
          animate={{
            x: [-10, 24, -10],
            y: [18, -15, 18],
            opacity: [0.26, 0.85, 0.26],
          }}
          transition={{
            duration: 6.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>

      <div className="auth-visual__depth-line auth-visual__depth-line--one" />
      <div className="auth-visual__depth-line auth-visual__depth-line--two" />
      <div className="auth-visual__depth-line auth-visual__depth-line--three" />
    </div>
  );
}