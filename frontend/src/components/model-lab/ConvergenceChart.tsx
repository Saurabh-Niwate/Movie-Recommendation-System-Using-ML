import React, { useState } from 'react';
import { ConvergenceData } from '../../types/modelLab';
import { TrendingDown, Activity } from 'lucide-react';

interface ConvergenceChartProps {
  data: ConvergenceData;
}

export const ConvergenceChart: React.FC<ConvergenceChartProps> = ({ data }) => {
  const [hoveredEpoch, setHoveredEpoch] = useState<number | null>(null);

  const epochs = data.epochs;
  if (!epochs || epochs.length === 0) return null;

  // Chart dimensions
  const width = 800;
  const height = 300;
  const padding = { top: 30, right: 40, bottom: 40, left: 60 };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Compute min/max for scaling
  const minEpoch = 1;
  const maxEpoch = Math.max(...epochs.map((e) => e.epoch));

  const allLoss = epochs.map((e) => e.train_loss);
  const allValRmse = epochs.map((e) => e.val_rmse);
  const minVal = Math.min(...allLoss, ...allValRmse) * 0.95;
  const maxVal = Math.max(...allLoss, ...allValRmse) * 1.05;

  const getX = (epoch: number) =>
    padding.left + ((epoch - minEpoch) / (maxEpoch - minEpoch)) * chartWidth;

  const getY = (val: number) =>
    padding.top + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;

  // Generate SVG path for train loss
  const lossPoints = epochs.map((e) => `${getX(e.epoch)},${getY(e.train_loss)}`).join(' ');
  // Generate SVG path for validation RMSE
  const valPoints = epochs.map((e) => `${getX(e.epoch)},${getY(e.val_rmse)}`).join(' ');

  const currentHoverData = hoveredEpoch ? epochs.find((e) => e.epoch === hoveredEpoch) : null;

  return (
    <div className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-5 shadow-2xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-zinc-800">
        <div>
          <h4 className="font-bold text-white text-base flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-[#E50914]" />
            <span>Training Convergence Curves (Funk-SVD SGD)</span>
          </h4>
          <p className="text-xs text-zinc-400 mt-0.5">
            {data.algorithm} • Converged in {data.training_time_sec}s (Best Epoch: {data.best_epoch})
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 text-xs font-medium">
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#E50914] rounded-full inline-block" />
            <span className="text-zinc-300">Train Loss</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-blue-400 rounded-full inline-block" />
            <span className="text-zinc-300">Validation RMSE</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none overflow-visible"
        >
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const y = padding.top + chartHeight * (1 - ratio);
            const val = minVal + ratio * (maxVal - minVal);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#27272a"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="#71717a"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="monospace"
                >
                  {val.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Vertical X-axis ticks */}
          {epochs.filter((e) => e.epoch % 2 === 0 || e.epoch === 1).map((e) => {
            const x = getX(e.epoch);
            return (
              <g key={e.epoch}>
                <line
                  x1={x}
                  y1={padding.top}
                  x2={x}
                  y2={padding.top + chartHeight}
                  stroke="#27272a"
                  strokeDasharray="2 2"
                />
                <text
                  x={x}
                  y={padding.top + chartHeight + 18}
                  fill="#71717a"
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  Ep {e.epoch}
                </text>
              </g>
            );
          })}

          {/* Loss Curve */}
          <polyline
            fill="none"
            stroke="#E50914"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={lossPoints}
          />

          {/* Val RMSE Curve */}
          <polyline
            fill="none"
            stroke="#60a5fa"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={valPoints}
          />

          {/* Epoch Dots & Interactivity */}
          {epochs.map((e) => {
            const x = getX(e.epoch);
            const lossY = getY(e.train_loss);
            const valY = getY(e.val_rmse);
            const isHovered = hoveredEpoch === e.epoch;

            return (
              <g
                key={e.epoch}
                onMouseEnter={() => setHoveredEpoch(e.epoch)}
                onMouseLeave={() => setHoveredEpoch(null)}
                className="cursor-pointer"
              >
                {/* Hit area */}
                <rect
                  x={x - (chartWidth / epochs.length) / 2}
                  y={padding.top}
                  width={chartWidth / epochs.length}
                  height={chartHeight}
                  fill="transparent"
                />

                {isHovered && (
                  <line
                    x1={x}
                    y1={padding.top}
                    x2={x}
                    y2={padding.top + chartHeight}
                    stroke="#a1a1aa"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                  />
                )}

                <circle
                  cx={x}
                  cy={lossY}
                  r={isHovered ? 5 : 3}
                  fill="#E50914"
                  stroke="#ffffff"
                  strokeWidth={isHovered ? 2 : 1}
                />
                <circle
                  cx={x}
                  cy={valY}
                  r={isHovered ? 5 : 3}
                  fill="#60a5fa"
                  stroke="#ffffff"
                  strokeWidth={isHovered ? 2 : 1}
                />
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {currentHoverData && (
          <div className="mt-3 p-3 bg-zinc-900 border border-zinc-700 rounded-lg flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" />
              <span className="font-bold text-white">
                Epoch {currentHoverData.epoch}
              </span>
            </div>
            <div className="flex items-center gap-6 font-mono">
              <span className="text-[#E50914]">
                Train Loss: {currentHoverData.train_loss.toFixed(4)}
              </span>
              <span className="text-blue-400">
                Val RMSE: {currentHoverData.val_rmse.toFixed(4)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
