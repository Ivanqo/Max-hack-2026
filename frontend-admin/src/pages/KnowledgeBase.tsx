import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Edit, ExternalLink, Plus, Search, Trash2, X } from 'lucide-react';
import { createKnowledgeItem, deleteKnowledgeItem, fetchKnowledgeItems, KnowledgeFormValues, updateKnowledgeItem } from '@/api/endpoints';
import type { KnowledgeBase as KnowledgeBaseItem, VerifiedStatus } from '@/types';
import { Badge, Button, Card, Chip, ConfirmDialog, EmptyState, ErrorState, Input, LoadingState, Select, Sheet, Switch, Textarea, useToast } from '@/ui';

const audienceOptions = [
  { value: 'all', label: 'Все' },
  { value: 'students', label: 'Студенты' },
  { value: 'freshmen', label: 'Первокурсники' },
  { value: 'graduates', label: 'Выпускники' },
  { value: 'postgraduates', label: 'Магистранты' },
  { value: 'international', label: 'Иностранные студенты' },
  { value: 'local', label: 'Локальные студенты' },
];

const verifiedOptions: { value: VerifiedStatus; label: string }[] = [
  { value: 'draft', label: 'Черновик' },
  { value: 'verified', label: 'Проверено' },
  { value: 'outdated', label: 'Устарело' },
];
const verifiedTone: Record<VerifiedStatus, 'neutral' | 'success' | 'danger'> = { draft: 'neutral', verified: 'success', outdated: 'danger' };

interface FormState {
  title: string;
  content: string;
  category: string;
  sourceUrl: string;
  audience: string[];
  verifiedStatus: VerifiedStatus;
  published: boolean;
  actualUntil: string;
}

function toFormState(item?: KnowledgeBaseItem): FormState {
  return {
    title: item?.title || '',
    content: item?.content || '',
    category: item?.category || '',
    sourceUrl: item?.sourceUrl || '',
    audience: item?.audience || [],
    verifiedStatus: item?.verifiedStatus || 'draft',
    published: item?.published ?? false,
    actualUntil: item?.actualUntil ? item.actualUntil.slice(0, 10) : '',
  };
}

function toPayload(form: FormState): KnowledgeFormValues {
  return {
    title: form.title,
    content: form.content,
    category: form.category,
    sourceUrl: form.sourceUrl,
    audience: form.audience,
    verifiedStatus: form.verifiedStatus,
    published: form.published,
    actualUntil: form.actualUntil || null,
  };
}

export const KnowledgeBase = () => {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['admin-knowledge'], queryFn: fetchKnowledgeItems });

  const [search, setSearch] = useState('');
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeBaseItem | null>(null);
  const [form, setForm] = useState<FormState>(toFormState());
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeBaseItem | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return q ? data.filter((a) => a.title.toLowerCase().includes(q)) : data;
  }, [data, search]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-knowledge'] });

  const createMutation = useMutation({
    mutationFn: (payload: KnowledgeFormValues) => createKnowledgeItem(payload),
    onSuccess: () => { toast.success('Материал создан'); setSheetOpen(false); invalidate(); },
    onError: () => toast.error('Не удалось сохранить материал'),
  });
  const updateMutation = useMutation({
    mutationFn: (payload: KnowledgeFormValues) => updateKnowledgeItem(editing!.id, payload),
    onSuccess: () => { toast.success('Изменения сохранены'); setSheetOpen(false); invalidate(); },
    onError: () => toast.error('Не удалось сохранить изменения'),
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteKnowledgeItem(id),
    onSuccess: () => { toast.success('Материал удалён'); setDeleteTarget(null); invalidate(); },
    onError: () => toast.error('Не удалось удалить материал'),
  });

  const openCreate = () => { setEditing(null); setForm(toFormState()); setSheetOpen(true); };
  const openEdit = (item: KnowledgeBaseItem) => { setEditing(item); setForm(toFormState(item)); setSheetOpen(true); };
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = toPayload(form);
    if (editing) updateMutation.mutate(payload);
    else createMutation.mutate(payload);
  };
  const saving = createMutation.isPending || updateMutation.isPending;
  const toggleAudience = (value: string) => {
    setForm((f) => ({ ...f, audience: f.audience.includes(value) ? f.audience.filter((a) => a !== value) : [...f.audience, value] }));
  };

  if (isLoading) return <LoadingState label="Загружаем базу знаний…" />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">База знаний</h1>
          <p className="mt-1 text-sm text-ink-500">Проверенные материалы университета для студентов.</p>
        </div>
        <Button onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить материал</Button>
      </div>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Искать материал…"
          className="w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="h-6 w-6 text-ink-400" />}
          title={search ? 'Ничего не найдено' : 'Материалов пока нет'}
          action={!search && <Button size="sm" onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>Добавить материал</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((item) => (
            <Card key={item.id}>
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="line-clamp-2 text-sm font-semibold text-ink-900">{item.title}</h3>
                <div className="flex shrink-0 gap-1">
                  {item.sourceUrl && (
                    <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-700">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                  <button onClick={() => openEdit(item)} className="rounded-lg p-1.5 text-brand-600 hover:bg-brand-50" aria-label="Редактировать"><Edit className="h-4 w-4" /></button>
                  <button onClick={() => setDeleteTarget(item)} className="rounded-lg p-1.5 text-rose-600 hover:bg-rose-50" aria-label="Удалить"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
              <div className="mb-2 flex flex-wrap gap-1.5">
                <Badge tone="brand">{item.category}</Badge>
                <Badge tone={verifiedTone[item.verifiedStatus]}>{verifiedOptions.find((v) => v.value === item.verifiedStatus)?.label}</Badge>
                <Badge tone={item.published ? 'success' : 'neutral'}>{item.published ? 'Опубликовано' : 'Не опубликовано'}</Badge>
              </div>
              <p className="line-clamp-3 text-sm text-ink-600">{item.content}</p>
              <p className="mt-2 text-xs text-ink-400">Обновлено {new Date(item.updatedAt).toLocaleDateString('ru-RU')}</p>
            </Card>
          ))}
        </div>
      )}

      <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title={editing ? 'Редактировать материал' : 'Новый материал'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Заголовок" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input label="Ответственное подразделение" required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Учебный офис" />
          <Textarea label="Содержание" required rows={6} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
          <Input label="Ссылка на источник" value={form.sourceUrl} onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })} placeholder="https://…" />
          <div>
            <p className="mb-2 text-sm font-medium text-ink-800">Аудитория</p>
            <div className="flex flex-wrap gap-2">
              {audienceOptions.map((opt) => (
                <Chip key={opt.value} selected={form.audience.includes(opt.value)} onClick={() => toggleAudience(opt.value)}>{opt.label}</Chip>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Статус проверки" value={form.verifiedStatus} onChange={(e) => setForm({ ...form, verifiedStatus: e.target.value as VerifiedStatus })}>
              {verifiedOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </Select>
            <Input label="Актуально до" type="date" value={form.actualUntil} onChange={(e) => setForm({ ...form, actualUntil: e.target.value })} />
          </div>
          <Switch checked={form.published} onChange={(v) => setForm({ ...form, published: v })} label="Опубликовано" hint="Видно студентам, если также проверено" />

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
        title="Удалить материал?"
        description={deleteTarget ? `«${deleteTarget.title}» будет удалён безвозвратно.` : undefined}
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
