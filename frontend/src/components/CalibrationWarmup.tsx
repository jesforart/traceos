import React, { useState } from 'react';
import { CalibrationPhaseComponent } from './CalibrationPhase';
import { CALIBRATION_PHASES, CalibrationSession, CalibrationStroke } from '../types/calibration';
import { Stroke } from '../types';
import { ulid } from '../utils/ulid';

interface CalibrationWarmupProps {
  onComplete: (session: CalibrationSession) => void;
  onCancel?: () => void;
}

export function CalibrationWarmup({ onComplete, onCancel }: CalibrationWarmupProps) {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [session, setSession] = useState<CalibrationSession>({
    id: ulid(),
    strokes: [],
    startedAt: Date.now(),
    currentPhase: 'feather'
  });
  const [isPhaseActive, setIsPhaseActive] = useState(false);

  const currentPhase = CALIBRATION_PHASES[currentPhaseIndex];
  const isComplete = currentPhaseIndex >= CALIBRATION_PHASES.length;

  const handlePhaseStart = () => {
    setIsPhaseActive(true);
  };

  const handlePhaseComplete = () => {
    setIsPhaseActive(false);

    if (currentPhaseIndex < CALIBRATION_PHASES.length - 1) {
      // Move to next phase
      const nextPhase = CALIBRATION_PHASES[currentPhaseIndex + 1];
      setCurrentPhaseIndex(currentPhaseIndex + 1);
      setSession(prev => ({
        ...prev,
        currentPhase: nextPhase.id
      }));
    } else {
      // All phases complete
      const completedSession: CalibrationSession = {
        ...session,
        currentPhase: 'complete',
        completedAt: Date.now()
      };
      setSession(completedSession);
      onComplete(completedSession);
    }
  };

  const handleStrokeCaptured = (stroke: Stroke) => {
    const calibrationStroke: CalibrationStroke = {
      stroke,
      phase: currentPhase.id,
      timestamp: Date.now()
    };

    setSession(prev => ({
      ...prev,
      strokes: [...prev.strokes, calibrationStroke]
    }));
  };

  if (isComplete) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '3rem'
      }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
          Calibration Complete!
        </h1>
        <p>Captured {session.strokes.length} strokes across 3 phases</p>
        <p>Analyzing your drawing style...</p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.5rem',
          marginTop: '2rem',
          maxWidth: '800px',
          marginLeft: 'auto',
          marginRight: 'auto'
        }}>
          {['feather', 'normal', 'heavy'].map(phase => (
            <div
              key={phase}
              style={{
                background: 'white',
                padding: '1.5rem',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <h3 style={{ color: '#0066FF', marginBottom: '0.5rem' }}>
                {phase.charAt(0).toUpperCase() + phase.slice(1)} Phase
              </h3>
              <p>{session.strokes.filter(s => s.phase === phase).length} strokes</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      width: '100%',
      minHeight: '100vh',
      background: '#f5f5f5'
    }}>
      <div style={{
        textAlign: 'center',
        padding: '1rem',
        background: '#0066FF',
        color: 'white',
        fontWeight: 'bold'
      }}>
        Phase {currentPhaseIndex + 1} of {CALIBRATION_PHASES.length}
      </div>

      <CalibrationPhaseComponent
        phase={currentPhase}
        onComplete={handlePhaseComplete}
        onStrokeCaptured={handleStrokeCaptured}
        isActive={isPhaseActive}
        onStart={handlePhaseStart}
      />

      {onCancel && (
        <button
          onClick={onCancel}
          style={{
            position: 'fixed',
            top: '1rem',
            right: '1rem',
            padding: '0.5rem 1rem',
            background: '#ff4444',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Cancel Calibration
        </button>
      )}
    </div>
  );
}
