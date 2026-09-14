import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { User, Mail, Phone, MapPin, Calendar, BookOpen, Bell, Save, X, Plus, Trash2 } from 'lucide-react';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  bio?: string;
  avatar?: string;
  joinedAt: string;
}

interface Skill {
  id: string;
  name: string;
  level: 'beginner' | 'intermediate' | 'advanced';
}

interface Subscription {
  id: string;
  courseName: string;
  courseId: string;
  startDate: string;
  status: 'active' | 'paused' | 'completed';
  progress: number;
}

// Mock API functions - replace with actual API calls
const fetchProfile = async (): Promise<UserProfile> => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  return {
    id: '1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 234 567 8900',
    location: 'San Francisco, CA',
    bio: 'Passionate learner exploring new technologies',
    joinedAt: '2024-01-15',
  };
};

const fetchSkills = async (): Promise<Skill[]> => {
  await new Promise(resolve => setTimeout(resolve, 800));
  return [
    { id: '1', name: 'JavaScript', level: 'advanced' },
    { id: '2', name: 'React', level: 'intermediate' },
    { id: '3', name: 'TypeScript', level: 'intermediate' },
  ];
};

const fetchSubscriptions = async (): Promise<Subscription[]> => {
  await new Promise(resolve => setTimeout(resolve, 900));
  return [
    {
      id: '1',
      courseName: 'Advanced Web Development',
      courseId: 'course-1',
      startDate: '2024-02-01',
      status: 'active',
      progress: 65,
    },
    {
      id: '2',
      courseName: 'Data Science Fundamentals',
      courseId: 'course-2',
      startDate: '2024-01-15',
      status: 'active',
      progress: 30,
    },
  ];
};

const updateProfile = async (data: Partial<UserProfile>): Promise<UserProfile> => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  return { ...data } as UserProfile;
};

const addSkill = async (skill: Omit<Skill, 'id'>): Promise<Skill> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return { ...skill, id: Date.now().toString() };
};

const deleteSkill = async (skillId: string): Promise<void> => {
  await new Promise(resolve => setTimeout(resolve, 500));
};

const updateSubscriptionStatus = async (data: { id: string; status: Subscription['status'] }): Promise<Subscription> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return {} as Subscription;
};

export default function Profile() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [newSkill, setNewSkill] = useState({ name: '', level: 'beginner' as Skill['level'] });
  const [editedProfile, setEditedProfile] = useState<Partial<UserProfile>>({});

  // Queries
  const { data: profile, isLoading: profileLoading, error: profileError } = useQuery({
    queryKey: ['profile'],
    queryFn: fetchProfile,
  });

  const { data: skills = [], isLoading: skillsLoading, error: skillsError } = useQuery({
    queryKey: ['skills'],
    queryFn: fetchSkills,
  });

  const { data: subscriptions = [], isLoading: subsLoading, error: subsError } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: fetchSubscriptions,
  });

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setIsEditing(false);
      setEditedProfile({});
    },
  });

  const addSkillMutation = useMutation({
    mutationFn: addSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      setShowAddSkill(false);
      setNewSkill({ name: '', level: 'beginner' });
    },
  });

  const deleteSkillMutation = useMutation({
    mutationFn: deleteSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  const updateSubscriptionMutation = useMutation({
    mutationFn: updateSubscriptionStatus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  useEffect(() => {
    if (profile && isEditing) {
      setEditedProfile({
        name: profile.name,
        email: profile.email,
        phone: profile.phone,
        location: profile.location,
        bio: profile.bio,
      });
    }
  }, [isEditing, profile]);

  const handleSaveProfile = () => {
    updateProfileMutation.mutate(editedProfile);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedProfile({});
  };

  const handleAddSkill = () => {
    if (newSkill.name.trim()) {
      addSkillMutation.mutate(newSkill);
    }
  };

  const handleDeleteSkill = (skillId: string) => {
    if (window.confirm('Are you sure you want to remove this skill?')) {
      deleteSkillMutation.mutate(skillId);
    }
  };

  const handleUpdateSubscription = (id: string, status: Subscription['status']) => {
    updateSubscriptionMutation.mutate({ id, status });
  };

  // Loading state
  if (profileLoading || skillsLoading || subsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (profileError || skillsError || subsError) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 mb-2">
              <X className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-xl font-semibold text-red-900 mb-2">Error Loading Profile</h2>
            <p className="text-red-700 mb-4">
              {(profileError as Error)?.message || (skillsError as Error)?.message || (subsError as Error)?.message || 'Something went wrong'}
            </p>
            <button
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['profile'] });
                queryClient.invalidateQueries({ queryKey: ['skills'] });
                queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
              }}
              className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
          <p className="mt-2 text-gray-600">Manage your personal information and preferences</p>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
            <div className="flex items-center space-x-4 mb-4 sm:mb-0">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                {profile.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{profile.name}</h2>
                <p className="text-gray-500 flex items-center mt-1">
                  <Calendar className="w-4 h-4 mr-1" />
                  Joined {new Date(profile.joinedAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
              </div>
            </div>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <User className="w-4 h-4" />
                <span>Edit Profile</span>
              </button>
            ) : (
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveProfile}
                  disabled={updateProfileMutation.isPending}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{updateProfileMutation.isPending ? 'Saving...' : 'Save'}</span>
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={updateProfileMutation.isPending}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                <User className="w-4 h-4 inline mr-1" />
                Full Name
              </label>
              {isEditing ? (
                <input
                  type="text"
                  id="name"
                  value={editedProfile.name || ''}
                  onChange={(e) => setEditedProfile({ ...editedProfile, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 px-4 py-2">{profile.name}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                <Mail className="w-4 h-4 inline mr-1" />
                Email Address
              </label>
              {isEditing ? (
                <input
                  type="email"
                  id="email"
                  value={editedProfile.email || ''}
                  onChange={(e) => setEditedProfile({ ...editedProfile, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 px-4 py-2">{profile.email}</p>
              )}
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                <Phone className="w-4 h-4 inline mr-1" />
                Phone Number
              </label>
              {isEditing ? (
                <input
                  type="tel"
                  id="phone"
                  value={editedProfile.phone || ''}
                  onChange={(e) => setEditedProfile({ ...editedProfile, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 px-4 py-2">{profile.phone || 'Not provided'}</p>
              )}
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Location
              </label>
              {isEditing ? (
                <input
                  type="text"
                  id="location"
                  value={editedProfile.location || ''}
                  onChange={(e) => setEditedProfile({ ...editedProfile, location: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 px-4 py-2">{profile.location || 'Not provided'}</p>
              )}
            </div>

            <div className="md:col-span-2">
              <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-2">
                Bio
              </label>
              {isEditing ? (
                <textarea
                  id="bio"
                  rows={4}
                  value={editedProfile.bio || ''}
                  onChange={(e) => setEditedProfile({ ...editedProfile, bio: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Tell us about yourself..."
                />
              ) : (
                <p className="text-gray-900 px-4 py-2">{profile.bio || 'No bio provided'}</p>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Skills Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center">
                <BookOpen className="w-5 h-5 mr-2" />
                My Skills
              </h3>
              <button
                onClick={() => setShowAddSkill(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 text-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Add Skill</span>
              </button>
            </div>

            {showAddSkill && (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Skill name"
                    value={newSkill.name}
                    onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <select
                    value={newSkill.level}
                    onChange={(e) => setNewSkill({ ...newSkill, level: e.target.value as Skill['level'] })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleAddSkill}
                      disabled={addSkillMutation.isPending || !newSkill.name.trim()}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      {addSkillMutation.isPending ? 'Adding...' : 'Add'}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddSkill(false);
                        setNewSkill({ name: '', level: 'beginner' });
                      }}
                      className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {skills.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>No skills added yet</p>
                <p className="text-sm mt-1">Start building your skill profile</p>
              </div>
            ) : (
              <div className="space-y-3">
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{skill.name}</h4>
                      <div className="flex items-center mt-1">
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            skill.level === 'beginner'
                              ? 'bg-green-100 text-green-700'
                              : skill.level === 'intermediate'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-purple-100 text-purple-700'
                          }`}
                        >
                          {skill.level.charAt(0).toUpperCase() + skill.level.slice(1)}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteSkill(skill.id)}
                      disabled={deleteSkillMutation.isPending}
                      className="text-red-600 hover:text-red-700 p-2 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                      aria-label="Delete skill"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Subscriptions Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <Bell className="w-5 h-5 mr-2" />
              My Subscriptions
            </h3>

            {subscriptions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>No active subscriptions</p>
                <p className="text-sm mt-1">Browse courses to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {subscriptions.map((sub) => (
                  <div
                    key={sub.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{sub.courseName}</h4>
                        <p className="text-sm text-gray-500 mt-1">
                          Started {new Date(sub.startDate).toLocaleDateString()}
                        </p>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          sub.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : sub.status === 'paused'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {sub.status.charAt(0).toUpperCase() + sub.status.slice(1)}
                      </span>
                    </div>

                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Progress</span>
                        <span className="font-medium text-gray-900">{sub.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${sub.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      {sub.status === 'active' ? (
                        <button
                          onClick={() => handleUpdateSubscription(sub.id, 'paused')}
                          disabled={updateSubscriptionMutation.isPending}
                          className="flex-1 bg-yellow-100 text-yellow-700 px-3 py-1.5 rounded text-sm hover:bg-yellow-200 transition-colors disabled:opacity-50"
                        >
                          Pause
                        </button>
                      ) : sub.status === 'paused' ? (
                        <button
                          onClick={() => handleUpdateSubscription(sub.id, 'active')}
                          disabled={updateSubscriptionMutation.isPending}
                          className="flex-1 bg-green-100 text-green-700 px-3 py-1.5 rounded text-sm hover:bg-green-200 transition-colors disabled:opacity-50"
                        >
                          Resume
                        </button>
                      ) : null}
                      <button
                        className="flex-1 bg-blue-100 text-blue-700 px-3 py-1.5 rounded text-sm hover:bg-blue-200 transition-colors"
                      >
                        View Course
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
