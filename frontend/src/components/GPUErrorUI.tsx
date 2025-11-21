/**
 * GPUErrorUI - Error display for GPU initialization failures
 *
 * IMPROVEMENT #12: Shows adapter name for debugging
 * Provides clear instructions for enabling WebGPU
 */

import React from 'react';

interface GPUErrorUIProps {
  error: string;
  adapterName: string | null;
}

export function GPUErrorUI({ error, adapterName }: GPUErrorUIProps) {
  return (
    <div style={{
      background: '#fff3cd',
      border: '1px solid #ffc107',
      borderRadius: '8px',
      padding: '1rem',
      marginBottom: '1rem',
      maxWidth: '600px'
    }}>
      <h3 style={{
        color: '#856404',
        marginBottom: '0.5rem',
        fontSize: '1rem'
      }}>
        ℹ️ GPU Rendering Unavailable
      </h3>
      <p style={{
        color: '#856404',
        fontSize: '0.875rem',
        marginBottom: '0.5rem'
      }}>
        {error}
      </p>
      {adapterName && (
        <p style={{
          color: '#856404',
          fontSize: '0.75rem',
          fontFamily: 'monospace',
          background: '#fff',
          padding: '0.25rem 0.5rem',
          borderRadius: '4px',
          marginBottom: '0.5rem'
        }}>
          Detected: {adapterName}
        </p>
      )}
      <details style={{ marginTop: '0.5rem' }}>
        <summary style={{
          cursor: 'pointer',
          color: '#856404',
          fontSize: '0.875rem',
          fontWeight: 'bold'
        }}>
          Enable WebGPU
        </summary>
        <div style={{
          marginTop: '0.5rem',
          fontSize: '0.8rem',
          color: '#666'
        }}>
          <p><strong>Chrome/Edge:</strong></p>
          <ol style={{ paddingLeft: '1.5rem', marginTop: '0.25rem' }}>
            <li>Go to <code>chrome://flags</code></li>
            <li>Search "WebGPU"</li>
            <li>Enable "Unsafe WebGPU"</li>
            <li>Restart browser</li>
          </ol>
          <p style={{ marginTop: '0.5rem' }}><strong>Firefox:</strong></p>
          <ol style={{ paddingLeft: '1.5rem', marginTop: '0.25rem' }}>
            <li>Go to <code>about:config</code></li>
            <li>Search "dom.webgpu.enabled"</li>
            <li>Set to true</li>
            <li>Restart browser</li>
          </ol>
          <p style={{ marginTop: '0.5rem' }}><strong>Safari:</strong></p>
          <ol style={{ paddingLeft: '1.5rem', marginTop: '0.25rem' }}>
            <li>Safari 18+ required</li>
            <li>WebGPU enabled by default</li>
          </ol>
        </div>
      </details>
    </div>
  );
}
