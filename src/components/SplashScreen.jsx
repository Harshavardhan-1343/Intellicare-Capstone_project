import React from 'react';
import { motion } from 'framer-motion';
import DNAVisualization from './DNAVisualization';

const SplashScreen = ({ dnaPosition }) => {
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{
        backgroundImage: 'url(/src/assets/dna-background.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-40" />
      
      {/* Content */}
      <div className="relative z-10 text-center text-white">
        <motion.h1
          className="text-6xl md:text-8xl font-bold mb-4"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
        >
          IntelliCare
        </motion.h1>
        
        <motion.p
          className="text-xl md:text-2xl font-light opacity-90"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
        >
          Smart Healthcare, Powered by AI
        </motion.p>

        <motion.div
          className="mt-12"
          initial={{ opacity: 1 }}
          animate={{ opacity: dnaPosition === 'hero' ? 0 : 1 }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-sm opacity-70 animate-pulse">Scroll to begin</p>
        </motion.div>
      </div>

      {/* DNA Animation */}
      <DNAVisualization position={dnaPosition} />
    </motion.div>
  );
};

export default SplashScreen;