/**
 * GPUDrawingTest - Test component for GPU rendering with calibration profile.
 *
 * This demonstrates the complete pipeline:
 * 1. Load calibration profile from backend
 * 2. Initialize WebGPU
 * 3. Render with profile-driven shaders
 * 4. Apply semantic weighting
 */

import React, { useState, useEffect } from 'react';
import { GPUDrawingSurface } from './GPUDrawingSurface';
import { ArtistProfile } from '../types/calibration';
import { FaceTag, FACE_TAGS } from '../types/semantic';

export function GPUDrawingTest() {
  const [profile, setProfile] = useState<ArtistProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<FaceTag>('other');
  const [color, setColor] = useState('#000000');

  // Load test profile from backend
  useEffect(() => {
    const loadProfile = async () => {
      try {
        // First, get all profiles
        const response = await fetch('http://localhost:8001/api/calibration/profiles');

        if (!response.ok) {
          throw new Error('Failed to fetch profiles');
        }

        const profiles: ArtistProfile[] = await response.json();

        if (profiles.length > 0) {
          // Use the first available profile
          setProfile(profiles[0]);
          console.log('[GPUDrawingTest] Loaded profile:', profiles[0].id);
        } else {
          // No profiles available - user needs to run calibration first
          setError('No calibration profiles found. Please complete calibration first.');
        }
      } catch (err) {
        console.error('[GPUDrawingTest] Failed to load profile:', err);
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>GPU Drawing Test</h2>
        <p>Loading calibration profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>GPU Drawing Test</h2>
        <p style={{ color: 'red' }}>{error}</p>
        <p>
          To use GPU rendering, you need to:
          <ol>
            <li>Complete the calibration warmup (10 seconds)</li>
            <li>Generate an artist profile</li>
            <li>Refresh this page to load the profile</li>
          </ol>
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>GPU Drawing Test</h2>

      {profile && (
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          <h3>Profile Loaded</h3>
          <p><strong>Artist:</strong> {profile.artistName}</p>
          <p><strong>ID:</strong> {profile.id}</p>
          <p><strong>Fingerprint:</strong> {profile.device.calibrationFingerprint}</p>
          <p><strong>Version:</strong> {profile.traceProfileVersion}</p>
          <p><strong>Engine:</strong> {profile.brushEngineVersion}</p>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '10px' }}>
          Color:
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            style={{ marginLeft: '10px' }}
          />
        </label>

        <label>
          Semantic Tag:
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value as FaceTag)}
            style={{ marginLeft: '10px', padding: '4px' }}
          >
            {FACE_TAGS.map(tag => (
              <option key={tag} value={tag}>
                {tag.replace('_', ' ')}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ border: '2px solid #ccc', borderRadius: '4px', overflow: 'hidden' }}>
        <GPUDrawingSurface
          width={800}
          height={600}
          profile={profile}
          color={color}
          semanticTag={selectedTag}
          onError={(err) => {
            console.error('[GPUDrawingTest] Drawing error:', err);
            setError(err.message);
          }}
        />
      </div>

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <p>
          <strong>Instructions:</strong> Draw on the canvas above. The rendering is GPU-accelerated
          and uses your personal calibration profile.
        </p>
        <p>
          <strong>Semantic Weighting:</strong> Different facial features have different rendering
          weights (e.g., eyes are sharper at 1.2x, skin is softer at 0.7x).
        </p>
      </div>
    </div>
  );
}
