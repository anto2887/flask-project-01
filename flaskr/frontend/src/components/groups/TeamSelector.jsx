import React, { useState, useEffect } from 'react';
import { getLeagueTeams } from '../../api/matches';

export const TeamSelector = ({ selectedLeague, onTeamsSelected }) => {
   const [teams, setTeams] = useState([]);
   const [selectedTeams, setSelectedTeams] = useState(new Set());
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);

   useEffect(() => {
       const loadTeams = async () => {
           if (!selectedLeague) return;
           setLoading(true);
           setError(null);
           
           try {
               const response = await getLeagueTeams(selectedLeague);
               if (response.status === 'success' && Array.isArray(response.data)) {
                   setTeams(response.data);
               }
           } catch (err) {
               console.error('Error loading teams:', err);
               setError(err.message || 'Failed to load teams');
               setTeams([]);
           } finally {
               setLoading(false);
           }
       };

       loadTeams();
   }, [selectedLeague]);

   const toggleTeam = (teamId) => {
       setSelectedTeams(prev => {
           const newSet = new Set(prev);
           if (newSet.has(teamId)) {
               newSet.delete(teamId);
           } else {
               newSet.add(teamId);
           }
           
           // Notify parent component of selected teams
           if (onTeamsSelected) {
               onTeamsSelected(Array.from(newSet));
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