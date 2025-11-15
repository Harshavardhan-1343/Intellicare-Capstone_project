import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Activity } from 'lucide-react';
import { useNavigate } from "react-router-dom";

const HeroSection = () => {
  const navigate = useNavigate();
  return (
    <section className="min-h-screen bg-gradient-to-br from-primary-50 to-white flex items-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <motion.div
            className="space-y-8"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.h1
              className="text-5xl lg:text-7xl font-bold text-gray-900 leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Smart Healthcare,{' '}
              <span className="text-primary-500">Smarter You</span>
            </motion.h1>
            
            <motion.p
              className="text-xl lg:text-2xl text-gray-600 leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              AI-powered chatbot to predict diseases, assess urgency, and guide your care with precision and compassion.
            </motion.p>
            
            <motion.div
              className="flex flex-col sm:flex-row gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              <motion.button
                className="bg-primary-500 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 hover:bg-primary-600 transition-colors shadow-lg"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate("/chatbot")}
              >
                Start Symptom Check
                <ArrowRight className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                className="border-2 border-primary-500 text-primary-500 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-primary-500 hover:text-white transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Learn More
              </motion.button>
            </motion.div>
            
            <motion.div
              className="flex items-center gap-6 pt-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-success" />
                <span className="text-gray-600">24/7 Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
                <span className="text-gray-600">AI-Powered</span>
              </div>
            </motion.div>
          </motion.div>
          
          {/* Right Content - DNA Animation */}
          <motion.div
            className="relative flex justify-center lg:justify-end"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <div className="relative w-96 h-96">
              {/* Main DNA Structure */}
              <motion.div
                className="absolute inset-0 rounded-full border-4 border-primary-200"
                animate={{ rotate: 360 }}
                transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              />
              
              {/* DNA Points */}
              {[...Array(12)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-4 h-4 bg-primary-500 rounded-full"
                  style={{
                    left: `${50 + 40 * Math.cos((i * Math.PI) / 6)}%`,
                    top: `${50 + 40 * Math.sin((i * Math.PI) / 6)}%`,
                  }}
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [0.7, 1, 0.7],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    delay: i * 0.25,
                  }}
                />
              ))}
              
              {/* Center Glow */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-primary-500 rounded-full opacity-10 animate-pulse-slow" />
              
              {/* Floating Elements */}
              <motion.div
                className="absolute -top-4 -right-4 w-8 h-8 bg-success rounded-full opacity-60"
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 4, repeat: Infinity }}
              />
              <motion.div
                className="absolute -bottom-4 -left-4 w-6 h-6 bg-warning rounded-full opacity-60"
                animate={{ y: [10, -10, 10] }}
                transition={{ duration: 3, repeat: Infinity }}
              />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;