import React, { useState, useEffect } from 'react';
import { usePredictions } from '../../contexts/PredictionContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { Link } from 'react-router-dom';

const RecentPredictions = () => {
  const { userPredictions, fetchUserPredictions, loading, error } = usePredictions();
  const [recentPredictions, setRecentPredictions] = useState([]);

  useEffect(() => {
    const loadPredictions = async () => {
      await fetchUserPredictions();
    };
    
    loadPredictions();
  }, [fetchUserPredictions]);

  useEffect(() => {
    if (userPredictions && userPredictions.length) {
      // Sort by submission time (newest first) and take first 5
      const sorted = [...userPredictions]
        .sort((a, b) => new Date(b.submission_time || 0) - new Date(a.submission_time || 0))
        .slice(0, 5);
      
      setRecentPredictions(sorted);
    }
  }, [userPredictions]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  if (recentPredictions.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-gray-500 mb-4">You haven't made any predictions yet</p>
        <Link 
          to="/predictions/new" 
          className="text-blue-600 hover:text-blue-800"
        >
          Make your first prediction →
        </Link>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {recentPredictions.map((prediction) => {
        const fixture = prediction.fixture || {};
        const result = getResultClass(prediction, fixture);
        
        return (
          <div 
            key={prediction.prediction_id} 
            className={`p-4 ${result.bgClass}`}
          >
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-500">
                {new Date(fixture.date).toLocaleDateString()}
              </span>
              <span className={`text-sm font-medium ${result.textClass}`}>
                {result.text}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <span className="font-medium">{fixture.home_team}</span>
                <span className="text-lg font-bold">
                  {prediction.score1} - {prediction.score2}
                </span>
                <span className="font-medium">{fixture.away_team}</span>
              </div>
              
              {prediction.points !== undefined && (
                <span className="text-blue-600 font-bold">
                  +{prediction.points} pts
                </span>
              )}
            </div>
            
            {fixture.status === 'FINISHED' && (
              <div className="mt-2 text-sm text-gray-500">
                Final score: {fixture.home_score} - {fixture.away_score}
              </div>
            )}
          </div>
        );
      })}
      
      <div className="p-4 bg-gray-50">
        <Link
          to="/predictions/history"
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          View all predictions →
        </Link>
      </div>
    </div>
  );
};

// Helper to determine result styling
const getResultClass = (prediction, fixture) => {
  // Return default if match hasn't ended
  if (fixture.status !== 'FINISHED' && 
      fixture.status !== 'FINISHED_AET' &&
      fixture.status !== 'FINISHED_PEN') {
    return {
      text: 'Pending',
      textClass: 'text-blue-600',
      bgClass: 'bg-white'
    };
  }

  // If we have points
  if (prediction.points !== undefined) {
    if (prediction.points === 3) {
      return {
        text: 'Perfect Score',
        textClass: 'text-green-600',
        bgClass: 'bg-green-50'
      };
    } else if (prediction.points === 1) {
      return {
        text: 'Correct Result',
        textClass: 'text-yellow-600',
        bgClass: 'bg-yellow-50'
      };
    } else {
      return {
        text: 'Incorrect',
        textClass: 'text-red-600',
        bgClass: 'bg-red-50'
      };
    }
  }

  return {
    text: 'Processed',
    textClass: 'text-gray-600',
    bgClass: 'bg-white'
  };
};

export default RecentPredictions;