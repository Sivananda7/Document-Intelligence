import { useState, useEffect, useMemo, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, ArrowLeft, CheckCircle, Percent, ShieldCheck } from 'lucide-react';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Recursive Form Renderer for arbitrary JSON
const NestedFormFields = ({ data, onChange, path = [] }) => {
    if (typeof data !== 'object' || data === null) {
        return (
            <input
                type={typeof data === 'number' ? 'number' : 'text'}
                value={data}
                onChange={(e) => onChange(path, e.target.value)}
                className="glass-input"
                style={{ width: '100%', padding: '0.65rem 1rem' }}
            />
        );
    }

    return (
        <div style={{ paddingLeft: path.length > 0 ? '1rem' : '0' }}>
            {Object.entries(data).map(([key, val]) => (
                <div key={key} style={{ marginBottom: typeof val === 'object' ? '1rem' : '0.85rem' }}>
                    <label style={{
                        display: 'block',
                        fontSize: '0.85rem',
                        fontWeight: 500,
                        color: 'var(--text-secondary)',
                        marginBottom: '0.3rem',
                        textTransform: 'capitalize',
                        fontFamily: 'Inter'
                    }}>
                        {key.replace(/_/g, ' ')}
                    </label>
                    {typeof val === 'object' && val !== null ? (
                        <div style={{ marginLeft: '0.5rem', paddingLeft: '1rem', borderLeft: '2px solid rgba(0, 0, 0, 0.05)' }}>
                            <NestedFormFields data={val} onChange={onChange} path={[...path, key]} />
                        </div>
                    ) : (
                        <NestedFormFields data={val} onChange={onChange} path={[...path, key]} />
                    )}
                </div>
            ))}
        </div>
    );
};

export default function ReviewView({ fileObj, onNext, queueInfo }) {
    const [documentId, setDocumentId] = useState(null);
    const [docData, setDocData] = useState(null);
    const [editedData, setEditedData] = useState(null);
    const [status, setStatus] = useState('UPLOADING');
    const [isConfirming, setIsConfirming] = useState(false);
    const [isCompleted, setIsCompleted] = useState(false);
    const uploadedFileRef = useRef(null);

    useEffect(() => {
        // Reset state for new files but don't blindly reset upload tracker to prevent strict-mode double uploads
        setDocumentId(null);
        setDocData(null);
        setEditedData(null);
        setStatus('UPLOADING');
        setIsCompleted(false);
    }, [fileObj]);

    useEffect(() => {
        const uploadFile = async () => {
            // Prevent double upload of the exact same file object
            if (uploadedFileRef.current === fileObj.file) return;
            uploadedFileRef.current = fileObj.file;

            try {
                const formData = new FormData();
                formData.append('file', fileObj.file);

                const response = await axios.post(`${BASE_URL}/documents/upload`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });

                setDocumentId(response.data.document_id);
                setStatus('PROCESSING');
            } catch (err) {
                console.error("Upload error:", err);
                setStatus('ERROR');
            }
        };

        if (fileObj && fileObj.file) {
            uploadFile();
        }
    }, [fileObj]);

    const dataStats = useMemo(() => {
        if (!editedData || Object.keys(editedData).length === 0) return { pctText: 'N/A', filledText: '0 / 0 Fields', confidence: 'N/A', color: 'var(--text-secondary)' };
        let total = 0;
        let filled = 0;

        const countFields = (obj) => {
            Object.values(obj).forEach(val => {
                if (val !== null && typeof val === 'object') {
                    countFields(val);
                } else {
                    total++;
                    if (val !== null && val !== undefined && String(val).trim() !== '') {
                        filled++;
                    }
                }
            });
        };

        countFields(editedData);
        const pct = total > 0 ? (filled / total) * 100 : 0;
        const confidence = pct >= 80 ? 'High' : pct >= 50 ? 'Medium' : 'Low';
        const color = pct >= 80 ? 'var(--success-color)' : pct >= 50 ? '#eab308' : 'var(--error-color)';
        return {
            pctText: pct.toFixed(0) + '%',
            filledText: `${filled} / ${total} Fields`,
            confidence,
            color
        };
    }, [editedData]);

    useEffect(() => {
        let intervalId;

        const pollStatus = async () => {
            try {
                const res = await axios.get(`${BASE_URL}/documents/${documentId}`);
                const { status, classification, extracted_data } = res.data;

                setStatus(status);
                if (status !== 'PROCESSING') {
                    setDocData(res.data);
                    setEditedData(extracted_data || {});
                    clearInterval(intervalId);
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        };

        if (status === 'PROCESSING' && documentId) {
            pollStatus(); // Initial fetch
            intervalId = setInterval(pollStatus, 3000);
        }

        return () => clearInterval(intervalId);
    }, [documentId, status]);

    // Deep update nested arbitrary JSON
    const handleFieldChange = (path, value) => {
        setEditedData((prev) => {
            const copy = JSON.parse(JSON.stringify(prev));
            let current = copy;
            for (let i = 0; i < path.length - 1; i++) {
                current = current[path[i]];
            }
            current[path[path.length - 1]] = value;
            return copy;
        });
    };

    const handleDecision = async (decisionStatus) => {
        setIsConfirming(decisionStatus);
        try {
            await axios.put(`${BASE_URL}/documents/${documentId}/confirm`, {
                extracted_data: editedData,
                classification: docData.classification,
                status: decisionStatus
            });
            setIsCompleted(decisionStatus);
        } catch (err) {
            console.error(err);
            alert(`Failed to ${decisionStatus.toLowerCase()} document data.`);
        } finally {
            setIsConfirming(false);
        }
    };


    if (isCompleted) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel"
                style={{ maxWidth: '600px', margin: '10vh auto', padding: '4rem', textAlign: 'center' }}
            >
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring' }} style={{ marginBottom: '2rem' }}>
                    <CheckCircle size={80} color="var(--success-color)" style={{ margin: '0 auto', filter: 'drop-shadow(0 0 15px rgba(34, 197, 94, 0.4))' }} />
                </motion.div>
                <button className="btn btn-primary" onClick={onNext} style={{ width: '100%' }}>
                    {queueInfo && queueInfo.current < queueInfo.total ? 'Process Next Document' : 'Finish & Upload More'}
                </button>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="dual-pane"
        >

            {/* Left side: Original Image Preview */}
            <div className="pane glass-panel">
                <div className="pane-header">
                    <button className="btn" onClick={onNext} style={{ padding: '0.4rem', background: 'transparent', marginRight: '1rem', border: '1px solid var(--glass-border)' }}>
                        <ArrowLeft size={20} color="var(--text-primary)" />
                    </button>
                    <h2>Document Source {queueInfo && <span style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 400 }}>({queueInfo.current} of {queueInfo.total})</span>}</h2>
                </div>
                <div className="document-preview">
                    {fileObj?.preview ? (
                        <img src={fileObj.preview} alt="Uploaded Document" className="document-image" />
                    ) : (
                        <div style={{ color: 'var(--text-secondary)' }}>No source preview available</div>
                    )}
                </div>
            </div>

            {/* Right side: JSON Form Editor via AI */}
            <div className="pane glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="pane-header" style={{ justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        <h2>AI Data Validation</h2>
                        <span className={`status-badge ${status.toLowerCase()}`}>
                            {status === 'UPLOADING' ? (
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Loader2 size={12} className="spinner" /> Uploading</span>
                            ) : status === 'PROCESSING' ? (
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Loader2 size={12} className="spinner" /> Analyzing</span>
                            ) : status === 'ERROR' ? (
                                <span>Error</span>
                            ) : (
                                docData?.classification || 'Unknown'
                            )}
                        </span>
                    </div>
                </div>

                {status === 'UPLOADING' ? (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                        <Loader2 size={50} className="spinner" style={{ marginBottom: '1.5rem', color: 'var(--primary-color)' }} />
                        <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>Uploading secure document...</h3>
                        <p style={{ color: 'var(--text-secondary)', maxWidth: '300px' }}>Sending file to extraction engine.</p>
                    </div>
                ) : status === 'PROCESSING' ? (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                        <Loader2 size={50} className="spinner" style={{ marginBottom: '1.5rem', color: 'var(--primary-color)' }} />
                        <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>Gemini 3 Flash is thinking...</h3>
                        <p style={{ color: 'var(--text-secondary)', maxWidth: '300px' }}>Running Computer Vision and LLM Pipeline for structural extraction.</p>
                    </div>
                ) : (
                    <>
                        <div className="json-editor">
                            <>
                                {editedData && Object.keys(editedData).length > 0 && (
                                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', padding: '1.2rem', background: 'rgba(0,0,0,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontFamily: 'Inter' }}>
                                                <Percent size={14} /> Extraction Completeness
                                            </div>
                                            <div style={{ fontSize: '1.4rem', fontWeight: 600, color: 'var(--primary-color)' }}>
                                                {dataStats.pctText}
                                            </div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                                                {dataStats.filledText} Filled
                                            </div>
                                        </div>
                                        <div style={{ width: '1px', background: 'var(--glass-border)', margin: '0 0.5rem' }}></div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontFamily: 'Inter' }}>
                                                <ShieldCheck size={14} /> AI Confidence Estimate
                                            </div>
                                            <div style={{ fontSize: '1.4rem', fontWeight: 600, textTransform: 'capitalize', color: dataStats.color }}>
                                                {dataStats.confidence}
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                                <AnimatePresence>
                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                        {editedData && Object.keys(editedData).length > 0 ? (
                                            <NestedFormFields data={editedData} onChange={handleFieldChange} />
                                        ) : (
                                            <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '3rem' }}>
                                                No structured data extracted from this document.
                                            </div>
                                        )}
                                    </motion.div>
                                </AnimatePresence>
                            </>
                        </div>

                        <div className="actions-footer">
                            <button
                                className="btn btn-danger"
                                onClick={() => handleDecision('REJECTED')}
                                disabled={isConfirming}
                                style={{ flex: 1, padding: '1rem' }}
                            >
                                {isConfirming === 'REJECTED' ? 'Rejecting...' : 'Reject Processing'}
                            </button>
                            <button
                                className="btn btn-success"
                                onClick={() => handleDecision('ACCEPTED')}
                                disabled={isConfirming}
                                style={{ flex: 2, padding: '1rem' }}
                            >
                                {isConfirming === 'ACCEPTED' ? 'Verifying...' : 'Accept Assessed Data'}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </motion.div>
    );
}
