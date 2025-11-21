import React from 'react';
import { SemanticElement, FACE_TAGS, FaceTag } from '../types/semantic';

interface TagPanelProps {
  elements: SemanticElement[];
  selectedStrokeIds: string[];
  onTagSelected: (tag: FaceTag) => void;
  onElementDelete: (elementId: string) => void;
  onElementUpdate: (elementId: string, newLabel: FaceTag) => void;
}

export function TagPanel({
  elements,
  selectedStrokeIds,
  onTagSelected,
  onElementDelete,
  onElementUpdate
}: TagPanelProps) {
  return (
    <div className="tag-panel">
      <div className="tag-assignment">
        <h3>Tag Selected Strokes</h3>

        {selectedStrokeIds.length > 0 ? (
          <>
            <p>{selectedStrokeIds.length} strokes selected</p>

            <div className="tag-buttons">
              {FACE_TAGS.map(tag => (
                <button
                  key={tag}
                  onClick={() => onTagSelected(tag)}
                  className="tag-button"
                >
                  {tag.replace('_', ' ')}
                </button>
              ))}
            </div>
          </>
        ) : (
          <p className="hint">Select strokes to tag them</p>
        )}
      </div>

      <div className="tagged-elements">
        <h3>Tagged Elements ({elements.length})</h3>

        {elements.length === 0 ? (
          <p className="hint">No elements tagged yet</p>
        ) : (
          <div className="element-list">
            {elements.map(element => (
              <div key={element.id} className="element-card">
                <div className="element-header">
                  <select
                    value={element.label}
                    onChange={(e) => onElementUpdate(element.id, e.target.value as FaceTag)}
                  >
                    {FACE_TAGS.map(tag => (
                      <option key={tag} value={tag}>
                        {tag.replace('_', ' ')}
                      </option>
                    ))}
                  </select>

                  {element.auto_detected && (
                    <span className="auto-badge" title={`Confidence: ${element.confidence}`}>
                      Auto
                    </span>
                  )}
                </div>

                <div className="element-info">
                  <span>{element.stroke_ids.length} strokes</span>
                  {element.confidence && (
                    <span>{Math.round(element.confidence * 100)}% confident</span>
                  )}
                </div>

                <button
                  onClick={() => onElementDelete(element.id)}
                  className="delete-button"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
