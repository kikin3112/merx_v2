import { useEffect, useRef } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export default function Modal({ open, onClose, title, children, maxWidth = 'max-w-lg' }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/60"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className={`cv-card w-full h-full md:h-auto md:rounded-xl shadow-xl ${maxWidth} md:mx-4 md:max-h-[90vh] flex flex-col`}>
        <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b cv-divider">
          <h2 className="text-lg font-semibold cv-text">{title}</h2>
          <button
            onClick={onClose}
            className="cv-icon-btn p-2 -mr-1"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
        <div className="overflow-y-auto px-4 py-4 md:px-6 flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
