import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/lib/api';

// Types
interface University {
  id: string;
  name: string;
}

interface Institute {
  id: string;
  name: string;
  universityId: string;
}

interface Course {
  id: string;
  name: string;
  instituteId: string;
}

interface Interest {
  id: string;
  name: string;
}

interface OnboardingData {
  universityId: string;
  instituteId: string;
  courseId: string;
  interests: string[];
  careerGoal: string;
}

interface StepProps {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
  isFirst: boolean;
  isLast: boolean;
}

// API functions
const fetchUniversities = async (): Promise<University[]> => {
  const response = await apiClient.get('/universities');
  return response.data;
};

const fetchInstitutes = async (universityId: string): Promise<Institute[]> => {
  const response = await apiClient.get(`/institutes?universityId=${universityId}`);
  return response.data;
};

const fetchCourses = async (instituteId: string): Promise<Course[]> => {
  const response = await apiClient.get(`/courses?instituteId=${instituteId}`);
  return response.data.map((course: { id: number; title: string }) => ({
    id: String(course.id),
    name: course.title,
    instituteId,
  }));
};

const fetchInterests = async (): Promise<Interest[]> => {
  const response = await apiClient.get('/interests');
  return response.data;
};

const submitOnboarding = async (data: OnboardingData): Promise<void> => {
  await apiClient.post('/onboarding', data);
};

// Custom hook for onboarding state
const useOnboardingState = () => {
  const [data, setData] = useState<OnboardingData>({
    universityId: '',
    instituteId: '',
    courseId: '',
    interests: [],
    careerGoal: '',
  });

  const updateField = (field: keyof OnboardingData, value: any) => {
    setData((prev) => {
      const updated = { ...prev, [field]: value };

      // Reset dependent fields
      if (field === 'universityId') {
        updated.instituteId = '';
        updated.courseId = '';
      } else if (field === 'instituteId') {
        updated.courseId = '';
      }

      return updated;
    });
  };

  return { data, updateField };
};

// Step 1: University Selection
const UniversityStep: React.FC<StepProps> = ({ data, onChange, onNext }) => {
  const { data: universities, isLoading, error } = useQuery({
    queryKey: ['universities'],
    queryFn: fetchUniversities,
  });

  const isValid = data.universityId !== '';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Select Your University</h2>
        <p className="mt-2 text-sm text-gray-600">
          Choose the university where you are currently studying
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Loading universities...</span>
          </div>
        </div>
      ) : universities && universities.length > 0 ? (
        <div className="space-y-3">
          {universities.map((university) => (
            <button
              key={university.id}
              type="button"
              onClick={() => onChange('universityId', university.id)}
              className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                data.universityId === university.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              aria-pressed={data.universityId === university.id}
            >
              <span className="font-medium text-gray-900">{university.name}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-md bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No universities available</p>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Continue to next step"
        >
          Continue
        </button>
      </div>
    </div>
  );
};

// Step 2: Institute Selection
const InstituteStep: React.FC<StepProps> = ({ data, onChange, onNext, onBack }) => {
  const { data: institutes, isLoading, error } = useQuery({
    queryKey: ['institutes', data.universityId],
    queryFn: () => fetchInstitutes(data.universityId),
    enabled: !!data.universityId,
  });

  const isValid = data.instituteId !== '';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Select Your Institute</h2>
        <p className="mt-2 text-sm text-gray-600">
          Choose your institute or faculty
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Loading institutes...</span>
          </div>
        </div>
      ) : institutes && institutes.length > 0 ? (
        <div className="space-y-3">
          {institutes.map((institute) => (
            <button
              key={institute.id}
              type="button"
              onClick={() => onChange('instituteId', institute.id)}
              className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                data.instituteId === institute.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              aria-pressed={data.instituteId === institute.id}
            >
              <span className="font-medium text-gray-900">{institute.name}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-md bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No institutes available</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Go back to previous step"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Continue to next step"
        >
          Continue
        </button>
      </div>
    </div>
  );
};

// Step 3: Course Selection
const CourseStep: React.FC<StepProps> = ({ data, onChange, onNext, onBack }) => {
  const { data: courses, isLoading, error } = useQuery({
    queryKey: ['courses', data.instituteId],
    queryFn: () => fetchCourses(data.instituteId),
    enabled: !!data.instituteId,
  });

  const isValid = data.courseId !== '';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Select Your Course</h2>
        <p className="mt-2 text-sm text-gray-600">
          Choose your current program or course of study
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Loading courses...</span>
          </div>
        </div>
      ) : courses && courses.length > 0 ? (
        <div className="space-y-3">
          {courses.map((course) => (
            <button
              key={course.id}
              type="button"
              onClick={() => onChange('courseId', course.id)}
              className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                data.courseId === course.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              aria-pressed={data.courseId === course.id}
            >
              <span className="font-medium text-gray-900">{course.name}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-md bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No courses available</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Go back to previous step"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Continue to next step"
        >
          Continue
        </button>
      </div>
    </div>
  );
};

// Step 4: Interests Selection
const InterestsStep: React.FC<StepProps> = ({ data, onChange, onNext, onBack }) => {
  const { data: interests, isLoading, error } = useQuery({
    queryKey: ['interests'],
    queryFn: fetchInterests,
  });

  const toggleInterest = (interestId: string) => {
    const current = data.interests;
    const updated = current.includes(interestId)
      ? current.filter((id) => id !== interestId)
      : [...current, interestId];
    onChange('interests', updated);
  };

  const isValid = data.interests.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Select Your Interests</h2>
        <p className="mt-2 text-sm text-gray-600">
          Choose one or more areas you are interested in
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Loading interests...</span>
          </div>
        </div>
      ) : interests && interests.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {interests.map((interest) => {
            const isSelected = data.interests.includes(interest.id);
            return (
              <button
                key={interest.id}
                type="button"
                onClick={() => toggleInterest(interest.id)}
                className={`rounded-lg border-2 p-4 text-left transition-colors ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                aria-pressed={isSelected}
              >
                <span className="font-medium text-gray-900">{interest.name}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="rounded-md bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No interests available</p>
        </div>
      )}

      {data.interests.length > 0 && (
        <div className="text-sm text-gray-600">
          {data.interests.length} {data.interests.length === 1 ? 'interest' : 'interests'} selected
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Go back to previous step"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Continue to next step"
        >
          Continue
        </button>
      </div>
    </div>
  );
};

// Step 5: Career Goal
const CareerGoalStep: React.FC<StepProps & { isSubmitting: boolean }> = ({
  data,
  onChange,
  onBack,
  isSubmitting,
}) => {
  const isValid = data.careerGoal.trim().length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">What is Your Career Goal?</h2>
        <p className="mt-2 text-sm text-gray-600">
          Tell us about your career aspirations and what you hope to achieve
        </p>
      </div>

      <div>
        <label htmlFor="careerGoal" className="block text-sm font-medium text-gray-700">
          Career Goal
        </label>
        <textarea
          id="careerGoal"
          rows={6}
          value={data.careerGoal}
          onChange={(e) => onChange('careerGoal', e.target.value)}
          placeholder="E.g., I want to become a software engineer at a leading tech company..."
          className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-describedby="careerGoalHelp"
        />
        <p id="careerGoalHelp" className="mt-2 text-sm text-gray-500">
          Share your goals and we will help match you with relevant opportunities
        </p>
      </div>

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Go back to previous step"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!isValid || isSubmitting}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Submitting...</span>
            </>
          ) : (
            'Complete Onboarding'
          )}
        </button>
      </div>
    </div>
  );
};

// Progress Indicator
interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStep, totalSteps }) => {
  const steps = [
    { number: 1, label: 'University' },
    { number: 2, label: 'Institute' },
    { number: 3, label: 'Course' },
    { number: 4, label: 'Interests' },
    { number: 5, label: 'Career Goal' },
  ];

  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;

          return (
            <li key={step.number} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold ${
                    isCompleted
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : isCurrent
                      ? 'border-blue-600 bg-white text-blue-600'
                      : 'border-gray-300 bg-white text-gray-500'
                  }`}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  {isCompleted ? (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={`mt-2 hidden text-xs font-medium sm:block ${
                    isCurrent ? 'text-gray-900' : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`mx-2 h-0.5 flex-1 ${
                    isCompleted ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

// Main Component
const Onboarding: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const { data, updateField } = useOnboardingState();

  const mutation = useMutation({
    mutationFn: submitOnboarding,
    onSuccess: () => {
      navigate('/dashboard');
    },
  });

  const handleNext = () => {
    setCurrentStep((prev) => Math.min(prev + 1, 5));
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(data);
  };

  const stepProps: Omit<StepProps, 'isFirst' | 'isLast'> = {
    data,
    onChange: updateField,
    onNext: handleNext,
    onBack: handleBack,
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to the Platform</h1>
          <p className="mt-2 text-gray-600">
            Let's get you set up in just a few steps
          </p>
        </div>

        <ProgressIndicator currentStep={currentStep} totalSteps={5} />

        <div className="rounded-lg bg-white p-6 shadow-md sm:p-8">
          <form onSubmit={handleSubmit}>
            {mutation.error && (
              <div className="mb-6 rounded-md bg-red-50 p-4" role="alert">
                <p className="text-sm text-red-800">
                  {mutation.error instanceof Error
                    ? mutation.error.message
                    : 'Failed to submit onboarding'}
                </p>
              </div>
            )}

            {currentStep === 1 && (
              <UniversityStep {...stepProps} isFirst={true} isLast={false} />
            )}
            {currentStep === 2 && (
              <InstituteStep {...stepProps} isFirst={false} isLast={false} />
            )}
            {currentStep === 3 && (
              <CourseStep {...stepProps} isFirst={false} isLast={false} />
            )}
            {currentStep === 4 && (
              <InterestsStep {...stepProps} isFirst={false} isLast={false} />
            )}
            {currentStep === 5 && (
              <CareerGoalStep
                {...stepProps}
                isFirst={false}
                isLast={true}
                isSubmitting={mutation.isPending}
              />
            )}
          </form>
        </div>

        <div className="mt-6 text-center text-sm text-gray-500">
          Step {currentStep} of 5
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
