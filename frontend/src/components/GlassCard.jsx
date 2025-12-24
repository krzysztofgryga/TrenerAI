import './GlassCard.css';

function GlassCard({
    children,
    className = '',
    variant = 'default',
    glow = false,
    animated = false,
    onClick
}) {
    const classes = [
        'glass-card',
        `glass-card--${variant}`,
        glow ? 'glass-card--glow' : '',
        animated ? 'glass-card--animated' : '',
        onClick ? 'glass-card--clickable' : '',
        className
    ].filter(Boolean).join(' ');

    return (
        <div className={classes} onClick={onClick}>
            {children}
        </div>
    );
}

export default GlassCard;
