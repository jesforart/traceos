/**
 * App - Main TraceOS application with dual renderer system
 *
 * IMPROVEMENTS APPLIED:
 * - #1: Block bad Windows "Basic Render Adapter"
 * - #4: RendererSurface abstraction
 * - #9: Error UI component
 * - #10: Global renderer state (RendererContext)
 * - #12: Show adapter name in error UI
 * - #15: Performance mode selector
 * - CRITICAL FIX #2: WebGPU Safari safety (try/catch + device.lost handler)
 */

import { useState, useEffect } from 'react';
import { RendererProvider, useRenderer } from './context/RendererContext';
import { RendererSurface } from './components/RendererSurface';
import { GPUErrorUI } from './components/GPUErrorUI';
import { PerformanceModeSelector } from './components/PerformanceModeSelector';
import { ArtistProfile } from './types/calibration';
import Week3DesignVariations from './pages/week3-design-variations';
import Week5StyleDNA from './pages/week5-style-dna';

function AppContent() {
  const { state, setMode, setAdapterName } = useRenderer();
  const [gpuAvailable, setGpuAvailable] = useState<boolean | null>(null);
  const [gpuError, setGpuError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [profile, setProfile] = useState<ArtistProfile | null>(null);
  const [currentPage, setCurrentPage] = useState<'week2' | 'week3' | 'week5'>('week2');

  // CRITICAL FIX #2 + IMPROVEMENT #1: GPU detection with adapter blocking and Safari safety
  useEffect(() => {
    const checkGPU = async () => {
      console.log('[App] Checking WebGPU support...');

      // CRITICAL FIX #2: Try/catch for Safari safety
      try {
        if (!navigator.gpu) {
          console.log('❌ WebGPU not supported');
          setGpuError('WebGPU not supported. Try Chrome 113+, Edge 113+, or Safari 18+.');
          setGpuAvailable(false);
          setMode('canvas2d');
          setChecking(false);
          return;
        }

        const adapter = await navigator.gpu.requestAdapter({
          powerPreference: 'high-performance'
        });

        if (!adapter) {
          console.log('❌ No WebGPU adapter found');
          setGpuError('No GPU adapter found. Check your graphics drivers.');
          setGpuAvailable(false);
          setMode('canvas2d');
          setChecking(false);
          return;
        }

        // IMPROVEMENT #1: Block bad Windows adapters
        const adapterInfo = (adapter as any).info || { vendor: '', architecture: '', device: '', description: '' };
        const adapterNameRaw = (adapterInfo.vendor || adapterInfo.device || (adapter as any).name || 'Unknown GPU');
        const adapterName = adapterNameRaw.toLowerCase();

        console.log('[App] GPU Adapter detected:', {
          name: adapterNameRaw,
          vendor: adapterInfo.vendor,
          architecture: adapterInfo.architecture,
          device: adapterInfo.device
        });

        if (adapterName.includes('basic') ||
            adapterName.includes('microsoft basic') ||
            adapterName.includes('software') ||
            adapterName.includes('llvmpipe')) {
          console.log('❌ Basic/Software GPU detected (blocked)');
          setGpuError(`Software GPU detected: "${adapterNameRaw}". Using Canvas2D for better performance.`);
          setAdapterName(adapterNameRaw);
          setGpuAvailable(false);
          setMode('canvas2d');
          setChecking(false);
          return;
        }

        // Request device to verify it actually works
        const device = await adapter.requestDevice();

        // CRITICAL FIX #2: Add device.lost handler for Safari
        device.lost.then((info) => {
          console.error('[App] GPU device lost:', info.reason, info.message);

          if (info.reason !== 'destroyed') {
            // Device lost unexpectedly - fall back to Canvas2D
            setGpuAvailable(false);
            setGpuError('GPU device lost - falling back to Canvas2D');
            setMode('canvas2d');
          }
        });

        // Add uncaptured error handler
        device.onuncapturederror = (event) => {
          console.error('[App] GPU uncaptured error:', event.error);
        };

        console.log('✅ WebGPU available:', adapterNameRaw);
        setAdapterName(adapterNameRaw);
        setGpuAvailable(true);
        setMode('gpu');
        setGpuError(null);

      } catch (error) {
        // CRITICAL FIX #2: Catch any WebGPU initialization errors
        console.error('[App] WebGPU check failed:', error);
        setGpuError(error instanceof Error ? error.message : 'Unknown GPU error');
        setGpuAvailable(false);
        setMode('canvas2d');
      }

      setChecking(false);
    };

    checkGPU();
  }, []); // Run once on mount - no dependencies needed

  // Load calibration profile if GPU is available
  useEffect(() => {
    if (!gpuAvailable) return;

    const loadProfile = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/calibration/profiles');

        if (!response.ok) {
          console.warn('[App] Failed to fetch profiles');
          return;
        }

        const profiles: ArtistProfile[] = await response.json();

        if (profiles.length > 0) {
          setProfile(profiles[0]);
          console.log('[App] Loaded calibration profile:', profiles[0].id);
        } else {
          console.log('[App] No calibration profiles available');
        }
      } catch (error) {
        console.error('[App] Failed to load profile:', error);
      }
    };

    loadProfile();
  }, [gpuAvailable]);

  if (checking) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <h2>Initializing TraceOS...</h2>
        <p style={{ color: '#666' }}>Checking GPU support</p>
      </div>
    );
  }

  // Show Week 3 page if selected
  if (currentPage === 'week3') {
    return <Week3DesignVariations />;
  }

  // Show Week 5 page if selected
  if (currentPage === 'week5') {
    return <Week5StyleDNA />;
  }

  return (
    <div className="app">
      <header>
        <div style={{ marginBottom: '1rem' }}>
          <button
            onClick={() => setCurrentPage('week2')}
            style={{
              padding: '0.5rem 1rem',
              marginRight: '0.5rem',
              background: '#0066FF',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Week 2: Drawing
          </button>
          <button
            onClick={() => setCurrentPage('week3')}
            style={{
              padding: '0.5rem 1rem',
              background: '#e0e0e0',
              color: '#666',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Week 3: Design Variations
          </button>
          <button
            onClick={() => setCurrentPage('week5')}
            style={{
              padding: '0.5rem 1rem',
              background: '#9333ea',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Week 5: Style DNA
          </button>
        </div>

        <h1>TraceOS - Week 2 🎨 Drawing</h1>
        <p>Draw with your Apple Pencil or mouse</p>
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: '0.5rem',
          flexWrap: 'wrap'
        }}>
          <div style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '12px',
            fontSize: '0.875rem',
            background: gpuAvailable ? '#e6f7e6' : '#fff3cd',
            color: gpuAvailable ? '#2d5016' : '#856404',
            fontWeight: 'bold'
          }}>
            {gpuAvailable ? '⚡ GPU Rendering' : '🖌️ Canvas2D Fallback'}
          </div>
          {state.adapterName && (
            <div style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              background: '#f0f0f0',
              color: '#666'
            }}>
              {state.adapterName}
            </div>
          )}
        </div>
      </header>

      <main>
        {/* IMPROVEMENT #9 + #12: Error UI with adapter name */}
        {gpuError && !gpuAvailable && (
          <GPUErrorUI error={gpuError} adapterName={state.adapterName} />
        )}

        {/* IMPROVEMENT #4: RendererSurface abstraction */}
        <RendererSurface
          width={800}
          height={600}
          gpuAvailable={gpuAvailable}
          profile={profile}
        />
      </main>

      <footer>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <p style={{ color: '#666', fontSize: '0.875rem', margin: 0 }}>
            {gpuAvailable
              ? 'Using WebGPU for 60 FPS rendering with your calibrated profile'
              : 'WebGPU unavailable - using optimized Canvas2D fallback (4-10x faster)'}
          </p>

          {/* IMPROVEMENT #15: Performance Mode Selector */}
          <PerformanceModeSelector />
        </div>
      </footer>

      <style>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        body, html {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                       Roboto, sans-serif;
          background: #f5f5f5;
          overflow: hidden;
          /* POLISH #1: Prevent double-tap zoom */
          touch-action: none;
          -webkit-user-select: none;
          user-select: none;
        }

        .app {
          display: flex;
          flex-direction: column;
          height: 100vh;
        }

        header {
          background: white;
          padding: 1rem;
          border-bottom: 1px solid #e0e0e0;
          text-align: center;
        }

        header h1 {
          margin-bottom: 0.25rem;
        }

        main {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          overflow: hidden;
        }

        footer {
          background: white;
          border-top: 1px solid #e0e0e0;
        }
      `}</style>
    </div>
  );
}

/**
 * App - Main entry point with RendererProvider
 *
 * IMPROVEMENT #10: Global state via RendererProvider
 */
export function App() {
  return (
    <RendererProvider>
      <AppContent />
    </RendererProvider>
  );
}
