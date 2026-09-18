import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Briefcase, Calendar, Edit, ExternalLink, Plus, Search, Trash2, X } from 'lucide-react';
import { createOpportunity, deleteOpportunity, fetchOpportunities, OpportunityFormValues, updateOpportunity } from '@/api/endpoints';
import type { Opportunity, OpportunityVerifiedStatus } from '@/types';
import { Badge, Button, Card, ConfirmDialog, EmptyState, ErrorState, Input, LoadingState, Select, Sheet, Switch, Textarea, useToast } from '@/ui';

const typeOptions = [
  { value: 'internship', label: 'Стажировка' },
  { value: 'vacancy', label: 'Вакансия' },
  { value: 'project', label: 'Проект' },
  { value: 'hackathon', label: 'Хакатон' },
  { value: 'event', label: 'Событие' },
  { value: 'course', label: 'Курс' },
];
const typeLabels = Object.fromEntries(typeOptions.map((o) => [o.value, o.label]));

const verifiedOptions: { value: OpportunityVerifiedStatus; label: string }[] = [
  { value: 'pending', label: 'На проверке' },
  { value: 'verified', label: 'Подтверждено' },
  { value: 'rejected', label: 'Отклонено' },
];
const verifiedTone: Record<OpportunityVerifiedStatus, 'neutral' | 'success' | 'danger'> = {
  pending: 'neutral',
  verified: 'success',
  rejected: 'danger',
};

const emptyForm: OpportunityFormValues = {
  title: '',
  description: '',
  type: 'internship',
  company: '',
  location: '',
  remote: false,
  requirements: [],
  deadline: null,
  sourceUrl: '',
  verifiedStatus: 'verified',
  published: true,
  skills: [],
};

interface FormState {
  title: string;
  description: string;
  type: string;
  company: string;
  location: string;
  remote: boolean;
  requirements: string;
  deadline: string;
  sourceUrl: string;
  verifiedStatus: string;
  published: boolean;
  skillsText: string;
}

function toFormState(o?: Opportunity): FormState {
  return {
    title: o?.title || '',
    description: o?.description || '',
    type: o?.type || 'internship',
    company: o?.company || '',
    location: o?.location || '',
    remote: o?.remote || false,
    requirements: (o?.requirements || []).join('\n'),
    deadline: o?.deadline ? o.deadline.slice(0, 10) : '',
    sourceUrl: o?.sourceUrl || '',
    verifiedStatus: o?.verifiedStatus || 'verified',
    published: o?.published ?? true,
    skillsText: (o?.skills || []).map((s) => s.name).join(', '),
  };
}

function toPayload(form: FormState): OpportunityFormValues {
  return {
    ...emptyForm,
    title: form.title,
    description: form.description,
    type: form.type,
    company: form.company,
    location: form.location,
    remote: form.remote,
    requirements: form.requirements.split('\n').map((s) => s.trim()).filter(Boolean),
    deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
    sourceUrl: form.sourceUrl,
    verifiedStatus: form.verifiedStatus,
    published: form.published,
    skills: form.skillsText.split(',').map((s) => s.trim()).filter(Boolean).map((name) => ({ name, level: 3 })),
  };
}

export function Opportunities() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['admin-opportunities'], queryFn: fetchOpportunities });

  const [search, setSearch] = useState('');
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<Opportunity | null>(null);
  const [form, setForm] = useState<FormState>(toFormState());
  const [deleteTarget, setDeleteTarget] = useState<Opportunity | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    if (!q) return data;
    return data.filter((o) => o.title.toLowerCase().includes(q) || o.company.toLowerCase().includes(q));
  }, [data, search]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-opportunities'] });

  const createMutation = useMutation({
    mutationFn: (payload: OpportunityFormValues) => createOpportunity(payload),
    onSuccess: () => {
      toast.success('Возможность создана');
      setSheetOpen(false);
      invalidate();
    },
    onError: () => toast.error('Не удалось сохранить возможность'),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: OpportunityFormValues) => updateOpportunity(editing!.id, payload),
    onSuccess: () => {
      toast.success('Изменения сохранены');
      setSheetOpen(false);
      invalidate();
    },
    onError: () => toast.error('Не удалось сохранить изменения'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteOpportunity(id),
    onSuccess: () => {
      toast.success('Возможность удалена');
      setDeleteTarget(null);
      invalidate();
    },
    onError: () => toast.error('Не удалось удалить возможность'),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(toFormState());
    setSheetOpen(true);
  };
  const openEdit = (o: Opportunity) => {
    setEditing(o);
    setForm(toFormState(o));
    setSheetOpen(true);
  };
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = toPayload(form);
    if (editing) updateMutation.mutate(payload);
    else createMutation.mutate(payload);
  };
  const saving = createMutation.isPending || updateMutation.isPending;

  if (isLoading) return <LoadingState label="Загружаем возможности…" />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Возможности</h1>
          <p className="mt-1 text-sm text-ink-500">Стажировки, проекты, хакатоны и события для студентов.</p>
        </div>
        <Button onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить возможность</Button>
      </div>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Искать по названию или организации…"
          className="w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="h-6 w-6 text-ink-400" />}
          title={search ? 'Ничего не найдено' : 'Возможностей пока нет'}
          message={search ? 'Попробуйте изменить запрос.' : 'Добавьте первую стажировку, проект или событие.'}
          action={!search && <Button size="sm" onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить возможность</Button>}
        />
      ) : (
        <>
          {/* Desktop table */}
          <Card padding="none" className="hidden overflow-hidden lg:block">
            <table className="w-full text-sm">
              <thead className="border-b border-ink-100 bg-ink-50/60 text-left text-xs font-semibold uppercase tracking-wide text-ink-500">
                <tr>
                  <th className="px-5 py-3">Название</th>
                  <th className="px-5 py-3">Тип</th>
                  <th className="px-5 py-3">Дедлайн</th>
                  <th className="px-5 py-3">Проверка</th>
                  <th className="px-5 py-3">Публикация</th>
                  <th className="px-5 py-3 text-right">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {filtered.map((o) => (
                  <tr key={o.id} className="hover:bg-ink-50/50">
                    <td className="px-5 py-3.5">
                      <p className="font-medium text-ink-900">{o.title}</p>
                      <p className="text-xs text-ink-400">{o.company}</p>
                    </td>
                    <td className="px-5 py-3.5"><Badge tone="brand">{typeLabels[o.type] || o.type}</Badge></td>
                    <td className="px-5 py-3.5 text-ink-600">{o.deadline ? new Date(o.deadline).toLocaleDateString('ru-RU') : '—'}</td>
                    <td className="px-5 py-3.5"><Badge tone={verifiedTone[o.verifiedStatus]}>{verifiedOptions.find((v) => v.value === o.verifiedStatus)?.label}</Badge></td>
                    <td className="px-5 py-3.5"><Badge tone={o.published ? 'success' : 'neutral'}>{o.published ? 'Опубликовано' : 'Не опубликовано'}</Badge></td>
                    <td className="px-5 py-3.5">
                      <div className="flex justify-end gap-1">
                        {o.sourceUrl && (
                          <a href={o.sourceUrl} target="_blank" rel="noopener noreferrer" className="rounded-lg p-2 text-ink-400 hover:bg-ink-100 hover:text-ink-700" aria-label="Открыть источник">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <button onClick={() => openEdit(o)} className="rounded-lg p-2 text-brand-600 hover:bg-brand-50" aria-label="Редактировать"><Edit className="h-4 w-4" /></button>
                        <button onClick={() => setDeleteTarget(o)} className="rounded-lg p-2 text-rose-600 hover:bg-rose-50" aria-label="Удалить"><Trash2 className="h-4 w-4" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* Mobile cards */}
          <div className="grid grid-cols-1 gap-4 lg:hidden">
            {filtered.map((o) => (
              <Card key={o.id}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-ink-900">{o.title}</p>
                    <p className="text-xs text-ink-400">{o.company}</p>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => openEdit(o)} className="rounded-lg p-1.5 text-brand-600 hover:bg-brand-50" aria-label="Редактировать"><Edit className="h-4 w-4" /></button>
                    <button onClick={() => setDeleteTarget(o)} className="rounded-lg p-1.5 text-rose-600 hover:bg-rose-50" aria-label="Удалить"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <Badge tone="brand">{typeLabels[o.type] || o.type}</Badge>
                  <Badge tone={verifiedTone[o.verifiedStatus]}>{verifiedOptions.find((v) => v.value === o.verifiedStatus)?.label}</Badge>
                  <Badge tone={o.published ? 'success' : 'neutral'}>{o.published ? 'Опубликовано' : 'Не опубликовано'}</Badge>
                </div>
                {o.deadline && (
                  <p className="mt-2 flex items-center gap-1 text-xs text-ink-400">
                    <Calendar className="h-3.5 w-3.5" /> до {new Date(o.deadline).toLocaleDateString('ru-RU')}
                  </p>
                )}
              </Card>
            ))}
          </div>
        </>
      )}

      <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title={editing ? 'Редактировать возможность' : 'Новая возможность'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Название" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Тип" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {typeOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </Select>
            <Input label="Дедлайн" type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Организация" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <Input label="Локация" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          </div>
          <Switch checked={form.remote} onChange={(v) => setForm({ ...form, remote: v })} label="Удалённый формат" />
          <Textarea label="Описание" required rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Textarea
            label="Требования"
            hint="По одному пункту в строке"
            rows={3}
            value={form.requirements}
            onChange={(e) => setForm({ ...form, requirements: e.target.value })}
          />
          <Input
            label="Ключевые навыки"
            hint="Через запятую — используются для подбора и оценки совпадения"
            value={form.skillsText}
            onChange={(e) => setForm({ ...form, skillsText: e.target.value })}
            placeholder="Python, Docker, SQL"
          />
          <Input label="Ссылка на источник / отклик" value={form.sourceUrl} onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })} placeholder="https://…" />
          <Select label="Статус проверки" value={form.verifiedStatus} onChange={(e) => setForm({ ...form, verifiedStatus: e.target.value })}>
            {verifiedOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </Select>
          <Switch checked={form.published} onChange={(v) => setForm({ ...form, published: v })} label="Опубликовано" hint="Видно студентам, если также подтверждено" />

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
        title="Удалить возможность?"
        description={deleteTarget ? `«${deleteTarget.title}» будет удалена безвозвратно.` : undefined}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
