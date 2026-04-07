import { useState } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, FileWarning } from 'lucide-react';
import { motion } from 'framer-motion';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export default function UploadView({ onUploadSuccess }) {
    const [files, setFiles] = useState([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState(null);

    const handleFiles = (selectedFiles) => {
        const fileArray = Array.from(selectedFiles);
        if (fileArray.length > 0) {
            setFiles(prev => [...prev, ...fileArray.map(f => ({
                file: f,
                preview: URL.createObjectURL(f)
            }))]);
            setError(null);
        } else {
            setError('Please select valid files.');
        }
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') setIsDragging(true);
        else setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const submitUpload = () => {
        if (files.length === 0) return;
        setIsUploading(true);
        // We pass the raw files to App.jsx to process one-by-one in the ReviewQueue
        onUploadSuccess(files);
    };

    const removeFile = (indexToRemove, e) => {
        e.stopPropagation();
        setFiles(files.filter((_, index) => index !== indexToRemove));
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel"
            style={{ maxWidth: '800px', margin: '0 auto', width: '100%', padding: '3rem' }}
        >
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 className="text-gradient" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
                    Intelligent Document Ingestion
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                    Upload identification cards, passports, utility bills, or legal documents.
                    Our AI pipeline will instantly classify and extract the crucial data.
                </p>
            </div>

            <div
                className={`upload-dropzone ${isDragging ? 'drag-active' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-upload').click()}
            >
                <UploadCloud className="upload-icon" />
                <h3>Drag & Drop to Upload</h3>
                <p>or click here to browse files (Any Format)</p>
                <input
                    id="file-upload"
                    type="file"
                    accept="image/jpeg, image/png, image/webp, application/pdf"
                    style={{ display: 'none' }}
                    multiple
                    onChange={(e) => handleFiles(e.target.files)}
                />
            </div>

            {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: '1.5rem', color: 'var(--error-color)', display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
                    <FileWarning size={20} />
                    {error}
                </motion.div>
            )}

            {files.length > 0 && !error && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, duration: 0.5 }}
                    style={{ marginTop: '2rem' }}
                >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                        {files.map((f, index) => (
                            <div key={index} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.8rem 1rem', background: 'rgba(0,0,0,0.02)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <CheckCircle size={18} color="var(--success-color)" />
                                    <div>
                                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{f.file.name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{(f.file.size / 1024 / 1024).toFixed(2)} MB</div>
                                    </div>
                                </div>
                                {!isUploading && (
                                    <button onClick={(e) => removeFile(index, e)} style={{ border: 'none', background: 'transparent', color: 'var(--error-color)', cursor: 'pointer', fontSize: '1.2rem', padding: '0 0.5rem' }}>&times;</button>
                                )}
                            </div>
                        ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
                        <button
                            className="btn btn-primary"
                            onClick={submitUpload}
                            disabled={isUploading}
                        >
                            {isUploading ? `Starting Pipeline...` : `Begin Pipeline for ${files.length} Document${files.length > 1 ? 's' : ''}`}
                        </button>
                    </div>
                </motion.div>
            )}
        </motion.div >
    );
}
