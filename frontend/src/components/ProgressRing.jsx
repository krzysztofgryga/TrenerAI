import './ProgressRing.css';

function ProgressRing({
    progress = 0,
    size = 120,
    strokeWidth = 8,
    label = '',
    sublabel = ''
}) {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (progress / 100) * circumference;

    return (
        <div className="progress-ring" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="progress-ring-svg">
                <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="var(--neon-purple)" />
                        <stop offset="50%" stopColor="var(--neon-pink)" />
                        <stop offset="100%" stopColor="var(--neon-cyan)" />
                    </linearGradient>
                </defs>

                {/* Background circle */}
                <circle
                    className="progress-ring-bg"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                />

                {/* Progress circle */}
                <circle
                    className="progress-ring-progress"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    stroke="url(#progressGradient)"
                />
            </svg>

            <div className="progress-ring-content">
                <span className="progress-ring-value">{Math.round(progress)}%</span>
                {label && <span className="progress-ring-label">{label}</span>}
                {sublabel && <span className="progress-ring-sublabel">{sublabel}</span>}
            </div>
        </div>
    );
}

export default ProgressRing;
