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

interface SkillOption {
  id: string;
  name: string;
  category: string;
}

interface SelectedSkill {
  name: string;
  level: number;
}

interface OnboardingData {
  universityId: string;
  instituteId: string;
  courseId: string;
  studyYear: string;
  interests: string[];
  skills: SelectedSkill[];
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

const fetchSkills = async (): Promise<SkillOption[]> => {
  const response = await apiClient.get('/skills');
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
    studyYear: '',
    interests: [],
    skills: [],
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
        <h2 className="text-2xl font-bold text-gray-900">Выберите университет</h2>
        <p className="mt-2 text-sm text-gray-600">
          Укажите университет, в котором вы сейчас учитесь
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            Не удалось загрузить университеты. Попробуйте еще раз.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Загружаем университеты...</span>
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
          <p className="text-gray-600">Университеты недоступны</p>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Перейти к следующему шагу"
        >
          Продолжить
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
        <h2 className="text-2xl font-bold text-gray-900">Выберите институт</h2>
        <p className="mt-2 text-sm text-gray-600">
          Укажите ваш институт или факультет
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            Не удалось загрузить институты. Попробуйте еще раз.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Загружаем институты...</span>
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
          <p className="text-gray-600">Институты недоступны</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Вернуться к предыдущему шагу"
        >
          Назад
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Перейти к следующему шагу"
        >
          Продолжить
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

  const isValid = data.courseId !== '' && data.studyYear !== '';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Выберите программу</h2>
        <p className="mt-2 text-sm text-gray-600">
          Укажите текущую образовательную программу и курс обучения
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            Не удалось загрузить программы. Попробуйте еще раз.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Загружаем программы...</span>
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
          <p className="text-gray-600">Программы недоступны</p>
        </div>
      )}

      <div>
        <label htmlFor="studyYear" className="block text-sm font-medium text-gray-700">
          Курс обучения
        </label>
        <select
          id="studyYear"
          value={data.studyYear}
          onChange={(e) => onChange('studyYear', e.target.value)}
          className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Выберите курс</option>
          {[1, 2, 3, 4, 5, 6].map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Вернуться к предыдущему шагу"
        >
          Назад
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Перейти к следующему шагу"
        >
          Продолжить
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
        <h2 className="text-2xl font-bold text-gray-900">Выберите интересы</h2>
        <p className="mt-2 text-sm text-gray-600">
          Отметьте одну или несколько тем, которые вам интересны
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            Не удалось загрузить интересы. Попробуйте еще раз.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Загружаем интересы...</span>
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
          <p className="text-gray-600">Интересы недоступны</p>
        </div>
      )}

      {data.interests.length > 0 && (
        <div className="text-sm text-gray-600">
          Выбрано интересов: {data.interests.length}
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Вернуться к предыдущему шагу"
        >
          Назад
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Перейти к следующему шагу"
        >
          Продолжить
        </button>
      </div>
    </div>
  );
};

// Step 5: Skills Selection
const SkillsStep: React.FC<StepProps> = ({ data, onChange, onNext, onBack }) => {
  const { data: skills, isLoading, error, refetch } = useQuery({
    queryKey: ['skills'],
    queryFn: fetchSkills,
  });

  const selected = new Map(data.skills.map((skill) => [skill.name, skill]));
  const toggleSkill = (name: string) => {
    const current = data.skills;
    const updated = selected.has(name)
      ? current.filter((item) => item.name !== name)
      : [...current, { name, level: 3 }];
    onChange('skills', updated);
  };
  const updateLevel = (name: string, level: number) => {
    onChange(
      'skills',
      data.skills.map((item) => (item.name === name ? { ...item, level } : item)),
    );
  };
  const isValid = data.skills.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Выберите навыки</h2>
        <p className="mt-2 text-sm text-gray-600">
          Укажите навыки, которые уже умеете применять в проектах
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <p className="text-sm text-red-800">
            Не удалось загрузить навыки. Попробуйте еще раз.
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Повторить
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" role="status">
            <span className="sr-only">Загружаем навыки...</span>
          </div>
        </div>
      ) : skills && skills.length > 0 ? (
        <div className="space-y-3">
          {skills.map((skill) => {
            const value = selected.get(skill.name);
            return (
              <div
                key={skill.id}
                className={`rounded-lg border-2 p-4 ${
                  value ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <button
                    type="button"
                    onClick={() => toggleSkill(skill.name)}
                    className="text-left font-medium text-gray-900"
                    aria-pressed={Boolean(value)}
                  >
                    {skill.name}
                  </button>
                  {value && (
                    <select
                      value={value.level}
                      onChange={(e) => updateLevel(skill.name, Number(e.target.value))}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                      aria-label={`Уровень навыка ${skill.name}`}
                    >
                      <option value={2}>Начальный</option>
                      <option value={3}>Средний</option>
                      <option value={4}>Продвинутый</option>
                      <option value={5}>Экспертный</option>
                    </select>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-md bg-gray-50 p-8 text-center">
          <p className="text-gray-600">Навыки недоступны</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Назад
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!isValid}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Продолжить
        </button>
      </div>
    </div>
  );
};

// Step 6: Career Goal
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
        <h2 className="text-2xl font-bold text-gray-900">Какая у вас карьерная цель?</h2>
        <p className="mt-2 text-sm text-gray-600">
          Расскажите, к какой роли или профессиональному результату хотите прийти
        </p>
      </div>

      <div>
        <label htmlFor="careerGoal" className="block text-sm font-medium text-gray-700">
          Карьерная цель
        </label>
        <textarea
          id="careerGoal"
          rows={6}
          value={data.careerGoal}
          onChange={(e) => onChange('careerGoal', e.target.value)}
          placeholder="Например: хочу стать бэкенд-разработчиком и работать над сервисами для студентов..."
          className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-describedby="careerGoalHelp"
        />
        <p id="careerGoalHelp" className="mt-2 text-sm text-gray-500">
          Опишите цель, а мы поможем подобрать релевантные возможности
        </p>
      </div>

      <div className="flex justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Вернуться к предыдущему шагу"
        >
          Назад
        </button>
        <button
          type="submit"
          disabled={!isValid || isSubmitting}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Отправляем...</span>
            </>
          ) : (
            'Завершить анкету'
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
    { number: 1, label: 'Университет' },
    { number: 2, label: 'Институт' },
    { number: 3, label: 'Программа' },
    { number: 4, label: 'Интересы' },
    { number: 5, label: 'Навыки' },
    { number: 6, label: 'Цель' },
  ];

  return (
    <nav aria-label="Прогресс" className="mb-8">
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
    setCurrentStep((prev) => Math.min(prev + 1, 6));
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
          <h1 className="text-3xl font-bold text-gray-900">Добро пожаловать в UniPath MAX</h1>
          <p className="mt-2 text-gray-600">
            Настроим профиль за несколько шагов
          </p>
        </div>

        <ProgressIndicator currentStep={currentStep} totalSteps={6} />

        <div className="rounded-lg bg-white p-6 shadow-md sm:p-8">
          <form onSubmit={handleSubmit}>
            {mutation.error && (
              <div className="mb-6 rounded-md bg-red-50 p-4" role="alert">
                <p className="text-sm text-red-800">
                  Не удалось отправить анкету. Попробуйте еще раз.
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
              <SkillsStep {...stepProps} isFirst={false} isLast={false} />
            )}
            {currentStep === 6 && (
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
          Шаг {currentStep} из 6
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
