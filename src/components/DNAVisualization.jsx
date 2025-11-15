import React from 'react';
import { motion } from 'framer-motion';

const DNAVisualization = ({ position }) => {
  const getPositionStyles = () => {
    switch (position) {
      case 'center':
        return {
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          scale: 1,
        };
      case 'hero':
        return {
          top: '20%',
          right: '10%',
          transform: 'none',
          scale: 0.6,
        };
      default:
        return {
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          scale: 1,
        };
    }
  };

  return (
    <motion.div
      className="absolute w-64 h-64 pointer-events-none"
      initial={getPositionStyles()}
      animate={getPositionStyles()}
      transition={{ duration: 1, ease: "easeInOut" }}
    >
      {/* DNA Helix Visualization */}
      <motion.div
        className="w-full h-full relative"
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      >
        {/* DNA Strands */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-primary-500 rounded-full"
            style={{
              left: `${50 + 30 * Math.cos((i * Math.PI) / 4)}%`,
              top: `${50 + 30 * Math.sin((i * Math.PI) / 4)}%`,
            }}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
        
        {/* Center glow */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-primary-500 rounded-full opacity-20 animate-pulse-slow" />
      </motion.div>
    </motion.div>
  );
};

export default DNAVisualization;