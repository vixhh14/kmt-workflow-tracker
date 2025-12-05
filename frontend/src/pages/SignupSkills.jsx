import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { Factory, Check, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';

const SignupSkills = () => {
    const navigate = useNavigate();
    const [signupData, setSignupData] = useState(null);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [skills, setSkills] = useState({}); // { machine_id: level_value }

    useEffect(() => {
        // Get signup data from session storage
        const data = sessionStorage.getItem('signupData');
        if (!data) {
            navigate('/signup');
            return;
        }
        setSignupData(JSON.parse(data));
        fetchMachines();
    }, []);

    const fetchMachines = async () => {
        try {
            const response = await api.get('/machines');
            // Filter out inactive machines if necessary, or show all
            setMachines(response.data);
        } catch (error) {
            console.error('Failed to fetch machines:', error);
            alert('Failed to load machines. Please refresh.');
        } finally {
            setLoading(false);
        }
    };

    const handleSkillChange = (machineId, value) => {
        setSkills(prev => ({
            ...prev,
            [machineId]: parseInt(value)
        }));
    };

    const hasSelectedSkills = Object.values(skills).some(val => val > 0);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!hasSelectedSkills) {
            return;
        }

        setSubmitting(true);

        try {
            // Map numeric levels to string values for backend compatibility
            const skillMap = {
                1: 'beginner',
                2: 'intermediate',
                3: 'expert',
                4: 'specialist'
            };

            const formattedSkills = Object.entries(skills)
                .filter(([_, level]) => level > 0)
                .map(([machineId, level]) => ({
                    machine_id: machineId,
                    skill_level: skillMap[level] || 'beginner'
                }));

            const payload = {
                ...signupData,
                skills: formattedSkills
            };

            await api.post('/auth/signup', payload);

            // Clear session storage
            sessionStorage.removeItem('signupData');

            // Show success message and redirect
            alert('Registration successful! Your account is pending admin approval.');
            navigate('/login');

        } catch (error) {
            console.error('Failed to create account:', error);
            alert(error.response?.data?.detail || 'Failed to create account. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
                <div className="text-center bg-white rounded-xl p-8 shadow-lg">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading machines...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col justify-center py-6 sm:py-12 px-4 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-4xl">
                <div className="text-center mb-6 sm:mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 bg-white/20 backdrop-blur-sm rounded-full mb-4">
                        <Factory className="text-white" size={28} />
                    </div>
                    <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Select Your Skills</h2>
                    <p className="mt-2 text-sm sm:text-base text-white/80">
                        Step 2 of 2: Indicate your proficiency level for each machine.
                    </p>
                </div>

                <div className="bg-white py-6 sm:py-8 px-4 sm:px-10 shadow-2xl rounded-2xl">
                    <form onSubmit={handleSubmit} className="space-y-6 sm:space-y-8">

                        {/* Selected count indicator */}
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">
                                Select at least one machine skill to continue
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${hasSelectedSkills ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                                }`}>
                                {Object.values(skills).filter(v => v > 0).length} selected
                            </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                            {machines.map((machine) => (
                                <div
                                    key={machine.id}
                                    className={`
                                        relative rounded-lg border p-4 transition-all duration-200
                                        ${skills[machine.id] > 0
                                            ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
                                            : 'border-gray-200 hover:border-gray-300 bg-white'}
                                    `}
                                >
                                    <div className="flex flex-col h-full justify-between space-y-3 sm:space-y-4">
                                        <div>
                                            <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate" title={machine.name}>
                                                {machine.name}
                                            </h3>
                                            {machine.type && (
                                                <p className="text-xs text-gray-500 mt-1">{machine.type}</p>
                                            )}
                                        </div>

                                        <div>
                                            <label htmlFor={`skill-${machine.id}`} className="block text-xs font-medium text-gray-700 mb-1">
                                                Skill Level
                                            </label>
                                            <select
                                                id={`skill-${machine.id}`}
                                                value={skills[machine.id] || 0}
                                                onChange={(e) => handleSkillChange(machine.id, e.target.value)}
                                                className="block w-full pl-3 pr-10 py-2.5 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-lg"
                                            >
                                                <option value="0">None</option>
                                                <option value="1">Beginner</option>
                                                <option value="2">Intermediate</option>
                                                <option value="3">Expert</option>
                                                <option value="4">Specialist</option>
                                            </select>
                                        </div>
                                    </div>

                                    {skills[machine.id] > 0 && (
                                        <div className="absolute top-2 right-2">
                                            <div className="bg-blue-500 rounded-full p-1">
                                                <Check size={12} className="text-white" />
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {machines.length === 0 && (
                            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                                <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
                                <h3 className="mt-2 text-sm font-medium text-gray-900">No machines found</h3>
                                <p className="mt-1 text-sm text-gray-500">Please contact your administrator.</p>
                            </div>
                        )}

                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-gray-200">
                            <button
                                type="button"
                                onClick={() => navigate('/signup')}
                                className="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2.5 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition"
                            >
                                <ArrowLeft className="mr-2 -ml-1 h-5 w-5" />
                                Back
                            </button>

                            <button
                                type="submit"
                                disabled={submitting || !hasSelectedSkills}
                                className={`
                                    w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white transition
                                    ${submitting || !hasSelectedSkills
                                        ? 'bg-gray-400 cursor-not-allowed'
                                        : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'}
                                `}
                            >
                                {submitting ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Creating Account...
                                    </>
                                ) : (
                                    <>
                                        Complete Registration
                                        <ArrowRight className="ml-2 -mr-1 h-5 w-5" />
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>

                <p className="text-center text-sm text-white/70 mt-6">
                    Already have an account?{' '}
                    <a href="/login" className="text-white font-semibold hover:underline">
                        Sign In
                    </a>
                </p>
            </div>
        </div>
    );
};

export default SignupSkills;
