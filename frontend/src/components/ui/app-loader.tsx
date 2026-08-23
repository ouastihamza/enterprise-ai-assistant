"use client";

import { motion } from "framer-motion";

export function AppLoader() {
  return (
    <main className="app-loader" aria-label="Loading AI Agency">
      <div className="app-loader__visual">
        <motion.div
          className="app-loader__orbit app-loader__orbit--one"
          animate={{ rotate: 360 }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "linear",
          }}
        />

        <motion.div
          className="app-loader__orbit app-loader__orbit--two"
          animate={{ rotate: -360 }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
          }}
        />

        <motion.div
          className="app-loader__core"
          animate={{
            scale: [0.9, 1.08, 0.9],
            opacity: [0.72, 1, 0.72],
          }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <p>Preparing your workspace</p>
    </main>
  );
}
