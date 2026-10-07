import { useState } from 'react';
import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import type { Reading } from '../types';

interface EnvironmentChartProps {
    readings: Reading[];
}

type Metric = 'temperature' | 'humidity' | 'gas';

const metrics = {
    temperature: {
        label: 'Température',
        unit: '°C',
        color: '#ef4444',
        dataKey: 'temperature',
    },
    humidity: {
        label: 'Humidité',
        unit: '%',
        color: '#3b82f6',
        dataKey: 'humidity',
    },
    gas: {
        label: 'Gaz',
        unit: '',
        color: '#f59e0b',
        dataKey: 'gas',
    },
} as const;

function EnvironmentChart({
    readings,
}: EnvironmentChartProps) {
    const [selectedMetric, setSelectedMetric] =
        useState<Metric>('temperature');

    const metric = metrics[selectedMetric];

    const chartData = readings
        .filter((reading) => {
            if (selectedMetric === 'temperature') {
                return reading.temp_c !== null;
            }

            if (selectedMetric === 'humidity') {
                return reading.humidity_pct !== null;
            }

            return reading.gas_raw !== null;
        })
        .slice(-30)
        .map((reading) => ({
            time: new Date(reading.received_at).toLocaleTimeString(
                'fr-FR',
                {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                },
            ),
            temperature: reading.temp_c,
            humidity: reading.humidity_pct,
            gas: reading.gas_raw,
        }));

    const latestReading = readings.at(-1);

    const currentValue =
        selectedMetric === 'temperature'
            ? latestReading?.temp_c
            : selectedMetric === 'humidity'
              ? latestReading?.humidity_pct
              : latestReading?.gas_raw;

    return (
        <div className="environment-content">
            <div className="environment-header">
                <div className="environment-value">
                    <span>{metric.label}</span>
                    <strong>
                        {currentValue != null
                            ? `${typeof currentValue === 'number' && selectedMetric !== 'gas'
                                ? currentValue.toFixed(1)
                                : currentValue}${metric.unit ? ` ${metric.unit}` : ''}`
                            : '--'}
                    </strong>
                </div>

                <div className="environment-tabs">
                    {(Object.keys(metrics) as Metric[]).map(
                        (metricKey) => (
                            <button
                                key={metricKey}
                                type="button"
                                className={
                                    selectedMetric === metricKey
                                        ? 'environment-tab active'
                                        : 'environment-tab'
                                }
                                onClick={() =>
                                    setSelectedMetric(metricKey)
                                }
                            >
                                {metrics[metricKey].label}
                            </button>
                        ),
                    )}
                </div>
            </div>

            <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip
                            formatter={(value) => [
                                value,
                                metric.label,
                            ]}
                        />

                        <Line
                            type="monotone"
                            dataKey={metric.dataKey}
                            name={metric.label}
                            stroke={metric.color}
                            strokeWidth={2}
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default EnvironmentChart;