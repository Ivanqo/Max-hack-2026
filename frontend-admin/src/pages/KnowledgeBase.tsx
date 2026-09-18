import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2 } from 'lucide-react';
import api from '@/api/client';
import { KnowledgeBase as KB } from '@/types';

export const KnowledgeBase = () => {
  const [articles, setArticles] = useState<KB[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: '',
    tags: '',
  });

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      const response = await api.get('/knowledge');
      setArticles(response.data);
    } catch (error) {
      console.error('Не удалось загрузить материалы:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        tags: formData.tags.split(',').map((tag) => tag.trim()),
      };

      if (editingId) {
        await api.put(`/admin/knowledge/${editingId}`, data);
      } else {
        await api.post('/admin/knowledge', data);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({ title: '', content: '', category: '', tags: '' });
      fetchArticles();
    } catch (error) {
      console.error('Не удалось сохранить материал:', error);
    }
  };

  const handleEdit = (article: KB) => {
    setEditingId(article.id);
    setFormData({
      title: article.title,
      content: article.content,
      category: article.category,
      tags: article.tags.join(', '),
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить этот материал?')) return;
    try {
      await api.delete(`/admin/knowledge/${id}`);
      fetchArticles();
    } catch (error) {
      console.error('Не удалось удалить материал:', error);
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">База знаний</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Добавить материал
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Редактировать материал' : 'Новый материал'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Заголовок
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
                Категория
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Теги через запятую
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Содержание
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                required
                rows={6}
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
                  setFormData({ title: '', content: '', category: '', tags: '' });
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
        {articles.map((article) => (
          <div key={article.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">{article.title}</h3>
                <p className="text-gray-600 mb-4">{article.content.substring(0, 200)}...</p>
                <div className="flex gap-2 mb-2">
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                    {article.category}
                  </span>
                  {article.tags.map((tag) => (
                    <span
                      key={tag}
                      className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-gray-500">
                  Обновлено: {new Date(article.updatedAt).toLocaleDateString('ru-RU')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(article)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <Edit size={20} />
                </button>
                <button
                  onClick={() => handleDelete(article.id)}
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
