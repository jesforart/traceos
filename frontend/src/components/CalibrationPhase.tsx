import React, { useState, useEffect } from 'react';
import { CalibrationPhase } from '../types/calibration';
import { Stroke } from '../types';

interface CalibrationPhaseProps {
  phase: CalibrationPhase;
  onComplete: () => void;
  onStrokeCaptured: (stroke: Stroke) => void;
  isActive: boolean;
  onStart: () => void;
}

export function CalibrationPhaseComponent({
  phase,
  onComplete,
  onStrokeCaptured,
  isActive,
  onStart
}: CalibrationPhaseProps) {
  const [timeLeft, setTimeLeft] = useState(phase.durationSeconds);
  const [strokeCount, setStrokeCount] = useState(0);

  useEffect(() => {
    if (!isActive) {
      setTimeLeft(phase.durationSeconds);
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 0.1) {
          onComplete();
          return 0;
        }
        return prev - 0.1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isActive, onComplete, phase.durationSeconds]);

  const handleStroke = (stroke: Stroke) => {
    if (isActive) {
      setStrokeCount((prev) => prev + 1);
      onStrokeCaptured(stroke);
    }
  };

  const progress = ((phase.durationSeconds - timeLeft) / phase.durationSeconds) * 100;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: '#333' }}>
          {phase.name}
        </h2>
        <p style={{ fontSize: '1.125rem', color: '#666', maxWidth: '600px' }}>
          {phase.instruction}
        </p>
      </div>

      {!isActive && timeLeft === phase.durationSeconds && (
        <button
          onClick={onStart}
          style={{
            padding: '1rem 2rem',
            fontSize: '1.25rem',
            background: '#0066FF',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            transition: 'transform 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          Start {phase.name} Phase
        </button>
      )}

      {isActive && (
        <>
          <div style={{ width: '100%', marginBottom: '1.5rem' }}>
            <div style={{
              fontSize: '3rem',
              fontWeight: 'bold',
              textAlign: 'center',
              color: '#0066FF',
              marginBottom: '1rem'
            }}>
              {timeLeft.toFixed(1)}s
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: '#e0e0e0',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div
                style={{
                  height: '100%',
                  background: '#0066FF',
                  width: `${progress}%`,
                  transition: 'width 0.1s linear'
                }}
              />
            </div>
          </div>

          <div style={{
            fontSize: '1.125rem',
            color: '#666',
            marginBottom: '1.5rem'
          }}>
            Strokes captured: {strokeCount}
          </div>

          <div style={{
            width: '100%',
            minHeight: '400px',
            background: 'white',
            border: '2px solid #0066FF',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <p style={{ fontSize: '1.5rem', color: '#ccc' }}>
              Draw now!
            </p>
          </div>
        </>
      )}

      {!isActive && timeLeft === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          background: '#f0f9ff',
          borderRadius: '8px'
        }}>
          <h3 style={{ color: '#00AA66', fontSize: '2rem', marginBottom: '0.5rem' }}>
            Phase Complete
          </h3>
          <p>Captured {strokeCount} strokes</p>
        </div>
      )}
    </div>
  );
}
