import React, { useState, useEffect } from 'react';
import axios from 'axios';

export const TeamSelector = () => {
   const [teams, setTeams] = useState([]);
   const [selectedTeams, setSelectedTeams] = useState(new Set());
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);

   const loadTeams = async (league) => {
       if (!league) return;
       setLoading(true);
       setError(null);
       
       try {
           const response = await axios.get(`/api/teams/${encodeURIComponent(league)}`, {
               headers: {
                   'X-Requested-With': 'XMLHttpRequest',
                   'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
               },
               withCredentials: true
           });

           if (response.data.status === 'success' && Array.isArray(response.data.teams)) {
               setTeams(response.data.teams);
           }
       } catch (err) {
           console.error('Error loading teams:', err);
           setError(err.response?.data?.message || 'Failed to load teams');
           setTeams([]);
       } finally {
           setLoading(false);
       }
   };

   useEffect(() => {
       const handleLeagueChange = (e) => {
           if (e.target.checked) {
               loadTeams(e.target.value);
           }
       };

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

           const form = document.getElementById('createGroupForm');
           if (form) {
               const existingInputs = form.querySelectorAll('input[name="tracked_teams"]');
               existingInputs.forEach(input => input.remove());
               
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
           <div className="p-4 text-center">
               <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
               <p className="mt-2">Loading teams...</p>
           </div>
       );
   }

   if (error) {
       return (
           <div className="p-4 text-center text-red-600">
               Error loading teams: {error}
           </div>
       );
   }

   return (
       <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           {teams.map(team => (
               <div
                   key={team.id}
                   onClick={() => toggleTeam(team.id)}
                   className={`team-option flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50 ${
                       selectedTeams.has(team.id) ? 'bg-blue-50 border-blue-500' : ''
                   }`}
               >
                   <input
                       type="checkbox"
                       className="mr-2"
                       checked={selectedTeams.has(team.id)}
                       onChange={() => toggleTeam(team.id)}
                       onClick={(e) => e.stopPropagation()}
                   />
                   <img
                       src={team.logo}
                       alt={`${team.name} logo`}
                       className="w-12 h-12 object-contain"
                       onError={(e) => e.target.style.display = 'none'}
                   />
                   <span className="ml-2">{team.name}</span>
               </div>
           ))}
       </div>
   );
};

export default TeamSelector;