import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2 } from 'lucide-react';
import api from '@/api/client';
import { CareerRole } from '@/types';

const demandLevelLabels: Record<CareerRole['demandLevel'], string> = {
  high: 'Высокий спрос',
  medium: 'Средний спрос',
  low: 'Низкий спрос',
};

export const CareerRoles = () => {
  const [roles, setRoles] = useState<CareerRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    skills: '',
    avgSalary: '',
    demandLevel: 'medium' as 'high' | 'medium' | 'low',
    educationPath: '',
  });

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await api.get('/career-roles');
      setRoles(response.data);
    } catch (error) {
      console.error('Не удалось загрузить карьерные роли:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        skills: formData.skills.split(',').map((s) => s.trim()),
        educationPath: formData.educationPath.split('\n').filter((p) => p.trim()),
      };

      if (editingId) {
        await api.put(`/admin/career-roles/${editingId}`, data);
      } else {
        await api.post('/admin/career-roles', data);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({
        title: '',
        description: '',
        skills: '',
        avgSalary: '',
        demandLevel: 'medium',
        educationPath: '',
      });
      fetchRoles();
    } catch (error) {
      console.error('Не удалось сохранить карьерную роль:', error);
    }
  };

  const handleEdit = (role: CareerRole) => {
    setEditingId(role.id);
    setFormData({
      title: role.title,
      description: role.description,
      skills: role.skills.join(', '),
      avgSalary: role.avgSalary,
      demandLevel: role.demandLevel,
      educationPath: role.educationPath.join('\n'),
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить эту карьерную роль?')) return;
    try {
      await api.delete(`/admin/career-roles/${id}`);
      fetchRoles();
    } catch (error) {
      console.error('Не удалось удалить карьерную роль:', error);
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Карьерные роли</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Добавить роль
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Редактировать карьерную роль' : 'Новая карьерная роль'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  Средняя зарплата
                </label>
                <input
                  type="text"
                  value={formData.avgSalary}
                  onChange={(e) => setFormData({ ...formData, avgSalary: e.target.value })}
                  required
                  placeholder="например, 80 000 - 120 000 ₽"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Уровень спроса
              </label>
              <select
                value={formData.demandLevel}
                onChange={(e) => setFormData({ ...formData, demandLevel: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="high">Высокий</option>
                <option value="medium">Средний</option>
                <option value="low">Низкий</option>
              </select>
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
                Навыки через запятую
              </label>
              <input
                type="text"
                value={formData.skills}
                onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Образовательный путь по одному пункту в строке
              </label>
              <textarea
                value={formData.educationPath}
                onChange={(e) => setFormData({ ...formData, educationPath: e.target.value })}
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
                    description: '',
                    skills: '',
                    avgSalary: '',
                    demandLevel: 'medium',
                    educationPath: '',
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
        {roles.map((role) => (
          <div key={role.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{role.title}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm ${
                      role.demandLevel === 'high'
                        ? 'bg-green-100 text-green-800'
                        : role.demandLevel === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {demandLevelLabels[role.demandLevel] ?? role.demandLevel}
                  </span>
                </div>
                <p className="text-gray-600 mb-2 font-semibold">{role.avgSalary}</p>
                <p className="text-gray-700 mb-4">{role.description}</p>
                <div className="mb-3">
                  <p className="text-sm font-medium text-gray-700 mb-2">Навыки:</p>
                  <div className="flex gap-2 flex-wrap">
                    {role.skills.map((skill) => (
                      <span
                        key={skill}
                        className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-500">
                  Обновлено: {new Date(role.updatedAt).toLocaleDateString('ru-RU')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(role)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <Edit size={20} />
                </button>
                <button
                  onClick={() => handleDelete(role.id)}
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
