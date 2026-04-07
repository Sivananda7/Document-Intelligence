import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';
import UploadView from './components/UploadView';
import ReviewView from './components/ReviewView';
import './index.css';

function App() {
  const [documentQueue, setDocumentQueue] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleUploadSuccess = (uploadedDocs) => {
    setDocumentQueue(uploadedDocs);
    setCurrentIndex(0);
  };

  const handleNextDocument = () => {
    if (currentIndex < documentQueue.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      setDocumentQueue([]);
      setCurrentIndex(0);
    }
  };

  const currentDoc = documentQueue[currentIndex];

  return (
    <div className="app-container">
      {/* Universal Header */}
      <header className="header">
        <h1 style={{ display: 'flex', alignItems: 'center', margin: 0, fontWeight: 600 }}>
          <BrainCircuit size={28} color="var(--primary-color)" style={{ marginRight: '10px' }} />
          Smart Document Intelligent
        </h1>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Vision & LLM Processing</span>
          <div style={{ padding: '0.5rem 1rem', background: 'var(--primary-color)', borderRadius: '20px', color: '#FFFFFF', fontWeight: 500, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem', boxShadow: '0 2px 10px rgba(0,0,0,0.08)' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#34c759', boxShadow: '0 0 8px #34c759' }}></div>
            Gemini 3 Flash Active
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          {documentQueue.length === 0 ? (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              transition={{ duration: 0.4 }}
              style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
            >
              <UploadView onUploadSuccess={handleUploadSuccess} />
            </motion.div>
          ) : (
            <motion.div
              key={`review-${currentIndex}`}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.4 }}
              style={{ flex: 1 }}
            >
              <ReviewView
                fileObj={currentDoc}
                onNext={handleNextDocument}
                queueInfo={{ current: currentIndex + 1, total: documentQueue.length }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
