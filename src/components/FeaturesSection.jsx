import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Bot, Stethoscope } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'Predictive Healthcare',
    description: 'Advanced AI algorithms analyze symptoms and medical history to predict potential health issues before they become critical.',
    color: 'text-purple-500',
    bgColor: 'bg-purple-50',
  },
  {
    icon: Bot,
    title: 'AI-Driven Support',
    description: 'Intelligent chatbot provides personalized health guidance, medication reminders, and instant medical consultations.',
    color: 'text-primary-500',
    bgColor: 'bg-primary-50',
  },
  {
    icon: Stethoscope,
    title: 'Efficient Triage',
    description: 'Smart triage system prioritizes cases based on urgency, ensuring critical patients receive immediate attention.',
    color: 'text-success',
    bgColor: 'bg-green-50',
  },
];

const FeaturesSection = () => {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Discover the Power of{' '}
            <span className="text-primary-500">IntelliCare</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Revolutionary healthcare technology that puts your wellbeing first
          </p>
        </motion.div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="group p-8 rounded-2xl border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:shadow-xl"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
              whileHover={{ scale: 1.05 }}
              viewport={{ once: true }}
            >
              <motion.div
                className={`w-16 h-16 ${feature.bgColor} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}
              >
                <feature.icon className={`w-8 h-8 ${feature.color}`} />
              </motion.div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                {feature.title}
              </h3>
              
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
              
              <motion.div
                className="mt-6 flex items-center text-primary-500 font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                whileHover={{ x: 5 }}
              >
                Learn more →
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;