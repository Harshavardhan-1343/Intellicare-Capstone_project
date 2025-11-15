// import React, { useState, useEffect } from 'react';
// import { motion, AnimatePresence } from 'framer-motion';
// import SplashScreen from './components/SplashScreen';
// import HeroSection from './components/HeroSection';
// import FeaturesSection from './components/FeaturesSection';
// import TriageSection from './components/TriageSection';
// import Footer from './components/Footer';

// function App() {
//   const [showSplash, setShowSplash] = useState(true);
//   const [dnaPosition, setDnaPosition] = useState('center');

//   useEffect(() => {
//     const timer = setTimeout(() => {
//       setDnaPosition('hero');
//       setTimeout(() => {
//         setShowSplash(false);
//       }, 1000);
//     }, 3000);

//     return () => clearTimeout(timer);
//   }, []);

//   return (
//     <div className="font-inter overflow-x-hidden">
//       <AnimatePresence>
//         {showSplash && (
//           <SplashScreen dnaPosition={dnaPosition} />
//         )}
//       </AnimatePresence>
      
//       {!showSplash && (
//         <motion.div
//           initial={{ opacity: 0 }}
//           animate={{ opacity: 1 }}
//           transition={{ duration: 0.5 }}
//         >
//           <HeroSection />
//           <FeaturesSection />
//           <TriageSection />
//           <Footer />
//         </motion.div>
//       )}
//     </div>
//   );
// }

// export default App;

// src/App.jsx
import React, { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

import SplashScreen from "./components/SplashScreen";
import HeroSection from "./components/HeroSection";
import FeaturesSection from "./components/FeaturesSection";
import TriageSection from "./components/TriageSection";
import Footer from "./components/Footer";
import ChatbotPage from "./components/ChatbotPage";

function HomeContent() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <TriageSection />
      <Footer />
    </>
  );
}

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [dnaPosition, setDnaPosition] = useState("center");

  useEffect(() => {
    const timer = setTimeout(() => {
      setDnaPosition("hero");
      setTimeout(() => {
        setShowSplash(false);
      }, 1000);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="font-inter overflow-x-hidden">
      <AnimatePresence>
        {showSplash && <SplashScreen dnaPosition={dnaPosition} />}
      </AnimatePresence>

      {!showSplash && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Routes>
            <Route path="/" element={<HomeContent />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
          </Routes>
        </motion.div>
      )}
    </div>
  );
}

export default App;
