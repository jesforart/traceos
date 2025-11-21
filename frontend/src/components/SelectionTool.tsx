import React from 'react';

interface SelectionToolProps {
  currentMode: 'lasso' | 'box' | 'individual' | null;
  onModeChange: (mode: 'lasso' | 'box' | 'individual' | null) => void;
}

export function SelectionTool({ currentMode, onModeChange }: SelectionToolProps) {
  return (
    <div className="selection-tool">
      <h3>Selection Tool</h3>

      <div className="tool-buttons">
        <button
          className={currentMode === 'lasso' ? 'active' : ''}
          onClick={() => onModeChange(currentMode === 'lasso' ? null : 'lasso')}
          title="Lasso Selection - Draw freeform selection"
        >
          Lasso
        </button>

        <button
          className={currentMode === 'box' ? 'active' : ''}
          onClick={() => onModeChange(currentMode === 'box' ? null : 'box')}
          title="Box Selection - Drag rectangle"
        >
          Box
        </button>

        <button
          className={currentMode === 'individual' ? 'active' : ''}
          onClick={() => onModeChange(currentMode === 'individual' ? null : 'individual')}
          title="Individual Selection - Click strokes"
        >
          Individual
        </button>
      </div>

      {currentMode && (
        <p className="tool-hint">
          {currentMode === 'lasso' && 'Draw around strokes to select'}
          {currentMode === 'box' && 'Drag to create selection box'}
          {currentMode === 'individual' && 'Click strokes to select'}
        </p>
      )}
    </div>
  );
}
