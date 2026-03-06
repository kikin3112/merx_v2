'use client';

import { useState, useEffect } from 'react';

const PHRASES = ['en orden.', 'bajo control.', 'sin caos.'];
const TYPE_SPEED = 75;
const DELETE_SPEED = 45;
const PAUSE_AFTER_TYPE = 2200;
const PAUSE_AFTER_DELETE = 350;

export function TypewriterText() {
  const [displayed, setDisplayed] = useState('');
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const phrase = PHRASES[phraseIdx];

    if (!isDeleting && displayed === phrase) {
      const t = setTimeout(() => setIsDeleting(true), PAUSE_AFTER_TYPE);
      return () => clearTimeout(t);
    }

    if (isDeleting && displayed === '') {
      const t = setTimeout(() => {
        setPhraseIdx((i) => (i + 1) % PHRASES.length);
        setIsDeleting(false);
      }, PAUSE_AFTER_DELETE);
      return () => clearTimeout(t);
    }

    const speed = isDeleting ? DELETE_SPEED : TYPE_SPEED;
    const t = setTimeout(() => {
      setDisplayed(isDeleting
        ? displayed.slice(0, -1)
        : phrase.slice(0, displayed.length + 1)
      );
    }, speed);

    return () => clearTimeout(t);
  }, [displayed, phraseIdx, isDeleting]);

  return (
    <span
      style={{
        display: 'block',
        minHeight: '1.1em',
        color: 'var(--primary)',
        whiteSpace: 'nowrap',
      }}
    >
      {displayed}
      <span
        aria-hidden="true"
        style={{
          display: 'inline-block',
          width: '3px',
          height: '0.8em',
          background: 'var(--primary)',
          marginLeft: '3px',
          verticalAlign: 'middle',
          borderRadius: '1px',
          animation: 'cursor-blink 0.7s step-end infinite',
        }}
      />
    </span>
  );
}
