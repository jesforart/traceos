/**
 * Week 5: Style DNA Encoding - Demo Page
 *
 * Interactive demonstration of 3-tier DNA system:
 * - StrokeDNA (30-dim): Real-time feature extraction
 * - ImageDNA (512-dim): Visual analysis
 * - TemporalDNA (32-dim): Learning & fatigue tracking
 */

import { useEffect, useRef, useState } from 'react';
import { globalStrokeDNAEncoder, type StrokeData } from '../lib/dna/encoders/StrokeDNAEncoder';
import { globalImageDNAEncoder } from '../lib/dna/encoders/ImageDNAEncoder';
import { globalTemporalDNAEncoder } from '../lib/dna/encoders/TemporalDNAEncoder';
import { globalAestheticRegulator, type AestheticMode } from '../lib/dna/AestheticRegulator';
import { globalAdaptiveBehaviorManager, globalBrushAdjuster, type AdaptiveBehavior } from '../lib/dna/AdaptiveBehaviorManager';
import { globalDNADistanceCalculator } from '../lib/dna/DNADistanceCalculator';
import { globalDNABlender } from '../lib/dna/DNABlender';
import { globalUMAPProjector } from '../lib/dna/UMAPProjector';
import { globalDNAPipeline } from '../lib/dna/DNAPipeline';
import { globalContextManager } from '../lib/dna/ArtistContextManager';
import { globalDNAStorage } from '../lib/dna/storage/DNAStorageManager';
import type { DNASession, StrokeDNA, PrettyScore } from '../lib/dna/types';
import { ulid } from '../utils/ulid';

export default function Week5StyleDNA() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentColor, setCurrentColor] = useState('#0066FF');
  const [brushSize, setBrushSize] = useState(5);
  const [currentStroke, setCurrentStroke] = useState<Array<{ x: number; y: number; timestamp: number }>>([]);

  // DNA state
  const [session, setSession] = useState<DNASession | null>(null);
  const [prettyScore, setPrettyScore] = useState<PrettyScore | null>(null);
  const [adaptiveBehaviors, setAdaptiveBehaviors] = useState<AdaptiveBehavior[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<string>('');
  const [aestheticMode, setAestheticMode] = useState<AestheticMode>('balanced');

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      await globalDNAStorage.initialize();

      const newSession: DNASession = {
        session_id: ulid(),
        started_at: Date.now(),
        total_strokes: 0,
        stroke_dnas: [],
        image_dnas: [],
        temporal_dnas: [],
        confidence_score: 0,
        context: globalContextManager.getContext()
      };

      setSession(newSession);
      globalAestheticRegulator.setMode(aestheticMode);
    };

    initSession();
  }, []);

  // Drawing handlers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsDrawing(true);
    setCurrentStroke([{ x, y, timestamp: Date.now() }]);

    // Draw point
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = currentColor;
    ctx.beginPath();
    ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
    ctx.fill();
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const newPoint = { x, y, timestamp: Date.now() };
    setCurrentStroke(prev => [...prev, newPoint]);

    // Draw line
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const lastPoint = currentStroke[currentStroke.length - 1];
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    ctx.moveTo(lastPoint.x, lastPoint.y);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = async () => {
    if (!isDrawing || currentStroke.length < 2 || !session) {
      setIsDrawing(false);
      return;
    }

    setIsDrawing(false);

    const canvas = canvasRef.current;
    if (!canvas) return;

    // Encode stroke DNA (hot path)
    const strokeData: StrokeData = {
      stroke_id: ulid(),
      points: currentStroke,
      tool: 'pen',
      color: currentColor,
      brush_size: brushSize,
      canvas_width: canvas.width,
      canvas_height: canvas.height
    };

    try {
      const result = await globalDNAPipeline.encodeStroke(
        strokeData,
        globalContextManager.getContext(),
        globalStrokeDNAEncoder
      );

      // Update session
      const updatedSession = {
        ...session,
        stroke_dnas: [...session.stroke_dnas, result.hot_path.stroke_dna],
        total_strokes: session.total_strokes + 1
      };

      setSession(updatedSession);

      // Update context
      globalContextManager.onStrokeComplete({
        tool: 'pen',
        color: currentColor,
        brush_size: brushSize
      });

      // Update metrics
      setPipelineMetrics(globalDNAPipeline.getPerformanceSummary());

      // Analyze every 10 strokes
      if (updatedSession.total_strokes % 10 === 0) {
        await analyzeSession(updatedSession);
      }

    } catch (error) {
      console.error('DNA encoding failed:', error);
    }

    setCurrentStroke([]);
  };

  // Analyze session
  const analyzeSession = async (currentSession: DNASession) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // 1. Encode ImageDNA
    const ctx = canvas.getContext('2d');
    if (ctx) {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const imageDNA = await globalImageDNAEncoder.encode(imageData, globalContextManager.getContext());
      currentSession.image_dnas.push(imageDNA);
    }

    // 2. Encode TemporalDNA
    const temporalDNA = await globalTemporalDNAEncoder.encode(
      currentSession,
      globalContextManager.getContext()
    );
    currentSession.temporal_dnas.push(temporalDNA);

    // 3. Calculate Pretty Score
    const score = globalAestheticRegulator.calculatePrettyScore(currentSession);
    setPrettyScore(score);

    // 4. Analyze adaptive behaviors
    const behaviors = globalAdaptiveBehaviorManager.analyzeBehaviors(
      temporalDNA,
      globalContextManager.getContext(),
      currentSession
    );
    setAdaptiveBehaviors(behaviors);

    // 5. Apply brush adjustments if needed
    const adjustedSettings = globalBrushAdjuster.getRecommendedSettings(temporalDNA, {
      size: brushSize,
      opacity: 1,
      smoothing: 0
    });

    if (adjustedSettings.adjusted) {
      setBrushSize(adjustedSettings.size);
    }

    setSession(currentSession);
  };

  // Demo functions
  const calculateDistances = () => {
    if (!session || session.stroke_dnas.length < 2) {
      alert('Need at least 2 strokes to calculate distances');
      return;
    }

    const dna1 = session.stroke_dnas[0].features;
    const dna2 = session.stroke_dnas[session.stroke_dnas.length - 1].features;

    const distance = globalDNADistanceCalculator.calculateDistance(dna1, dna2);
    alert(`Distance between first and last stroke: ${distance.toFixed(4)}`);
  };

  const blendStrokes = () => {
    if (!session || session.stroke_dnas.length < 2) {
      alert('Need at least 2 strokes to blend');
      return;
    }

    const dna1 = session.stroke_dnas[0];
    const dna2 = session.stroke_dnas[session.stroke_dnas.length - 1];

    const blended = globalDNABlender.blendStrokeDNA(dna1, dna2, 0.5);
    alert(`Blended DNA created with ${blended.features.length} features`);
  };

  const projectToUMAP = async () => {
    if (!session || session.stroke_dnas.length < 3) {
      alert('Need at least 3 strokes for UMAP projection');
      return;
    }

    const projection = await globalUMAPProjector.projectStrokeDNAs(session.stroke_dnas);
    console.log('UMAP projection:', projection);
    alert(`Projected ${projection.coordinates.length} strokes to 3D space`);
  };

  const saveSession = async () => {
    if (!session) return;

    await globalDNAStorage.saveSession(session);
    alert('Session saved to storage!');
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Reset session
    const newSession: DNASession = {
      session_id: ulid(),
      started_at: Date.now(),
      total_strokes: 0,
      stroke_dnas: [],
      image_dnas: [],
      temporal_dnas: [],
      confidence_score: 0,
      context: globalContextManager.getContext()
    };

    setSession(newSession);
    setPrettyScore(null);
    setAdaptiveBehaviors([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Week 5: Style DNA Encoding</h1>
        <p className="text-blue-200 mb-8">3-Tier DNA System for Creative Intelligence</p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Canvas Column */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Drawing Canvas</h2>

              {/* Controls */}
              <div className="flex gap-4 mb-4">
                <div>
                  <label className="block text-sm mb-1">Color</label>
                  <input
                    type="color"
                    value={currentColor}
                    onChange={(e) => setCurrentColor(e.target.value)}
                    className="w-16 h-10 rounded cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">Brush Size: {brushSize}px</label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={brushSize}
                    onChange={(e) => setBrushSize(Number(e.target.value))}
                    className="w-32"
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">Aesthetic Mode</label>
                  <select
                    value={aestheticMode}
                    onChange={(e) => {
                      const mode = e.target.value as AestheticMode;
                      setAestheticMode(mode);
                      globalAestheticRegulator.setMode(mode);
                    }}
                    className="bg-white/20 rounded px-2 py-1"
                  >
                    <option value="strict">Strict</option>
                    <option value="balanced">Balanced</option>
                    <option value="creative">Creative</option>
                  </select>
                </div>
                <button
                  onClick={clearCanvas}
                  className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded font-semibold ml-auto"
                >
                  Clear
                </button>
              </div>

              {/* Canvas */}
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="border-2 border-blue-400 rounded bg-white cursor-crosshair"
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
              />

              {/* DNA Operations */}
              <div className="mt-4 flex gap-2 flex-wrap">
                <button
                  onClick={calculateDistances}
                  className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded font-semibold"
                >
                  Calculate Distances
                </button>
                <button
                  onClick={blendStrokes}
                  className="bg-purple-500 hover:bg-purple-600 px-4 py-2 rounded font-semibold"
                >
                  Blend Strokes
                </button>
                <button
                  onClick={projectToUMAP}
                  className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded font-semibold"
                >
                  UMAP Projection
                </button>
                <button
                  onClick={saveSession}
                  className="bg-yellow-500 hover:bg-yellow-600 px-4 py-2 rounded font-semibold text-black"
                >
                  Save Session
                </button>
              </div>
            </div>
          </div>

          {/* Stats Column */}
          <div className="space-y-6">
            {/* Session Stats */}
            <div className="bg-white/10 backdrop-blur rounded-lg p-4">
              <h3 className="font-bold mb-2">Session Stats</h3>
              {session && (
                <div className="text-sm space-y-1">
                  <div>Total Strokes: {session.total_strokes}</div>
                  <div>StrokeDNAs: {session.stroke_dnas.length}</div>
                  <div>ImageDNAs: {session.image_dnas.length}</div>
                  <div>TemporalDNAs: {session.temporal_dnas.length}</div>
                  <div>Confidence: {(session.confidence_score * 100).toFixed(1)}%</div>
                </div>
              )}
            </div>

            {/* Pretty Score */}
            {prettyScore && (
              <div className={`bg-white/10 backdrop-blur rounded-lg p-4 border-2 ${
                prettyScore.passes_threshold ? 'border-green-400' : 'border-red-400'
              }`}>
                <h3 className="font-bold mb-2">Pretty Score</h3>
                <div className="text-2xl font-bold mb-2">
                  {(prettyScore.overall_score * 100).toFixed(1)}%
                </div>
                <div className="text-sm space-y-1">
                  <div>Color Harmony: {(prettyScore.color_harmony * 100).toFixed(0)}%</div>
                  <div>Composition: {(prettyScore.composition_balance * 100).toFixed(0)}%</div>
                  <div>Complexity: {(prettyScore.visual_complexity * 100).toFixed(0)}%</div>
                  <div>Consistency: {(prettyScore.style_consistency * 100).toFixed(0)}%</div>
                </div>
                {prettyScore.recommendation && (
                  <div className="mt-2 text-xs text-blue-200">
                    {prettyScore.recommendation}
                  </div>
                )}
              </div>
            )}

            {/* Adaptive Behaviors */}
            {adaptiveBehaviors.length > 0 && (
              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <h3 className="font-bold mb-2">Adaptive Behaviors</h3>
                <div className="text-sm space-y-2">
                  {adaptiveBehaviors.slice(0, 3).map((behavior) => (
                    <div key={behavior.behavior_id} className={`p-2 rounded ${
                      behavior.priority === 'critical' ? 'bg-red-500/30' :
                      behavior.priority === 'high' ? 'bg-orange-500/30' :
                      'bg-blue-500/30'
                    }`}>
                      <div className="font-semibold">{behavior.type}</div>
                      <div className="text-xs">{behavior.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pipeline Metrics */}
            {pipelineMetrics && (
              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <h3 className="font-bold mb-2">Pipeline Performance</h3>
                <pre className="text-xs whitespace-pre-wrap">
                  {pipelineMetrics}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Feature Summary */}
        <div className="mt-8 bg-white/10 backdrop-blur rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Week 5 Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="font-bold text-lg mb-2">🧬 StrokeDNA (30-dim)</h3>
              <ul className="text-sm space-y-1 text-blue-200">
                <li>✓ Geometric features (10)</li>
                <li>✓ Statistical features (10)</li>
                <li>✓ Dynamic features (10)</li>
                <li>✓ Bounds normalization</li>
                <li>✓ Hot path encoding (&lt;16ms)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">🎨 ImageDNA (512-dim)</h3>
              <ul className="text-sm space-y-1 text-blue-200">
                <li>✓ VGG19-inspired features</li>
                <li>✓ Dominant color extraction</li>
                <li>✓ Texture analysis</li>
                <li>✓ Cold path encoding</li>
                <li>✓ Web Worker processing</li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">⏱️  TemporalDNA (32-dim)</h3>
              <ul className="text-sm space-y-1 text-blue-200">
                <li>✓ Learning metrics (10)</li>
                <li>✓ Fatigue indicators (10)</li>
                <li>✓ Style evolution (10)</li>
                <li>✓ Adaptive behaviors</li>
                <li>✓ Brush adjustments</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
