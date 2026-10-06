import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';

const data = [
    { time: '10:00', temperature: 23.8 },
    { time: '10:05', temperature: 24.1 },
    { time: '10:10', temperature: 24.3 },
    { time: '10:15', temperature: 24.7 },
    { time: '10:20', temperature: 24.5 },
    { time: '10:25', temperature: 24.9 },
    { time: '10:30', temperature: 25.1 },
];

function EnvironmentChart() {
    return (
        <div className="environment-content">
            <div className="environment-value">
                <span>Température</span>
                <strong>25.1 °C</strong>
            </div>

            <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis domain={['dataMin - 1', 'dataMax + 1']} />
                        <Tooltip />
                        <Line
                            type="monotone"
                            dataKey="temperature"
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