import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, ShieldCheck, ShieldOff, Users as UsersIcon } from 'lucide-react';
import { fetchStudentProfile, fetchUsers, setUserActive } from '@/api/endpoints';
import { useAuthUser } from '@/contexts/AuthContext';
import { adminQueryKey } from '@/lib/adminQueryScope';
import { Badge, Card, EmptyState, ErrorState, LoadingState, Sheet, useToast } from '@/ui';

const roleLabels: Record<string, string> = {
  admin: 'Администратор',
  university_admin: 'Администратор вуза',
  institute_admin: 'Администратор института',
  editor: 'Редактор',
  student: 'Студент',
  mentor: 'Ментор',
  organizer: 'Организатор',
};

export const Users = () => {
  const [search, setSearch] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const user = useAuthUser();
  const queryClient = useQueryClient();
  const toast = useToast();
  const usersKey = adminQueryKey(user, 'users', search);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: usersKey,
    queryFn: () => fetchUsers(search || undefined),
  });
  const profileQuery = useQuery({
    queryKey: adminQueryKey(user, 'student-profile', selectedStudent),
    queryFn: () => fetchStudentProfile(selectedStudent!),
    enabled: selectedStudent !== null,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) => setUserActive(id, active),
    onSuccess: (_, vars) => {
      toast.success(vars.active ? 'Пользователь активирован' : 'Пользователь деактивирован');
      queryClient.invalidateQueries({ queryKey: adminQueryKey(user, 'users') });
    },
    onError: () => toast.error('Не удалось изменить статус пользователя'),
  });

  if (isLoading) return <LoadingState label="Загружаем пользователей…" />;
  if (isError || !data) {
    return (
      <ErrorState
        title="Не удалось загрузить пользователей"
        message="Возможно, у вашей роли нет доступа к этому разделу — он доступен только администраторам платформы."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Пользователи</h1>
        <p className="mt-1 text-sm text-ink-500">Все аккаунты вашего университета: студенты, редакторы, администраторы.</p>
      </div>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Искать по имени или почте…"
          className="w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {data.results.length === 0 ? (
        <EmptyState icon={<UsersIcon className="h-6 w-6 text-ink-400" />} title="Пользователи не найдены" />
      ) : (
        <Card padding="none" className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-ink-100 bg-ink-50/60 text-left text-xs font-semibold uppercase tracking-wide text-ink-500">
              <tr>
                <th className="px-5 py-3">Пользователь</th>
                <th className="hidden px-5 py-3 sm:table-cell">Роль</th>
                <th className="hidden px-5 py-3 md:table-cell">Университет</th>
                <th className="px-5 py-3">Статус</th>
                <th className="px-5 py-3 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {data.results.map((user) => (
                <tr key={user.id} className="hover:bg-ink-50/50">
                  <td className="px-5 py-3.5">
                    {user.role === 'student' ? (
                      <button className="text-left font-medium text-brand-700 hover:underline" onClick={() => setSelectedStudent(user.id)}>
                        {user.full_name || user.email}
                      </button>
                    ) : <p className="font-medium text-ink-900">{user.full_name || user.email}</p>}
                    <p className="text-xs text-ink-400">{user.email}</p>
                  </td>
                  <td className="hidden px-5 py-3.5 text-ink-600 sm:table-cell">{roleLabels[user.role] || user.role}</td>
                  <td className="hidden px-5 py-3.5 text-ink-600 md:table-cell">{user.university || '—'}</td>
                  <td className="px-5 py-3.5">
                    <Badge tone={user.is_active ? 'success' : 'neutral'}>{user.is_active ? 'Активен' : 'Отключён'}</Badge>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {user.role === 'student' && (
                      <button onClick={() => setSelectedStudent(user.id)} className="mr-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-50">
                        Профиль
                      </button>
                    )}
                    <button
                      onClick={() => toggleMutation.mutate({ id: user.id, active: !user.is_active })}
                      disabled={toggleMutation.isPending}
                      className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-ink-600 hover:bg-ink-100 disabled:opacity-50"
                    >
                      {user.is_active ? <ShieldOff className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                      {user.is_active ? 'Отключить' : 'Включить'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      <Sheet open={selectedStudent !== null} onClose={() => setSelectedStudent(null)} title="Профиль студента">
        {profileQuery.isLoading ? <LoadingState label="Загружаем профиль…" /> : profileQuery.isError || !profileQuery.data ? (
          <ErrorState title="Не удалось загрузить профиль" onRetry={() => profileQuery.refetch()} />
        ) : (
          <div className="space-y-5 text-sm">
            <section>
              <h3 className="font-semibold text-ink-900">{profileQuery.data.user.full_name}</h3>
              <p className="text-ink-500">{profileQuery.data.user.email}</p>
              <p className="mt-1 text-ink-600">{profileQuery.data.user.university || 'Университет не указан'} · MAX {profileQuery.data.user.max_linked ? 'связан' : 'не связан'}</p>
            </section>
            {profileQuery.data.profile ? (
              <>
                <section className="space-y-1">
                  <h3 className="font-semibold text-ink-900">Обучение и цель</h3>
                  <p>{[profileQuery.data.profile.institute, profileQuery.data.profile.program, profileQuery.data.profile.study_year && `${profileQuery.data.profile.study_year} курс`].filter(Boolean).join(' · ') || 'Данные об обучении не заполнены'}</p>
                  <p>Карьерная цель: {profileQuery.data.profile.career_goal || 'не указана'}</p>
                  <p>Анкета: {profileQuery.data.profile.onboarding_completed ? 'заполнена' : 'не завершена'}</p>
                </section>
                <section>
                  <h3 className="mb-2 font-semibold text-ink-900">Интересы</h3>
                  <p>{profileQuery.data.profile.interests.join(', ') || 'Не указаны'}</p>
                </section>
              </>
            ) : <p className="text-ink-500">Студент ещё не заполнил профиль.</p>}
            <section>
              <h3 className="mb-2 font-semibold text-ink-900">Навыки</h3>
              {profileQuery.data.skills.length ? <ul className="space-y-1">{profileQuery.data.skills.map((skill) => <li key={skill.name}>{skill.name} · {skill.level}/5{skill.verified ? ' · подтверждён' : ''}</li>)}</ul> : <p className="text-ink-500">Навыки не указаны</p>}
            </section>
            <section>
              <h3 className="mb-2 font-semibold text-ink-900">Подписки на возможности</h3>
              {profileQuery.data.subscriptions.length ? <ul className="space-y-1">{profileQuery.data.subscriptions.map((sub) => <li key={sub.id}>{sub.topic} · {sub.active ? 'активна' : 'приостановлена'}</li>)}</ul> : <p className="text-ink-500">Подписок нет</p>}
            </section>
          </div>
        )}
      </Sheet>
    </div>
  );
};
