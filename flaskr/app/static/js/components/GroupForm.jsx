window.GroupForm = () => {
    const [formData, setFormData] = React.useState({
        name: '',
        league: '',
        privacy_type: 'PRIVATE',
        description: ''
    });
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const getCsrfToken = () => {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.content : '';
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const formDataToSend = new FormData(e.target);
            const csrfToken = getCsrfToken();

            const response = await fetch('/group/create', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: formDataToSend,
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                throw new Error(data.message || 'Failed to create group');
            }
        } catch (err) {
            setError(err.message);
            const errorContainer = document.getElementById('errorContainer');
            if (errorContainer) {
                errorContainer.classList.remove('hidden');
                const errorMessage = errorContainer.querySelector('#errorMessage');
                if (errorMessage) {
                    errorMessage.textContent = err.message;
                }
                setTimeout(() => {
                    errorContainer.classList.add('hidden');
                }, 5000);
            }
        } finally {
            setLoading(false);
        }
    };

    return React.createElement('form', {
        id: 'createGroupForm',
        className: 'space-y-6',
        onSubmit: handleSubmit
    }, [
        // CSRF Token
        React.createElement('input', {
            key: 'csrf',
            type: 'hidden',
            name: 'csrf_token',
            value: getCsrfToken()
        }),

        // Group Name
        React.createElement('div', { key: 'name-group', className: 'form-group' }, [
            React.createElement('label', {
                key: 'name-label',
                htmlFor: 'name',
                className: 'block text-[#05445E] font-medium mb-2'
            }, 'Group Name'),
            React.createElement('input', {
                key: 'name-input',
                type: 'text',
                id: 'name',
                name: 'name',
                className: 'w-full p-2 border rounded',
                value: formData.name,
                onChange: handleInputChange,
                required: true
            })
        ]),

        // League Selection
        React.createElement('div', { key: 'league-group', className: 'form-group' }, [
            React.createElement('label', {
                key: 'league-label',
                className: 'block text-[#05445E] font-medium mb-2'
            }, 'Select League'),
            React.createElement('div', {
                key: 'league-options',
                className: 'grid grid-cols-1 gap-4 md:grid-cols-3'
            }, [
                ['Premier League', 'La Liga', 'UEFA Champions League'].map(league =>
                    React.createElement('label', {
                        key: league,
                        className: 'flex items-center space-x-3 p-4 border rounded hover:bg-[#75E6DA] cursor-pointer'
                    }, [
                        React.createElement('input', {
                            key: `${league}-input`,
                            type: 'radio',
                            name: 'league',
                            value: league,
                            checked: formData.league === league,
                            onChange: handleInputChange,
                            required: true
                        }),
                        React.createElement('span', { key: `${league}-text` }, league)
                    ])
                )
            ])
        ]),

        // Team Selection
        React.createElement('div', { key: 'team-group', className: 'form-group' }, [
            React.createElement('label', {
                key: 'team-label',
                className: 'block text-[#05445E] font-medium mb-2'
            }, 'Select Teams to Track'),
            React.createElement(window.TeamSelector, { key: 'team-selector' })
        ]),

        // Privacy Selection
        React.createElement('div', { key: 'privacy-group', className: 'form-group' }, [
            React.createElement('label', {
                key: 'privacy-label',
                className: 'block text-[#05445E] font-medium mb-2'
            }, 'Group Privacy'),
            React.createElement('select', {
                key: 'privacy-select',
                name: 'privacy_type',
                className: 'w-full p-2 border rounded',
                value: formData.privacy_type,
                onChange: handleInputChange,
                required: true
            }, [
                React.createElement('option', {
                    key: 'private',
                    value: 'PRIVATE'
                }, 'Private (Invite code only)'),
                React.createElement('option', {
                    key: 'semi-private',
                    value: 'SEMI_PRIVATE'
                }, 'Semi-Private (Invite code + admin approval)')
            ])
        ]),

        // Description
        React.createElement('div', { key: 'description-group', className: 'form-group' }, [
            React.createElement('label', {
                key: 'description-label',
                htmlFor: 'description',
                className: 'block text-[#05445E] font-medium mb-2'
            }, 'Group Description (Optional)'),
            React.createElement('textarea', {
                key: 'description-input',
                id: 'description',
                name: 'description',
                className: 'w-full p-2 border rounded',
                rows: '3',
                value: formData.description,
                onChange: handleInputChange
            })
        ]),

        // Submit and Cancel buttons
        React.createElement('div', {
            key: 'button-group',
            className: 'flex justify-between items-center'
        }, [
            React.createElement('button', {
                key: 'submit-button',
                type: 'submit',
                className: `bg-[#189AB4] text-white px-6 py-2 rounded hover:bg-[#05445E] ${loading ? 'opacity-50 cursor-not-allowed' : ''}`,
                disabled: loading
            }, loading ? 'Creating...' : 'Create Group'),
            React.createElement('a', {
                key: 'cancel-link',
                href: '/',
                className: 'text-[#189AB4] hover:text-[#05445E]'
            }, 'Cancel')
        ])
    ]);
};

export default GroupForm;