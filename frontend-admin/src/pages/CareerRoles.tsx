import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Compass, Edit, Plus, Search, Trash2, X } from 'lucide-react';
import { CareerRoleFormValues, createCareerRole, deleteCareerRole, fetchCareerRoles, updateCareerRole } from '@/api/endpoints';
import type { CareerRole, DemandLevel } from '@/types';
import { Badge, Button, Card, ConfirmDialog, EmptyState, ErrorState, Input, LoadingState, Select, Sheet, Switch, Textarea, useToast } from '@/ui';

const demandOptions: { value: DemandLevel; label: string }[] = [
  { value: 'high', label: 'Высокий спрос' },
  { value: 'medium', label: 'Средний спрос' },
  { value: 'low', label: 'Низкий спрос' },
];
const demandTone: Record<DemandLevel, 'success' | 'warning' | 'neutral'> = { high: 'success', medium: 'warning', low: 'neutral' };

interface FormState {
  title: string;
  description: string;
  avgSalary: string;
  demandLevel: DemandLevel;
  active: boolean;
  educationPathText: string;
  skillsText: string;
}

function toFormState(role?: CareerRole): FormState {
  return {
    title: role?.title || '',
    description: role?.description || '',
    avgSalary: role?.avgSalary || '',
    demandLevel: role?.demandLevel || 'medium',
    active: role?.active ?? true,
    educationPathText: (role?.educationPath || []).join('\n'),
    skillsText: (role?.skills || []).join(', '),
  };
}

function toPayload(form: FormState): CareerRoleFormValues {
  return {
    title: form.title,
    description: form.description,
    avgSalary: form.avgSalary,
    demandLevel: form.demandLevel,
    active: form.active,
    educationPath: form.educationPathText.split('\n').map((s) => s.trim()).filter(Boolean),
    skills: form.skillsText.split(',').map((s) => s.trim()).filter(Boolean).map((name) => ({ name, level: 3 })),
  };
}

export const CareerRoles = () => {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['admin-career-roles'], queryFn: fetchCareerRoles });

  const [search, setSearch] = useState('');
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<CareerRole | null>(null);
  const [form, setForm] = useState<FormState>(toFormState());
  const [deleteTarget, setDeleteTarget] = useState<CareerRole | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return q ? data.filter((r) => r.title.toLowerCase().includes(q)) : data;
  }, [data, search]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-career-roles'] });

  const createMutation = useMutation({
    mutationFn: (payload: CareerRoleFormValues) => createCareerRole(payload),
    onSuccess: () => { toast.success('Карьерная роль создана'); setSheetOpen(false); invalidate(); },
    onError: () => toast.error('Не удалось сохранить роль'),
  });
  const updateMutation = useMutation({
    mutationFn: (payload: CareerRoleFormValues) => updateCareerRole(editing!.id, payload),
    onSuccess: () => { toast.success('Изменения сохранены'); setSheetOpen(false); invalidate(); },
    onError: () => toast.error('Не удалось сохранить изменения'),
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCareerRole(id),
    onSuccess: () => { toast.success('Роль удалена'); setDeleteTarget(null); invalidate(); },
    onError: () => toast.error('Не удалось удалить роль'),
  });

  const openCreate = () => { setEditing(null); setForm(toFormState()); setSheetOpen(true); };
  const openEdit = (role: CareerRole) => { setEditing(role); setForm(toFormState(role)); setSheetOpen(true); };
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = toPayload(form);
    if (editing) updateMutation.mutate(payload);
    else createMutation.mutate(payload);
  };
  const saving = createMutation.isPending || updateMutation.isPending;

  if (isLoading) return <LoadingState label="Загружаем карьерные роли…" />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Карьерные роли</h1>
          <p className="mt-1 text-sm text-ink-500">Целевые роли, навыки и требуемые уровни для Career GPS.</p>
        </div>
        <Button onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить роль</Button>
      </div>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Искать роль…"
          className="w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Compass className="h-6 w-6 text-ink-400" />}
          title={search ? 'Ничего не найдено' : 'Карьерных ролей пока нет'}
          message={search ? undefined : 'Добавьте роль, чтобы студенты видели маршрут Career GPS.'}
          action={!search && <Button size="sm" onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить роль</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((role) => (
            <Card key={role.id}>
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="text-base font-semibold text-ink-900">{role.title}</h3>
                <div className="flex shrink-0 gap-1">
                  <button onClick={() => openEdit(role)} className="rounded-lg p-1.5 text-brand-600 hover:bg-brand-50" aria-label="Редактировать"><Edit className="h-4 w-4" /></button>
                  <button onClick={() => setDeleteTarget(role)} className="rounded-lg p-1.5 text-rose-600 hover:bg-rose-50" aria-label="Удалить"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
              <div className="mb-2 flex flex-wrap gap-1.5">
                <Badge tone={demandTone[role.demandLevel]}>{demandOptions.find((d) => d.value === role.demandLevel)?.label}</Badge>
                {!role.active && <Badge tone="neutral">Неактивна</Badge>}
              </div>
              {role.avgSalary && <p className="mb-2 text-sm font-semibold text-ink-700">{role.avgSalary}</p>}
              <p className="mb-3 line-clamp-3 text-sm text-ink-600">{role.description}</p>
              {role.skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {role.skills.slice(0, 5).map((s) => <Badge key={s} tone="brand" size="sm">{s}</Badge>)}
                  {role.skills.length > 5 && <Badge tone="neutral" size="sm">+{role.skills.length - 5}</Badge>}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title={editing ? 'Редактировать роль' : 'Новая карьерная роль'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Название" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Средняя зарплата" value={form.avgSalary} onChange={(e) => setForm({ ...form, avgSalary: e.target.value })} placeholder="120 000 – 180 000 ₽" />
            <Select label="Уровень спроса" value={form.demandLevel} onChange={(e) => setForm({ ...form, demandLevel: e.target.value as DemandLevel })}>
              {demandOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </Select>
          </div>
          <Textarea label="Описание" required rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Input
            label="Ключевые навыки"
            hint="Через запятую — используются для расчёта готовности в Career GPS"
            value={form.skillsText}
            onChange={(e) => setForm({ ...form, skillsText: e.target.value })}
            placeholder="Python, Django, SQL"
          />
          <Textarea
            label="Путь к профессии"
            hint="По одному шагу в строке — показывается студентам"
            rows={3}
            value={form.educationPathText}
            onChange={(e) => setForm({ ...form, educationPathText: e.target.value })}
            placeholder={'Освоить основы Python\nСделать pet-проект\nПодать заявку на стажировку'}
          />
          <Switch checked={form.active} onChange={(v) => setForm({ ...form, active: v })} label="Роль активна" hint="Видна студентам при выборе карьерной цели" />

          <div className="flex gap-2 pt-2">
            <Button type="submit" loading={saving} fullWidth>{editing ? 'Сохранить' : 'Создать'}</Button>
            <Button type="button" variant="outline" onClick={() => setSheetOpen(false)}><X className="h-4 w-4" /></Button>
          </div>
        </form>
      </Sheet>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="Удалить карьерную роль?"
        description={deleteTarget ? `«${deleteTarget.title}» будет удалена безвозвратно.` : undefined}
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
