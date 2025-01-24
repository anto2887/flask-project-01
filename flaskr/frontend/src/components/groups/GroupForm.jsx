import React, { useState } from 'react';
import { TeamSelector } from './TeamSelector';
import axios from 'axios';

export const GroupForm = () => {
    const [formData, setFormData] = useState({
        name: '',
        league: '',
        privacy_type: 'PRIVATE',
        description: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

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

            const response = await axios.post('/group/create', formDataToSend, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                withCredentials: true
            });

            if (response.data.status === 'success') {
                window.location.href = response.data.redirect_url;
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to create group');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form id="createGroupForm" className="space-y-6" onSubmit={handleSubmit}>
            <input type="hidden" name="csrf_token" value={getCsrfToken()} />

            <div className="form-group">
                <label htmlFor="name" className="block text-[#05445E] font-medium mb-2">
                    Group Name
                </label>
                <input
                    type="text"
                    id="name"
                    name="name"
                    className="w-full p-2 border rounded"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                />
            </div>

            <div className="form-group">
                <label className="block text-[#05445E] font-medium mb-2">
                    Select League
                </label>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    {['Premier League', 'La Liga', 'UEFA Champions League'].map(league => (
                        <label key={league} className="flex items-center space-x-3 p-4 border rounded hover:bg-[#75E6DA] cursor-pointer">
                            <input
                                type="radio"
                                name="league"
                                value={league}
                                checked={formData.league === league}
                                onChange={handleInputChange}
                                required
                            />
                            <span>{league}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="form-group">
                <label className="block text-[#05445E] font-medium mb-2">
                    Select Teams to Track
                </label>
                <TeamSelector />
            </div>

            <div className="form-group">
                <label className="block text-[#05445E] font-medium mb-2">
                    Group Privacy
                </label>
                <select
                    name="privacy_type"
                    className="w-full p-2 border rounded"
                    value={formData.privacy_type}
                    onChange={handleInputChange}
                    required
                >
                    <option value="PRIVATE">Private (Invite code only)</option>
                    <option value="SEMI_PRIVATE">Semi-Private (Invite code + admin approval)</option>
                </select>
            </div>

            <div className="form-group">
                <label htmlFor="description" className="block text-[#05445E] font-medium mb-2">
                    Group Description (Optional)
                </label>
                <textarea
                    id="description"
                    name="description"
                    className="w-full p-2 border rounded"
                    rows="3"
                    value={formData.description}
                    onChange={handleInputChange}
                />
            </div>

            <div className="flex justify-between items-center">
                <button
                    type="submit"
                    className={`bg-[#189AB4] text-white px-6 py-2 rounded hover:bg-[#05445E] ${
                        loading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    disabled={loading}
                >
                    {loading ? 'Creating...' : 'Create Group'}
                </button>
                <a href="/" className="text-[#189AB4] hover:text-[#05445E]">
                    Cancel
                </a>
            </div>

            {error && (
                <div id="errorContainer" className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <p id="errorMessage">{error}</p>
                </div>
            )}
        </form>
    );
};

export default GroupForm;