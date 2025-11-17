import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Download, Printer, Share2, Calendar, User, Activity, AlertTriangle, Stethoscope } from "lucide-react";

export default function ReportPage() {
  const [reportData, setReportData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Retrieve report from sessionStorage
    const storedReport = sessionStorage.getItem('medicalReport');
    if (storedReport) {
      setReportData(JSON.parse(storedReport));
    } else {
      // No report available, redirect back
      navigate('/');
    }
  }, [navigate]);

  const downloadReport = () => {
    if (!reportData) return;
    const blob = new Blob([reportData.report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical-report-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    window.print();
  };

  const shareReport = async () => {
    if (navigator.share && reportData) {
      try {
        await navigator.share({
          title: 'Medical Report',
          text: 'Medical Assessment Report',
          url: window.location.href
        });
      } catch (err) {
        console.log('Share failed:', err);
      }
    }
  };

  if (!reportData) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a2e] to-[#16213e] text-gray-100">
        <div className="text-center">
          <div className="animate-spin w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-400">Loading report...</p>
        </div>
      </div>
    );
  }

  const { diagnosisData, timestamp, patientData } = reportData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a2e] to-[#16213e] text-gray-100">
      {/* Header */}
      <div className="sticky top-0 z-10 backdrop-blur-xl bg-black/40 border-b border-white/10 shadow-lg print:hidden">
        <div className="px-6 py-4 flex justify-between items-center">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 hover:scale-105 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium">Back to Home</span>
          </button>

          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Medical Assessment Report
          </h1>

          <div className="flex items-center gap-3">
            <button
              onClick={shareReport}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 hover:scale-105"
              title="Share Report"
            >
              <Share2 className="w-5 h-5" />
            </button>
            <button
              onClick={printReport}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 hover:scale-105"
              title="Print Report"
            >
              <Printer className="w-5 h-5" />
            </button>
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 border border-white/10 transition-all duration-300 hover:scale-105 shadow-lg shadow-green-500/30"
            >
              <Download className="w-4 h-4" />
              <span className="text-sm font-medium">Download</span>
            </button>
          </div>
        </div>
      </div>

      {/* Report Content */}
      <div className="px-6 py-8">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Report Header */}
          <div className="glassmorphism-card p-8 rounded-2xl border-l-4 border-cyan-500">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-3xl font-bold text-white mb-2">Patient Medical Report</h2>
                <p className="text-gray-400">AI-Assisted Preliminary Assessment</p>
              </div>
              <div className="text-right text-sm text-gray-400">
                <div className="flex items-center gap-2 justify-end mb-1">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(timestamp).toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}</span>
                </div>
                <div>{new Date(timestamp).toLocaleTimeString('en-US')}</div>
              </div>
            </div>

            {/* Patient Info */}
            {patientData && (
              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/10">
                {patientData.age && (
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                      <User className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <div className="text-xs text-gray-400">Age</div>
                      <div className="font-semibold">{patientData.age} years</div>
                    </div>
                  </div>
                )}
                {patientData.gender && (
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                      <User className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <div className="text-xs text-gray-400">Gender</div>
                      <div className="font-semibold capitalize">{patientData.gender}</div>
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-400">Report ID</div>
                    <div className="font-mono text-xs">{reportData.report?.match(/MED-\d+-\d+/)?.[0] || 'N/A'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Triage Assessment */}
          {diagnosisData?.triage_level && (
            <div className={`glassmorphism-card p-6 rounded-2xl border-l-4 animate-slide-in ${
              diagnosisData.triage_level <= 2 ? 'border-red-500' :
              diagnosisData.triage_level === 3 ? 'border-yellow-500' :
              'border-green-500'
            }`}>
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
                  diagnosisData.triage_level <= 2 ? 'bg-red-500/20' :
                  diagnosisData.triage_level === 3 ? 'bg-yellow-500/20' :
                  'bg-green-500/20'
                }`}>
                  <AlertTriangle className={`w-8 h-8 ${
                    diagnosisData.triage_level <= 2 ? 'text-red-400' :
                    diagnosisData.triage_level === 3 ? 'text-yellow-400' :
                    'text-green-400'
                  }`} />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">Triage Assessment</h3>
                  <div className={`text-2xl font-bold ${
                    diagnosisData.triage_level <= 2 ? 'text-red-400' :
                    diagnosisData.triage_level === 3 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    Level {diagnosisData.triage_level}/5 - {diagnosisData.triage_level_name}
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white/5 rounded-xl">
                <div className="text-sm font-semibold text-gray-300 mb-2">Recommended Action:</div>
                <div className="text-base text-white">{diagnosisData.recommendation}</div>
              </div>
            </div>
          )}

          {/* Differential Diagnoses */}
          {diagnosisData?.diagnoses && diagnosisData.diagnoses.length > 0 && (
            <div className="glassmorphism-card p-6 rounded-2xl border-l-4 border-blue-500 animate-slide-in" style={{animationDelay: '0.1s'}}>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Stethoscope className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold text-white">Differential Diagnoses</h3>
              </div>

              <div className="space-y-4">
                {diagnosisData.diagnoses.map((diag, idx) => (
                  <div key={idx} className="p-5 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-all">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                        <span className="text-lg font-bold text-cyan-400">{idx + 1}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-lg font-semibold text-white">{diag.disease}</h4>
                          {diag.probability && (
                            <div className="flex items-center gap-2">
                              <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full"
                                  style={{ width: `${diag.probability * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-bold text-cyan-400 min-w-[50px]">
                                {(diag.probability * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>
                        {diag.confidence && (
                          <div className="mb-2">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                              diag.confidence === 'high' ? 'bg-green-500/20 text-green-400' :
                              diag.confidence === 'moderate' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {diag.confidence} confidence
                            </span>
                          </div>
                        )}
                        {diag.explanation && (
                          <p className="text-sm text-gray-400 leading-relaxed">{diag.explanation}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Department Recommendation */}
          {diagnosisData?.department && (
            <div className="glassmorphism-card p-6 rounded-2xl border-l-4 border-purple-500 animate-slide-in" style={{animationDelay: '0.2s'}}>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-purple-500/20 flex items-center justify-center">
                  <span className="text-3xl">🏥</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white mb-1">Recommended Department</h3>
                  <div className="text-2xl font-bold text-purple-400">{diagnosisData.department}</div>
                </div>
              </div>
            </div>
          )}

          {/* Symptoms Summary */}
          {patientData?.symptoms && patientData.symptoms.length > 0 && (
            <div className="glassmorphism-card p-6 rounded-2xl animate-slide-in" style={{animationDelay: '0.3s'}}>
              <h3 className="text-lg font-bold text-white mb-4">Reported Symptoms</h3>
              <div className="flex flex-wrap gap-2">
                {patientData.symptoms.map((symptom, idx) => (
                  <span key={idx} className="px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-sm">
                    {symptom}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Important Disclaimer */}
          <div className="glassmorphism-card p-6 rounded-2xl border-2 border-red-500/50 animate-slide-in" style={{animationDelay: '0.4s'}}>
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-bold text-red-400 mb-2">Important Medical Disclaimer</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                  This is an AI-assisted preliminary assessment and does NOT constitute professional medical advice, 
                  diagnosis, or treatment. This assessment is based on limited information provided in a text-based 
                  conversation and should not replace an in-person evaluation by a qualified healthcare professional. 
                  Please seek immediate medical attention if you are experiencing a medical emergency. For accurate 
                  diagnosis and treatment, please consult with a licensed physician or healthcare provider.
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center text-sm text-gray-500 py-8">
            <p>Generated by IntelliCare</p>
          </div>
        </div>
      </div>

      {/* Print Styles */}
      <style jsx>{`
        @media print {
          .print\:hidden {
            display: none !important;
          }
          
          body {
            background: white !important;
          }
          
          .glassmorphism-card {
            background: white !important;
            border: 1px solid #ddd !important;
            box-shadow: none !important;
          }
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-slide-in {
          animation: slideIn 0.5s ease-out;
        }

        .glassmorphism-card {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
      `}</style>
    </div>
  );
}