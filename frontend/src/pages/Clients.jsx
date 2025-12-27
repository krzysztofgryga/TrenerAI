import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users,
    UserPlus,
    Copy,
    Check,
    Trash2,
    Clock,
    RefreshCw,
    ChevronRight,
    Mail,
    Calendar
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
    getTrainerClients,
    generateInvitationCode,
    getMyInvitations,
    deleteInvitation
} from '../services/backendService';
import GlassCard from '../components/GlassCard';
import './Clients.css';

function Clients() {
    const navigate = useNavigate();
    const { isTrainer } = useAuth();

    const [clients, setClients] = useState([]);
    const [invitations, setInvitations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [newCode, setNewCode] = useState(null);
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState(null);

    // Redirect non-trainers
    useEffect(() => {
        if (!isTrainer) {
            navigate('/');
        }
    }, [isTrainer, navigate]);

    // Fetch data
    useEffect(() => {
        if (isTrainer) {
            fetchData();
        }
    }, [isTrainer]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [clientsData, invitationsData] = await Promise.all([
                getTrainerClients(),
                getMyInvitations()
            ]);
            setClients(clientsData);
            setInvitations(invitationsData);
        } catch (err) {
            console.error('Error fetching data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateCode = async () => {
        setGenerating(true);
        setError(null);
        try {
            const result = await generateInvitationCode(24);
            setNewCode(result);
            // Refresh invitations list
            const updatedInvitations = await getMyInvitations();
            setInvitations(updatedInvitations);
        } catch (err) {
            setError(err.message);
        } finally {
            setGenerating(false);
        }
    };

    const handleCopyCode = async () => {
        if (newCode?.code) {
            try {
                await navigator.clipboard.writeText(newCode.code);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        }
    };

    const handleDeleteInvitation = async (code) => {
        if (await deleteInvitation(code)) {
            setInvitations(invitations.filter(inv => inv.code !== code));
            if (newCode?.code === code) {
                setNewCode(null);
            }
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('pl-PL', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const isExpired = (expiresAt) => {
        return new Date(expiresAt) < new Date();
    };

    const getInitials = (name) => {
        if (!name) return 'K';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    if (!isTrainer) return null;

    return (
        <div className="page clients">
            <header className="page-header">
                <h1 className="page-title">Moi klienci</h1>
            </header>

            {/* Generate Invitation Section */}
            <section className="section">
                <h2 className="section-title">Zaproś klienta</h2>
                <GlassCard className="invite-card" glow>
                    <div className="invite-content">
                        <div className="invite-icon">
                            <UserPlus size={32} />
                        </div>
                        <div className="invite-text">
                            <h3>Wygeneruj kod zaproszenia</h3>
                            <p>Przekaż kod klientowi - wygasa po 24h</p>
                        </div>
                    </div>

                    {newCode && (
                        <div className="code-display">
                            <span className="code-value">{newCode.code}</span>
                            <button
                                className="code-copy-btn"
                                onClick={handleCopyCode}
                                title="Kopiuj kod"
                            >
                                {copied ? <Check size={20} /> : <Copy size={20} />}
                            </button>
                        </div>
                    )}

                    {error && (
                        <div className="invite-error">{error}</div>
                    )}

                    <button
                        className="btn btn-primary invite-btn"
                        onClick={handleGenerateCode}
                        disabled={generating}
                    >
                        {generating ? (
                            <>
                                <RefreshCw size={18} className="spinning" />
                                Generowanie...
                            </>
                        ) : (
                            <>
                                <UserPlus size={18} />
                                {newCode ? 'Wygeneruj nowy kod' : 'Generuj kod'}
                            </>
                        )}
                    </button>
                </GlassCard>
            </section>

            {/* Active Invitations */}
            {invitations.length > 0 && (
                <section className="section">
                    <h2 className="section-title">Aktywne zaproszenia</h2>
                    <div className="invitations-list">
                        {invitations.map((inv) => (
                            <GlassCard
                                key={inv.code}
                                className={`invitation-item ${inv.is_used ? 'invitation-item--used' : ''} ${isExpired(inv.expires_at) ? 'invitation-item--expired' : ''}`}
                            >
                                <div className="invitation-code">{inv.code}</div>
                                <div className="invitation-info">
                                    <Clock size={14} />
                                    <span>
                                        {inv.is_used ? 'Wykorzystany' :
                                         isExpired(inv.expires_at) ? 'Wygasł' :
                                         `Wygasa: ${formatDate(inv.expires_at)}`}
                                    </span>
                                </div>
                                {!inv.is_used && !isExpired(inv.expires_at) && (
                                    <button
                                        className="invitation-delete"
                                        onClick={() => handleDeleteInvitation(inv.code)}
                                        title="Usuń"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                )}
                            </GlassCard>
                        ))}
                    </div>
                </section>
            )}

            {/* Clients List */}
            <section className="section">
                <div className="section-header">
                    <h2 className="section-title">
                        <Users size={20} />
                        Klienci ({clients.length})
                    </h2>
                </div>

                {loading ? (
                    <GlassCard className="loading-card">
                        <RefreshCw size={24} className="spinning" />
                        <span>Ładowanie...</span>
                    </GlassCard>
                ) : clients.length === 0 ? (
                    <GlassCard className="empty-card">
                        <Users size={48} className="empty-icon" />
                        <h3>Brak klientów</h3>
                        <p>Wygeneruj kod zaproszenia i przekaż go klientowi</p>
                    </GlassCard>
                ) : (
                    <div className="clients-list">
                        {clients.map((client) => (
                            <GlassCard
                                key={client.id}
                                className="client-card"
                                onClick={() => console.log('Client details', client.id)}
                            >
                                <div className="client-avatar">
                                    {getInitials(client.client?.name)}
                                </div>
                                <div className="client-info">
                                    <span className="client-name">
                                        {client.client?.name || 'Klient'}
                                    </span>
                                    <span className="client-email">
                                        <Mail size={12} />
                                        {client.client?.email}
                                    </span>
                                    <span className="client-date">
                                        <Calendar size={12} />
                                        Od: {formatDate(client.created_at)}
                                    </span>
                                </div>
                                <ChevronRight size={20} className="client-arrow" />
                            </GlassCard>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}

export default Clients;
