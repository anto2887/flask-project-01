const TeamSelector = () => {
    const [teams, setTeams] = React.useState([]);
    const [selectedTeams, setSelectedTeams] = React.useState(new Set());
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const loadTeams = async (league) => {
        if (!league) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = metaTag ? metaTag.content : '';
            
            const response = await fetch(`/group/api/teams/${encodeURIComponent(league)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Failed to fetch teams');
            }

            const data = await response.json();
            if (data.status === 'success' && Array.isArray(data.teams)) {
                setTeams(data.teams);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            setError(err.message);
            setTeams([]);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        function handleLeagueChange(e) {
            if (e.target.checked) {
                loadTeams(e.target.value);
            }
        }

        const leagueInputs = document.querySelectorAll('input[name="league"]');
        leagueInputs.forEach(input => {
            input.addEventListener('change', handleLeagueChange);
        });

        return () => {
            leagueInputs.forEach(input => {
                input.removeEventListener('change', handleLeagueChange);
            });
        };
    }, []);

    const toggleTeam = (teamId) => {
        setSelectedTeams(prev => {
            const newSet = new Set(prev);
            if (newSet.has(teamId)) {
                newSet.delete(teamId);
            } else {
                newSet.add(teamId);
            }

            // Update form hidden inputs
            const form = document.getElementById('createGroupForm');
            if (form) {
                // Remove existing team inputs
                const existingInputs = form.querySelectorAll('input[name="tracked_teams"]');
                existingInputs.forEach(input => input.remove());
                
                // Add new team inputs
                newSet.forEach(id => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'tracked_teams';
                    input.value = id;
                    form.appendChild(input);
                });
            }

            return newSet;
        });
    };

    if (loading) {
        return (
            React.createElement('div', { className: 'p-4 text-center' },
                React.createElement('div', { 
                    className: 'animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto'
                }),
                React.createElement('p', { className: 'mt-2' }, 'Loading teams...')
            )
        );
    }

    if (error) {
        return React.createElement('div', { 
            className: 'p-4 text-center text-red-600'
        }, `Error loading teams: ${error}`);
    }

    return React.createElement('div', { 
        className: 'grid grid-cols-2 md:grid-cols-4 gap-4' 
    }, teams.map(team => 
        React.createElement('div', {
            key: team.id,
            onClick: () => toggleTeam(team.id),
            className: `team-option flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50 ${
                selectedTeams.has(team.id) ? 'bg-blue-50 border-blue-500' : ''
            }`
        }, [
            React.createElement('img', {
                key: 'img',
                src: team.logo,
                alt: `${team.name} logo`,
                className: 'w-12 h-12 object-contain',
                onError: (e) => e.target.style.display = 'none'
            }),
            React.createElement('span', {
                key: 'name',
                className: 'ml-2'
            }, team.name)
        ])
    ));
};