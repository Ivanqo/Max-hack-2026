import { useEffect, useState } from 'react';
import { AlertCircle, Plus, Edit, Trash2 } from 'lucide-react';
import api from '@/api/client';
import { Opportunity } from '@/types';

const opportunityTypeLabels: Record<Opportunity['type'], string> = {
  internship: 'Стажировка',
  job: 'Вакансия',
  project: 'Проект',
};

const opportunityStatusLabels: Record<Opportunity['status'], string> = {
  active: 'Активна',
  inactive: 'Неактивна',
};

export const Opportunities = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [savingError, setSavingError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: '',
    type: 'internship' as 'internship' | 'job' | 'project',
    location: '',
    remote: false,
    requirements: '',
    status: 'active' as 'active' | 'inactive',
  });

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const fetchOpportunities = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/admin/opportunities');
      setOpportunities(response.data);
    } catch (err: any) {
      setError('Не удалось загрузить возможности.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingError('');
    try {
      const data = {
        ...formData,
        requirements: formData.requirements.split('\n').filter((r) => r.trim()),
      };

      if (editingId) {
        await api.put(`/admin/opportunities/${editingId}`, data);
      } else {
        await api.post('/admin/opportunities', data);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({
        title: '',
        company: '',
        description: '',
        type: 'internship',
        location: '',
        remote: false,
        requirements: '',
        status: 'active',
      });
      fetchOpportunities();
    } catch (err: any) {
      setSavingError('Не удалось сохранить возможность.');
    }
  };

  const handleEdit = (opp: Opportunity) => {
    setEditingId(opp.id);
    setFormData({
      title: opp.title,
      company: opp.company,
      description: opp.description,
      type: opp.type,
      location: opp.location,
      remote: opp.remote,
      requirements: opp.requirements.join('\n'),
      status: opp.status,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить эту возможность?')) return;
    try {
      await api.delete(`/admin/opportunities/${id}`);
      fetchOpportunities();
    } catch (err: any) {
      setError('Не удалось удалить возможность.');
    }
  };

  if (loading) {
    return <div className="rounded-lg bg-white p-6 shadow">Загружаем возможности...</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-red-600" />
          <div>
            <h1 className="font-semibold text-red-900">Не удалось загрузить возможности</h1>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={fetchOpportunities}
              className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Повторить
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Возможности</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Добавить возможность
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Редактировать возможность' : 'Новая возможность'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {savingError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {savingError}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Название
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Компания
                </label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="internship">Стажировка</option>
                  <option value="job">Вакансия</option>
                  <option value="project">Проект</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Локация
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Статус
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="active">Активна</option>
                  <option value="inactive">Неактивна</option>
                </select>
              </div>
            </div>
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.remote}
                  onChange={(e) => setFormData({ ...formData, remote: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm font-medium text-gray-700">Удаленный формат</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Описание
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Требования по одному в строке
              </label>
              <textarea
                value={formData.requirements}
                onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                {editingId ? 'Обновить' : 'Создать'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({
                    title: '',
                    company: '',
                    description: '',
                    type: 'internship',
                    location: '',
                    remote: false,
                    requirements: '',
                    status: 'active',
                  });
                }}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Отменить
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-6">
        {opportunities.map((opp) => (
          <div key={opp.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{opp.title}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm ${
                      opp.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {opportunityStatusLabels[opp.status] ?? opp.status}
                  </span>
                </div>
                <p className="text-gray-600 mb-2">{opp.company}</p>
                <p className="text-gray-700 mb-4">{opp.description}</p>
                <div className="flex gap-2 flex-wrap mb-2">
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                    {opportunityTypeLabels[opp.type] ?? opp.type}
                  </span>
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                    {opp.location}
                  </span>
                  {opp.remote && (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                      Удаленно
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500">
                  Обновлено: {new Date(opp.updatedAt).toLocaleDateString('ru-RU')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(opp)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <Edit size={20} />
                </button>
                <button
                  onClick={() => handleDelete(opp.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
